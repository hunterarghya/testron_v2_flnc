from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from django.db import connection

from core.context import StudentStatus
from core.db.locking import for_update
from core.errors import NotFound
from modules.students.models import PerformanceShare, Student


def insert_student(user_id: UUID, *, status: StudentStatus) -> None:
    Student.objects.create(user_id=user_id, status=status)


def get_status(user_id: UUID) -> StudentStatus:
    status = Student.objects.filter(user_id=user_id).values_list("status", flat=True).first()
    if status is None:
        raise NotFound("student")
    return StudentStatus(status)


def get_status_for_update(user_id: UUID) -> StudentStatus:
    status = for_update(Student.objects.filter(user_id=user_id)).values_list("status", flat=True)
    found = status.first()
    if found is None:
        raise NotFound("student")
    return StudentStatus(found)


def mark_pending(user_id: UUID, *, now: datetime) -> None:
    Student.objects.filter(user_id=user_id).update(status=StudentStatus.PENDING, requested_at=now)


def is_performance_shared(user_id: UUID) -> bool:
    return PerformanceShare.objects.filter(student_id=user_id).exists()


def find_status(user_id: UUID) -> StudentStatus | None:
    """The student's admission status, or None for an account that isn't a student."""
    status = Student.objects.filter(user_id=user_id).values_list("status", flat=True).first()
    return StudentStatus(status) if status is not None else None


def lock_statuses_for_update(user_ids: Sequence[UUID]) -> dict[UUID, StudentStatus]:
    """The statuses of these students, locked in id order so two bulk actions can't deadlock."""
    rows = for_update(Student.objects.filter(user_id__in=user_ids).order_by("user_id"))
    return {
        user_id: StudentStatus(status) for user_id, status in rows.values_list("user_id", "status")
    }


def mark_approved(user_ids: Sequence[UUID], *, now: datetime) -> None:
    Student.objects.filter(user_id__in=user_ids).update(status=StudentStatus.ACTIVE, decided_at=now)


def mark_declined(user_ids: Sequence[UUID], *, now: datetime) -> None:
    Student.objects.filter(user_id__in=user_ids).update(
        status=StudentStatus.DECLINED, decided_at=now
    )


def mark_deactivated(user_ids: Sequence[UUID], *, now: datetime) -> None:
    Student.objects.filter(user_id__in=user_ids).update(
        status=StudentStatus.DEACTIVATED, deactivated_at=now
    )


def mark_reactivated(user_ids: Sequence[UUID], *, now: datetime) -> None:
    Student.objects.filter(user_id__in=user_ids).update(
        status=StudentStatus.ACTIVE, deactivated_at=None
    )


def mark_anonymized(user_id: UUID, *, number: int, now: datetime) -> None:
    Student.objects.filter(user_id=user_id).update(
        status=StudentStatus.ANONYMIZED, anonymized_at=now, anonymized_number=number
    )
    PerformanceShare.objects.filter(student_id=user_id).delete()


def next_anonymized_number() -> int:
    """1, 2, 3 … never reused, even if a transaction rolls back (a Postgres sequence)."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT nextval('students_anonymized_seq')")
        number: int = cursor.fetchone()[0]
    return number
