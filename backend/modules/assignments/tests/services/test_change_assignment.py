"""Changing an assignment: settings, audience, password, cancel (domain_model.md §3.5 #3-6)."""

from datetime import timedelta
from uuid import UUID

import pytest

from conftest import MakeCtx
from core.bulk import Skip
from core.clock import FrozenClock
from core.context import Actor, Ctx, Role
from core.context import StudentStatus as S
from core.errors import FieldsInvalid, NotFound
from modules.assignments.domain.assignment import SettingsPatch
from modules.assignments.domain.errors import AssignmentCancelled, AssignmentStarted
from modules.assignments.domain.settings import PasswordMismatch
from modules.assignments.domain.values import LifecycleState, WindowKind
from modules.assignments.domain.window import Window
from modules.assignments.models import Assignment
from modules.assignments.services.commands.add_audience import add_audience
from modules.assignments.services.commands.cancel_assignment import cancel_assignment
from modules.assignments.services.commands.create_assignment import create_assignment
from modules.assignments.services.commands.remove_audience import remove_audience
from modules.assignments.services.commands.replace_audience import replace_audience
from modules.assignments.services.commands.set_password import set_password
from modules.assignments.services.commands.update_assignment import update_assignment
from modules.assignments.services.queries.get_assignment import get_assignment
from modules.assignments.services.queries.reveal_password import REVEAL_ACTION, reveal_password
from modules.audit import public as audit
from tests.factories.assignments import assignable_test, new_assignment
from tests.factories.identity import make_user
from tests.factories.students import make_student

pytestmark = pytest.mark.django_db


@pytest.fixture
def teacher_ctx(make_ctx: MakeCtx) -> Ctx:
    return make_ctx(Actor(user_id=make_user(teacher=True).id, role=Role.TEACHER))


def assign(ctx: Ctx, students: list[UUID], **changes: object) -> UUID:
    created = create_assignment(ctx, new=new_assignment(assignable_test().id, students, **changes))
    return created.row.record.id


def locked(ctx: Ctx, students: list[UUID]) -> UUID:
    """A MANUAL (locked) assignment: it waits for Start, so nothing has started."""
    return assign(ctx, students, window=Window(WindowKind.MANUAL))


def start(assignment_id: UUID, ctx: Ctx) -> None:
    Assignment.objects.filter(pk=assignment_id).update(activated_at=ctx.now)


def test_before_the_start_every_setting_changes(teacher_ctx: Ctx) -> None:
    assignment_id = locked(teacher_ctx, [make_student().id])
    soon = teacher_ctx.now + timedelta(hours=1)
    patch = SettingsPatch(title=" Renamed ", window=Window(WindowKind.SCHEDULED, starts_at=soon))

    updated = update_assignment(teacher_ctx, assignment_id=assignment_id, patch=patch)

    assert (updated.row.record.settings.title, updated.row.state) == (
        "Renamed",
        LifecycleState.SCHEDULED,
    )


def test_after_the_start_only_title_and_publication_change(teacher_ctx: Ctx) -> None:
    assignment_id = locked(teacher_ctx, [make_student().id])
    start(assignment_id, teacher_ctx)

    updated = update_assignment(
        teacher_ctx, assignment_id=assignment_id, patch=SettingsPatch(title="Live title")
    )
    assert updated.editable_fields == ("title", "publication", "password")
    with pytest.raises(AssignmentStarted):
        update_assignment(
            teacher_ctx, assignment_id=assignment_id, patch=SettingsPatch(requires_activation=True)
        )


def test_a_past_start_is_only_checked_when_the_window_changes(
    make_ctx: MakeCtx, frozen_clock: FrozenClock
) -> None:
    """Waiting for Start after its start time: not started, and its window is in the past."""
    ctx = make_ctx(Actor(user_id=make_user(teacher=True).id, role=Role.TEACHER))
    soon = ctx.now + timedelta(minutes=5)
    window = Window(WindowKind.SCHEDULED, starts_at=soon)
    assignment_id = assign(ctx, [make_student().id], window=window, requires_activation=True)
    frozen_clock.advance(minutes=10)
    later = make_ctx(ctx.actor)

    updated = update_assignment(later, assignment_id=assignment_id, patch=SettingsPatch(title="Ok"))
    assert updated.row.state is LifecycleState.WAITING
    with pytest.raises(FieldsInvalid):
        update_assignment(later, assignment_id=assignment_id, patch=SettingsPatch(window=window))


