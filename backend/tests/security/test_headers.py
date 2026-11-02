"""Security headers (architecture.md §5.15, security.md §4.3)."""

from pathlib import Path

import pytest
from django.test import Client
from pytest_django.fixtures import Settings as DjangoSettings

from core.http.csp import inline_script_hashes

pytestmark = pytest.mark.django_db
SHELL = (
    '<!doctype html><script type="importmap">{"imports":{}}</script>'
    '<script type="module" src="/_nuxt/entry.js"></script>'
    "<script>window.__NUXT__={};</script>"
    '<script type="application/json" id="__NUXT_DATA__">[]</script>'
)


def csp_directives(header: str) -> dict[str, list[str]]:
    parts = (directive.split() for directive in header.split(";"))
    return {words[0]: words[1:] for words in parts if words}


def test_api_responses_carry_the_security_headers(client: Client) -> None:
    response = client.get("/api/v1/healthz")

    csp = csp_directives(response["Content-Security-Policy"])
    assert csp["script-src"] == ["'self'"]
    assert csp["frame-ancestors"] == ["'none'"]
    assert csp["default-src"] == ["'self'"]
    assert csp["img-src"] == ["'self'", "https://ik.imagekit.io", "data:"]
    assert response["X-Content-Type-Options"] == "nosniff"
    assert response["Referrer-Policy"] == "same-origin"
    assert response["Permissions-Policy"] == "camera=(), microphone=(), geolocation=()"
    assert response["Cache-Control"] == "no-store"


def test_problem_responses_are_not_cached_either(client: Client) -> None:
    assert client.get("/api/v1/nope")["Cache-Control"] == "no-store"


def test_spa_inline_scripts_are_allowed_by_hash_only(
    client: Client, settings: DjangoSettings, tmp_path: Path
) -> None:
    (tmp_path / "200.html").write_text(SHELL, encoding="utf-8")
    settings.SPA_BUILD_DIR = tmp_path

    response = client.get("/admin/students")

    script_src = csp_directives(response["Content-Security-Policy"])["script-src"]
    assert script_src == ["'self'", *sorted(inline_script_hashes(SHELL))]
    assert "'unsafe-inline'" not in script_src
    assert "Cache-Control" not in response or response["Cache-Control"] == "no-cache"


def test_hsts_is_sent_in_production(client: Client, settings: DjangoSettings) -> None:
    settings.SECURE_HSTS_SECONDS = 31_536_000
    settings.SECURE_HSTS_INCLUDE_SUBDOMAINS = True

    response = client.get("/api/v1/healthz", secure=True)

    assert response["Strict-Transport-Security"] == "max-age=31536000; includeSubDomains"
