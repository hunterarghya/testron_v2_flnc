"""The only place that reads the time (architecture.md §5.5).

Use cases read `now` once per request and pass it down, so a request sees one
consistent instant. Tests swap in a FrozenClock to control time exactly.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from typing import Protocol


class Clock(Protocol):
    def now(self) -> datetime: ...


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


class FrozenClock:
    """A clock that only moves when told to."""

    def __init__(self, at: datetime) -> None:
        self._now = _require_aware(at)

    def now(self) -> datetime:
        return self._now

    def advance(self, **delta: float) -> None:
        """Move forward, e.g. `advance(minutes=5)`."""
        self._now += timedelta(**delta)

    def set(self, at: datetime) -> None:
        self._now = _require_aware(at)


class _Active:
    clock: Clock = SystemClock()


def get_clock() -> Clock:
    return _Active.clock


def now() -> datetime:
    """The current instant from the active clock (also the model field default)."""
    return _Active.clock.now()


@contextmanager
def use_clock(clock: Clock) -> Iterator[Clock]:
    """Swap the process clock for the duration of a block (tests, E2E time control)."""
    previous, _Active.clock = _Active.clock, clock
    try:
        yield clock
    finally:
        _Active.clock = previous


def _require_aware(at: datetime) -> datetime:
    # A time without a zone is ambiguous; every stored time is UTC
    if at.tzinfo is None:
        raise ValueError("FrozenClock needs a timezone-aware datetime")
    return at.astimezone(UTC)
