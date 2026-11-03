"""Lifecycle states and assignment_end (domain_model.md §3.5, §5.1, §5.6): one row per case."""

from datetime import UTC, datetime, timedelta

import pytest

from modules.assignments.domain.lifecycle import (
    ExtensionGrant,
    Timeline,
    assignment_end,
    common_anchor,
    has_started,
    lifecycle_state,
)
from modules.assignments.domain.values import LifecycleState as S
from modules.assignments.domain.values import WindowKind
from modules.assignments.domain.window import Window

NOW = datetime(2026, 11, 12, 10, 0, tzinfo=UTC)
HOUR = timedelta(hours=1)


def timeline(window: Window, **changes: object) -> Timeline:
    values: dict[str, object] = {
        "window": window,
        "requires_activation": False,
        "total_duration_s": 3600,
    }
    return Timeline(**(values | changes))  # type: ignore[arg-type]


MANUAL = Window(WindowKind.MANUAL)
SCHEDULED = Window(WindowKind.SCHEDULED, starts_at=NOW + HOUR)
STARTED = Window(WindowKind.SCHEDULED, starts_at=NOW - timedelta(minutes=30))
DEADLINE = Window(WindowKind.DEADLINE, opens_at=NOW - HOUR, closes_at=NOW + HOUR)
OPEN = Window(WindowKind.OPEN)


@pytest.mark.parametrize(
    ("case", "running", "state"),
    [
        (timeline(MANUAL, cancelled_at=NOW), False, S.CANCELLED),
        (timeline(MANUAL), False, S.WAITING),
        (timeline(MANUAL, activated_at=NOW - timedelta(minutes=10)), False, S.LIVE),
        (timeline(MANUAL, activated_at=NOW - 2 * HOUR), False, S.CLOSED),
        (timeline(MANUAL, activated_at=NOW - 2 * HOUR), True, S.LIVE),
        (timeline(MANUAL, activated_at=NOW, ended_at=NOW), True, S.CLOSED),
        (timeline(SCHEDULED), False, S.SCHEDULED),
        (timeline(STARTED), False, S.LIVE),
        (timeline(STARTED, requires_activation=True), False, S.WAITING),
        (timeline(DEADLINE), False, S.LIVE),
        (
            timeline(Window(WindowKind.DEADLINE, opens_at=NOW + HOUR, closes_at=NOW + 3 * HOUR)),
            False,
            S.SCHEDULED,
        ),
        (
            timeline(Window(WindowKind.DEADLINE, opens_at=NOW - 3 * HOUR, closes_at=NOW - HOUR)),
            False,
            S.CLOSED,
        ),
        (timeline(OPEN), False, S.LIVE),
        (timeline(OPEN, requires_activation=True), False, S.WAITING),
    ],
)
def test_states(case: Timeline, running: bool, state: S) -> None:
    assert lifecycle_state(case, [], now=NOW, attempts_in_progress=running) is state


def test_extensions_for_everyone_move_the_end() -> None:
    started = timeline(MANUAL, activated_at=NOW - timedelta(minutes=70))
    extensions = [
        ExtensionGrant(600, for_everyone=True, stage_index=None),
        ExtensionGrant(900, for_everyone=False, stage_index=None),
    ]

    assert assignment_end(started, extensions) == NOW + timedelta(minutes=0)
    assert (
        lifecycle_state(
            started, extensions, now=NOW - timedelta(seconds=1), attempts_in_progress=False
        )
        is S.LIVE
    )


def test_deadline_end_counts_only_final_stage_extensions_for_everyone() -> None:
    extensions = [
        ExtensionGrant(600, True, None),
        ExtensionGrant(300, True, 0),
        ExtensionGrant(900, False, None),
    ]

    assert assignment_end(timeline(DEADLINE), extensions) == NOW + HOUR + timedelta(minutes=10)


@pytest.mark.parametrize(
    ("case", "anchor"),
    [
        (timeline(MANUAL), None),
        (timeline(MANUAL, activated_at=NOW), NOW),
        (timeline(SCHEDULED), NOW + HOUR),
        (timeline(SCHEDULED, requires_activation=True), None),
        (
            timeline(SCHEDULED, requires_activation=True, activated_at=NOW + 2 * HOUR),
            NOW + 2 * HOUR,
        ),
        (timeline(SCHEDULED, requires_activation=True, activated_at=NOW), NOW + HOUR),
        (timeline(DEADLINE), None),
    ],
)
def test_common_anchor(case: Timeline, anchor: datetime | None) -> None:
    assert common_anchor(case) == anchor


def test_open_windows_never_end_and_unstarted_clocks_have_no_end() -> None:
    assert assignment_end(timeline(OPEN), []) is None
    assert assignment_end(timeline(MANUAL), []) is None


def test_started_means_activated_or_live() -> None:
    assert has_started(S.WAITING, timeline(MANUAL)) is False
    assert has_started(S.WAITING, timeline(MANUAL, activated_at=NOW)) is True
    assert has_started(S.LIVE, timeline(OPEN)) is True
    assert has_started(S.SCHEDULED, timeline(SCHEDULED)) is False


def test_ending_for_everyone_is_the_end() -> None:
    ended = timeline(MANUAL, activated_at=NOW - HOUR, ended_at=NOW - timedelta(minutes=5))

    assert assignment_end(ended, []) == NOW - timedelta(minutes=5)
