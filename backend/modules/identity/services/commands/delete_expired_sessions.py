from datetime import datetime

from core.db.batches import delete_first
from modules.identity.repositories import sessions


def delete_expired_sessions(*, now: datetime, limit: int) -> int:
    """Housekeeping (database_schema.md §5.4): sessions past their expiry log no one in.
    No policy: the caller is housekeeping, work no person asked for."""
    return delete_first(sessions.expired(now), limit)
