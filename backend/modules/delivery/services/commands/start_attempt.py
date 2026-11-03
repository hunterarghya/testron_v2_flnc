import secrets
from dataclasses import dataclass, replace
from datetime import timedelta
from uuid import UUID

from django.db import transaction

from core.context import Ctx
from core.errors import RateLimited
from core.ids import uuid7
from core.rate_limit import RateLimit, hit
from modules.assignments import public as assignments
from modules.delivery.domain.errors import NoAttemptsLeft, PasswordIncorrect, PasswordRequired
from modules.delivery.domain.gate import GateStatus, ensure_may_start
from modules.delivery.domain.paper import read_paper
from modules.delivery.domain.plan import build_plan, plan_json
from modules.delivery.domain.stages import opening
from modules.delivery.policies import ensure_active_student
from modules.delivery.repositories import attempts, stage_progress
from modules.delivery.services.attempt_views import AttemptStateView, state_view
from modules.delivery.services.commands.finalize_expired import finalize_expired
from modules.delivery.services.gate_views import entry_times
from modules.delivery.services.live import LiveAttempt, clock_for
from modules.delivery.services.opening import open_attempt

# 5 tries, then a 30 s wait, per student per assignment (E-25)
PASSWORD_TRIES = RateLimit(limit=5, window=timedelta(minutes=10), block=timedelta(seconds=30))


@dataclass(frozen=True, slots=True)
class Started:
    view: AttemptStateView
    # False: the attempt already in progress was resumed (E-02)
    created: bool


def start_attempt(
    ctx: Ctx, *, assignment_id: UUID, password: str | None, client_id: UUID | None
) -> Started:
    """P-02 -> P-03 (domain_model.md §5.4): the checks in order, the first failure wins; then a
    new sitting in one transaction. One in progress is resumed instead, with no password."""
    student_id = ensure_active_student(ctx.actor)
    mine = assignments.get_student_assignment(assignment_id, student_id)
    # A sitting whose time ran out ends first, so it isn't resumed
    sittings = finalize_expired(ctx, student_id, [mine])[assignment_id]
    sittings = replace(sittings, has_grant=mine.has_unused_grant)
    gate = ensure_may_start(entry_times(mine), sittings, now=ctx.now)
    if sittings.in_progress_attempt_id is not None and gate.status is GateStatus.IN_PROGRESS:
        view = open_attempt(ctx, sittings.in_progress_attempt_id, student_id, client_id=client_id)
        return Started(view, created=False)
    _check_password(ctx, mine, student_id, password)
    return _begin(ctx, mine, student_id, take=sittings.used + 1, granted=gate.granted)


def _check_password(
    ctx: Ctx, mine: assignments.StudentAssignment, student_id: UUID, password: str | None
) -> None:
    """Check 7. Every try counts, before the use case's transaction (core.rate_limit)."""
    if not mine.has_password:
        return
    if not password:
        raise PasswordRequired()
    tries = hit(f"test-password:{mine.assignment_id}:{student_id}", PASSWORD_TRIES, now=ctx.now)
    if not tries.allowed:
        raise RateLimited(retry_after_s=tries.retry_after_s)
    if not assignments.is_password_correct(mine.assignment_id, password):
        raise PasswordIncorrect(tries_left=tries.remaining)


def _begin(
    ctx: Ctx, mine: assignments.StudentAssignment, student_id: UUID, *, take: int, granted: bool
) -> Started:
    paper = read_paper(assignments.get_paper_content(mine.assignment_id))
    seed = secrets.randbits(63)
    plan = build_plan(paper, seed)
    # Shared by everyone on a common clock (always known once the gate lets them in);
    # otherwise, and for a granted sitting, the attempt's own start (§5.1)
    shared = mine.window.common_clock and not granted
    anchor_at = (mine.entry.anchor_at if shared else None) or ctx.now
    clock = clock_for(mine, anchor_at=anchor_at, durations_s=plan.durations_s, granted=granted)
    progress = opening(clock, now=ctx.now)
    new = attempts.NewAttempt(
        assignment_id=mine.assignment_id,
        student_id=student_id,
        take_number=take,
        is_granted=granted,
        started_at=ctx.now,
        anchor_at=anchor_at,
        seed=seed,
        plan=plan_json(plan),
        current_stage_index=progress.current,
        max_score=mine.paper.total_marks,
        active_client_id=uuid7(),
    )
    with transaction.atomic():
        attempt = attempts.insert_attempt(new)
        if attempt is None:
            return _started_meanwhile(ctx, mine.assignment_id, student_id)
        stage_progress.insert_stages(attempt.id, progress.stages)
        if granted and not assignments.consume_retake_grant(
            mine.assignment_id, student_id, attempt_id=attempt.id
        ):
            raise NoAttemptsLeft()
        live = LiveAttempt(attempt, clock, progress)
    view = state_view(live, terms=mine, paper=paper, stored={}, now=ctx.now)
    return Started(view, created=True)


def _started_meanwhile(ctx: Ctx, assignment_id: UUID, student_id: UUID) -> Started:
    """A start at the same instant won (E-01): return its attempt, keeping its device id."""
    running = attempts.lock_in_progress(assignment_id, student_id)
    if running is None:
        raise NoAttemptsLeft()
    view = open_attempt(ctx, running.id, student_id, client_id=None, take_over=False)
    return Started(view, created=False)
