from importlib import import_module
from pathlib import Path

from django.apps import apps

from config.api import ROUTERS, api

MODULES_DIR = Path(__file__).resolve().parents[2] / "modules"


def test_every_module_with_routes_is_mounted() -> None:
    with_routes = sorted(path.parent.name for path in MODULES_DIR.glob("*/routes.py"))
    mounted = {id(router) for router in ROUTERS}

    for name in with_routes:
        assert id(import_module(f"modules.{name}.routes").router) in mounted, name


def test_every_module_is_an_installed_app() -> None:
    modules = {path.parent.name for path in MODULES_DIR.glob("*/apps.py")}

    assert len(modules) == 11
    assert all(apps.is_installed(f"modules.{name}") for name in modules)


def test_every_module_has_a_public_surface() -> None:
    for apps_file in MODULES_DIR.glob("*/apps.py"):
        assert (apps_file.parent / "public.py").exists(), apps_file.parent.name


def test_operation_ids_are_controller_names() -> None:
    operation = api.get_openapi_schema()["paths"]["/api/v1/healthz"]["get"]

    assert operation["operationId"] == "get_health"


def test_api_docs_are_off_outside_debug() -> None:
    # Tests run with DEBUG=False, like production
    assert api.docs_url is None
    assert api.openapi_url is None
