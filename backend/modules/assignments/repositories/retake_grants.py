from collections.abc import Sequence
from uuid import UUID

from modules.assignments.models import RetakeGrant


def with_unused_grant(student_id: UUID, assignment_ids: Sequence[UUID]) -> set[UUID]:
    """The assignments where the student has a retake grant not used yet (§5.7)."""
    rows = RetakeGrant.objects.filter(
        student_id=student_id, assignment_id__in=assignment_ids, consumed_by_attempt_id__isnull=True
    ).values_list("assignment_id", flat=True)
    return set(rows)
