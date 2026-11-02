from dataclasses import dataclass

from core.context import Ctx, StudentStatus
from modules.students.domain.values import StudentRow
from modules.students.policies import ensure_teacher
from modules.students.repositories import student_list


@dataclass(frozen=True, slots=True)
class StudentPage:
    rows: list[StudentRow]
    total: int


def list_students(
    ctx: Ctx, *, status: StudentStatus, search: str | None, offset: int, limit: int
) -> StudentPage:
    """One tab of the teacher's Students table (T-14): Active, Pending, Declined or
    Deactivated, optionally searched by name or email. Pending shows the newest request
    first; the other tabs sort by name. Two queries, however many students there are.
    """
    ensure_teacher(ctx.actor)
    rows, total = student_list.list_students(status, search=search, offset=offset, limit=limit)
    return StudentPage(rows=rows, total=total)
