from check_coverage import CoverageFiles, gate_results


def summary(
    lines: tuple[int, int], branches: tuple[int, int] = (0, 0)
) -> dict[str, dict[str, int]]:
    return {
        "summary": {
            "covered_lines": lines[0],
            "num_statements": lines[1],
            "covered_branches": branches[0],
            "num_branches": branches[1],
        }
    }


def percents(files: CoverageFiles) -> dict[str, float]:
    return {gate.name: percent for gate, percent in gate_results(files)}


def test_empty_scopes_count_as_covered() -> None:
    assert percents({}) == {"domain + policies": 100.0, "services": 100.0}


def test_a_missed_domain_branch_fails_the_domain_gate() -> None:
    files = {"modules/delivery/domain/timeline.py": summary((10, 10), (3, 4))}

    assert percents(files)["domain + policies"] < 100


def test_policies_count_towards_the_domain_gate() -> None:
    files = {"modules/delivery/policies.py": summary((1, 2))}

    assert percents(files)["domain + policies"] == 50.0


def test_services_gate_counts_lines_only() -> None:
    files = {"modules/delivery/services/commands/start.py": summary((9, 10), (0, 4))}

    assert percents(files)["services"] == 90.0


def test_windows_paths_are_matched() -> None:
    files = {"modules\\delivery\\domain\\plan.py": summary((1, 2))}

    assert percents(files)["domain + policies"] == 50.0


def test_files_outside_the_gates_are_ignored() -> None:
    files = {"core/config.py": summary((0, 10))}

    assert percents(files) == {"domain + policies": 100.0, "services": 100.0}
