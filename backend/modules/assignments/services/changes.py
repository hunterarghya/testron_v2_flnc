"""What every change to an assignment shares: the teacher check, one change at a time, and
the rule on what may still change (domain_model.md §3.5 #5-6)."""

from collections.abc import Collection
from uuid import UUID

from core.context import Ctx
from modules.assignments.domain.assignment import AssignmentRecord
from modules.assignments.domain.editing import ensure_editable
from modules.assignments.policies import ensure_teacher
from modules.assignments.repositories import assignments
from modules.assignments.services.views import is_started


def lock_for_change(ctx: Ctx, assignment_id: UUID, fields: Collection[str]) -> AssignmentRecord:
    """Lock the assignment for this transaction, once these fields may still change. No
    fields: only that it isn't cancelled (adding or removing students)."""
    ensure_teacher(ctx.actor)
    record = assignments.lock_record(assignment_id)
    ensure_editable(
        fields,
        cancelled=record.timeline.cancelled_at is not None,
        started=is_started(record, now=ctx.now),
    )
    return record
