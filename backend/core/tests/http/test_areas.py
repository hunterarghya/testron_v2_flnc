import pytest
from django.test import RequestFactory
from pytest_django.fixtures import Settings as DjangoSettings

from core.context import ANONYMOUS, Actor
from core.errors import AccountNotActive, DomainError, Forbidden, NotAuthenticated
from core.http.areas import SignedInArea, StudentArea, TeacherArea, anonymous_actor
from core.tests.http.actors import (
    ACTIVE_STUDENT,
    DEACTIVATED_STUDENT,
    PENDING_STUDENT,
    RESOLVER,
    TEACHER,
    as_actor,
)

Guard = SignedInArea | TeacherArea | StudentArea


@pytest.fixture(autouse=True)
def _test_resolver(settings: DjangoSettings) -> None:
    settings.ACTOR_RESOLVER = RESOLVER


def guard_result(guard: Guard, actor: Actor) -> Actor | type[DomainError]:
    request = as_actor(RequestFactory().get("/"), actor)
    try:
        return guard(request)
    except DomainError as error:
        return type(error)


# security.md §3.1, one row per actor kind
@pytest.mark.parametrize(
    ("guard", "actor", "expected"),
    [
        (SignedInArea(), ANONYMOUS, NotAuthenticated),
        (SignedInArea(), PENDING_STUDENT, PENDING_STUDENT),
        (SignedInArea(), ACTIVE_STUDENT, ACTIVE_STUDENT),
        (SignedInArea(), TEACHER, TEACHER),
        (TeacherArea(), ANONYMOUS, NotAuthenticated),
        (TeacherArea(), PENDING_STUDENT, Forbidden),
        (TeacherArea(), ACTIVE_STUDENT, Forbidden),
        (TeacherArea(), TEACHER, TEACHER),
        (StudentArea(), ANONYMOUS, NotAuthenticated),
        (StudentArea(), PENDING_STUDENT, AccountNotActive),
        (StudentArea(), DEACTIVATED_STUDENT, AccountNotActive),
        (StudentArea(), ACTIVE_STUDENT, ACTIVE_STUDENT),
        (StudentArea(), TEACHER, Forbidden),
    ],
)
def test_area_admits_only_its_actors(
    guard: Guard, actor: Actor, expected: Actor | type[DomainError]
) -> None:
    assert guard_result(guard, actor) == expected


def test_inactive_student_is_told_their_status() -> None:
    request = as_actor(RequestFactory().get("/"), PENDING_STUDENT)

    with pytest.raises(AccountNotActive) as error:
        StudentArea()(request)

    assert error.value.context == {"status": "PENDING"}


def test_default_resolver_treats_everyone_as_anonymous() -> None:
    assert anonymous_actor(RequestFactory().get("/")) == ANONYMOUS
