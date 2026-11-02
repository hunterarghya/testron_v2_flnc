from core.context import Ctx
from modules.authoring.repositories import app_settings


def ensure_app_settings(ctx: Ctx) -> bool:
    """Create the settings row with the defaults if it's missing (`manage.py seed`,
    database_schema.md §6). Never overwrites the teacher's choices. True when created."""
    return app_settings.insert_default_app_settings(now=ctx.now)
