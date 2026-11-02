"""Fail when a folder's test coverage is below its gate (testing_strategy.md §6).

coverage.py can only enforce one overall number (`fail_under`), so the stricter
per-folder gates are checked here from its JSON report (`coverage json`).

Usage: python scripts/check_coverage.py backend/coverage.json
"""

import json
import sys
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path, PurePath


@dataclass(frozen=True, slots=True)
class Gate:
    name: str
    patterns: tuple[str, ...]
    minimum: float
    # True: every line and every branch counts. False: lines only.
    branches: bool


GATES = (
    Gate("domain + policies", ("modules/*/domain/*", "modules/*/policies.py"), 100, True),
    Gate("services", ("modules/*/services/*",), 90, False),
)


CoverageFiles = dict[str, dict[str, dict[str, int]]]


def gate_results(files: CoverageFiles) -> list[tuple[Gate, float]]:
    """(gate, percent) for every gate; a scope with no code counts as fully covered."""
    return [(gate, _percent(gate, _summaries(files, gate))) for gate in GATES]


def _summaries(files: CoverageFiles, gate: Gate) -> list[dict[str, int]]:
    return [
        data["summary"]
        for path, data in files.items()
        if any(fnmatch(PurePath(path).as_posix(), pattern) for pattern in gate.patterns)
    ]


def _percent(gate: Gate, summaries: list[dict[str, int]]) -> float:
    covered = sum(summary["covered_lines"] for summary in summaries)
    total = sum(summary["num_statements"] for summary in summaries)
    if gate.branches:
        covered += sum(summary.get("covered_branches", 0) for summary in summaries)
        total += sum(summary.get("num_branches", 0) for summary in summaries)
    return 100.0 if total == 0 else 100.0 * covered / total


def main(argv: list[str]) -> int:
    files: CoverageFiles = json.loads(Path(argv[1]).read_text(encoding="utf-8"))["files"]
    failed = 0
    for gate, percent in gate_results(files):
        ok = percent >= gate.minimum
        failed += not ok
        verdict = "ok" if ok else "FAIL"
        sys.stdout.write(f"{verdict}: {gate.name} {percent:.1f}% (gate {gate.minimum:g}%)\n")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
