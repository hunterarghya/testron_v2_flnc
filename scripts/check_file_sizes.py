"""Fail when a source file is longer than its limit (project_structure.md §1.2, ADR-031).

A file over its limit is a design signal: split it by responsibility. Limits are never
raised for one file.

Usage: python scripts/check_file_sizes.py [repo_dir]
"""

import os
import sys
from collections.abc import Iterator
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROOTS = ("backend", "frontend", "scripts")

PYTHON = 200
PYTHON_SERVICE = 120
TEST = 400
VUE = 200
VUE_PAGE = 80
TYPESCRIPT = 200

# Generated or third-party files are not ours to split (S-07)
_SKIPPED_DIRS = frozenset(
    {
        ".venv",
        "node_modules",
        ".nuxt",
        ".output",
        "dist",
        "__pycache__",
        ".mypy_cache",
        ".ruff_cache",
        ".pytest_cache",
        "migrations",
        "coverage",
        "test-results",
    }
)
_SKIPPED_FILES = frozenset({"schema.d.ts"})
_TS_TEST_SUFFIXES = (".spec.ts", ".test.ts")


def limit_for(path: Path) -> int | None:
    """The line limit for a file, or None when the file has no limit."""
    if path.name in _SKIPPED_FILES:
        return None
    if path.suffix == ".py":
        return _python_limit(path)
    if path.suffix == ".vue":
        return VUE_PAGE if "pages" in path.parts else VUE
    if path.suffix == ".ts":
        return TEST if _is_test(path) else TYPESCRIPT
    return None


def oversized_files(repo: Path) -> Iterator[tuple[Path, int, int]]:
    """(path, lines, limit) for every file over its limit."""
    for path in _source_files(repo):
        limit = limit_for(path.relative_to(repo))
        if limit is None:
            continue
        lines = len(path.read_text(encoding="utf-8").splitlines())
        if lines > limit:
            yield path.relative_to(repo), lines, limit


def _python_limit(path: Path) -> int:
    if _is_test(path):
        return TEST
    if "services" in path.parts and {"commands", "queries"} & set(path.parts):
        return PYTHON_SERVICE
    return PYTHON


def _is_test(path: Path) -> bool:
    return (
        "tests" in path.parts
        or path.name.startswith("test_")
        or path.name == "conftest.py"
        or path.name.endswith(_TS_TEST_SUFFIXES)
    )


def _source_files(repo: Path) -> Iterator[Path]:
    for root in ROOTS:
        for folder, dirs, files in os.walk(repo / root):
            # Pruned in place, so node_modules and .venv are never even listed
            dirs[:] = sorted(name for name in dirs if name not in _SKIPPED_DIRS)
            yield from (Path(folder) / name for name in sorted(files))


def main(argv: list[str]) -> int:
    repo = Path(argv[1]) if len(argv) > 1 else REPO
    oversized = list(oversized_files(repo))
    for path, lines, limit in oversized:
        sys.stdout.write(f"{path.as_posix()}: {lines} lines (limit {limit})\n")
    sys.stdout.write(f"File sizes: {len(oversized)} file(s) over the limit\n")
    return 1 if oversized else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
