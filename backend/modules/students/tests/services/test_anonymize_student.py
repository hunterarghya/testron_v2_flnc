import pytest

from conftest import MakeCtx
from core.context import Actor, Ctx, Role
from core.context import StudentStatus as S
from core.errors import ConfirmationMismatch, Forbidden, NotFound
from modules.students.domain.errors import AdmissionStepNotAllowed
from modules.students.models import PerformanceShare, Student
from modules.students.services.commands.anonymize_student import anonymize_student
from tests.factories.identity import User, make_user
from tests.factories.students import make_student

pytestmark = pytest.mark.django_db


@pytest.fixture
def teacher_ctx(make_ctx: MakeCtx) -> Ctx:
    teacher = make_user(teacher=True)
    return make_ctx(Actor(user_id=teacher.id, role=Role.TEACHER))


def test_deleted_student_keeps_their_row_but_loses_who_they_were(teacher_ctx: Ctx) -> None:
    student = make_student(S.DEACTIVATED, name="Rina Das", google_sub="google-1")
    PerformanceShare.objects.create(student_id=student.id, shared_since=teacher_ctx.now)

    anonymize_student(teacher_ctx, student_id=student.id, confirm_name="Rina Das")

    row = Student.objects.get(user_id=student.id)
    number = row.anonymized_number
    assert row.status == S.ANONYMIZED
    account = User.objects.get(pk=student.id)
    assert account.name == f"Deleted student #{number}"
    assert account.email == f"deleted-student-{number}@anonymized.invalid"
    assert not account.has_usable_password()
    assert (account.google_sub, account.is_active) == (None, False)
    assert not PerformanceShare.objects.exists()


def test_numbers_are_never_reused(teacher_ctx: Ctx) -> None:
    first, second = make_student(name="A One"), make_student(name="B Two")

    anonymize_student(teacher_ctx, student_id=first.id, confirm_name="A One")
    anonymize_student(teacher_ctx, student_id=second.id, confirm_name="B Two")

    # A sequence: never rolled back, so earlier tests' numbers are gone too
    numbers = [Student.objects.get(user_id=s.id).anonymized_number for s in (first, second)]
    assert numbers[0] is not None
    assert numbers[1] == numbers[0] + 1


def test_wrong_name_changes_nothing(teacher_ctx: Ctx) -> None:
    student = make_student(name="Rina Das")

    with pytest.raises(ConfirmationMismatch):
        anonymize_student(teacher_ctx, student_id=student.id, confirm_name="Rina")

    assert User.objects.get(pk=student.id).name == "Rina Das"


@pytest.mark.parametrize("status", [S.PENDING, S.DECLINED, S.UNVERIFIED])
def test_only_admitted_students_can_be_deleted(teacher_ctx: Ctx, status: S) -> None:
    student = make_student(status, name="Rina Das")

    with pytest.raises(AdmissionStepNotAllowed):
        anonymize_student(teacher_ctx, student_id=student.id, confirm_name="Rina Das")


def test_deleting_twice_is_refused(teacher_ctx: Ctx) -> None:
    student = make_student(name="Rina Das")
    anonymize_student(teacher_ctx, student_id=student.id, confirm_name="Rina Das")

    with pytest.raises(AdmissionStepNotAllowed):
        anonymize_student(
            teacher_ctx, student_id=student.id, confirm_name=User.objects.get(pk=student.id).name
        )


def test_unknown_student_is_not_found(teacher_ctx: Ctx) -> None:
    with pytest.raises(NotFound):
        anonymize_student(teacher_ctx, student_id=teacher_ctx.actor.user_id, confirm_name="x")  # type: ignore[arg-type]


def test_only_the_teacher_may_delete(make_ctx: MakeCtx) -> None:
    student = make_student(name="Rina Das")
    student_ctx = make_ctx(Actor(user_id=student.id, role=Role.STUDENT, student_status=S.ACTIVE))

    with pytest.raises(Forbidden):
        anonymize_student(student_ctx, student_id=student.id, confirm_name="Rina Das")
