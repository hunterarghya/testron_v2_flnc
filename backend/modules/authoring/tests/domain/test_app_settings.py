"""Teacher defaults and branding rules (database_schema.md §3.4, domain_model.md §4.2)."""

from dataclasses import replace
from decimal import Decimal

import pytest

from modules.authoring.domain.app_settings import (
    DEFAULT_APP_SETTINGS,
    apply_changes,
    settings_errors,
)
from modules.authoring.domain.settings_rules import marks_error, range_error


def test_the_defaults_are_valid() -> None:
    assert settings_errors(DEFAULT_APP_SETTINGS) == []


def test_changes_tidy_the_name_and_keep_the_rest() -> None:
    changed = apply_changes(DEFAULT_APP_SETTINGS, {"coaching_name": "  Sen's   Biology "})

    assert changed.coaching_name == "Sen's Biology"
    assert changed.default_marks == DEFAULT_APP_SETTINGS.default_marks


@pytest.mark.parametrize(
    ("value", "zero_allowed", "ok"),
    [
        (Decimal("4"), False, True),
        (Decimal("0.25"), False, True),
        (Decimal("99999.99"), False, True),
        (Decimal(0), False, False),
        (Decimal(0), True, True),
        (Decimal("-1"), True, False),
        (Decimal("0.125"), True, False),
        (Decimal("100000"), True, False),
        (Decimal("NaN"), True, False),
        (Decimal("Infinity"), True, False),
    ],
)
def test_marks_rules(value: Decimal, zero_allowed: bool, ok: bool) -> None:
    assert (marks_error("marks", value, zero_allowed=zero_allowed) is None) is ok


@pytest.mark.parametrize(("value", "ok"), [(-1, False), (0, True), (60, True), (61, False)])
def test_range_rule_includes_both_ends(value: int, ok: bool) -> None:
    assert (range_error("grace", value, (0, 60)) is None) is ok


def test_every_broken_value_is_reported_at_once() -> None:
    broken = replace(
        DEFAULT_APP_SETTINGS,
        coaching_name="",
        default_marks=Decimal(0),
        default_negative_marks=Decimal("-1"),
        default_integrity_grace_s=61,
        default_integrity_max_warnings=0,
    )

    assert [error.field for error in settings_errors(broken)] == [
        "coaching_name",
        "default_marks",
        "default_negative_marks",
        "default_integrity_grace_s",
        "default_integrity_max_warnings",
    ]


def test_a_name_over_80_characters_is_refused() -> None:
    assert settings_errors(replace(DEFAULT_APP_SETTINGS, coaching_name="x" * 81))
