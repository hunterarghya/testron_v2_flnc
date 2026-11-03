"""Start, the lobby and what students may see of assignments (T-09; A-01, A-02)."""

from datetime import timedelta
from uuid import UUID

import pytest

from conftest import MakeCtx
from core.clock import FrozenClock
from core.context import Actor, Ctx, Role
from core.errors import NotFound
from modules.assignments import public as assignments
from modules.assignments.domain.entry import ActivationNotRequired
from modules.assignments.domain.errors import AssignmentCancelled
from modules.assignments.domain.values import LifecycleState, WindowKind
from modules.assignments.domain.window import Window
from modules.assignments.services.commands.activate_assignment import activate_assignment
from modules.assignments.services.commands.cancel_assignment import cancel_assignment
from modules.assignments.services.commands.create_assignment import create_assignment
from modules.assignments.services.queries.get_lobby import get_lobby
from tests.factories.assignments import assignable_test, new_assignment
from tests.factories.identity import make_user
from tests.factories.students import make_student

pytestmark = pytest.mark.django_db
LOCKED = Window(WindowKind.MANUAL, late_entry_s=600)


@pytest.fixture
def teacher_ctx(make_ctx: MakeCtx) -> Ctx:
    return make_ctx(Actor(user_id=make_user(teacher=True).id, role=Role.TEACHER))


def assign(ctx: Ctx, students: list[UUID], **changes: object) -> UUID:
    created = create_assignment(ctx, new=new_assignment(assignable_test().id, students, **changes))
    return created.row.record.id


def test_start_sets_the_shared_clock_once(teacher_ctx: Ctx, frozen_clock: FrozenClock) -> None:
    assignment_id = assign(teacher_ctx, [make_student().id], window=LOCKED)

    first = activate_assignment(teacher_ctx, assignment_id=assignment_id)
    frozen_clock.advance(minutes=1)
    again = activate_assignment(
        Ctx(teacher_ctx.actor, frozen_clock.now(), "r"), assignment_id=assignment_id
    )

    assert first == again
    assert (first.activated_at, first.anchor_at) == (teacher_ctx.now, teacher_ctx.now)
    assert first.ends_at == teacher_ctx.now + timedelta(hours=1)


def test_start_is_refused_where_it_means_nothing(teacher_ctx: Ctx) -> None:
    open_id = assign(teacher_ctx, [make_student().id])
    cancelled_id = assign(teacher_ctx, [make_student().id], window=LOCKED)
    cancel_assignment(teacher_ctx, assignment_id=cancelled_id)

    with pytest.raises(ActivationNotRequired):
        activate_assignment(teacher_ctx, assignment_id=open_id)
    with pytest.raises(AssignmentCancelled):
        activate_assignment(teacher_ctx, assignment_id=cancelled_id)


def test_the_lobby_shows_who_polled_in_the_last_30_seconds(
    teacher_ctx: Ctx, frozen_clock: FrozenClock
) -> None:
    early, late, absent = (make_student(name=n) for n in ("Aditi", "Arjun", "Rahul"))
    assignment_id = assign(teacher_ctx, [early.id, late.id, absent.id], window=LOCKED)
    assignments.touch_lobby_presence(assignment_id, early.id, now=frozen_clock.now())
    frozen_clock.advance(seconds=40)
    assignments.touch_lobby_presence(assignment_id, late.id, now=frozen_clock.now())
    assignments.touch_lobby_presence(assignment_id, late.id, now=frozen_clock.now())

    lobby = get_lobby(Ctx(teacher_ctx.actor, frozen_clock.now(), "r"), assignment_id=assignment_id)

    assert [s.name for s in lobby.joined] == ["Arjun"]
    assert [s.name for s in lobby.not_joined] == ["Aditi", "Rahul"]
    assert lobby.state is LifecycleState.WAITING


def test_students_see_only_their_own_live_assignments(teacher_ctx: Ctx) -> None:
    me, other = make_student().id, make_student().id
    mine = assign(teacher_ctx, [me], title="Mine")
    assign(teacher_ctx, [other], title="Theirs")
    cancel_assignment(teacher_ctx, assignment_id=assign(teacher_ctx, [me], title="Off"))

    listed = assignments.list_student_assignments(me)

    assert [a.title for a in listed] == ["Mine"]
    assert listed[0].paper.question_count == 1
    assert assignments.get_student_assignment(mine, me).assignment_id == mine
    with pytest.raises(NotFound):
        assignments.get_student_assignment(mine, other)
