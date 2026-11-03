from collections import defaultdict
from collections.abc import Sequence
from uuid import UUID

from modules.assignments.domain.lifecycle import ExtensionGrant
from modules.assignments.models import Extension


def grants_by_assignment(assignment_ids: Sequence[UUID]) -> dict[UUID, list[ExtensionGrant]]:
    grants: dict[UUID, list[ExtensionGrant]] = defaultdict(list)
    rows = Extension.objects.filter(assignment_id__in=assignment_ids).values_list(
        "assignment_id", "seconds", "student_id", "stage_index"
    )
    for assignment_id, seconds, student_id, stage_index in rows:
        grants[assignment_id].append(ExtensionGrant(seconds, student_id is None, stage_index))
    return grants
