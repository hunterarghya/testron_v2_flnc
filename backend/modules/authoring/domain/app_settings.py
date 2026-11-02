"""The teacher's defaults for new tests and the coaching centre's branding (database_schema.md
§3.4 `app_settings`, T-19). One row for the whole installation."""

from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal
from typing import TypedDict

from core.errors import FieldError
from core.text import clean_text_line
from modules.authoring.domain.settings_rules import (
    GRACE_SECONDS,
    MAX_WARNINGS,
    marks_error,
    range_error,
)
from modules.authoring.domain.values import IntegrityAction

MAX_COACHING_NAME_LENGTH = 80


@dataclass(frozen=True, slots=True)
class AppSettingsView:
    coaching_name: str
    logo_url: str | None
    default_marks: Decimal
    default_negative_marks: Decimal
    default_integrity_grace_s: int
    default_integrity_max_warnings: int
    default_integrity_action: IntegrityAction
    # None until the row exists
    updated_at: datetime | None


class AppSettingsChanges(TypedDict, total=False):
    """Only the fields the teacher changed (PATCH). `logo_url: None` removes the logo."""

    coaching_name: str
    logo_url: str | None
    default_marks: Decimal
    default_negative_marks: Decimal
    default_integrity_grace_s: int
    default_integrity_max_warnings: int
    default_integrity_action: IntegrityAction


# Until the teacher changes them (domain_model.md §4.2 defaults)
DEFAULT_APP_SETTINGS = AppSettingsView(
    coaching_name="Test Platform",
    logo_url=None,
    default_marks=Decimal("4.00"),
    default_negative_marks=Decimal("1.00"),
    default_integrity_grace_s=5,
    default_integrity_max_warnings=3,
    default_integrity_action=IntegrityAction.AUTO_SUBMIT,
    updated_at=None,
)


def apply_changes(current: AppSettingsView, changes: AppSettingsChanges) -> AppSettingsView:
    """The settings after the change, with the name tidied. Not checked yet."""
    if "coaching_name" in changes:
        changes = {**changes, "coaching_name": clean_text_line(changes["coaching_name"])}
    return replace(current, **changes)


def settings_errors(settings: AppSettingsView) -> list[FieldError]:
    """Every broken value at once, so the form can mark them all."""
    problems = [
        _name_error(settings.coaching_name),
        marks_error("default_marks", settings.default_marks, zero_allowed=False),
        marks_error("default_negative_marks", settings.default_negative_marks, zero_allowed=True),
        range_error("default_integrity_grace_s", settings.default_integrity_grace_s, GRACE_SECONDS),
        range_error(
            "default_integrity_max_warnings", settings.default_integrity_max_warnings, MAX_WARNINGS
        ),
    ]
    return [problem for problem in problems if problem is not None]


def _name_error(name: str) -> FieldError | None:
    if name and len(name) <= MAX_COACHING_NAME_LENGTH:
        return None
    return FieldError("coaching_name", "invalid", f"Use 1 to {MAX_COACHING_NAME_LENGTH} characters")
