from collections import defaultdict
from collections.abc import Sequence
from uuid import UUID

from django.db.models import Q, QuerySet

from modules.assignments.domain.lifecycle import ExtensionGrant
from modules.assignments.models import Extension


def grants_by_assignment(assignment_ids: Sequence[UUID]) -> dict[UUID, list[ExtensionGrant]]:
    return _grouped(Extension.objects.filter(assignment_id__in=assignment_ids))


def grants_for_student(
    assignment_ids: Sequence[UUID], student_id: UUID
) -> dict[UUID, list[ExtensionGrant]]:
    """Only those that apply to this student: for everyone, or for them (§5.2)."""
    mine = Q(student__isnull=True) | Q(student_id=student_id)
    return _grouped(Extension.objects.filter(mine, assignment_id__in=assignment_ids))


def _grouped(rows: QuerySet[Extension]) -> dict[UUID, list[ExtensionGrant]]:
    grants: dict[UUID, list[ExtensionGrant]] = defaultdict(list)
    values = rows.values_list("assignment_id", "seconds", "student_id", "stage_index")
    for assignment_id, seconds, student_id, stage_index in values:
        grants[assignment_id].append(ExtensionGrant(seconds, student_id is None, stage_index))
    return grants
