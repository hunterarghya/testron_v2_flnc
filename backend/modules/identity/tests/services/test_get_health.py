from datetime import UTC, datetime

import pytest
from django.db import OperationalError

from core.context import ANONYMOUS, Ctx
from modules.identity.domain.errors import DatabaseUnavailable
from modules.identity.repositories import health
from modules.identity.services.queries.get_health import get_health

NOON = datetime(2026, 11, 12, 4, 30, tzinfo=UTC)
CTX = Ctx(actor=ANONYMOUS, now=NOON, request_id="req-test")


def broken_database() -> None:
    raise OperationalError("connection refused")


def test_health_reports_server_time_and_version() -> None:
    view = get_health(CTX, deep=False)

    assert view.server_now == NOON
    assert (view.version, view.commit) == ("dev", "unknown")


def test_shallow_check_never_touches_the_database(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(health, "ping_database", broken_database)

    assert get_health(CTX, deep=False).server_now == NOON


@pytest.mark.django_db
def test_deep_check_passes_when_the_database_answers() -> None:
    assert get_health(CTX, deep=True).server_now == NOON


def test_deep_check_fails_when_the_database_is_down(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(health, "ping_database", broken_database)

    with pytest.raises(DatabaseUnavailable):
        get_health(CTX, deep=True)
