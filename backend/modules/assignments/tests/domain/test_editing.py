"""What may change and when results come out (domain_model.md §3.5 #5-6, §7)."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from modules.assignments.domain.editing import (
    AFTER_START,
    BEFORE_START,
    PublicationState,
    editable_fields,
    ensure_cancellable,
    ensure_editable,
    publication_state,
    publish_at,
)
from modules.assignments.domain.errors import (
    AssignmentCancelled,
    AssignmentHasAttempts,
    AssignmentStarted,
)
from modules.assignments.domain.lifecycle import Timeline
from modules.assignments.domain.settings import Publication
from modules.assignments.domain.values import PublicationMode as M
from modules.assignments.domain.values import WindowKind
from modules.assignments.domain.window import Window

NOW = datetime(2026, 11, 12, 10, 0, tzinfo=UTC)
TIMELINE = Timeline(Window(WindowKind.MANUAL), requires_activation=False, total_duration_s=600)


@pytest.mark.parametrize(
    ("cancelled", "started", "fields"),
    [(True, False, ()), (True, True, ()), (False, False, BEFORE_START), (False, True, AFTER_START)],
)
def test_editable_fields(cancelled: bool, started: bool, fields: tuple[str, ...]) -> None:
    assert editable_fields(cancelled=cancelled, started=started) == fields


def test_after_the_start_only_title_publication_and_password_change() -> None:
    ensure_editable(["title", "publication", "password"], cancelled=False, started=True)

    with pytest.raises(AssignmentStarted) as raised:
        ensure_editable(["title", "window"], cancelled=False, started=True)
    assert raised.value.context == {"editable_fields": list(AFTER_START)}


def test_a_cancelled_assignment_changes_nothing_not_even_the_audience() -> None:
    with pytest.raises(AssignmentCancelled):
        ensure_editable([], cancelled=True, started=False)


def test_cancel_before_anyone_begins_and_before_start() -> None:
    ensure_cancellable(TIMELINE, has_attempts=False)

    with pytest.raises(AssignmentHasAttempts):
        ensure_cancellable(TIMELINE, has_attempts=True)
    with pytest.raises(AssignmentStarted):
        ensure_cancellable(replace(TIMELINE, activated_at=NOW), has_attempts=False)
    with pytest.raises(AssignmentCancelled):
        ensure_cancellable(replace(TIMELINE, cancelled_at=NOW), has_attempts=False)


@pytest.mark.parametrize(
    ("mode", "published_at", "state"),
    [
        (M.MANUAL, None, PublicationState.UNPUBLISHED),
        (M.AUTO_IMMEDIATE, None, PublicationState.SCHEDULED),
        (M.AUTO_DELAYED, None, PublicationState.SCHEDULED),
        (M.MANUAL, NOW, PublicationState.PUBLISHED),
    ],
)
def test_publication_state(mode: M, published_at: datetime | None, state: PublicationState) -> None:
    delay = 60 if mode is M.AUTO_DELAYED else None
    assert publication_state(Publication(mode=mode, delay_s=delay), published_at) is state


@pytest.mark.parametrize(
    ("publication", "end", "expected"),
    [
        (Publication(), NOW, None),
        (Publication(mode=M.AUTO_IMMEDIATE), None, None),
        (Publication(mode=M.AUTO_IMMEDIATE), NOW, NOW),
        (Publication(mode=M.AUTO_DELAYED, delay_s=3600), NOW, NOW + timedelta(hours=1)),
    ],
)
def test_publish_at(
    publication: Publication, end: datetime | None, expected: datetime | None
) -> None:
    assert publish_at(publication, end) == expected
