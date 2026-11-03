from datetime import datetime
from uuid import UUID

from core.context import Ctx
from modules.assignments.repositories import assignments
from modules.assignments.services.changes import lock_started


def mark_assignment_ended(ctx: Ctx, *, assignment_id: UUID) -> datetime:
    """D-04's first half: the assignment ends now for everyone (domain_model.md §5.5), in the
    caller's transaction. Ending twice keeps the first instant. Delivery then ends the
    sittings still running at that instant (end_for_everyone)."""
    record = lock_started(ctx, assignment_id)
    if record.timeline.ended_at is not None:
        return record.timeline.ended_at
    assignments.mark_ended(assignment_id, now=ctx.now)
    return ctx.now
