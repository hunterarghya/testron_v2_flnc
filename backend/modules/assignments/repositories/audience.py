from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from django.db.models import Count

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


def counts(assignment_ids: Sequence[UUID]) -> dict[UUID, int]:
    rows = (
        AudienceMember.objects.filter(assignment_id__in=assignment_ids)
        .values_list("assignment_id")
        .annotate(n=Count("student_id"))
    )
    return dict(rows.values_list("assignment_id", "n"))
