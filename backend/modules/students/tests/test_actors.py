import pytest
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from django.test import RequestFactory

from core.context import ANONYMOUS, Role, StudentStatus
from modules.students.actors import resolve_actor
from tests.factories.identity import User, make_user
from tests.factories.students import make_student

pytestmark = pytest.mark.django_db


def request_by(user: User | AnonymousUser) -> HttpRequest:
    request = RequestFactory().get("/")
    request.user = user
    return request


def test_visitor_is_anonymous() -> None:
    assert resolve_actor(request_by(AnonymousUser())) == ANONYMOUS


@pytest.mark.parametrize("status", [StudentStatus.PENDING, StudentStatus.ACTIVE])
def test_student_carries_their_admission_status(status: StudentStatus) -> None:
    student = make_student(status)

    actor = resolve_actor(request_by(student))

    assert (actor.user_id, actor.role, actor.student_status) == (student.id, Role.STUDENT, status)


def test_teacher_has_no_admission_status() -> None:
    teacher = make_user(teacher=True)

    actor = resolve_actor(request_by(teacher))

    assert (actor.role, actor.student_status) == (Role.TEACHER, None)
    assert actor.is_teacher
