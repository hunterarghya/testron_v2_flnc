"""The `SessionUser` the SPA boots from (api_contract.md §3.1), shared by every use case that
logs someone in or reports who is logged in."""

from dataclasses import dataclass
from uuid import UUID

from core.context import Role, StudentStatus
from modules.identity.public import get_user_summary
from modules.students.repositories import students


@dataclass(frozen=True, slots=True)
class SessionUserView:
    id: UUID
    name: str
    email: str
    role: Role
    # None for the teacher, who has no admission status
    status: StudentStatus | None
    has_password: bool
    performance_shared: bool


def build_session_user(user_id: UUID) -> SessionUserView:
    user = get_user_summary(user_id)
    is_student = user.role is Role.STUDENT
    return SessionUserView(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        status=students.get_status(user_id) if is_student else None,
        has_password=user.has_password,
        performance_shared=is_student and students.is_performance_shared(user_id),
    )
