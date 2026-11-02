from dataclasses import dataclass
from uuid import UUID

from core.context import Role
from modules.identity.repositories import users


@dataclass(frozen=True, slots=True)
class UserSummary:
    id: UUID
    email: str
    name: str
    role: Role
    has_password: bool
    email_verified: bool


def get_user_summary(user_id: UUID) -> UserSummary:
    """The account facts other modules show about a user (never the password or codes)."""
    user = users.get_user(user_id)
    return UserSummary(
        id=user.id,
        email=user.email,
        name=user.name,
        role=Role(user.role),
        has_password=user.has_usable_password(),
        email_verified=user.email_verified_at is not None,
    )
