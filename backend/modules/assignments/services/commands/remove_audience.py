from collections.abc import Sequence
from uuid import UUID

from django.db import transaction

from core.bulk import BulkOutcome
from core.context import Ctx
from modules.assignments.domain.audience import plan_removals
from modules.assignments.repositories import attempt_facts, audience
from modules.assignments.services.changes import lock_for_change


def remove_audience(ctx: Ctx, *, assignment_id: UUID, student_ids: Sequence[UUID]) -> BulkOutcome:
    """Remove students who haven't begun, at any time (domain_model.md §3.5 #3, E-11). If any
    of them has begun, nobody is removed."""
    with transaction.atomic():
        lock_for_change(ctx, assignment_id, [])
        outcome = plan_removals(
            student_ids,
            set(audience.member_ids(assignment_id)),
            attempt_facts.students_with_attempts(assignment_id),
        )
        audience.remove_members(assignment_id, outcome.applied)
    return outcome
