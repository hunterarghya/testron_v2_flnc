"""How often housekeeping runs and what it clears (database_schema.md §5.4)."""

from dataclasses import dataclass
from datetime import datetime, timedelta

EVERY = timedelta(minutes=10)
# Rows per table per run, so the request that triggers it stays fast
BATCH = 200
OTP_KEPT_FOR = timedelta(days=7)
RATE_LIMITS_KEPT_FOR = timedelta(days=1)
# Lazy finalization normally ends these long before
ABANDONED_AFTER = timedelta(hours=24)


@dataclass(frozen=True, slots=True)
class Cutoffs:
    due_after: datetime
    otps_before: datetime
    rate_limits_before: datetime
    abandoned_before: datetime


def cutoffs(now: datetime) -> Cutoffs:
    return Cutoffs(
        due_after=now - EVERY,
        otps_before=now - OTP_KEPT_FOR,
        rate_limits_before=now - RATE_LIMITS_KEPT_FOR,
        abandoned_before=now - ABANDONED_AFTER,
    )
