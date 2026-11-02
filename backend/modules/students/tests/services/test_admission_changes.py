"""approve / decline / deactivate / reactivate (domain_model.md §3.2, T-14)."""

from uuid import UUID, uuid4

import pytest

from conftest import MakeCtx
from core.clock import FrozenClock
from core.context import Actor, Ctx, Role
from core.context import StudentStatus as S
from core.errors import Forbidden
from modules.students.models import Student
from modules.students.services.commands.approve_students import approve_students
from modules.students.services.commands.deactivate_students import deactivate_students
from modules.students.services.commands.decline_students import decline_students
from modules.students.services.commands.reactivate_students import reactivate_students
from tests.factories.identity import User, make_user
from tests.factories.students import make_student

pytestmark = pytest.mark.django_db


@pytest.fixture
def teacher_ctx(make_ctx: MakeCtx) -> Ctx:
    teacher = make_user(teacher=True)
    return make_ctx(Actor(user_id=teacher.id, role=Role.TEACHER))


def status_of(user_id: UUID) -> S:
    return S(Student.objects.get(user_id=user_id).status)


def is_active(user_id: UUID) -> bool:
    return User.objects.get(pk=user_id).is_active


def test_approve_turns_requests_into_active_students(
    teacher_ctx: Ctx, frozen_clock: FrozenClock
) -> None:
    first, second = make_student(S.PENDING), make_student(S.PENDING)

    outcome = approve_students(teacher_ctx, student_ids=[first.id, second.id])

    assert outcome.applied == (first.id, second.id)
    for student in (first, second):
        assert status_of(student.id) is S.ACTIVE
        assert is_active(student.id)
    assert Student.objects.get(user_id=first.id).decided_at == frozen_clock.now()


def test_approving_twice_skips_instead_of_failing(teacher_ctx: Ctx) -> None:
    student = make_student(S.PENDING)
    approve_students(teacher_ctx, student_ids=[student.id])

    outcome = approve_students(teacher_ctx, student_ids=[student.id])

    assert outcome.applied == ()
    assert [(skip.student_id, skip.reason) for skip in outcome.skipped] == [
        (student.id, "status_active")
    ]


def test_unknown_ids_and_the_teacher_are_skipped_as_not_found(teacher_ctx: Ctx) -> None:
    unknown = uuid4()

    outcome = approve_students(teacher_ctx, student_ids=[unknown, teacher_ctx.actor.user_id])  # type: ignore[list-item]

    assert {skip.reason for skip in outcome.skipped} == {"not_found"}


def test_decline_is_final_and_keeps_the_account_inactive(teacher_ctx: Ctx) -> None:
    student = make_student(S.PENDING)

    decline_students(teacher_ctx, student_ids=[student.id])

    assert status_of(student.id) is S.DECLINED
    assert not is_active(student.id)
    assert approve_students(teacher_ctx, student_ids=[student.id]).applied == ()


def test_deactivate_then_reactivate(teacher_ctx: Ctx, frozen_clock: FrozenClock) -> None:
    student = make_student(S.ACTIVE)

    deactivate_students(teacher_ctx, student_ids=[student.id])
    assert (status_of(student.id), is_active(student.id)) == (S.DEACTIVATED, False)
    assert Student.objects.get(user_id=student.id).deactivated_at == frozen_clock.now()

    reactivate_students(teacher_ctx, student_ids=[student.id])
    assert (status_of(student.id), is_active(student.id)) == (S.ACTIVE, True)
    assert Student.objects.get(user_id=student.id).deactivated_at is None


@pytest.mark.parametrize(
    "command", [approve_students, decline_students, deactivate_students, reactivate_students]
)
def test_only_the_teacher_may_change_admission(make_ctx: MakeCtx, command: object) -> None:
    student = make_student(S.PENDING)
    student_ctx = make_ctx(Actor(user_id=student.id, role=Role.STUDENT, student_status=S.ACTIVE))

    with pytest.raises(Forbidden):
        command(student_ctx, student_ids=[student.id])  # type: ignore[operator]

    assert status_of(student.id) is S.PENDING
