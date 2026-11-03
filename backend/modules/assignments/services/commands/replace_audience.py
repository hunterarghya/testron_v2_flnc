from collections.abc import Sequence
from uuid import UUID

from django.db import transaction

from core.context import Ctx
from modules.assignments.repositories import assignments, audience
from modules.assignments.services.changes import lock_for_change
from modules.assignments.services.inputs import active_audience
from modules.assignments.services.views import AssignmentDetail, assignment_detail


def replace_audience(
    ctx: Ctx, *, assignment_id: UUID, student_ids: Sequence[UUID]
) -> AssignmentDetail:
    """A new list of students, before the start only (domain_model.md §3.5 #3): at least one,
    all ACTIVE. Students already in keep the time they were added."""
    with transaction.atomic():
        lock_for_change(ctx, assignment_id, ["audience"])
        audience.replace_members(assignment_id, active_audience(student_ids), now=ctx.now)
    return assignment_detail(assignments.get_record(assignment_id), now=ctx.now)
