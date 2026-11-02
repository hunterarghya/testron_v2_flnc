from datetime import UTC, datetime, timedelta, timezone

import pytest

from core.clock import FrozenClock, SystemClock, get_clock, now, use_clock

NOON = datetime(2026, 11, 12, 4, 30, tzinfo=UTC)


def test_system_clock_is_utc() -> None:
    assert SystemClock().now().tzinfo is UTC


def test_frozen_clock_stays_still() -> None:
    clock = FrozenClock(NOON)

    assert clock.now() == clock.now() == NOON


def test_frozen_clock_advances_on_request() -> None:
    clock = FrozenClock(NOON)

    clock.advance(minutes=5, seconds=30)

    assert clock.now() == NOON + timedelta(minutes=5, seconds=30)


def test_frozen_clock_can_jump() -> None:
    clock = FrozenClock(NOON)

    clock.set(NOON + timedelta(days=1))

    assert clock.now() == NOON + timedelta(days=1)


def test_frozen_clock_converts_to_utc() -> None:
    kolkata = timezone(timedelta(hours=5, minutes=30))

    assert FrozenClock(datetime(2026, 11, 12, 10, 0, tzinfo=kolkata)).now() == NOON


def test_v1_f34_naive_time_is_rejected() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        FrozenClock(datetime(2026, 11, 12, 4, 30))


def test_use_clock_swaps_and_restores() -> None:
    original = get_clock()

    with use_clock(FrozenClock(NOON)):
        assert now() == NOON

    assert get_clock() is original


def test_use_clock_restores_after_an_error() -> None:
    original = get_clock()

    with pytest.raises(RuntimeError), use_clock(FrozenClock(NOON)):
        raise RuntimeError

    assert get_clock() is original
