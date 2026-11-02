"""share_performance / unshare_performance (domain_model.md §3.2 PerformanceShare, D-06)."""

import pytest

from conftest import MakeCtx
from core.context import Actor, Ctx, Role
from core.context import StudentStatus as S
from core.errors import Invalid
from modules.students.models import GroupMembership, PerformanceShare
from modules.students.services.commands.add_group_members import add_group_members
from modules.students.services.commands.anonymize_student import anonymize_student
from modules.students.services.commands.create_group import create_group
from modules.students.services.commands.share_performance import share_performance
from modules.students.services.commands.unshare_performance import unshare_performance
from tests.factories.identity import make_user
from tests.factories.students import make_student

pytestmark = pytest.mark.django_db


@pytest.fixture
def teacher_ctx(make_ctx: MakeCtx) -> Ctx:
    return make_ctx(Actor(user_id=make_user(teacher=True).id, role=Role.TEACHER))


def shared() -> set[object]:
    return set(PerformanceShare.objects.values_list("student_id", flat=True))


def test_sharing_with_students_is_off_by_default_then_on(teacher_ctx: Ctx) -> None:
    student = make_student()
    assert shared() == set()

    outcome = share_performance(teacher_ctx, student_ids=[student.id], group_id=None)

    assert outcome.applied == (student.id,)
    assert shared() == {student.id}


def test_sharing_with_a_group_covers_its_current_members_only(teacher_ctx: Ctx) -> None:
    group_id = create_group(teacher_ctx, name="11 A", description="").id
    now_member, later_member = make_student(), make_student()
    add_group_members(teacher_ctx, group_id=group_id, student_ids=[now_member.id])

    share_performance(teacher_ctx, student_ids=None, group_id=group_id)
    add_group_members(teacher_ctx, group_id=group_id, student_ids=[later_member.id])

    assert shared() == {now_member.id}


def test_sharing_twice_and_with_pending_students_is_skipped(teacher_ctx: Ctx) -> None:
    active, pending = make_student(), make_student(S.PENDING)
    share_performance(teacher_ctx, student_ids=[active.id], group_id=None)

    outcome = share_performance(teacher_ctx, student_ids=[active.id, pending.id], group_id=None)

    assert {skip.reason for skip in outcome.skipped} == {"already_shared", "status_pending"}


def test_exactly_one_of_students_or_group(teacher_ctx: Ctx) -> None:
    with pytest.raises(Invalid):
        share_performance(teacher_ctx, student_ids=None, group_id=None)


def test_unshare_turns_it_off(teacher_ctx: Ctx) -> None:
    student = make_student()
    share_performance(teacher_ctx, student_ids=[student.id], group_id=None)

    unshare_performance(teacher_ctx, student_ids=[student.id])

    assert shared() == set()


def test_deleting_a_student_removes_sharing_and_groups(teacher_ctx: Ctx) -> None:
    group_id = create_group(teacher_ctx, name="11 A", description="").id
    student = make_student(name="Rina Das")
    add_group_members(teacher_ctx, group_id=group_id, student_ids=[student.id])
    share_performance(teacher_ctx, student_ids=[student.id], group_id=None)

    anonymize_student(teacher_ctx, student_id=student.id, confirm_name="Rina Das")

    assert shared() == set()
    assert not GroupMembership.objects.filter(student_id=student.id).exists()
