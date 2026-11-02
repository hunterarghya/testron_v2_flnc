from django.db import transaction

from core.context import Ctx
from core.errors import FieldError, FieldsInvalid
from modules.authoring.domain.app_settings import (
    AppSettingsChanges,
    AppSettingsView,
    apply_changes,
    settings_errors,
)
from modules.authoring.policies import ensure_teacher
from modules.authoring.repositories import app_settings
from modules.media import public as media


def update_app_settings(ctx: Ctx, *, changes: AppSettingsChanges) -> AppSettingsView:
    """Change some of the teacher's defaults or the branding (T-19, database_schema.md §3.4).

    Only the fields sent change. New tests take the defaults; existing tests keep their own
    settings. The logo must be an image uploaded here (`media.is_allowed_image_url`).
    """
    ensure_teacher(ctx.actor)
    with transaction.atomic():
        app_settings.insert_default_app_settings(now=ctx.now)
        updated = apply_changes(app_settings.lock_app_settings(), changes)
        errors = settings_errors(updated)
        if "logo_url" in changes and not _is_allowed_logo(updated.logo_url):
            errors.append(FieldError("logo_url", "invalid", "Upload the logo here"))
        if errors:
            raise FieldsInvalid(*errors)
        return app_settings.save_app_settings(updated, now=ctx.now)


def _is_allowed_logo(url: str | None) -> bool:
    # Removing the logo is always fine
    return url is None or media.is_allowed_image_url(url)
