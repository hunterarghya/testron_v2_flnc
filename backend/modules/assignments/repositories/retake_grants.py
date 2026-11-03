from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from modules.assignments.models import RetakeGrant


def with_unused_grant(student_id: UUID, assignment_ids: Sequence[UUID]) -> set[UUID]:
    """The assignments where the student has a retake grant not used yet (§5.7)."""
    rows = RetakeGrant.objects.filter(
        student_id=student_id, assignment_id__in=assignment_ids, consumed_by_attempt__isnull=True
    ).values_list("assignment_id", flat=True)
    return set(rows)


def consume_oldest(assignment_id: UUID, student_id: UUID, *, attempt_id: UUID) -> bool:
    """Use the oldest unused grant for this sitting (domain_model.md §3.6 #2); False if none."""
    oldest = (
        RetakeGrant.objects.select_for_update()
        .filter(
            assignment_id=assignment_id, student_id=student_id, consumed_by_attempt__isnull=True
        )
        .order_by("granted_at", "id")
        .values_list("id", flat=True)
        .first()
    )
    if oldest is None:
        return False
    RetakeGrant.objects.filter(pk=oldest).update(consumed_by_attempt_id=attempt_id)
    return True


def insert_grants(assignment_id: UUID, student_ids: Sequence[UUID], *, now: datetime) -> None:
    RetakeGrant.objects.bulk_create(
        [
            RetakeGrant(assignment_id=assignment_id, student_id=s, granted_at=now)
            for s in student_ids
        ]
    )
