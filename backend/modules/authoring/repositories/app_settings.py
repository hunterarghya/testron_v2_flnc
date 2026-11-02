from dataclasses import asdict
from datetime import datetime

from core.db.locking import for_update
from modules.authoring.domain.app_settings import DEFAULT_APP_SETTINGS, AppSettingsView
from modules.authoring.domain.values import IntegrityAction
from modules.authoring.models import AppSettings

_ROW_ID = 1


def _view(row: AppSettings) -> AppSettingsView:
    return AppSettingsView(
        coaching_name=row.coaching_name,
        logo_url=row.logo_url,
        default_marks=row.default_marks,
        default_negative_marks=row.default_negative_marks,
        default_integrity_grace_s=row.default_integrity_grace_s,
        default_integrity_max_warnings=row.default_integrity_max_warnings,
        default_integrity_action=IntegrityAction(row.default_integrity_action),
        updated_at=row.updated_at,
    )


def find_app_settings() -> AppSettingsView | None:
    row = AppSettings.objects.filter(pk=_ROW_ID).first()
    return _view(row) if row else None


def insert_default_app_settings(*, now: datetime) -> bool:
    """Create the row with the defaults unless it exists. True when it was created."""
    values = asdict(DEFAULT_APP_SETTINGS) | {"updated_at": now}
    # get_or_create also copes with two callers creating it at the same moment
    _, created = AppSettings.objects.get_or_create(pk=_ROW_ID, defaults=values)
    return created


def lock_app_settings() -> AppSettingsView:
    return _view(for_update(AppSettings.objects.filter(pk=_ROW_ID)).get())


def save_app_settings(settings: AppSettingsView, *, now: datetime) -> AppSettingsView:
    values = asdict(settings) | {"updated_at": now}
    AppSettings.objects.filter(pk=_ROW_ID).update(**values)
    return _view(AppSettings.objects.get(pk=_ROW_ID))
