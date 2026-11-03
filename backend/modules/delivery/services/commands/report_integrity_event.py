from dataclasses import dataclass, replace
from datetime import datetime
from uuid import UUID

from django.db import transaction

from core.context import Ctx
from core.errors import NotFound
from modules.assignments import public as assignments
from modules.delivery.domain.attempt import is_takeover
from modules.delivery.domain.errors import AttemptTakenOver
from modules.delivery.domain.integrity import WarningAction, decide_warning, warning_action
from modules.delivery.domain.values import IntegrityKind
from modules.delivery.policies import ensure_active_student
from modules.delivery.repositories import attempts, integrity_events
from modules.delivery.services.attempt_views import AttemptClockView, clock_view
from modules.delivery.services.commands.end_attempt import end_attempt
from modules.delivery.services.live import LiveAttempt, open_live


@dataclass(frozen=True, slots=True)
class IntegrityReport:
    event_id: UUID
    kind: IntegrityKind
    # Device time corrected by the server-clock offset
    left_at: datetime
    # Still away after the grace period: this departure may cost a warning
    beyond_grace: bool
    returned_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class IntegrityAck:
    counted: bool
    warning_count: int
    max_warnings: int
    action: WarningAction
    clock: AttemptClockView


def report_integrity_event(
    ctx: Ctx, *, attempt_id: UUID, client_id: UUID | None, report: IntegrityReport
) -> IntegrityAck:
    """P-06 (domain_model.md §5.8): record a departure, and once it outlasts the grace period
    count it, at most once per event however often it's sent (E-20). The attempt is locked,
    so two tabs reporting at once can't both count (F-29). Reaching the limit ends the
    attempt. After the end, reports are ignored (E-21)."""
    student_id = ensure_active_student(ctx.actor)
    counted = False
    with transaction.atomic():
        attempt = attempts.lock_for_student(attempt_id, student_id)
        terms = assignments.get_sitting_terms(attempt.assignment_id, student_id)
        live = open_live(ctx, attempt, terms)
        taken_over = live.attempt.in_progress and is_takeover(live.attempt, client_id)
        if live.attempt.in_progress and not taken_over:
            live, counted = _record(ctx, live, report, terms.integrity)
    if taken_over:
        raise AttemptTakenOver()
    return IntegrityAck(
        counted=counted,
        warning_count=live.attempt.warning_count,
        max_warnings=terms.integrity.max_warnings,
        action=warning_action(in_progress=live.attempt.in_progress, counted=counted),
        clock=clock_view(live, now=ctx.now),
    )


def _record(
    ctx: Ctx, live: LiveAttempt, report: IntegrityReport, integrity: assignments.Integrity
) -> tuple[LiveAttempt, bool]:
    attempt = live.attempt
    stored = integrity_events.find(report.event_id)
    if stored is not None and stored[0] != attempt.id:
        raise NotFound("event")
    if stored is None:
        integrity_events.insert_event(
            report.event_id, attempt.id, kind=report.kind, left_at=report.left_at, now=ctx.now
        )
    if report.returned_at is not None:
        integrity_events.mark_returned(report.event_id, returned_at=report.returned_at)
    already = stored is not None and stored[1]
    decision = decide_warning(
        warning_count=attempt.warning_count,
        max_warnings=integrity.max_warnings,
        action=integrity.action,
        already_counted=already,
        beyond_grace=report.beyond_grace,
    )
    if decision.counts_now:
        integrity_events.mark_counted(report.event_id)
        attempts.set_warning_count(attempt.id, decision.warning_count)
        attempt = replace(attempt, warning_count=decision.warning_count)
    if decision.ends_with is not None:
        attempt = end_attempt(attempt, reason=decision.ends_with, ended_at=ctx.now, now=ctx.now)
    return replace(live, attempt=attempt), already or decision.counts_now
