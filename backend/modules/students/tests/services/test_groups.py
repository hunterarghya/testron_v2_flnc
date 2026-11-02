"""Group commands and queries (domain_model.md §3.2, T-16, T-17)."""

from uuid import UUID, uuid4

import pytest
from pytest_django import DjangoAssertNumQueries

from conftest import MakeCtx
from core.context import Actor, Ctx, Role
from core.context import StudentStatus as S
from core.errors import Forbidden, NotFound
from modules.students.domain.errors import GroupArchived, GroupNameTaken
from modules.students.models import GroupMembership
from modules.students.services.commands.add_group_members import add_group_members
from modules.students.services.commands.approve_students import approve_students
from modules.students.services.commands.archive_group import archive_group
from modules.students.services.commands.create_group import create_group
from modules.students.services.commands.deactivate_students import deactivate_students
from modules.students.services.commands.remove_group_members import remove_group_members
from modules.students.services.commands.restore_group import restore_group
from modules.students.services.commands.update_group import update_group
from modules.students.services.queries.get_group import get_group
from modules.students.services.queries.list_groups import list_groups
from modules.students.services.queries.preview_audience import preview_audience
from tests.factories.identity import make_user
from tests.factories.students import make_student

pytestmark = pytest.mark.django_db


@pytest.fixture
def teacher_ctx(make_ctx: MakeCtx) -> Ctx:
    return make_ctx(Actor(user_id=make_user(teacher=True).id, role=Role.TEACHER))


def new_group(ctx: Ctx, name: str = "Class 11 A") -> UUID:
    return create_group(ctx, name=name, description="").id


def test_create_then_list(teacher_ctx: Ctx) -> None:
    create_group(teacher_ctx, name="Class 12 B", description="  Evening  batch ")
    new_group(teacher_ctx, "Class 11 A")

    listed = list_groups(teacher_ctx, archived=False, search=None)

    assert [group.name for group in listed] == ["Class 11 A", "Class 12 B"]
    assert listed[1].description == "Evening batch"


@pytest.mark.parametrize("clash", ["Class 11 A", "class  11 a", "CLASS 11 A"])
def test_names_are_unique_among_active_groups(teacher_ctx: Ctx, clash: str) -> None:
    new_group(teacher_ctx)

    with pytest.raises(GroupNameTaken):
        new_group(teacher_ctx, clash)


def test_an_archived_groups_name_can_be_reused_but_not_restored_over(teacher_ctx: Ctx) -> None:
    old = new_group(teacher_ctx)
    archive_group(teacher_ctx, group_id=old)
    new_group(teacher_ctx)

    with pytest.raises(GroupNameTaken):
        restore_group(teacher_ctx, group_id=old)


def test_rename_keeps_what_was_left_out(teacher_ctx: Ctx) -> None:
    group_id = create_group(teacher_ctx, name="Class 11 A", description="Morning").id

    renamed = update_group(teacher_ctx, group_id=group_id, name="Class 11 B", description=None)

    assert (renamed.name, renamed.description) == ("Class 11 B", "Morning")


def test_archive_and_restore_are_safe_to_repeat(teacher_ctx: Ctx) -> None:
    group_id = new_group(teacher_ctx)

    first = archive_group(teacher_ctx, group_id=group_id)
    second = archive_group(teacher_ctx, group_id=group_id)

    assert first.archived_at == second.archived_at is not None
    assert [g.id for g in list_groups(teacher_ctx, archived=True, search=None)] == [group_id]
    assert restore_group(teacher_ctx, group_id=group_id).archived_at is None


def test_members_come_and_go_with_reasons(teacher_ctx: Ctx) -> None:
    group_id = new_group(teacher_ctx)
    active, pending = make_student(S.ACTIVE, name="Aditi"), make_student(S.PENDING)

    added = add_group_members(teacher_ctx, group_id=group_id, student_ids=[active.id, pending.id])
    again = add_group_members(teacher_ctx, group_id=group_id, student_ids=[active.id])
    removed = remove_group_members(teacher_ctx, group_id=group_id, student_ids=[active.id])

    assert added.applied == (active.id,)
    assert [skip.reason for skip in added.skipped] == ["status_pending"]
    assert [skip.reason for skip in again.skipped] == ["already_member"]
    assert removed.applied == (active.id,)


def test_archived_groups_cannot_change_members(teacher_ctx: Ctx) -> None:
    group_id = new_group(teacher_ctx)
    archive_group(teacher_ctx, group_id=group_id)

    with pytest.raises(GroupArchived):
        add_group_members(teacher_ctx, group_id=group_id, student_ids=[make_student().id])


def test_group_detail_lists_members_by_name(
    teacher_ctx: Ctx, django_assert_max_num_queries: DjangoAssertNumQueries
) -> None:
    group_id = new_group(teacher_ctx)
    ids = [make_student(name=name).id for name in ("Tapas", "Aditi", "Mitra")]
    add_group_members(teacher_ctx, group_id=group_id, student_ids=ids)

    with django_assert_max_num_queries(3):
        found = get_group(teacher_ctx, group_id=group_id)

    assert [member.name for member in found.members] == ["Aditi", "Mitra", "Tapas"]
    assert found.group.member_count == 3


def test_unknown_group_is_not_found(teacher_ctx: Ctx) -> None:
    with pytest.raises(NotFound):
        get_group(teacher_ctx, group_id=uuid4())


def test_audience_preview_has_each_active_student_once(teacher_ctx: Ctx) -> None:
    eleven, twelve = new_group(teacher_ctx, "11 A"), new_group(teacher_ctx, "12 B")
    both, inactive = make_student(name="Both"), make_student(S.ACTIVE, name="Later off")
    add_group_members(teacher_ctx, group_id=eleven, student_ids=[both.id, inactive.id])
    add_group_members(teacher_ctx, group_id=twelve, student_ids=[both.id])
    deactivate_students(teacher_ctx, student_ids=[inactive.id])

    preview = preview_audience(teacher_ctx, group_ids=[eleven, twelve, eleven])

    assert [(c.name, sorted(c.group_names)) for c in preview] == [("Both", ["11 A", "12 B"])]


def test_approve_can_put_students_straight_into_groups(teacher_ctx: Ctx) -> None:
    group_id = new_group(teacher_ctx)
    student = make_student(S.PENDING)

    approve_students(teacher_ctx, student_ids=[student.id], group_ids=[group_id])

    assert GroupMembership.objects.filter(group_id=group_id, student_id=student.id).exists()


def test_approving_into_an_archived_group_changes_nothing(teacher_ctx: Ctx) -> None:
    group_id = new_group(teacher_ctx)
    archive_group(teacher_ctx, group_id=group_id)
    student = make_student(S.PENDING)

    with pytest.raises(GroupArchived):
        approve_students(teacher_ctx, student_ids=[student.id], group_ids=[group_id])

    assert approve_students(teacher_ctx, student_ids=[student.id]).applied == (student.id,)


def test_only_the_teacher_manages_groups(make_ctx: MakeCtx) -> None:
    student = make_student()
    student_ctx = make_ctx(Actor(user_id=student.id, role=Role.STUDENT, student_status=S.ACTIVE))

    with pytest.raises(Forbidden):
        create_group(student_ctx, name="Mine", description="")
