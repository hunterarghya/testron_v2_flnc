from dataclasses import dataclass
from uuid import UUID

from core.context import Ctx, StudentStatus
from modules.students.domain.values import StudentRow
from modules.students.policies import ensure_teacher
from modules.students.repositories import student_list


@dataclass(frozen=True, slots=True)
class StudentPage:
    rows: list[StudentRow]
    total: int


def list_students(
    ctx: Ctx,
    *,
    status: StudentStatus,
    search: str | None,
    group_id: UUID | None = None,
    offset: int,
    limit: int,
) -> StudentPage:
    """One tab of the teacher's Students table (T-14): Active, Pending, Declined or
    Deactivated, optionally searched by name or email or narrowed to one group. Pending
    shows the newest request first; the other tabs sort by name. Three queries, however
    many students there are.
    """
    ensure_teacher(ctx.actor)
    rows, total = student_list.list_students(
        status, search=search, group_id=group_id, offset=offset, limit=limit
    )
    return StudentPage(rows=rows, total=total)
