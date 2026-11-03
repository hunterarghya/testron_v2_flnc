from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from django.db import transaction

from core.context import Ctx
from core.errors import ConfirmationMismatch
from modules.assignments import public as assignments
from modules.delivery.policies import ensure_teacher
from modules.delivery.repositories import attempts, stage_progress
from modules.delivery.services.live import bring_up_to_date

CONFIRMATION = "END"


@dataclass(frozen=True, slots=True)
class EndedForEveryone:
    ended_at: datetime
    # Sittings that were still running and ended now
    ended_attempts: int


def end_for_everyone(ctx: Ctx, *, assignment_id: UUID, confirm: str) -> EndedForEveryone:
    """D-04 (domain_model.md §5.5, E-31): the teacher types END; the assignment ends now, and
    every sitting still running ends at that instant and is graded, in one transaction,
    retakes included. A sitting whose own time ran out before ends at its own deadline.
    Saves racing it are either in before the end or refused. Safe to repeat."""
    ensure_teacher(ctx.actor)
    if confirm.strip() != CONFIRMATION:
        raise ConfirmationMismatch()
    with transaction.atomic():
        ended_at = assignments.mark_assignment_ended(ctx, assignment_id=assignment_id)
        frame = assignments.get_monitor_frame(ctx, assignment_id=assignment_id)
        running = attempts.lock_running_of(assignment_id, skip_locked=False)
        stages = stage_progress.stages_by_attempt([a.id for a in running])
        ended = [
            bring_up_to_date(ctx, a, frame.terms_for(a.student_id), stages[a.id]) for a in running
        ]
    return EndedForEveryone(ended_at, sum(not live.attempt.in_progress for live in ended))
