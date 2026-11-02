from uuid import UUID

from core.context import Ctx, StudentStatus
from core.errors import NotFound
from modules.students.domain.values import StudentDetail
from modules.students.policies import ensure_teacher
from modules.students.repositories import memberships, student_list

# The statuses the Students table lists. Unverified sign-ups and deleted students have no page.
_SHOWN = (
    StudentStatus.ACTIVE,
    StudentStatus.PENDING,
    StudentStatus.DECLINED,
    StudentStatus.DEACTIVATED,
)


def get_student(ctx: Ctx, *, student_id: UUID) -> StudentDetail:
    """One student's page for the teacher (T-15): details, groups and sharing. Their attempts
    and performance join in Phases 6 and 7."""
    ensure_teacher(ctx.actor)
    row = student_list.find_student_row(student_id, statuses=_SHOWN)
    if row is None:
        raise NotFound("student")
    return StudentDetail(row=row, groups=memberships.groups_of_student(student_id))
