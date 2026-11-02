from datetime import datetime
from uuid import UUID

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
