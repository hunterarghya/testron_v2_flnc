"""create_assignment (domain_model.md §3.5 #1-4, §4.3; V1 F-03, F-27)."""

from datetime import timedelta
from decimal import Decimal

import pytest

from conftest import MakeCtx
from core.context import Actor, Ctx, Role
from core.context import StudentStatus as S
from core.errors import Conflict, FieldsInvalid, Forbidden
from modules.assignments.domain.settings import PasswordMismatch
from modules.assignments.domain.values import WindowKind
from modules.assignments.domain.window import Window
from modules.assignments.models import AnswerKey, Assignment, AudienceMember, Paper
from modules.assignments.services.commands.create_assignment import create_assignment
from modules.assignments.services.password_cipher import decrypt_password
from modules.authoring import public as authoring
from tests.factories.assignments import assignable_test, new_assignment
from tests.factories.authoring import change_test, make_test, reload_test
from tests.factories.identity import make_user
from tests.factories.students import make_student

pytestmark = pytest.mark.django_db


@pytest.fixture
def teacher_ctx(make_ctx: MakeCtx) -> Ctx:
    return make_ctx(Actor(user_id=make_user(teacher=True).id, role=Role.TEACHER))


def test_creates_the_assignment_with_its_paper_key_and_audience(teacher_ctx: Ctx) -> None:
    test = assignable_test()
    students = [make_student().id, make_student().id]

    created = create_assignment(teacher_ctx, new=new_assignment(test.id, students))

    record = created.row.record
    assert (record.settings.title, record.timing_kind, record.timeline.total_duration_s) == (
        "Cell Biology",
        "TOTAL",
        3600,
    )
    paper = Paper.objects.get(pk=record.id)
    assert [q["marks"] for q in authoring.paper_questions(paper.content)] == ["4.00"]
    assert len(paper.content_hash) == 64
    assert AnswerKey.objects.get(pk=record.id).version == 1
    assert {a.student_id for a in AudienceMember.objects.filter(assignment_id=record.id)} == set(
        students
    )
    assert [s.student_id for s in created.audience] == students
    assert reload_test(test.id).last_assigned_at == teacher_ctx.now


def test_the_paper_has_no_answers(teacher_ctx: Ctx) -> None:
    created = create_assignment(
        teacher_ctx, new=new_assignment(assignable_test().id, [make_student().id])
    )

    text = str(Paper.objects.get(pk=created.row.record.id).content)
    assert "is_correct" not in text
    assert "correct_option_ids" not in text


def test_editing_the_test_later_never_changes_the_paper(teacher_ctx: Ctx) -> None:
    test = assignable_test()
    created = create_assignment(teacher_ctx, new=new_assignment(test.id, [make_student().id]))

    change_test(test.id, marks=Decimal(10), title="Changed")

    paper = Paper.objects.get(pk=created.row.record.id).content
    assert (paper["title"], authoring.paper_questions(paper)[0]["marks"]) == (
        "Cell Biology",
        "4.00",
    )


def test_the_password_is_stored_encrypted(teacher_ctx: Ctx) -> None:
    new = new_assignment(
        assignable_test().id, [make_student().id], password="abc123", password_confirm="abc123"
    )

    created = create_assignment(teacher_ctx, new=new)

    token = Assignment.objects.get(pk=created.row.record.id).password_ciphertext
    assert token is not None
    assert "abc123" not in token
    assert decrypt_password(token) == "abc123"
    assert created.row.locked is True


def test_a_timing_override_applies_to_the_paper_only(teacher_ctx: Ctx) -> None:
    test = assignable_test()
    override = authoring.TimingOverride(kind=authoring.TimingKind.TOTAL, duration_s=1800)

    created = create_assignment(
        teacher_ctx, new=new_assignment(test.id, [make_student().id], timing_override=override)
    )

    assert created.row.record.timeline.total_duration_s == 1800
    assert reload_test(test.id).duration_s == 3600


@pytest.mark.parametrize(
    ("changes", "error"),
    [
        ({"password": "abcd", "password_confirm": "abce"}, PasswordMismatch),
        ({"title": "  "}, FieldsInvalid),
        ({"window": Window(WindowKind.SCHEDULED, starts_at=None)}, FieldsInvalid),
    ],
)
def test_bad_answers_write_nothing(
    teacher_ctx: Ctx, changes: dict[str, object], error: type[Exception]
) -> None:
    with pytest.raises(error):
        create_assignment(
            teacher_ctx, new=new_assignment(assignable_test().id, [make_student().id], **changes)
        )

    assert not Assignment.objects.exists()


def test_a_window_too_short_for_the_test_is_refused(teacher_ctx: Ctx) -> None:
    opens = teacher_ctx.now + timedelta(hours=1)
    window = Window(WindowKind.DEADLINE, opens_at=opens, closes_at=opens + timedelta(minutes=30))

    with pytest.raises(FieldsInvalid):
        create_assignment(
            teacher_ctx,
            new=new_assignment(assignable_test().id, [make_student().id], window=window),
        )
    assert not Paper.objects.exists()


def test_a_test_with_problems_is_refused(teacher_ctx: Ctx) -> None:
    with pytest.raises(Conflict) as raised:
        create_assignment(teacher_ctx, new=new_assignment(make_test().id, [make_student().id]))

    assert raised.value.code == "test_has_problems"
    assert not Assignment.objects.exists()


@pytest.mark.parametrize("status", [S.PENDING, S.DEACTIVATED])
def test_only_active_students_can_be_the_audience(teacher_ctx: Ctx, status: S) -> None:
    students = [make_student().id, make_student(status).id]

    with pytest.raises(FieldsInvalid):
        create_assignment(teacher_ctx, new=new_assignment(assignable_test().id, students))


def test_an_empty_audience_is_refused(teacher_ctx: Ctx) -> None:
    with pytest.raises(FieldsInvalid):
        create_assignment(teacher_ctx, new=new_assignment(assignable_test().id, []))


def test_students_cannot_assign(make_ctx: MakeCtx) -> None:
    student = make_student()
    ctx = make_ctx(Actor(user_id=student.id, role=Role.STUDENT))

    with pytest.raises(Forbidden):
        create_assignment(ctx, new=new_assignment(assignable_test().id, [student.id]))
