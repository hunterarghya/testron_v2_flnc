"""How often a code may be emailed to one address (api_contract.md §5: 1 per 60 s, 5 per hour).

Counted per email address whether or not an account exists, so the limit itself never
reveals which addresses are registered. Call it before the use case's transaction.
"""

from datetime import datetime, timedelta

from core.rate_limit import RateLimit, ensure_within
from modules.identity.domain.values import OtpPurpose

_COOLDOWN = RateLimit(limit=1, window=timedelta(seconds=60))
_HOURLY = RateLimit(limit=5, window=timedelta(hours=1))


def ensure_can_send_code(email: str, purpose: OtpPurpose, *, now: datetime) -> None:
    ensure_within(f"otp-send:{purpose}:{email}:cooldown", _COOLDOWN, now=now)
    ensure_within(f"otp-send:{purpose}:{email}:hour", _HOURLY, now=now)
