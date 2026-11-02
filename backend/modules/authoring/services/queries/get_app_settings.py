from core.context import Ctx
from modules.authoring.domain.app_settings import DEFAULT_APP_SETTINGS, AppSettingsView
from modules.authoring.policies import ensure_teacher
from modules.authoring.repositories import app_settings


def get_app_settings(ctx: Ctx) -> AppSettingsView:
    """The teacher's defaults and branding for T-19 (the defaults until first saved)."""
    ensure_teacher(ctx.actor)
    return app_settings.find_app_settings() or DEFAULT_APP_SETTINGS
