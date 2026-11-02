from pathlib import Path

import pytest
from django.test import Client
from pytest_django.fixtures import Settings as DjangoSettings

SHELL = "<!doctype html><div id='__nuxt'></div>"


@pytest.fixture
def built_spa(tmp_path: Path, settings: DjangoSettings) -> Path:
    (tmp_path / "200.html").write_text(SHELL, encoding="utf-8")
    settings.SPA_BUILD_DIR = tmp_path
    return tmp_path


@pytest.mark.usefixtures("built_spa")
@pytest.mark.parametrize("route", ["/admin/tests/123", "/attempts/abc", "/login", "/nope"])
def test_app_routes_get_the_spa_shell(client: Client, route: str) -> None:
    response = client.get(route)

    assert response.status_code == 200
    assert response.content.decode() == SHELL
    assert response["Cache-Control"] == "no-cache"


@pytest.mark.usefixtures("built_spa")
def test_unknown_api_path_is_still_a_404(client: Client) -> None:
    assert client.get("/api/v1/does-not-exist").status_code == 404


def test_no_shell_without_a_build(client: Client, settings: DjangoSettings, tmp_path: Path) -> None:
    settings.SPA_BUILD_DIR = tmp_path

    assert client.get("/admin").status_code == 404


@pytest.mark.usefixtures("built_spa")
def test_unknown_api_path_is_a_problem_not_a_page(client: Client) -> None:
    response = client.get("/api/v2/anything")

    assert response.status_code == 404
    assert response["Content-Type"] == "application/problem+json"
    assert response.json()["code"] == "not_found"
