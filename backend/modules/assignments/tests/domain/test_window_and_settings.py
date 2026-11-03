"""Window, publication, integrity, title and password rules (domain_model.md §3.5)."""

from datetime import UTC, datetime, timedelta

import pytest

from core.errors import FieldsInvalid
from modules.assignments.domain.settings import (
    Integrity,
    PasswordMismatch,
    Publication,
    assignment_title,
    checked_password,
    content_hash,
    ensure_integrity_valid,
    ensure_publication_valid,
)
from modules.assignments.domain.values import PublicationMode, WindowKind
from modules.assignments.domain.window import Window, ensure_window_valid

NOW = datetime(2026, 11, 12, 10, 0, tzinfo=UTC)
HOUR = timedelta(hours=1)


@pytest.mark.parametrize(
    "window",
    [
        Window(WindowKind.MANUAL),
        Window(WindowKind.MANUAL, planned_at=NOW + HOUR, late_entry_s=600),
        Window(WindowKind.SCHEDULED, starts_at=NOW + HOUR, late_entry_s=0),
        Window(WindowKind.DEADLINE, opens_at=NOW, closes_at=NOW + HOUR),
        Window(WindowKind.OPEN),
    ],
)
def test_valid_windows(window: Window) -> None:
    ensure_window_valid(window, now=NOW, total_duration_s=3600)


@pytest.mark.parametrize(
    ("window", "field"),
    [
        (Window(WindowKind.SCHEDULED, starts_at=NOW), "window.starts_at"),
        (Window(WindowKind.SCHEDULED), "window.starts_at"),
        (Window(WindowKind.DEADLINE, opens_at=NOW, closes_at=NOW), "window.closes_at"),
        (Window(WindowKind.DEADLINE, opens_at=NOW), "window.closes_at"),
        # Shorter than the test itself
        (
            Window(WindowKind.DEADLINE, opens_at=NOW, closes_at=NOW + timedelta(minutes=59)),
            "window.closes_at",
        ),
        (Window(WindowKind.OPEN, late_entry_s=60), "window.late_entry_s"),
        (Window(WindowKind.MANUAL, late_entry_s=-1), "window.late_entry_s"),
    ],
)
def test_invalid_windows(window: Window, field: str) -> None:
    with pytest.raises(FieldsInvalid) as error:
        ensure_window_valid(window, now=NOW, total_duration_s=3600)

    assert error.value.field_errors()[0].field == field


def test_common_clock_windows() -> None:
    assert [Window(k).common_clock for k in WindowKind] == [True, True, False, False]


def test_publication_delay_only_when_delayed() -> None:
    ensure_publication_valid(Publication())
    ensure_publication_valid(Publication(mode=PublicationMode.AUTO_DELAYED, delay_s=3600))
    for wrong in (Publication(mode=PublicationMode.AUTO_DELAYED), Publication(delay_s=60)):
        with pytest.raises(FieldsInvalid):
            ensure_publication_valid(wrong)


def test_integrity_ranges() -> None:
    ensure_integrity_valid(Integrity(5, 3, "AUTO_SUBMIT"))
    with pytest.raises(FieldsInvalid) as error:
        ensure_integrity_valid(Integrity(61, 0, "AUTO_SUBMIT"))

    assert [e.field for e in error.value.field_errors()] == [
        "integrity.grace_s",
        "integrity.max_warnings",
    ]


def test_title_and_password() -> None:
    assert assignment_title("  Cell   test ") == "Cell test"
    assert checked_password("Bio 2026", "Bio 2026") == "Bio 2026"
    with pytest.raises(FieldsInvalid):
        assignment_title(" ")
    with pytest.raises(FieldsInvalid):
        checked_password("abc", "abc")
    with pytest.raises(PasswordMismatch):
        checked_password("bio-2026", "bio-2025")


def test_content_hash_ignores_key_order() -> None:
    assert content_hash({"a": 1, "b": "কোষ"}) == content_hash({"b": "কোষ", "a": 1})
    assert len(content_hash({})) == 64