def test_replace_audience_before_the_start_only(teacher_ctx: Ctx) -> None:
    first, second = make_student().id, make_student().id
    assignment_id = locked(teacher_ctx, [first])

    updated = replace_audience(teacher_ctx, assignment_id=assignment_id, student_ids=[second])
    assert [s.student_id for s in updated.audience] == [second]

    start(assignment_id, teacher_ctx)
    with pytest.raises(AssignmentStarted):
        replace_audience(teacher_ctx, assignment_id=assignment_id, student_ids=[first])


def test_add_audience_after_the_start_skips_who_cannot_join(teacher_ctx: Ctx) -> None:
    member, newcomer, pending = make_student().id, make_student().id, make_student(S.PENDING).id
    assignment_id = locked(teacher_ctx, [member])
    start(assignment_id, teacher_ctx)

    outcome = add_audience(
        teacher_ctx, assignment_id=assignment_id, student_ids=[member, newcomer, pending]
    )

    assert outcome.applied == (newcomer,)
    assert outcome.skipped == (Skip(member, "already_member"), Skip(pending, "status_pending"))
    assert len(get_assignment(teacher_ctx, assignment_id=assignment_id).audience) == 2


def test_remove_audience_any_time_for_students_who_never_began(teacher_ctx: Ctx) -> None:
    keep, leave = make_student().id, make_student().id
    assignment_id = locked(teacher_ctx, [keep, leave])
    start(assignment_id, teacher_ctx)

    outcome = remove_audience(teacher_ctx, assignment_id=assignment_id, student_ids=[leave])

    assert outcome.applied == (leave,)
    assert [
        s.student_id for s in get_assignment(teacher_ctx, assignment_id=assignment_id).audience
    ] == [keep]


def test_set_change_reveal_and_remove_the_password(teacher_ctx: Ctx) -> None:
    assignment_id = locked(teacher_ctx, [make_student().id])

    set_password(teacher_ctx, assignment_id=assignment_id, password="1234", password_confirm="1234")
    assert reveal_password(teacher_ctx, assignment_id=assignment_id) == "1234"
    with pytest.raises(PasswordMismatch):
        set_password(teacher_ctx, assignment_id=assignment_id, password="1234", password_confirm="")

    set_password(teacher_ctx, assignment_id=assignment_id, password=None, password_confirm=None)
    assert reveal_password(teacher_ctx, assignment_id=assignment_id) is None


def test_every_reveal_is_audited(teacher_ctx: Ctx) -> None:
    assignment_id = locked(teacher_ctx, [make_student().id])

    reveal_password(teacher_ctx, assignment_id=assignment_id)
    reveal_password(teacher_ctx, assignment_id=assignment_id)

    entries = audit.entries_for("assignment", assignment_id)
    assert entries == [(REVEAL_ACTION, teacher_ctx.actor.user_id, {})] * 2


def test_cancel_then_nothing_changes(teacher_ctx: Ctx) -> None:
    assignment_id = locked(teacher_ctx, [make_student().id])

    cancel_assignment(teacher_ctx, assignment_id=assignment_id)

    detail = get_assignment(teacher_ctx, assignment_id=assignment_id)
    assert (detail.row.state, detail.editable_fields) == (LifecycleState.CANCELLED, ())
    with pytest.raises(AssignmentCancelled):
        add_audience(teacher_ctx, assignment_id=assignment_id, student_ids=[make_student().id])
    with pytest.raises(AssignmentCancelled):
        cancel_assignment(teacher_ctx, assignment_id=assignment_id)


def test_no_cancel_after_start(teacher_ctx: Ctx) -> None:
    assignment_id = locked(teacher_ctx, [make_student().id])
    start(assignment_id, teacher_ctx)

    with pytest.raises(AssignmentStarted):
        cancel_assignment(teacher_ctx, assignment_id=assignment_id)


def test_an_open_assignment_no_one_began_can_be_cancelled(teacher_ctx: Ctx) -> None:
    assignment_id = assign(teacher_ctx, [make_student().id])

    cancel_assignment(teacher_ctx, assignment_id=assignment_id)

    assert Assignment.objects.get(pk=assignment_id).cancelled_at == teacher_ctx.now


def test_a_missing_assignment_is_not_found(teacher_ctx: Ctx) -> None:
    missing = make_user().id
    with pytest.raises(NotFound):
        cancel_assignment(teacher_ctx, assignment_id=missing)
    with pytest.raises(NotFound):
        reveal_password(teacher_ctx, assignment_id=missing)
