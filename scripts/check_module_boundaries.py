"""Fail when a module imports another module's internals (project_structure.md §4.1, R-08).

`modules.X` may import `modules.Y` only through `modules.Y.public`. Import-linter can't
express that rule concisely, so this script reads every module file's imports.

Usage: python scripts/check_module_boundaries.py [backend_dir]
"""

import ast
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"
# Positions in a dotted name: modules.<module>.<layer>
_MODULE = 1
_LAYER = 2


@dataclass(frozen=True, slots=True)
class Violation:
    path: Path
    line: int
    imported: str

    def __str__(self) -> str:
        target = self.imported.split(".")[_MODULE]
        return (
            f"{self.path}:{self.line}: imports {self.imported} "
            f"(only modules.{target}.public may be imported)"
        )


def find_violations(backend: Path) -> list[Violation]:
    violations: list[Violation] = []
    for path in sorted((backend / "modules").rglob("*.py")):
        own = path.relative_to(backend / "modules").parts[0]
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        violations += [
            Violation(path, line, name)
            for line, name in imported_names(tree)
            if is_forbidden(name, own_module=own)
        ]
    return violations


def imported_names(tree: ast.AST) -> Iterator[tuple[int, str]]:
    """Every dotted name an import statement brings in, with its line."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            yield from ((node.lineno, alias.name) for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            yield from ((node.lineno, name) for name in _from_import_names(node))


def is_forbidden(name: str, *, own_module: str) -> bool:
    parts = name.split(".")
    if parts[0] != "modules" or len(parts) <= _MODULE or parts[_MODULE] == own_module:
        return False
    return len(parts) <= _LAYER or parts[_LAYER] != "public"


def _from_import_names(node: ast.ImportFrom) -> list[str]:
    module = node.module or ""
    # `from modules.x.public import f` names the module itself;
    # `from modules.x import repositories` names what it pulls out of the package
    if len(module.split(".")) > _LAYER:
        return [module]
    return [f"{module}.{alias.name}" for alias in node.names]


def main(argv: list[str]) -> int:
    backend = Path(argv[1]) if len(argv) > 1 else BACKEND
    violations = find_violations(backend)
    for violation in violations:
        sys.stdout.write(f"{violation}\n")
    sys.stdout.write(f"Module boundaries: {len(violations)} violation(s)\n")
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
