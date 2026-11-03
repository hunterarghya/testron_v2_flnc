"""Entry times, Start and lobby presence (domain_model.md §5.4 checks 4-6, T-09)."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from modules.assignments.domain.entry import (
    ActivationNotRequired,
    Entry,
    ensure_activatable,
    entry_window,
    is_joined,
    is_locked,
)
from modules.assignments.domain.errors import AssignmentCancelled
from modules.assignments.domain.lifecycle import ExtensionGrant, Timeline
from modules.assignments.domain.values import WindowKind
from modules.assignments.domain.window import Window

NOW = datetime(2026, 11, 12, 10, 0, tzinfo=UTC)
HOUR = timedelta(hours=1)
TEN_MIN = timedelta(minutes=10)


def timeline(window: Window, **changes: object) -> Timeline:
    base = Timeline(window, requires_activation=False, total_duration_s=3600)
    return replace(base, **changes)  # type: ignore[arg-type]


MANUAL = Window(WindowKind.MANUAL, late_entry_s=600)
SCHEDULED = Window(WindowKind.SCHEDULED, starts_at=NOW)
DEADLINE = Window(WindowKind.DEADLINE, opens_at=NOW, closes_at=NOW + 3 * HOUR)


@pytest.mark.parametrize(
    ("case", "expected"),
    [
        (timeline(MANUAL), Entry(None, True, None, None, None)),
        (
            timeline(MANUAL, activated_at=NOW),
            Entry(None, False, NOW + TEN_MIN, NOW, NOW + HOUR),
        ),
        (timeline(SCHEDULED), Entry(NOW, False, NOW + HOUR, NOW, NOW + HOUR)),
        (timeline(SCHEDULED, requires_activation=True), Entry(NOW, True, None, None, None)),
        (timeline(DEADLINE), Entry(NOW, False, NOW + 3 * HOUR, None, NOW + 3 * HOUR)),
        (timeline(Window(WindowKind.OPEN)), Entry(None, False, None, None, None)),
        (
            timeline(Window(WindowKind.OPEN), ended_at=NOW),
            Entry(None, False, NOW, None, NOW),
        ),
    ],
)
def test_entry_window(case: Timeline, expected: Entry) -> None:
    assert entry_window(case, []) == expected


def test_extensions_for_everyone_keep_a_shared_clock_open_longer() -> None:
    started = timeline(Window(WindowKind.MANUAL), activated_at=NOW)

    entry = entry_window(started, [ExtensionGrant(600, for_everyone=True, stage_index=None)])

    assert entry.closes_at == entry.ends_at == NOW + HOUR + TEN_MIN


def test_start_is_for_locked_or_activation_tests_only() -> None:
    ensure_activatable(timeline(MANUAL))
    ensure_activatable(timeline(Window(WindowKind.OPEN), requires_activation=True))

    with pytest.raises(ActivationNotRequired):
        ensure_activatable(timeline(Window(WindowKind.OPEN)))
    with pytest.raises(AssignmentCancelled):
        ensure_activatable(timeline(MANUAL, cancelled_at=NOW))


def test_joined_means_seen_in_the_last_30_seconds() -> None:
    assert is_joined(NOW - timedelta(seconds=30), now=NOW) is True
    assert is_joined(NOW - timedelta(seconds=31), now=NOW) is False


@pytest.mark.parametrize(
    ("case", "has_password", "locked"),
    [
        (timeline(MANUAL), False, True),
        (timeline(Window(WindowKind.OPEN)), False, False),
        (timeline(Window(WindowKind.OPEN)), True, True),
        (timeline(SCHEDULED, requires_activation=True), False, True),
    ],
)
def test_locked_means_waiting_for_start_or_a_password(
    case: Timeline, has_password: bool, locked: bool
) -> None:
    assert is_locked(case, has_password=has_password) is locked
