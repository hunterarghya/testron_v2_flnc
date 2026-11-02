"""The teacher's Students table (T-14): the page, the total, and the page's groups: 3 queries."""

from uuid import UUID

from django.db.models import Exists, OuterRef, Q, QuerySet

from core.context import StudentStatus
from modules.students.domain.values import StudentRow
from modules.students.models import PerformanceShare, Student
from modules.students.repositories.memberships import group_names_by_student


def list_students(
    status: StudentStatus, *, search: str | None, group_id: UUID | None, offset: int, limit: int
) -> tuple[list[StudentRow], int]:
    students = _filtered(status, search, group_id)
    page = (
        students.select_related("user")
        .annotate(shared=Exists(PerformanceShare.objects.filter(student_id=OuterRef("user_id"))))
        .order_by(*_ordering(status))[offset : offset + limit]
    )
    found = list(page)
    names = group_names_by_student([student.user_id for student in found])
    return [_row(student, names[student.user_id]) for student in found], students.count()


def _filtered(
    status: StudentStatus, search: str | None, group_id: UUID | None
) -> QuerySet[Student]:
    # The account (name, email) is identity's table; it is only read here, never written
    students = Student.objects.filter(status=status)
    if search:
        students = students.filter(
            Q(user__name__icontains=search) | Q(user__email__icontains=search)
        )
    if group_id:
        students = students.filter(memberships__group_id=group_id)
    return students


def _ordering(status: StudentStatus) -> tuple[str, ...]:
    # Pending: the newest request first; every other tab: by name
    if status is StudentStatus.PENDING:
        return ("-requested_at", "user_id")
    return ("user__name", "user_id")


def _row(student: Student, group_names: list[str]) -> StudentRow:
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
        group_names=group_names,
    )
