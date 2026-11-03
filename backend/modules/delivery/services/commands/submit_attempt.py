from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from django.db import transaction

from core.context import Ctx
from modules.assignments import public as assignments
from modules.delivery.domain.attempt import is_takeover
from modules.delivery.domain.errors import AttemptTakenOver
from modules.delivery.domain.values import EndReason
from modules.delivery.policies import ensure_active_student
from modules.delivery.repositories import attempts
from modules.delivery.services.commands.end_attempt import end_attempt
from modules.delivery.services.live import open_live


@dataclass(frozen=True, slots=True)
class Ending:
    end_reason: EndReason
    ended_at: datetime
    # True only when the result shows at once (auto-publish); results come in Phase 6
    result_available: bool = False


def submit_attempt(ctx: Ctx, *, attempt_id: UUID, client_id: UUID | None) -> Ending:
    """P-07 Submit (domain_model.md §5.5): ended and graded together. Safe to repeat: an
    attempt already ended, by submitting or by its deadline, returns that same ending."""
    student_id = ensure_active_student(ctx.actor)
    with transaction.atomic():
        attempt = attempts.lock_for_student(attempt_id, student_id)
        terms = assignments.get_sitting_terms(attempt.assignment_id, student_id)
        ended = open_live(ctx, attempt, terms).attempt
        taken_over = ended.in_progress and is_takeover(ended, client_id)
        if ended.in_progress and not taken_over:
            ended = end_attempt(ended, reason=EndReason.SUBMITTED, ended_at=ctx.now, now=ctx.now)
    if taken_over or ended.end_reason is None or ended.ended_at is None:
        raise AttemptTakenOver()
    return Ending(end_reason=ended.end_reason, ended_at=ended.ended_at)
