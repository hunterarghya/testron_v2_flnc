"""Sections and rapid fire through the use cases (domain_model.md §5.3; P-04, P-05; E-2, E-4,
E-6, Q-7; V1 F-11)."""

from datetime import timedelta

import pytest

from core.clock import FrozenClock
from core.context import Ctx
from core.errors import DomainError
from modules.delivery.domain.values import StageState
from modules.delivery.services.attempt_views import AttemptStateView
from modules.delivery.services.commands.move_to_next_stage import move_to_next_stage
from modules.delivery.services.commands.return_to_stage import return_to_stage
from modules.delivery.services.queries.get_attempt_state import get_attempt_state
from tests.factories.assignments import assign, rapid_test, sectioned_test
from tests.factories.delivery import answer, as_student, begin, choice, option_id
from tests.factories.students import make_student

pytestmark = pytest.mark.django_db


def _sit(clock: FrozenClock, test: object) -> tuple[Ctx, AttemptStateView]:
    me = make_student().id
    ctx = as_student(me, now=clock.now())
    return ctx, begin(ctx, assign([me], now=ctx.now, test=test))  # type: ignore[arg-type]


def _next(ctx: Ctx, state: AttemptStateView, from_stage: int) -> AttemptStateView:
    return move_to_next_stage(
        ctx,
        attempt_id=state.attempt.id,
        from_stage_index=from_stage,
        client_id=state.attempt.active_client_id,
    )


def test_next_section_closes_it_and_shows_the_next_ones_questions(
    frozen_clock: FrozenClock,
) -> None:
    ctx, state = _sit(frozen_clock, sectioned_test(allow_return=False))

    moved = _next(ctx, state, 0)

    assert [s.state for s in moved.clock.stages] == [StageState.CLOSED, StageState.OPEN]
    assert [q.number for q in moved.questions] == [2]
    assert moved.stage_meta[1].title == "S2"
    # Its own 20 minutes start now, not at the shared boundary
    assert moved.clock.stages[1].deadline_at == ctx.now + timedelta(minutes=20)
    assert _next(ctx, state, 0).attempt.current_stage_index == 1
    with pytest.raises(DomainError) as closed:
        answer(ctx, state, 1, None)
    assert closed.value.code == "stage_closed"


def test_returning_while_the_left_section_still_runs_e4(frozen_clock: FrozenClock) -> None:
    ctx, state = _sit(frozen_clock, sectioned_test(allow_return=True))
    moved = _next(ctx, state, 0)
    assert [s.state for s in moved.clock.stages] == [StageState.LEFT, StageState.OPEN]
    assert [q.number for q in moved.questions] == [1, 2]

    back = return_to_stage(
        ctx, attempt_id=state.attempt.id, stage_index=0, client_id=state.attempt.active_client_id
    )
    assert back.attempt.current_stage_index == 0

    frozen_clock.advance(minutes=11)
    later = as_student(state.attempt.student_id, now=frozen_clock.now())
    reloaded = get_attempt_state(
        later, attempt_id=state.attempt.id, client_id=state.attempt.active_client_id
    )
    # Section 1 ran out while the student was in it: on to section 2, its timer still running
    assert reloaded.attempt.current_stage_index == 1
    assert [s.state for s in reloaded.clock.stages] == [StageState.CLOSED, StageState.OPEN]
    with pytest.raises(DomainError) as refused:
        return_to_stage(
            later,
            attempt_id=state.attempt.id,
            stage_index=0,
            client_id=state.attempt.active_client_id,
        )
    assert refused.value.code == "stage_closed"


def test_a_section_timeout_moves_on_by_itself_e2(frozen_clock: FrozenClock) -> None:
    ctx, state = _sit(frozen_clock, sectioned_test(allow_return=False))
    frozen_clock.advance(minutes=10, seconds=5)

    later = as_student(state.attempt.student_id, now=frozen_clock.now())
    reloaded = get_attempt_state(
        later, attempt_id=state.attempt.id, client_id=state.attempt.active_client_id
    )

    assert reloaded.attempt.current_stage_index == 1
    assert reloaded.clock.notice is not None
    assert reloaded.clock.stages[1].deadline_at == ctx.now + timedelta(minutes=30)


def test_rapid_fire_shows_one_question_and_next_locks_it_v1_f11(frozen_clock: FrozenClock) -> None:
    ctx, state = _sit(frozen_clock, rapid_test())
    assert [q.number for q in state.questions] == [1]
    answer(ctx, state, 1, choice(option_id(state, 1, "A")))

    moved = _next(ctx, state, 0)

    assert [q.number for q in moved.questions] == [2]
    assert moved.clock.stages[1].deadline_at == ctx.now + timedelta(seconds=30)
    with pytest.raises(DomainError) as locked:
        answer(ctx, state, 1, None, seq=2)
    assert locked.value.code == "stage_closed"
    last = _next(ctx, moved, 1)
    with pytest.raises(DomainError) as no_next:
        _next(ctx, last, 2)
    assert no_next.value.code == "stage_navigation_invalid"


def test_moves_need_the_active_device(frozen_clock: FrozenClock) -> None:
    ctx, state = _sit(frozen_clock, rapid_test())
    with pytest.raises(DomainError) as refused:
        move_to_next_stage(ctx, attempt_id=state.attempt.id, from_stage_index=0, client_id=None)
    assert refused.value.code == "attempt_taken_over"
