"""The image must contain all of the app's code (ADR-086). A `**/name` line in .dockerignore
drops every folder or file with that name anywhere: `**/tests` once dropped the student's
test gate (pages/tests) and the Test Library (pages/admin/tests) from the built SPA, and
the unit tests never noticed because they don't run the image."""

from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
# The source the image is built from; nothing in here may be ignored
SHIPPED = [REPO / "frontend" / "app", REPO / "backend" / "modules", REPO / "backend" / "core"]


def _anywhere_names() -> list[str]:
    """The names behind every `**/name` line: those match at any depth."""
    lines = (REPO / ".dockerignore").read_text(encoding="utf-8").splitlines()
    return [line.removeprefix("**/") for line in lines if line.startswith("**/")]


def _is_test_code(path: Path) -> bool:
    # Backend test folders are meant to stay out (backend/**/tests)
    return "tests" in path.relative_to(REPO).parts[:-1] and path.is_relative_to(REPO / "backend")


def test_no_ignore_line_drops_app_code() -> None:
    names = set(_anywhere_names())
    dropped = [
        path.relative_to(REPO).as_posix()
        for root in SHIPPED
        for path in root.rglob("*")
        if path.name in names and "__pycache__" not in path.parts and not _is_test_code(path)
    ]

    assert dropped == []


def test_the_test_folders_are_still_left_out() -> None:
    lines = (REPO / ".dockerignore").read_text(encoding="utf-8").splitlines()

    assert {"backend/**/tests", "frontend/tests"} <= set(lines)
