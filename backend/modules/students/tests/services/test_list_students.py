from datetime import timedelta

import pytest
from pytest_django import DjangoAssertNumQueries

from conftest import MakeCtx
from core.clock import FrozenClock
from core.context import Actor, Ctx, Role
from core.context import StudentStatus as S
from core.errors import Forbidden
from modules.students.models import PerformanceShare, Student
from modules.students.services.queries.list_students import StudentPage, list_students
from tests.factories.identity import make_user
from tests.factories.students import make_student

pytestmark = pytest.mark.django_db


@pytest.fixture
def teacher_ctx(make_ctx: MakeCtx) -> Ctx:
    teacher = make_user(teacher=True)
    return make_ctx(Actor(user_id=teacher.id, role=Role.TEACHER))


def listed(
    ctx: Ctx, status: S = S.ACTIVE, search: str | None = None, *, limit: int = 50
) -> StudentPage:
    return list_students(ctx, status=status, search=search, offset=0, limit=limit)


def names(page: StudentPage) -> list[str]:
    return [row.name for row in page.rows]


def test_each_tab_shows_only_its_status(teacher_ctx: Ctx) -> None:
    make_student(S.ACTIVE, name="Active One")
    make_student(S.PENDING, name="Pending One")
    make_student(S.UNVERIFIED, name="Unverified One")

    assert names(listed(teacher_ctx, S.ACTIVE)) == ["Active One"]
    assert names(listed(teacher_ctx, S.PENDING)) == ["Pending One"]


def test_active_tab_is_sorted_by_name(teacher_ctx: Ctx) -> None:
    for name in ("Tapas Kar", "Aditi Roy", "Mitra Sen"):
        make_student(name=name)

    assert names(listed(teacher_ctx)) == ["Aditi Roy", "Mitra Sen", "Tapas Kar"]


def test_pending_tab_shows_the_newest_request_first(
    teacher_ctx: Ctx, frozen_clock: FrozenClock
) -> None:
    older, newer = make_student(S.PENDING, name="Older"), make_student(S.PENDING, name="Newer")
    Student.objects.filter(user_id=older.id).update(
        requested_at=frozen_clock.now() - timedelta(days=1)
    )
    Student.objects.filter(user_id=newer.id).update(requested_at=frozen_clock.now())

    assert names(listed(teacher_ctx, S.PENDING)) == ["Newer", "Older"]


@pytest.mark.parametrize("search", ["rina", "RINA@ex"])
def test_search_matches_name_or_email(teacher_ctx: Ctx, search: str) -> None:
    make_student(name="Rina Das", email="rina@example.com")
    make_student(name="Tapas Kar", email="tapas@example.com")

    assert names(listed(teacher_ctx, search=search)) == ["Rina Das"]


def test_rows_show_the_performance_share(teacher_ctx: Ctx) -> None:
    student = make_student(name="Rina Das")
    PerformanceShare.objects.create(student_id=student.id, shared_since=teacher_ctx.now)

    assert listed(teacher_ctx).rows[0].performance_shared


def test_page_has_the_total(teacher_ctx: Ctx) -> None:
    for number in range(5):
        make_student(name=f"Student {number}")

    page = listed(teacher_ctx, limit=2)

    assert (len(page.rows), page.total) == (2, 5)


def test_query_count_does_not_grow_with_students(
    teacher_ctx: Ctx, django_assert_max_num_queries: DjangoAssertNumQueries
) -> None:
    for number in range(30):
        make_student(name=f"Student {number}")

    with django_assert_max_num_queries(2):
        listed(teacher_ctx)


def test_only_the_teacher_may_list(make_ctx: MakeCtx) -> None:
    student = make_student()

    with pytest.raises(Forbidden):
        listed(make_ctx(Actor(user_id=student.id, role=Role.STUDENT, student_status=S.ACTIVE)))
