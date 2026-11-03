"""Next section, rapid-fire Next and returning (domain_model.md §5.3; E-4, Q-7)."""

from datetime import UTC, datetime, timedelta

import pytest

from modules.delivery.domain.errors import StageClosed, StageNavigationInvalid
from modules.delivery.domain.navigation import move_next, return_to
from modules.delivery.domain.stages import Progress, StageTimes
from modules.delivery.domain.timeline import Clock

T0 = datetime(2026, 11, 12, 4, 30, tzinfo=UTC)
CLOCK = Clock(anchor_at=T0, durations_s=(600, 600, 600))


def _at(seconds: int) -> datetime:
    return T0 + timedelta(seconds=seconds)


START = Progress((StageTimes(entered_at=T0), StageTimes(), StageTimes()), 0, 0)


def test_moving_on_closes_the_stage_when_returning_isnt_allowed() -> None:
    moved = move_next(CLOCK, START, from_stage=0, allow_return=False, now=_at(100))

    assert (moved.current, moved.furthest) == (1, 1)
    assert moved.stages[0] == StageTimes(entered_at=T0, left_at=_at(100), closed_at=_at(100))
    assert moved.stages[1].entered_at == _at(100)


def test_moving_on_leaves_the_stage_open_when_returning_is_allowed() -> None:
    moved = move_next(CLOCK, START, from_stage=0, allow_return=True, now=_at(100))
    assert moved.stages[0].closed_at is None
    assert moved.stages[0].left_at == _at(100)


def test_a_retried_move_changes_nothing() -> None:
    moved = move_next(CLOCK, START, from_stage=0, allow_return=False, now=_at(100))
    assert move_next(CLOCK, moved, from_stage=0, allow_return=False, now=_at(105)) == moved


@pytest.mark.parametrize("from_stage", [1, 2])
def test_only_the_current_stage_can_be_left(from_stage: int) -> None:
    with pytest.raises(StageNavigationInvalid):
        move_next(CLOCK, START, from_stage=from_stage, allow_return=False, now=_at(100))


def test_the_last_stage_has_no_next() -> None:
    last = Progress((StageTimes(entered_at=T0),) * 3, 2, 2)
    with pytest.raises(StageNavigationInvalid):
        move_next(CLOCK, last, from_stage=2, allow_return=False, now=_at(100))


def test_entering_again_keeps_the_first_entry_q7() -> None:
    back = Progress(
        (StageTimes(entered_at=T0), StageTimes(entered_at=_at(50), left_at=_at(80)), StageTimes()),
        0,
        1,
    )
    moved = move_next(CLOCK, back, from_stage=0, allow_return=True, now=_at(200))
    assert moved.stages[1].entered_at == _at(50)
    assert (moved.current, moved.furthest) == (1, 1)


AHEAD = Progress(
    (StageTimes(entered_at=T0, left_at=_at(100)), StageTimes(entered_at=_at(100)), StageTimes()),
    1,
    1,
)


def test_returning_to_a_running_stage_leaves_the_current_one_open() -> None:
    back = return_to(CLOCK, AHEAD, index=0, allow_return=True, now=_at(300))
    assert (back.current, back.furthest) == (0, 1)
    assert back.stages[1] == StageTimes(entered_at=_at(100), left_at=_at(300))
    forward = return_to(CLOCK, back, index=1, allow_return=True, now=_at(320))
    assert forward.current == 1
    assert return_to(CLOCK, forward, index=1, allow_return=True, now=_at(330)) == forward


@pytest.mark.parametrize(
    ("index", "allow", "seconds", "error"),
    [
        (0, False, 300, StageNavigationInvalid),
        (2, True, 300, StageNavigationInvalid),
        (-1, True, 300, StageNavigationInvalid),
        (0, True, 600, StageClosed),
    ],
)
def test_returning_is_refused(
    index: int, allow: bool, seconds: int, error: type[Exception]
) -> None:
    with pytest.raises(error):
        return_to(CLOCK, AHEAD, index=index, allow_return=allow, now=_at(seconds))


def test_a_closed_stage_cant_be_returned_to() -> None:
    closed = Progress(
        (
            StageTimes(entered_at=T0, left_at=_at(10), closed_at=_at(10)),
            StageTimes(entered_at=_at(10)),
            StageTimes(),
        ),
        1,
        1,
    )
    with pytest.raises(StageClosed):
        return_to(CLOCK, closed, index=0, allow_return=True, now=_at(20))
