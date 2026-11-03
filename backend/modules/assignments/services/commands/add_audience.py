from collections.abc import Sequence
from uuid import UUID

from django.db import transaction

from core.bulk import BulkOutcome
from core.context import Ctx
from modules.assignments.domain.audience import plan_additions
from modules.assignments.repositories import audience
from modules.assignments.services.changes import lock_for_change
from modules.students import public as students


def add_audience(ctx: Ctx, *, assignment_id: UUID, student_ids: Sequence[UUID]) -> BulkOutcome:
    """Add students, even after the start (domain_model.md §3.5 #3). Only ACTIVE students not
    already in are added; the rest are skipped with a reason."""
    with transaction.atomic():
        lock_for_change(ctx, assignment_id, [])
        statuses = {s.student_id: s.status for s in students.describe_students(student_ids)}
        outcome = plan_additions(student_ids, statuses, set(audience.member_ids(assignment_id)))
        audience.add_members(assignment_id, outcome.applied, now=ctx.now)
    return outcome
