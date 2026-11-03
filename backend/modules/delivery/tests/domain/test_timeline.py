"""The attempt clock as tables (domain_model.md §5.1-5.3), from the shared JSON fixture, and
its invariants as properties (testing_strategy.md §3.1)."""

from datetime import datetime, timedelta
from typing import cast

import pytest
from hypothesis import given
from hypothesis import strategies as st

from modules.delivery.domain.errors import EntryClosed
from modules.delivery.domain.stages import Progress, StageTimes, catch_up, opening
from modules.delivery.domain.timeline import (
    Clock,
    Extension,
    attempt_deadline,
    boundary,
    stage_deadline,
)
from tests.fixtures.domain import Row, at, load_table, rows

TABLE = load_table("timeline")
BASE = datetime.fromisoformat(cast("str", TABLE["base"]))


def _when(seconds: object) -> datetime | None:
    return at(BASE, seconds)


def _instant(seconds: object) -> datetime:
    return BASE + timedelta(seconds=cast("int", seconds))


def _clock(row: Row) -> Clock:
    extensions = cast("list[list[int | None]]", row.get("extensions", []))
    return Clock(
        anchor_at=_instant(row["anchor"]),
        durations_s=tuple(cast("list[int]", row["durations"])),
        extensions=tuple(Extension(cast("int", s), i) for s, i in extensions),
        closes_at=_when(row.get("closes_at")),
        ended_at=_when(row.get("ended_at")),
    )


def _times(values: object) -> list[datetime | None]:
    return [_when(v) for v in cast("list[object]", values)]


@pytest.mark.parametrize("row", rows(TABLE, "deadlines"), ids=lambda r: str(r["name"]))
def test_deadlines(row: Row) -> None:
    clock = _clock(row)
    entered = _times(row["entered"])
    assert [boundary(clock, i) for i in range(clock.last + 1)] == _times(row["boundaries"])
    assert attempt_deadline(clock) == _when(row["attempt_deadline"])
    deadlines = [stage_deadline(clock, i, when) for i, when in enumerate(entered)]
    assert deadlines == _times(row["stage_deadlines"])


def _stage(raw: object) -> StageTimes:
    stage = cast("dict[str, object]", raw)
    return StageTimes(
        entered_at=_when(stage.get("entered")),
        left_at=_when(stage.get("left")),
        closed_at=_when(stage.get("closed")),
        missed=bool(stage.get("missed", False)),
    )


@pytest.mark.parametrize("row", rows(TABLE, "catch_up"), ids=lambda r: str(r["name"]))
def test_catch_up(row: Row) -> None:
    progress = Progress(
        stages=tuple(_stage(s) for s in cast("list[object]", row["stages"])),
        current=cast("int", row["current"]),
        furthest=cast("int", row["furthest"]),
    )
    result = catch_up(_clock(row), progress, now=_instant(row["now"]))
    assert result.progress.current == row["expect_current"]
    assert result.ended_at == _when(row["expect_ended_at"])
    assert [s.entered_at for s in result.progress.stages] == _times(row["expect_entered"])
    assert [s.closed_at for s in result.progress.stages] == _times(row["expect_closed"])


@pytest.mark.parametrize("row", rows(TABLE, "opening"), ids=lambda r: str(r["name"]))
def test_opening(row: Row) -> None:
    now = _instant(row["now"])
    if "expect_error" in row:
        with pytest.raises(EntryClosed):
            opening(_clock(row), now=now)
        return
    progress = opening(_clock(row), now=now)
    assert progress.current == progress.furthest == row["expect_current"]
    assert [s.entered_at for s in progress.stages] == _times(row["expect_entered"])
    assert [s.missed for s in progress.stages] == row["expect_missed"]


def test_the_table_has_enough_rows() -> None:
    assert len(rows(TABLE, "deadlines")) >= 40


# Properties: true for any clock (testing_strategy.md §3.1)
durations = st.lists(st.integers(1, 7200), min_size=1, max_size=6)
extensions = st.lists(
    st.tuples(st.integers(1, 3600), st.one_of(st.none(), st.integers(0, 5))), max_size=4
)
offsets = st.one_of(st.none(), st.integers(0, 40_000))


@st.composite
def clocks(draw: st.DrawFn) -> Clock:
    lengths = draw(durations)
    extra = [Extension(s, i if i is None else i % len(lengths)) for s, i in draw(extensions)]
    return Clock(
        anchor_at=BASE,
        durations_s=tuple(lengths),
        extensions=tuple(extra),
        closes_at=_when(draw(offsets)),
        ended_at=_when(draw(offsets)),
    )


@given(clocks(), st.integers(0, 40_000))
def test_no_stage_ends_after_its_boundary_or_the_attempt(clock: Clock, entered: int) -> None:
    deadline = attempt_deadline(clock)
    assert deadline <= boundary(clock, clock.last)
    for i in range(clock.last + 1):
        own = stage_deadline(clock, i, _when(entered))
        assert own <= boundary(clock, i)
        assert own <= deadline


@given(clocks(), st.integers(1, 3600), st.one_of(st.none(), st.integers(0, 5)))
def test_an_extension_never_makes_a_deadline_earlier(
    clock: Clock, seconds: int, index: int | None
) -> None:
    stage = index if index is None else index % (clock.last + 1)
    longer = Clock(
        clock.anchor_at,
        clock.durations_s,
        (*clock.extensions, Extension(seconds, stage)),
        clock.closes_at,
        clock.ended_at,
    )
    assert attempt_deadline(longer) >= attempt_deadline(clock)
    for i in range(clock.last + 1):
        assert boundary(longer, i) >= boundary(clock, i)
        assert stage_deadline(longer, i, None) >= stage_deadline(clock, i, None)


@given(clocks(), st.integers(0, 7200), st.integers(0, 7200))
def test_moving_on_earlier_never_makes_the_next_stage_end_later(
    clock: Clock, early: int, late: int
) -> None:
    first, second = sorted((early, late))
    for i in range(clock.last + 1):
        assert stage_deadline(clock, i, _when(first)) <= stage_deadline(clock, i, _when(second))
