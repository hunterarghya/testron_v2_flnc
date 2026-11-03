from uuid import UUID

from django.db import transaction

from core.context import Ctx
from modules.assignments import public as assignments
from modules.delivery.domain.errors import AttemptEnded
from modules.delivery.domain.values import EndReason
from modules.delivery.policies import ensure_teacher
from modules.delivery.repositories import attempt_rows, attempts
from modules.delivery.repositories.attempt_rows import AttemptRow
from modules.delivery.services.commands.end_attempt import end_attempt
from modules.delivery.services.live import open_live


def force_submit_attempt(ctx: Ctx, *, attempt_id: UUID) -> AttemptRow:
    """T-10 Force submit [G-1]: the teacher ends one student's sitting now, and it is graded.
    One that has already ended (or just ran out of time) is attempt_ended, and that ending
    is kept."""
    ensure_teacher(ctx.actor)
    with transaction.atomic():
        attempt = attempts.lock_any(attempt_id)
        terms = assignments.get_sitting_terms(attempt.assignment_id, attempt.student_id)
        live = open_live(ctx, attempt, terms)
        if live.attempt.in_progress:
            end_attempt(
                live.attempt, reason=EndReason.FORCE_SUBMITTED, ended_at=ctx.now, now=ctx.now
            )
    if not live.attempt.in_progress:
        raise AttemptEnded(ended_at=live.attempt.ended_at, end_reason=live.attempt.end_reason)
    return attempt_rows.row_of(attempt_id)
