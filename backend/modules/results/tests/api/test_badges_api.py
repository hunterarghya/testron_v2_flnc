"""GET /admin/badges: the numbers on the teacher's menu (api_contract.md §2.2)."""

import pytest

from core.clock import FrozenClock
from core.context import StudentStatus
from tests.clients import logged_in
from tests.factories.identity import make_user
from tests.factories.students import make_student

pytestmark = pytest.mark.django_db


def test_badges_count_pending_students(frozen_clock: FrozenClock) -> None:
    teacher = logged_in(make_user(teacher=True).email)
    make_student(StudentStatus.PENDING)

    assert teacher.get("/api/v1/admin/badges").json() == {
        "pending_students": 1,
        "results_to_publish": 0,
    }
