from collections.abc import Sequence
from uuid import UUID

from modules.identity.repositories import sessions


def end_sessions(*, user_ids: Sequence[UUID]) -> None:
    """Log these users out on every device at once (domain_model.md §3.1: deactivation)."""
    sessions.delete_sessions_of_many(user_ids)
