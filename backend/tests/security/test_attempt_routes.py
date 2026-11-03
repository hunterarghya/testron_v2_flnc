"""A student can't reopen, reset, delete or rewrite their own attempt (security.md §5, V1
F-05): no such route exists, and status changes only through the commands."""

from tests.security.operations import all_operations


def test_v1_f05_attempt_has_no_patch_or_delete() -> None:
    attempt_routes = [op for op in all_operations() if op.path.startswith("/api/v1/attempts/")]
    assert attempt_routes
    assert all(op.method in ("GET", "POST", "PUT") for op in attempt_routes)
    puts = {op.path for op in attempt_routes if op.method == "PUT"}
    assert puts == {"/api/v1/attempts/{attempt_id}/responses/{question_id}"}
