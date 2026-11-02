from datetime import datetime
from decimal import Decimal
from typing import Literal, Self, cast

from ninja import Schema
from pydantic import ConfigDict, Field

from modules.authoring.domain.app_settings import AppSettingsChanges, AppSettingsView
from modules.authoring.domain.values import IntegrityAction
from modules.authoring.services.queries.get_app_info import AppInfo

Action = Literal["AUTO_SUBMIT", "DISQUALIFY"]


class AppInfoOut(Schema):
    model_config = ConfigDict(extra="forbid")

    coaching_name: str
    logo_url: str | None

    @classmethod
    def from_info(cls, info: AppInfo) -> Self:
        return cls(coaching_name=info.coaching_name, logo_url=info.logo_url)


class AppSettingsOut(AppInfoOut):
    # Marks travel as decimal strings ("4.00"), never floats (CLAUDE.md rule 7)
    default_marks: Decimal
    default_negative_marks: Decimal
    default_integrity_grace_s: int
    default_integrity_max_warnings: int
    default_integrity_action: Action
    updated_at: datetime | None

    @classmethod
    def from_view(cls, settings: AppSettingsView) -> Self:
        return cls(
            coaching_name=settings.coaching_name,
            logo_url=settings.logo_url,
            default_marks=settings.default_marks,
            default_negative_marks=settings.default_negative_marks,
            default_integrity_grace_s=settings.default_integrity_grace_s,
            default_integrity_max_warnings=settings.default_integrity_max_warnings,
            default_integrity_action=settings.default_integrity_action.value,
            updated_at=settings.updated_at,
        )


class AppSettingsPatchIn(Schema):
    """Any subset of the settings. Values are checked by the use case, reported per field."""

    model_config = ConfigDict(extra="forbid")

    coaching_name: str | None = Field(default=None, max_length=200)
    # null removes the logo
    logo_url: str | None = Field(default=None, max_length=2048)
    default_marks: Decimal | None = Field(default=None, max_digits=7, decimal_places=2)
    default_negative_marks: Decimal | None = Field(default=None, max_digits=7, decimal_places=2)
    default_integrity_grace_s: int | None = None
    default_integrity_max_warnings: int | None = None
    default_integrity_action: Action | None = None

    def changes(self) -> AppSettingsChanges:
        """Only the fields that were sent. A sent null means "remove", which only the logo
        allows; for the others it means "leave as is"."""
        sent = self.model_dump(exclude_unset=True)
        changes = {
            name: value for name, value in sent.items() if value is not None or name == "logo_url"
        }
        if "default_integrity_action" in changes:
            changes["default_integrity_action"] = IntegrityAction(
                changes["default_integrity_action"]
            )
        return cast("AppSettingsChanges", changes)
