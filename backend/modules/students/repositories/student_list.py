"""The teacher's Students table (T-14): one query for the page, one for the total."""

from django.db.models import Exists, OuterRef, Q, QuerySet

from core.context import StudentStatus
from modules.students.domain.values import StudentRow
from modules.students.models import PerformanceShare, Student


def list_students(
    status: StudentStatus, *, search: str | None, offset: int, limit: int
) -> tuple[list[StudentRow], int]:
    students = _filtered(status, search)
    page = (
        students.select_related("user")
        .annotate(shared=Exists(PerformanceShare.objects.filter(student_id=OuterRef("user_id"))))
        .order_by(*_ordering(status))[offset : offset + limit]
    )
    return [_row(student) for student in page], students.count()


def _filtered(status: StudentStatus, search: str | None) -> QuerySet[Student]:
    # The account (name, email) is identity's table; it is only read here, never written
    students = Student.objects.filter(status=status)
    if search:
        students = students.filter(
            Q(user__name__icontains=search) | Q(user__email__icontains=search)
        )
    return students


def _ordering(status: StudentStatus) -> tuple[str, ...]:
    # Pending: the newest request first; every other tab: by name
    if status is StudentStatus.PENDING:
        return ("-requested_at", "user_id")
    return ("user__name", "user_id")


def _row(student: Student) -> StudentRow:
    return StudentRow(
        id=student.user_id,
        name=student.user.name,
        email=student.user.email,
        status=StudentStatus(student.status),
        joined_at=student.user.created_at,
        requested_at=student.requested_at,
        decided_at=student.decided_at,
        deactivated_at=student.deactivated_at,
        performance_shared=bool(getattr(student, "shared", False)),
    )
