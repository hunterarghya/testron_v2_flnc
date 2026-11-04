from datetime import datetime

from core.db.batches import delete_first
from modules.identity.repositories import email_otps


def delete_old_otps(*, created_before: datetime, limit: int) -> int:
    """Housekeeping (database_schema.md §5.4): codes older than a week are of no use, used or
    not. No policy: the caller is housekeeping, work no person asked for."""
    return delete_first(email_otps.created_before(created_before), limit)
