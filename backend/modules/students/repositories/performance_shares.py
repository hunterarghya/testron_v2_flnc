from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from modules.students.models import PerformanceShare


def shared_ids(student_ids: Sequence[UUID]) -> set[UUID]:
    return set(
        PerformanceShare.objects.filter(student_id__in=student_ids).values_list(
            "student_id", flat=True
        )
    )


def share(student_ids: Sequence[UUID], *, now: datetime) -> None:
    PerformanceShare.objects.bulk_create(
        [PerformanceShare(student_id=sid, shared_since=now) for sid in student_ids],
        ignore_conflicts=True,
    )


def unshare(student_ids: Sequence[UUID]) -> None:
    PerformanceShare.objects.filter(student_id__in=student_ids).delete()
