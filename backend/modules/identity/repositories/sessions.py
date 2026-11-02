from collections.abc import Sequence
from uuid import UUID

from modules.identity.models import UserSession


def delete_sessions_of(user_id: UUID) -> None:
    """Log the user out everywhere: every device, every browser."""
    delete_sessions_of_many([user_id])


def delete_sessions_of_many(user_ids: Sequence[UUID]) -> None:
    UserSession.objects.filter(user_id__in=user_ids).delete()
