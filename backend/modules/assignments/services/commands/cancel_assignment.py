from uuid import UUID

from django.db import transaction

from core.context import Ctx
from modules.assignments.domain.editing import ensure_cancellable
from modules.assignments.policies import ensure_teacher
from modules.assignments.repositories import assignments, attempt_facts


def cancel_assignment(ctx: Ctx, *, assignment_id: UUID) -> None:
    """Call the assignment off while no one has begun and before Start (D-08,
    domain_model.md §3.5 #6). It stays, read-only, shown as Cancelled."""
    ensure_teacher(ctx.actor)
    with transaction.atomic():
        record = assignments.lock_record(assignment_id)
        has_attempts = bool(attempt_facts.students_with_attempts(assignment_id))
        ensure_cancellable(record.timeline, has_attempts=has_attempts)
        assignments.mark_cancelled(assignment_id, now=ctx.now)
