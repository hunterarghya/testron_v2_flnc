from pathlib import Path

import pytest
from check_module_boundaries import find_violations, is_forbidden, main

REPO_BACKEND = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    ("name", "forbidden"),
    [
        ("modules.identity.public", False),
        ("modules.delivery.repositories.attempts", False),  # own module
        ("modules.identity.repositories.users", True),
        ("modules.identity.models", True),
        ("modules.identity", True),
        ("core.http.areas", False),
        ("django.db", False),
    ],
)
def test_only_another_modules_public_api_may_be_imported(name: str, forbidden: bool) -> None:
    assert is_forbidden(name, own_module="delivery") is forbidden


def write_module_file(backend: Path, relative: str, source: str) -> None:
    path = backend / "modules" / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")


@pytest.mark.parametrize(
    "source",
    [
        "from modules.identity.repositories import users\n",
        "import modules.identity.models\n",
        "from modules.identity import repositories\n",
        "from modules import identity\n",
    ],
)
def test_import_of_another_modules_internals_is_found(tmp_path: Path, source: str) -> None:
    write_module_file(tmp_path, "delivery/services/x.py", source)

    violations = find_violations(tmp_path)

    assert [violation.line for violation in violations] == [1]


@pytest.mark.parametrize(
    "source",
    [
        "from modules.identity.public import get_user\n",
        "from modules.identity import public\n",
        "from modules.delivery.domain import timeline\n",
    ],
)
def test_allowed_imports_pass(tmp_path: Path, source: str) -> None:
    write_module_file(tmp_path, "delivery/services/x.py", source)

    assert find_violations(tmp_path) == []


def test_the_real_codebase_passes() -> None:
    assert main(["check", str(REPO_BACKEND)]) == 0
