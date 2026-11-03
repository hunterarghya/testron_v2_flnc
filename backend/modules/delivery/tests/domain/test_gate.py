"""The gate and the cards (domain_model.md §5.4 checks 2-6 in order, §5.7; P-01, P-02)."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from core.errors import DomainError
from modules.delivery.domain.errors import EntryClosed, NotOpenYet
from modules.delivery.domain.gate import (
    CardState,
    EntryTimes,
    Gate,
    GateStatus,
    Sittings,
    SittingTimes,
    card_state,
    ensure_may_start,
    gate,
    time_left_if_started_now,
)

NOW = datetime(2026, 11, 12, 10, 0, tzinfo=UTC)
MIN = timedelta(minutes=1)
OPEN = EntryTimes(opens_at=None, awaits_start=False, closes_at=None)
LATER = EntryTimes(opens_at=NOW + MIN, awaits_start=True, closes_at=None)
WAITING = EntryTimes(opens_at=NOW - MIN, awaits_start=True, closes_at=None)
CLOSED = EntryTimes(opens_at=None, awaits_start=False, closes_at=NOW)
RUNNING = Sittings(in_progress_attempt_id=uuid4(), used=1)
S = GateStatus


@pytest.mark.parametrize(
    ("entry", "sittings", "expected"),
    [
        (OPEN, Sittings(), Gate(S.READY)),
        (LATER, Sittings(), Gate(S.NOT_OPEN)),
        (WAITING, Sittings(), Gate(S.WAITING_FOR_TEACHER)),
        (CLOSED, Sittings(), Gate(S.ENTRY_CLOSED)),
        (CLOSED, Sittings(has_grant=True), Gate(S.READY, granted=True)),
        (CLOSED, RUNNING, Gate(S.IN_PROGRESS)),
        (OPEN, Sittings(used=1), Gate(S.NO_ATTEMPTS_LEFT)),
        (WAITING, Sittings(used=1, has_grant=True), Gate(S.READY, granted=True)),
        # A grant doesn't skip checks 4-5 for a first sitting: only a closed entry
        (WAITING, Sittings(has_grant=True), Gate(S.WAITING_FOR_TEACHER)),
    ],
)
def test_gate(entry: EntryTimes, sittings: Sittings, expected: Gate) -> None:
    assert gate(entry, sittings, now=NOW) == expected


@pytest.mark.parametrize(
    ("current", "card"),
    [
        (Gate(S.IN_PROGRESS), CardState.RESUME),
        (Gate(S.READY), CardState.START),
        (Gate(S.READY, granted=True), CardState.RETAKE_AVAILABLE),
        (Gate(S.WAITING_FOR_TEACHER), CardState.JOIN),
        (Gate(S.NOT_OPEN), CardState.STARTS_IN),
        (Gate(S.ENTRY_CLOSED), None),
        (Gate(S.NO_ATTEMPTS_LEFT), None),
    ],
)
def test_card_state(current: Gate, card: CardState | None) -> None:
    assert card_state(current) is card


HOUR_S = 3600
SHARED = SittingTimes(HOUR_S, common_clock=True, anchor_at=NOW - 6 * MIN, ends_at=NOW + 54 * MIN)


@pytest.mark.parametrize(
    ("current", "times", "left"),
    [
        (Gate(S.WAITING_FOR_TEACHER), SHARED, None),
        (Gate(S.READY), SHARED, 54 * 60),
        (Gate(S.READY), SittingTimes(HOUR_S, True, NOW + MIN, None), HOUR_S),
        (Gate(S.READY), SittingTimes(HOUR_S, True, None, None), None),
        (Gate(S.READY), SittingTimes(HOUR_S, False, None, NOW + 20 * MIN), 20 * 60),
        (Gate(S.READY), SittingTimes(HOUR_S, False, None, None), HOUR_S),
        (Gate(S.READY, granted=True), SHARED, HOUR_S),
        (Gate(S.READY), SittingTimes(HOUR_S, True, NOW - 90 * MIN, NOW - MIN), 0),
    ],
)
def test_time_left_if_started_now(current: Gate, times: SittingTimes, left: int | None) -> None:
    assert time_left_if_started_now(current, times, now=NOW) == left


@pytest.mark.parametrize(
    ("entry", "sittings", "error"),
    [
        (LATER, Sittings(), "not_open_yet"),
        (WAITING, Sittings(), "waiting_for_teacher"),
        (CLOSED, Sittings(), "entry_closed"),
        (OPEN, Sittings(used=1), "no_attempts_left"),
    ],
)
def test_start_refuses_with_the_first_failing_check(
    entry: EntryTimes, sittings: Sittings, error: str
) -> None:
    with pytest.raises(DomainError) as raised:
        ensure_may_start(entry, sittings, now=NOW)
    assert raised.value.code == error


def test_start_tells_when_it_opens_and_closed() -> None:
    with pytest.raises(NotOpenYet) as early:
        ensure_may_start(LATER, Sittings(), now=NOW)
    assert early.value.context == {"opens_at": NOW + MIN, "server_now": NOW}
    with pytest.raises(EntryClosed) as late:
        ensure_may_start(CLOSED, Sittings(), now=NOW)
    assert late.value.context == {"closed_at": NOW}


@pytest.mark.parametrize(
    ("entry", "sittings", "expected"),
    [
        (OPEN, Sittings(), Gate(S.READY)),
        (CLOSED, RUNNING, Gate(S.IN_PROGRESS)),
        (CLOSED, Sittings(has_grant=True), Gate(S.READY, granted=True)),
        (OPEN, Sittings(used=2, has_grant=True), Gate(S.READY, granted=True)),
    ],
)
def test_start_lets_in_a_regular_or_granted_sitting_or_resumes(
    entry: EntryTimes, sittings: Sittings, expected: Gate
) -> None:
    assert ensure_may_start(entry, sittings, now=NOW) == expected
