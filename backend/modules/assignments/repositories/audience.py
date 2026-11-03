from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from modules.assignments.models import AudienceMember


def member_ids(assignment_id: UUID) -> list[UUID]:
    """In the order they were added."""
    rows = AudienceMember.objects.filter(assignment_id=assignment_id).order_by("added_at")
    return list(rows.values_list("student_id", flat=True))


def add_members(assignment_id: UUID, student_ids: Sequence[UUID], *, now: datetime) -> None:
    AudienceMember.objects.bulk_create(
        [
            AudienceMember(assignment_id=assignment_id, student_id=sid, added_at=now)
            for sid in student_ids
        ],
        ignore_conflicts=True,
    )


def remove_members(assignment_id: UUID, student_ids: Sequence[UUID]) -> None:
    AudienceMember.objects.filter(assignment_id=assignment_id, student_id__in=student_ids).delete()


def replace_members(assignment_id: UUID, student_ids: Sequence[UUID], *, now: datetime) -> None:
    AudienceMember.objects.filter(assignment_id=assignment_id).exclude(
        student_id__in=student_ids
    ).delete()
    add_members(assignment_id, student_ids, now=now)


def members_by_assignment(assignment_ids: Sequence[UUID]) -> dict[UUID, set[UUID]]:
    members: dict[UUID, set[UUID]] = {aid: set() for aid in assignment_ids}
    rows = AudienceMember.objects.filter(assignment_id__in=assignment_ids).values_list(
        "assignment_id", "student_id"
    )
    for assignment_id, student_id in rows:
        members[assignment_id].add(student_id)
    return members
