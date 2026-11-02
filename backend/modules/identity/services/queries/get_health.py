import logging
from dataclasses import dataclass
from datetime import datetime

from django.db import DatabaseError

from core.config import get_settings
from core.context import Ctx
from modules.identity.domain.errors import DatabaseUnavailable
from modules.identity.repositories import health

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class HealthView:
    server_now: datetime
    version: str
    commit: str


def get_health(ctx: Ctx, *, deep: bool) -> HealthView:
    """Say the app is alive, with the server time and the running version.

    Anyone may ask: hosts use it as the liveness check, and open lobby, gate and exam
    pages ping it to keep a sleeping host awake (api_contract.md §2.1, §4). With
    `deep`, the database must answer too; deploy checks use that.
    """
    if deep:
        _ensure_database_answers()
    settings = get_settings()
    return HealthView(server_now=ctx.now, version=settings.app_version, commit=settings.app_commit)


def _ensure_database_answers() -> None:
    try:
        health.ping_database()
    except DatabaseError as error:
        logger.warning("database ping failed", exc_info=True)
        raise DatabaseUnavailable() from error
