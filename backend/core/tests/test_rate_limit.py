from datetime import timedelta

import pytest
from django.db import transaction

from core.clock import FrozenClock
from core.errors import RateLimited
from core.rate_limit import RateLimit, ensure_within, hit

pytestmark = pytest.mark.django_db

THREE_PER_MINUTE = RateLimit(limit=3, window=timedelta(minutes=1))
FIVE_THEN_BLOCK = RateLimit(limit=5, window=timedelta(minutes=10), block=timedelta(seconds=30))


def hits(key: str, rule: RateLimit, clock: FrozenClock, count: int) -> list[bool]:
    return [hit(key, rule, now=clock.now()).allowed for _ in range(count)]


def test_allows_up_to_the_limit_then_refuses(frozen_clock: FrozenClock) -> None:
    assert hits("login:ip:1.2.3.4", THREE_PER_MINUTE, frozen_clock, 5) == [
        True,
        True,
        True,
        False,
        False,
    ]


def test_refusal_says_when_to_retry(frozen_clock: FrozenClock) -> None:
    hits("k", THREE_PER_MINUTE, frozen_clock, 3)
    frozen_clock.advance(seconds=20)

    assert hit("k", THREE_PER_MINUTE, now=frozen_clock.now()).retry_after_s == 40


def test_a_new_window_starts_fresh(frozen_clock: FrozenClock) -> None:
    hits("k", THREE_PER_MINUTE, frozen_clock, 4)
    frozen_clock.advance(minutes=1)

    assert hits("k", THREE_PER_MINUTE, frozen_clock, 3) == [True, True, True]


def test_keys_are_counted_separately(frozen_clock: FrozenClock) -> None:
    hits("login:email:a@example.com", THREE_PER_MINUTE, frozen_clock, 3)

    assert hit("login:email:b@example.com", THREE_PER_MINUTE, now=frozen_clock.now()).allowed


def test_going_over_starts_a_block(frozen_clock: FrozenClock) -> None:
    hits("test-password:a:s", FIVE_THEN_BLOCK, frozen_clock, 5)

    sixth = hit("test-password:a:s", FIVE_THEN_BLOCK, now=frozen_clock.now())

    assert (sixth.allowed, sixth.retry_after_s) == (False, 30)


def test_tries_during_a_block_are_refused(frozen_clock: FrozenClock) -> None:
    hits("k", FIVE_THEN_BLOCK, frozen_clock, 6)
    frozen_clock.advance(seconds=10)

    during = hit("k", FIVE_THEN_BLOCK, now=frozen_clock.now())

    assert (during.allowed, during.retry_after_s) == (False, 20)


def test_after_a_block_the_tries_start_again(frozen_clock: FrozenClock) -> None:
    hits("k", FIVE_THEN_BLOCK, frozen_clock, 6)
    frozen_clock.advance(seconds=30)

    assert hits("k", FIVE_THEN_BLOCK, frozen_clock, 6) == [True] * 5 + [False]


def test_ensure_within_raises_429_with_retry_after(frozen_clock: FrozenClock) -> None:
    for _ in range(3):
        ensure_within("k", THREE_PER_MINUTE, now=frozen_clock.now())

    with pytest.raises(RateLimited) as error:
        ensure_within("k", THREE_PER_MINUTE, now=frozen_clock.now())

    assert error.value.status == 429
    assert error.value.response_headers() == {"Retry-After": "60"}
    assert error.value.context == {"retry_after_s": 60}


def test_a_hit_cannot_hide_inside_a_use_case_transaction(frozen_clock: FrozenClock) -> None:
    # It would be rolled back with a failed login, and the limit would never trigger
    with pytest.raises(RuntimeError), transaction.atomic():
        hit("k", THREE_PER_MINUTE, now=frozen_clock.now())


def test_each_allowed_try_says_how_many_are_left(frozen_clock: FrozenClock) -> None:
    left = [hit("k:left", THREE_PER_MINUTE, now=frozen_clock.now()).remaining for _ in range(3)]
    assert left == [2, 1, 0]
