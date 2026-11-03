"""The only names other modules may import from authoring (R-08)."""

from modules.authoring.domain.freeze import FrozenTest, TimingOverride, paper_questions
from modules.authoring.domain.values import TimingKind
from modules.authoring.services.commands.ensure_app_settings import ensure_app_settings
from modules.authoring.services.commands.freeze_test import freeze_test
from modules.authoring.services.queries.get_app_info import get_coaching_name

__all__ = [
    "FrozenTest",
    "TimingKind",
    "TimingOverride",
    "ensure_app_settings",
    "freeze_test",
    "get_coaching_name",
    "paper_questions",
]
