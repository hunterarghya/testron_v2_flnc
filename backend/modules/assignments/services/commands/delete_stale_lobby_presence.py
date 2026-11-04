from core.db.batches import delete_first
from modules.assignments.repositories import presence


def delete_stale_lobby_presence(*, limit: int) -> int:
    """Housekeeping (database_schema.md §3.5, §5.4): lobby rows matter only while a test
    waits for Start; once it has started, ended or been cancelled they are dropped. No
    policy: the caller is housekeeping, work no person asked for."""
    return delete_first(presence.no_longer_waiting(), limit)
