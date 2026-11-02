from dataclasses import dataclass

from modules.authoring.domain.app_settings import DEFAULT_APP_SETTINGS
from modules.authoring.repositories import app_settings


@dataclass(frozen=True, slots=True)
class AppInfo:
    coaching_name: str
    logo_url: str | None


def get_app_info() -> AppInfo:
    """The branding every screen's header shows, to anyone, logged in or not (`GET /app`).

    Public on purpose, so it has no policy: the name and logo are on every page anyway.
    Emails use the same name (core.mail, backlog O-11).
    """
    settings = app_settings.find_app_settings() or DEFAULT_APP_SETTINGS
    return AppInfo(coaching_name=settings.coaching_name, logo_url=settings.logo_url)


def get_coaching_name() -> str:
    """For core.mail's `MAIL_BRAND_NAME` hook (ADR-060)."""
    return get_app_info().coaching_name
