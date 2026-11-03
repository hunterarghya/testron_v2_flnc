"""HTTP clients logged in through the real login endpoint, for API tests."""

from collections.abc import Mapping
from typing import Any

from django.test import Client

# The factories' default password (tests/factories/identity.py)
DEFAULT_PASSWORD = "correct-horse-battery"


def logged_in(email: str, password: str = DEFAULT_PASSWORD) -> Client:
    client = Client()
    response = client.post(
        "/api/v1/auth/login",
        {"email": email, "password": password},
        content_type="application/json",
    )
    if response.status_code != 200:
        raise AssertionError(f"login as {email} failed: {response.status_code}")
    return client


def send(
    client: Client,
    method: str,
    path: str,
    body: Mapping[str, object] | None = None,
    *,
    headers: Mapping[str, str] | None = None,
) -> Any:
    """A JSON request; returns Django's test response."""
    return getattr(client, method)(
        path, body or {}, content_type="application/json", headers=dict(headers or {})
    )
