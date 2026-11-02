from pathlib import Path

import pytest
from check_file_sizes import (
    PYTHON,
    PYTHON_SERVICE,
    TEST,
    TYPESCRIPT,
    VUE,
    VUE_PAGE,
    limit_for,
    main,
    oversized_files,
)

REPO = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize(
    ("path", "limit"),
    [
        ("backend/core/errors.py", PYTHON),
        ("backend/modules/delivery/services/commands/start_attempt.py", PYTHON_SERVICE),
        ("backend/modules/delivery/services/queries/get_monitor.py", PYTHON_SERVICE),
        ("backend/modules/delivery/tests/services/test_start_attempt.py", TEST),
        ("backend/conftest.py", TEST),
        ("frontend/app/features/gate/components/Gate.vue", VUE),
        ("frontend/app/pages/admin/index.vue", VUE_PAGE),
        ("frontend/app/engine/clock.ts", TYPESCRIPT),
        ("frontend/tests/e2e/locked_test.spec.ts", TEST),
        ("frontend/app/api/schema.d.ts", None),
        ("backend/uv.lock", None),
    ],
)
def test_each_kind_of_file_has_its_limit(path: str, limit: int | None) -> None:
    assert limit_for(Path(path)) == limit


def write_lines(path: Path, count: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("x = 1\n" * count, encoding="utf-8")


def test_a_250_line_service_fails(tmp_path: Path) -> None:
    write_lines(tmp_path / "backend/modules/m/services/commands/do_it.py", 250)

    assert list(oversized_files(tmp_path)) == [
        (Path("backend/modules/m/services/commands/do_it.py"), 250, PYTHON_SERVICE)
    ]


def test_a_file_at_its_limit_passes(tmp_path: Path) -> None:
    write_lines(tmp_path / "backend/core/x.py", PYTHON)

    assert list(oversized_files(tmp_path)) == []


def test_migrations_and_dependencies_are_skipped(tmp_path: Path) -> None:
    write_lines(tmp_path / "backend/modules/m/migrations/0001_initial.py", 900)
    write_lines(tmp_path / "backend/.venv/lib/big.py", 900)

    assert list(oversized_files(tmp_path)) == []


def test_the_real_codebase_passes() -> None:
    assert main(["check", str(REPO)]) == 0
