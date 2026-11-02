"""The area matrix (security.md §3.1): every route, as every kind of caller.

Each case asserts only the area decision: who is turned away at the door (401/403) and who
gets through. What happens after that (a 404, a 422 for an empty body) is the use case's
business and is tested elsewhere.
"""

from collections.abc import Callable
from enum import StrEnum

import pytest
from django.test import Client

from core.context import StudentStatus
from tests.factories.identity import make_user
from tests.factories.students import make_student
from tests.security.operations import ROUTE_AREAS, Area, Operation, all_operations, area_of

pytestmark = pytest.mark.django_db
OPERATIONS = all_operations()
DENIALS = frozenset({"not_authenticated", "forbidden", "account_not_active"})


class Caller(StrEnum):
    ANONYMOUS = "anonymous"
    PENDING_STUDENT = "pending-student"
    ACTIVE_STUDENT = "active-student"
    TEACHER = "teacher"


# security.md §3.1: the problem code each caller gets, or None when let through
EXPECTED: dict[Area, dict[Caller, str | None]] = {
    Area.PUBLIC: dict.fromkeys(Caller),
    Area.SIGNED_IN: {
        Caller.ANONYMOUS: "not_authenticated",
        Caller.PENDING_STUDENT: None,
        Caller.ACTIVE_STUDENT: None,
        Caller.TEACHER: None,
    },
    Area.TEACHER: {
        Caller.ANONYMOUS: "not_authenticated",
        Caller.PENDING_STUDENT: "forbidden",
        Caller.ACTIVE_STUDENT: "forbidden",
        Caller.TEACHER: None,
    },
    Area.STUDENT: {
        Caller.ANONYMOUS: "not_authenticated",
        Caller.PENDING_STUDENT: "account_not_active",
        Caller.ACTIVE_STUDENT: None,
        Caller.TEACHER: "forbidden",
    },
}

_CALLERS: dict[Caller, Callable[[], Client]] = {
    Caller.ANONYMOUS: Client,
    Caller.PENDING_STUDENT: lambda: _logged_in(make_student(StudentStatus.PENDING)),
    Caller.ACTIVE_STUDENT: lambda: _logged_in(make_student(StudentStatus.ACTIVE)),
    Caller.TEACHER: lambda: _logged_in(make_user(teacher=True)),
}


def _logged_in(user: object) -> Client:
    client = Client()
    client.force_login(user)  # type: ignore[arg-type]
    return client


def _denial(client: Client, operation: Operation) -> str | None:
    response = getattr(client, operation.method.lower())(
        operation.url(), {}, content_type="application/json"
    )
    if response.status_code not in (401, 403):
        return None
    code = response.json().get("code")
    return code if code in DENIALS else None


@pytest.mark.parametrize("operation", OPERATIONS, ids=lambda op: op.key)
def test_every_route_has_an_area(operation: Operation) -> None:
    assert area_of(operation) is not None, f"add {operation.key} to tests/security/operations.py"


@pytest.mark.parametrize("caller", list(Caller))
@pytest.mark.parametrize("operation", OPERATIONS, ids=lambda op: op.key)
def test_area_lets_in_exactly_the_right_callers(operation: Operation, caller: Caller) -> None:
    area = area_of(operation)
    assert area is not None

    assert _denial(_CALLERS[caller](), operation) == EXPECTED[area][caller]


def test_route_table_has_no_stale_entries() -> None:
    existing = {operation.key for operation in OPERATIONS}

    assert set(ROUTE_AREAS) <= existing
