"""The only names other modules may import from authoring (R-08)."""

from modules.authoring.services.commands.ensure_app_settings import ensure_app_settings
from modules.authoring.services.queries.get_app_info import get_coaching_name

__all__ = ["ensure_app_settings", "get_coaching_name"]
