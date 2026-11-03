"""A stage move by the student: lock the attempt, catch up, check the device, apply the move,
store it, and answer with the whole attempt (the next stage's questions). Shared by
move_to_next_stage and return_to_stage."""

from collections.abc import Callable
from dataclasses import replace
from uuid import UUID

from django.db import transaction

from core.context import Ctx
from modules.assignments import public as assignments
from modules.delivery.domain.attempt import write_refusal
from modules.delivery.domain.paper import PaperView
from modules.delivery.domain.stages import Progress
from modules.delivery.policies import ensure_active_student
from modules.delivery.repositories import attempts, responses, stage_progress
from modules.delivery.services.attempt_views import AttemptStateView, state_view
from modules.delivery.services.live import LiveAttempt, open_live, paper_of

# Given the attempt brought up to date and its paper, the progress after the move
Move = Callable[[LiveAttempt, PaperView], Progress]


def move_stage(
    ctx: Ctx, *, attempt_id: UUID, client_id: UUID | None, move: Move
) -> AttemptStateView:
    student_id = ensure_active_student(ctx.actor)
    with transaction.atomic():
        attempt = attempts.lock_for_student(attempt_id, student_id)
        terms = assignments.get_sitting_terms(attempt.assignment_id, student_id)
        live = open_live(ctx, attempt, terms)
        paper = paper_of(attempt)
        refusal = write_refusal(live.attempt, client_id)
        if refusal is None:
            live = _apply(ctx, live, move(live, paper))
        stored = responses.of_attempt(attempt_id)
    if refusal is not None:
        raise refusal
    return state_view(live, terms=terms, paper=paper, stored=stored, now=ctx.now)


def _apply(ctx: Ctx, live: LiveAttempt, moved: Progress) -> LiveAttempt:
    attempt = live.attempt
    stage_progress.save_changes(attempt.id, live.progress.stages, moved.stages)
    attempts.save_position(attempt.id, current=moved.current, furthest=moved.furthest, now=ctx.now)
    position = replace(
        attempt, current_stage_index=moved.current, furthest_stage_index=moved.furthest
    )
    return replace(live, attempt=position, progress=moved, notice=None)
