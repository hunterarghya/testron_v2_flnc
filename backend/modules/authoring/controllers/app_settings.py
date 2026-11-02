from django.http import HttpRequest

from core.http.context import ctx_from
from modules.authoring.dto.app_settings import AppInfoOut, AppSettingsOut, AppSettingsPatchIn
from modules.authoring.services.commands import update_app_settings as updating
from modules.authoring.services.queries import get_app_info as app_info
from modules.authoring.services.queries import get_app_settings as reading


def get_app_info(request: HttpRequest) -> AppInfoOut:
    return AppInfoOut.from_info(app_info.get_app_info())


def get_app_settings(request: HttpRequest) -> AppSettingsOut:
    return AppSettingsOut.from_view(reading.get_app_settings(ctx_from(request)))


def update_app_settings(request: HttpRequest, payload: AppSettingsPatchIn) -> AppSettingsOut:
    settings = updating.update_app_settings(ctx_from(request), changes=payload.changes())
    return AppSettingsOut.from_view(settings)
