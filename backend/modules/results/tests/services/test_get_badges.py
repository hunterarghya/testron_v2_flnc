"""get_badges: the teacher's menu counts (screens.md, teacher shell)."""

from uuid import uuid4

import pytest

from conftest import MakeCtx
from core.context import Actor, Role, StudentStatus
from core.errors import Forbidden
from modules.results.services.queries.get_badges import get_badges

pytestmark = pytest.mark.django_db


def test_only_the_teacher_sees_the_badges(make_ctx: MakeCtx) -> None:
    student = Actor(user_id=uuid4(), role=Role.STUDENT, student_status=StudentStatus.ACTIVE)

    with pytest.raises(Forbidden):
        get_badges(make_ctx(student))


def test_nothing_to_publish_before_results_exist(make_ctx: MakeCtx) -> None:
    badges = get_badges(make_ctx(Actor(user_id=uuid4(), role=Role.TEACHER)))

    assert (badges.pending_students, badges.results_to_publish) == (0, 0)
