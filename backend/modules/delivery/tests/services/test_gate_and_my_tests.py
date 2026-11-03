"""list_my_tests and get_gate_state (P-01, P-02; domain_model.md §5.4; A-01, A-02)."""

from datetime import timedelta
from uuid import UUID

import pytest
from pytest_django import DjangoAssertNumQueries

from conftest import MakeCtx
from core.clock import FrozenClock
from core.context import Actor, Ctx, Role
from core.context import StudentStatus as S
from core.errors import Forbidden, NotFound
from modules.delivery.domain.gate import CardState, GateStatus
from modules.delivery.services.queries.get_gate_state import get_gate_state
from modules.delivery.services.queries.list_my_tests import list_my_tests
from tests.factories.assignments import assign, last_seen, locked, scheduled, start
from tests.factories.identity import make_user
from tests.factories.students import make_student

pytestmark = pytest.mark.django_db


@pytest.fixture
def teacher_ctx(make_ctx: MakeCtx) -> Ctx:
    return make_ctx(Actor(user_id=make_user(teacher=True).id, role=Role.TEACHER))


def student_ctx(make_ctx: MakeCtx, student_id: UUID) -> Ctx:
    return make_ctx(Actor(user_id=student_id, role=Role.STUDENT, student_status=S.ACTIVE))


def test_my_tests_splits_available_and_upcoming(teacher_ctx: Ctx, make_ctx: MakeCtx) -> None:
    me = make_student().id
    soon = teacher_ctx.now + timedelta(hours=2)
    assign(now=teacher_ctx.now, student_ids=[me], title="Open now")
    assign(now=teacher_ctx.now, student_ids=[me], title="Locked", window=locked())
    assign(now=teacher_ctx.now, student_ids=[me], title="Later", window=scheduled(soon))
    assign(now=teacher_ctx.now, student_ids=[make_student().id], title="Not mine")

    tests = list_my_tests(student_ctx(make_ctx, me))

    assert [(c.view.assignment.title, c.state) for c in tests.available] == [
        ("Locked", CardState.JOIN),
        ("Open now", CardState.START),
    ]
    assert [(c.view.assignment.title, c.state) for c in tests.upcoming] == [
        ("Later", CardState.STARTS_IN)
    ]


def test_my_tests_reads_a_fixed_number_of_queries(
    teacher_ctx: Ctx, make_ctx: MakeCtx, django_assert_num_queries: DjangoAssertNumQueries
) -> None:
    me = make_student().id
    for title in ("A", "B", "C"):
        assign(now=teacher_ctx.now, student_ids=[me], title=title)

    # assignments, papers, extensions, retake grants, attempts (nothing running: no lock)
    with django_assert_num_queries(5):
        list_my_tests(student_ctx(make_ctx, me))


def test_the_gate_waits_for_start_then_opens(
    teacher_ctx: Ctx, make_ctx: MakeCtx, frozen_clock: FrozenClock
) -> None:
    me = make_student().id
    assignment_id = assign(now=teacher_ctx.now, student_ids=[me], window=locked(600))

    waiting = get_gate_state(student_ctx(make_ctx, me), assignment_id=assignment_id)
    start(assignment_id, now=teacher_ctx.now)
    frozen_clock.advance(minutes=6)
    late = get_gate_state(student_ctx(make_ctx, me), assignment_id=assignment_id)
    frozen_clock.advance(minutes=5)
    closed = get_gate_state(student_ctx(make_ctx, me), assignment_id=assignment_id)

    assert (waiting.gate.status, waiting.time_left_if_started_now_s) == (
        GateStatus.WAITING_FOR_TEACHER,
        None,
    )
    assert (late.gate.status, late.time_left_if_started_now_s) == (GateStatus.READY, 54 * 60)
    assert closed.gate.status is GateStatus.ENTRY_CLOSED


def test_each_gate_poll_marks_the_student_joined(teacher_ctx: Ctx, make_ctx: MakeCtx) -> None:
    me = make_student().id
    assignment_id = assign(now=teacher_ctx.now, student_ids=[me], window=locked())

    get_gate_state(student_ctx(make_ctx, me), assignment_id=assignment_id)

    assert last_seen(assignment_id, me) == teacher_ctx.now


def test_the_gate_of_someone_elses_test_is_not_found(teacher_ctx: Ctx, make_ctx: MakeCtx) -> None:
    assignment_id = assign(now=teacher_ctx.now, student_ids=[make_student().id])
    outsider = make_student().id

    with pytest.raises(NotFound):
        get_gate_state(student_ctx(make_ctx, outsider), assignment_id=assignment_id)
    assert last_seen(assignment_id, outsider) is None


def test_teachers_have_no_test_list(teacher_ctx: Ctx) -> None:
    with pytest.raises(Forbidden):
        list_my_tests(teacher_ctx)
