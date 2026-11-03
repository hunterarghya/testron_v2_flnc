"""What the student's palette and timer show for each stage, and where answers may go
(domain_model.md §3.6 #4, §7.4)."""

from datetime import UTC, datetime, timedelta

import pytest

from modules.delivery.domain.attempt import end_reason_at_deadline
from modules.delivery.domain.errors import QuestionNotInStage, StageClosed
from modules.delivery.domain.stages import (
    Progress,
    StageTimes,
    deadline_at,
    ensure_answerable,
    stage_state,
)
from modules.delivery.domain.timeline import Clock
from modules.delivery.domain.values import EndReason, StageState

T0 = datetime(2026, 11, 12, 4, 30, tzinfo=UTC)
CLOCK = Clock(anchor_at=T0, durations_s=(600, 600, 600))


def _at(seconds: int) -> datetime:
    return T0 + timedelta(seconds=seconds)


PROGRESS = Progress(
    stages=(
        StageTimes(closed_at=_at(600), missed=True),
        StageTimes(entered_at=_at(700), left_at=_at(800)),
        StageTimes(entered_at=_at(800)),
    ),
    current=2,
    furthest=2,
)


@pytest.mark.parametrize(
    ("index", "now", "state"),
    [
        (0, 900, StageState.MISSED),
        (1, 900, StageState.LEFT),
        (1, 1200, StageState.CLOSED),
        (2, 900, StageState.OPEN),
    ],
)
def test_stage_state(index: int, now: int, state: StageState) -> None:
    assert stage_state(CLOCK, PROGRESS, index, now=_at(now)) is state


def test_a_stage_not_entered_yet() -> None:
    fresh = Progress((StageTimes(entered_at=T0), StageTimes(), StageTimes()), 0, 0)
    assert stage_state(CLOCK, fresh, 1, now=T0) is StageState.NOT_ENTERED
    assert deadline_at(CLOCK, fresh, 1) == _at(1200)


def test_deadlines_shown_per_stage() -> None:
    assert deadline_at(CLOCK, PROGRESS, 0) is None
    assert deadline_at(CLOCK, PROGRESS, 1) == _at(1200)
    closed = Progress((StageTimes(entered_at=T0, closed_at=_at(100)),), 0, 0)
    assert deadline_at(Clock(T0, (600,)), closed, 0) == _at(100)


@pytest.mark.parametrize(
    ("index", "now", "error"),
    [
        (None, 900, QuestionNotInStage),
        (0, 900, StageClosed),
        (1, 1200, StageClosed),
    ],
)
def test_only_open_or_returnable_stages_take_answers(
    index: int | None, now: int, error: type[Exception]
) -> None:
    with pytest.raises(error):
        ensure_answerable(CLOCK, PROGRESS, index, now=_at(now))


def test_answers_go_to_the_open_stage_or_one_left_but_running() -> None:
    ensure_answerable(CLOCK, PROGRESS, 2, now=_at(900))
    ensure_answerable(CLOCK, PROGRESS, 1, now=_at(900))
    fresh = Progress((StageTimes(entered_at=T0), StageTimes()), 0, 0)
    with pytest.raises(QuestionNotInStage):
        ensure_answerable(Clock(T0, (600, 600)), fresh, 1, now=T0)


def test_a_closed_stage_names_itself() -> None:
    with pytest.raises(StageClosed) as closed:
        ensure_answerable(CLOCK, PROGRESS, 0, now=_at(900))
    assert closed.value.context == {"stage_index": 0}


@pytest.mark.parametrize(
    ("ended_for_everyone", "reason"),
    [(None, EndReason.TIMED_OUT), (900, EndReason.ENDED_BY_TEACHER), (2000, EndReason.TIMED_OUT)],
)
def test_why_time_ran_out(ended_for_everyone: int | None, reason: EndReason) -> None:
    cut = None if ended_for_everyone is None else _at(ended_for_everyone)
    assert end_reason_at_deadline(_at(900), ended_for_everyone_at=cut) is reason
