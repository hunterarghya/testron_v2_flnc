"""get_student (T-15) and count_pending_students (the menu badge)."""

from uuid import uuid4

import pytest

from conftest import MakeCtx
from core.context import Actor, Ctx, Role
from core.context import StudentStatus as S
from core.errors import Forbidden, NotFound
from modules.students.public import count_pending_students
from modules.students.services.commands.add_group_members import add_group_members
from modules.students.services.commands.anonymize_student import anonymize_student
from modules.students.services.commands.archive_group import archive_group
from modules.students.services.commands.create_group import create_group
from modules.students.services.commands.deactivate_students import deactivate_students
from modules.students.services.commands.share_performance import share_performance
from modules.students.services.queries.get_student import get_student
from tests.factories.identity import make_user
from tests.factories.students import make_student

pytestmark = pytest.mark.django_db


@pytest.fixture
def teacher_ctx(make_ctx: MakeCtx) -> Ctx:
    return make_ctx(Actor(user_id=make_user(teacher=True).id, role=Role.TEACHER))


def test_profile_shows_details_active_groups_and_sharing(teacher_ctx: Ctx) -> None:
    student = make_student(name="Aditi Roy")
    kept = create_group(teacher_ctx, name="Class 11 A", description="")
    gone = create_group(teacher_ctx, name="Old batch", description="")
    for group in (kept, gone):
        add_group_members(teacher_ctx, group_id=group.id, student_ids=[student.id])
    archive_group(teacher_ctx, group_id=gone.id)
    share_performance(teacher_ctx, student_ids=[student.id], group_id=None)

    detail = get_student(teacher_ctx, student_id=student.id)

    assert (detail.row.name, detail.row.status, detail.row.performance_shared) == (
        "Aditi Roy",
        S.ACTIVE,
        True,
    )
    assert [(group.id, group.name) for group in detail.groups] == [(kept.id, "Class 11 A")]
    assert detail.row.group_names == ["Class 11 A"]


def test_unverified_sign_ups_have_no_page(teacher_ctx: Ctx) -> None:
    student = make_student(S.UNVERIFIED)

    with pytest.raises(NotFound):
        get_student(teacher_ctx, student_id=student.id)


def test_deleted_students_have_no_page(teacher_ctx: Ctx) -> None:
    student = make_student(name="Aditi Roy")
    deactivate_students(teacher_ctx, student_ids=[student.id])
    anonymize_student(teacher_ctx, student_id=student.id, confirm_name="Aditi Roy")

    with pytest.raises(NotFound):
        get_student(teacher_ctx, student_id=student.id)


def test_unknown_student_is_not_found(teacher_ctx: Ctx) -> None:
    with pytest.raises(NotFound):
        get_student(teacher_ctx, student_id=uuid4())


def test_only_the_teacher_sees_a_profile(make_ctx: MakeCtx) -> None:
    student = make_student()
    ctx = make_ctx(Actor(user_id=student.id, role=Role.STUDENT, student_status=S.ACTIVE))

    with pytest.raises(Forbidden):
        get_student(ctx, student_id=student.id)


def test_pending_count_is_only_pending_students() -> None:
    make_student(S.PENDING)
    make_student(S.PENDING)
    make_student(S.ACTIVE)
    make_student(S.UNVERIFIED)

    assert count_pending_students() == 2
