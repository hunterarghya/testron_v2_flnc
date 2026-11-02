"""Fixed-window rate limits over the `rate_limit_buckets` table (api_contract.md §5).

One upsert per hit. Each hit commits in its own transaction, before the use case's
transaction starts: otherwise a failed login, whose transaction rolls back, would roll
back its own hit too and the limit would never trigger. Calling `hit` inside another
transaction is therefore an error (`atomic(durable=True)`).

The table belongs to the identity module's migrations; core uses it by name only,
because core may not import a module.
"""

import math
from dataclasses import dataclass
from datetime import datetime, timedelta

from django.db import connection, transaction

from core.errors import RateLimited


@dataclass(frozen=True, slots=True)
class RateLimit:
    limit: int
    window: timedelta
    # After going over the limit, refuse for this long (default: until the window ends)
    block: timedelta | None = None


@dataclass(frozen=True, slots=True)
class RateDecision:
    allowed: bool
    retry_after_s: int = 0


# The counter starts again when its window is over, or when a block has run out.
# A running block is never reset.
# (`excluded.window_started_at` is the new row's value: now.)
_COUNT_HIT = """
INSERT INTO rate_limit_buckets AS bucket (key, window_started_at, hits, blocked_until)
VALUES (%(key)s, %(now)s, 1, NULL)
ON CONFLICT (key) DO UPDATE SET
    window_started_at = CASE
        WHEN bucket.blocked_until IS NOT NULL AND bucket.blocked_until <= excluded.window_started_at
            THEN excluded.window_started_at
        WHEN bucket.blocked_until IS NULL AND bucket.window_started_at <= %(window_cutoff)s
            THEN excluded.window_started_at
        ELSE bucket.window_started_at END,
    hits = CASE
        WHEN bucket.blocked_until IS NOT NULL AND bucket.blocked_until <= excluded.window_started_at
            THEN 1
        WHEN bucket.blocked_until IS NULL AND bucket.window_started_at <= %(window_cutoff)s
            THEN 1
        ELSE bucket.hits + 1 END,
    blocked_until = CASE
        WHEN bucket.blocked_until IS NOT NULL AND bucket.blocked_until <= excluded.window_started_at
            THEN NULL
        ELSE bucket.blocked_until END
RETURNING window_started_at, hits, blocked_until
"""
_START_BLOCK = "UPDATE rate_limit_buckets SET blocked_until = %(until)s WHERE key = %(key)s"


def hit(key: str, rule: RateLimit, *, now: datetime) -> RateDecision:
    """Count one try for `key` and say whether it is allowed."""
    with transaction.atomic(durable=True), connection.cursor() as cursor:
        cursor.execute(_COUNT_HIT, {"key": key, "now": now, "window_cutoff": now - rule.window})
        window_started_at, hits, blocked_until = cursor.fetchone()
        decision = decide(
            hits,
            rule,
            now=now,
            window_ends_at=window_started_at + rule.window,
            blocked_until=blocked_until,
        )
        if not decision.allowed and blocked_until is None and rule.block is not None:
            cursor.execute(_START_BLOCK, {"key": key, "until": now + rule.block})
            decision = RateDecision(allowed=False, retry_after_s=_seconds(rule.block))
    return decision


def ensure_within(key: str, rule: RateLimit, *, now: datetime) -> None:
    """Count one try; raise RateLimited (HTTP 429 with Retry-After) when over the limit."""
    decision = hit(key, rule, now=now)
    if not decision.allowed:
        raise RateLimited(retry_after_s=decision.retry_after_s)


def decide(
    hits: int,
    rule: RateLimit,
    *,
    now: datetime,
    window_ends_at: datetime,
    blocked_until: datetime | None,
) -> RateDecision:
    """The pure decision for a counter state: a running block wins, then the hit count."""
    if blocked_until is not None and blocked_until > now:
        return RateDecision(allowed=False, retry_after_s=_seconds(blocked_until - now))
    if hits <= rule.limit:
        return RateDecision(allowed=True)
    return RateDecision(allowed=False, retry_after_s=_seconds(window_ends_at - now))


def _seconds(delta: timedelta) -> int:
    # Rounded up and at least 1, so a client that waits exactly this long gets through
    return max(1, math.ceil(delta.total_seconds()))
