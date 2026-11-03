"""The gate (P-02) and the test list's cards (P-01): may this student begin now, and if not,
why (domain_model.md §5.4 checks 2-6, in order; §5.7 granted sittings)."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from uuid import UUID


class GateStatus(StrEnum):
    NOT_OPEN = "NOT_OPEN"
    WAITING_FOR_TEACHER = "WAITING_FOR_TEACHER"
    READY = "READY"
    IN_PROGRESS = "IN_PROGRESS"
    ENTRY_CLOSED = "ENTRY_CLOSED"
    NO_ATTEMPTS_LEFT = "NO_ATTEMPTS_LEFT"


class CardState(StrEnum):
    START = "START"
    JOIN = "JOIN"
    RESUME = "RESUME"
    STARTS_IN = "STARTS_IN"
    RETAKE_AVAILABLE = "RETAKE_AVAILABLE"


@dataclass(frozen=True, slots=True)
class Sittings:
    """What the student has done with this assignment so far."""

    in_progress_attempt_id: UUID | None = None
    # Attempts made, ended or not
    used: int = 0
    # An unused retake grant (or a late first sitting) from the teacher
    has_grant: bool = False


@dataclass(frozen=True, slots=True)
class EntryTimes:
    """The assignment's side of entry (from assignments' `Entry`)."""

    opens_at: datetime | None
    awaits_start: bool
    closes_at: datetime | None


@dataclass(frozen=True, slots=True)
class Gate:
    status: GateStatus
    # READY on a retake grant: its own clock, no window or Start needed (§5.7)
    granted: bool = False


@dataclass(frozen=True, slots=True)
class SittingTimes:
    duration_s: int
    # Everyone shares one clock (MANUAL, SCHEDULED)
    common_clock: bool
    anchor_at: datetime | None
    # When the shared clock ends, or a deadline closes
    ends_at: datetime | None


def gate(entry: EntryTimes, sittings: Sittings, *, now: datetime) -> Gate:
    if sittings.in_progress_attempt_id is not None:
        return Gate(GateStatus.IN_PROGRESS)
    if sittings.used > 0:
        status = GateStatus.READY if sittings.has_grant else GateStatus.NO_ATTEMPTS_LEFT
        return Gate(status, granted=sittings.has_grant)
    regular = _regular_entry(entry, now)
    if regular is GateStatus.ENTRY_CLOSED and sittings.has_grant:
        return Gate(GateStatus.READY, granted=True)
    return Gate(regular)


def _regular_entry(entry: EntryTimes, now: datetime) -> GateStatus:
    if entry.opens_at is not None and now < entry.opens_at:
        return GateStatus.NOT_OPEN
    if entry.awaits_start:
        return GateStatus.WAITING_FOR_TEACHER
    if entry.closes_at is not None and entry.closes_at <= now:
        return GateStatus.ENTRY_CLOSED
    return GateStatus.READY


def card_state(current: Gate) -> CardState | None:
    """None: not on My Tests (missed or used up; Past Tests shows those)."""
    match current.status:
        case GateStatus.IN_PROGRESS:
            return CardState.RESUME
        case GateStatus.READY:
            return CardState.RETAKE_AVAILABLE if current.granted else CardState.START
        case GateStatus.WAITING_FOR_TEACHER:
            return CardState.JOIN
        case GateStatus.NOT_OPEN:
            return CardState.STARTS_IN
        case _:
            return None


def time_left_if_started_now(current: Gate, times: SittingTimes, *, now: datetime) -> int | None:
    """P-02's late-joiner message ("You have 44 min"): how long a sitting begun now would
    last. None when the student can't begin, or the shared clock hasn't started yet."""
    if current.status is not GateStatus.READY:
        return None
    duration = timedelta(seconds=times.duration_s)
    if current.granted:
        return times.duration_s
    if times.common_clock:
        if times.anchor_at is None:
            return None
        start = max(now, times.anchor_at)
        end = times.ends_at or times.anchor_at + duration
    else:
        start = now
        end = start + duration if times.ends_at is None else min(start + duration, times.ends_at)
    return max(0, int((end - start).total_seconds()))
