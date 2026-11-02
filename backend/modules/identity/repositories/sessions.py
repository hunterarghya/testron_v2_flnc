from uuid import UUID

from modules.identity.models import UserSession


def delete_sessions_of(user_id: UUID) -> None:
    """Log the user out everywhere: every device, every browser."""
    UserSession.objects.filter(user_id=user_id).delete()
