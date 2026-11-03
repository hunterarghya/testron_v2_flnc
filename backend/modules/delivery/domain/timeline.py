"""The attempt's clock (domain_model.md §5.1-5.2): when each stage and the whole attempt must
end. One pure function of the stage durations, the anchor, the extensions and the window's
limits; `now` is never read here.

    boundary(i)       = anchor + sum over k <= i of (d_k + ext(k))
    attempt_deadline  = min(boundary(last), closes_at + all extensions, ended_at)
    stage_deadline(i) = min(entered_at(i) + d_i + ext(i), boundary(i), attempt_deadline)
"""

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True, slots=True)
class Extension:
    """Extra time that applies to this attempt: for everyone, or for this student."""

    seconds: int
    # None: the final stage
    stage_index: int | None


@dataclass(frozen=True, slots=True)
class Clock:
    anchor_at: datetime
    durations_s: tuple[int, ...]
    extensions: tuple[Extension, ...] = ()
    # A DEADLINE window's close; None for other windows and for granted sittings (§5.7)
    closes_at: datetime | None = None
    # The teacher ended the test for everyone
    ended_at: datetime | None = None

    @property
    def last(self) -> int:
        return len(self.durations_s) - 1


def extension_s(clock: Clock, index: int) -> int:
    """ext(i): extensions for stage i; the final stage also gets those with no stage."""
    final = index == clock.last
    return sum(
        e.seconds
        for e in clock.extensions
        if e.stage_index == index or (final and e.stage_index is None)
    )


def boundary(clock: Clock, index: int) -> datetime:
    """The latest instant stage `index` may end: everyone's stage ends here on a shared clock."""
    seconds = sum(clock.durations_s[k] + extension_s(clock, k) for k in range(index + 1))
    return clock.anchor_at + timedelta(seconds=seconds)


def attempt_deadline(clock: Clock) -> datetime:
    limits = [boundary(clock, clock.last), clock.ended_at]
    if clock.closes_at is not None:
        # A deadline window can't run past its close, unless the teacher extends it
        added = sum(e.seconds for e in clock.extensions)
        limits.append(clock.closes_at + timedelta(seconds=added))
    return min(limit for limit in limits if limit is not None)


def stage_deadline(clock: Clock, index: int, entered_at: datetime | None) -> datetime:
    """A stage's timer runs from its first entry, even after the student leaves it [Q-7]."""
    limit = min(boundary(clock, index), attempt_deadline(clock))
    if entered_at is None:
        return limit
    own = entered_at + timedelta(seconds=clock.durations_s[index] + extension_s(clock, index))
    return min(own, limit)
