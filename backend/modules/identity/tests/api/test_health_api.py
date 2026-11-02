import pytest
from django.db import OperationalError
from django.test import Client

from core.clock import FrozenClock
from modules.identity.repositories import health

URL = "/api/v1/healthz"


def test_health_is_public_and_returns_server_time(
    client: Client, frozen_clock: FrozenClock
) -> None:
    response = client.get(URL)

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "server_now": "2026-11-12T04:30:00Z",
        "version": "dev",
        "commit": "unknown",
    }


def test_health_response_carries_a_request_id(client: Client) -> None:
    assert client.get(URL).has_header("X-Request-ID")


@pytest.mark.django_db
def test_deep_health_checks_the_database(client: Client) -> None:
    assert client.get(URL, {"deep": "1"}).status_code == 200


def test_deep_health_is_503_problem_when_the_database_is_down(
    client: Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken_database() -> None:
        raise OperationalError("connection refused")

    monkeypatch.setattr(health, "ping_database", broken_database)

    response = client.get(URL, {"deep": "1"})

    assert response.status_code == 503
    assert response["Content-Type"] == "application/problem+json"
    assert response.json()["code"] == "database_unavailable"
    assert "connection refused" not in response.content.decode()


def test_bad_deep_value_is_a_validation_error(client: Client) -> None:
    response = client.get(URL, {"deep": "maybe"})

    assert response.status_code == 422
    assert response.json()["errors"][0]["field"] == "deep"
