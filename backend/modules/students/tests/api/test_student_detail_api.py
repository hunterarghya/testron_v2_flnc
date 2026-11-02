"""GET /admin/students/{id}: one student's page (api_contract.md §2.3, T-15)."""

import pytest
from django.test import Client

from core.clock import FrozenClock
from core.context import StudentStatus
from tests.clients import logged_in
from tests.factories.identity import make_user
from tests.factories.students import make_student

pytestmark = pytest.mark.django_db


def test_student_detail_answers_404_for_strangers(frozen_clock: FrozenClock) -> None:
    teacher: Client = logged_in(make_user(teacher=True).email)
    student = make_student(StudentStatus.ACTIVE, name="Aditi Roy")

    found = teacher.get(f"/api/v1/admin/students/{student.id}").json()
    missing = teacher.get(f"/api/v1/admin/students/{make_user().id}")

    assert (found["student"]["name"], found["groups"]) == ("Aditi Roy", [])
    assert missing.status_code == 404
