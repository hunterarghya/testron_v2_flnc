"""Real requests at the same moment, each on its own connection (testing_strategy.md §3.8;
V1 F-29): one attempt from many starts (E-01), and no save lands after the end."""

from uuid import UUID, uuid4

import pytest

from core.clock import FrozenClock
from core.context import Ctx
from modules.delivery.domain.errors import AttemptEnded
from modules.delivery.domain.values import EndReason, IntegrityKind
from modules.delivery.models import Attempt
from modules.delivery.services.attempt_views import AttemptStateView
from modules.delivery.services.commands.report_integrity_event import (
    IntegrityAck,
    IntegrityReport,
    report_integrity_event,
)
from modules.delivery.services.commands.save_response import Saved
from modules.delivery.services.commands.start_attempt import Started, start_attempt
from modules.delivery.services.commands.submit_attempt import Ending, submit_attempt
from tests.concurrency import run_together
from tests.factories.assignments import assign, exam_test
from tests.factories.delivery import (
    answer,
    as_student,
    begin,
    choice,
    grades_of,
    numeric,
    option_id,
)
from tests.factories.students import make_student

pytestmark = pytest.mark.django_db(transaction=True)


def test_v1_f29_concurrent_start_makes_one_attempt(frozen_clock: FrozenClock) -> None:
    me = make_student().id
    assignment_id = assign([me], now=frozen_clock.now())
    ctx = as_student(me, now=frozen_clock.now())

    outcomes = run_together(
        *[
            lambda: start_attempt(ctx, assignment_id=assignment_id, password=None, client_id=None)
            for _ in range(10)
        ]
    )

    assert all(isinstance(outcome, Started) for outcome in outcomes), outcomes
    started = [o for o in outcomes if isinstance(o, Started)]
    assert len({o.view.attempt.id for o in started}) == 1
    assert sum(o.created for o in started) == 1
    assert Attempt.objects.filter(assignment_id=assignment_id).count() == 1


def test_saves_racing_submit_are_either_graded_or_refused(frozen_clock: FrozenClock) -> None:
    me = make_student().id
    ctx = as_student(me, now=frozen_clock.now())
    state = begin(ctx, assign([me], now=ctx.now, test=exam_test()))
    client = state.attempt.active_client_id

    outcomes = run_together(
        lambda: answer(ctx, state, 1, choice(option_id(state, 1, "A"))),
        lambda: answer(ctx, state, 2, choice(option_id(state, 2, "A"))),
        lambda: answer(ctx, state, 3, numeric("46")),
        lambda: submit_attempt(ctx, attempt_id=state.attempt.id, client_id=client),
    )

    saves, ending = outcomes[:3], outcomes[3]
    assert isinstance(ending, Ending), ending
    assert all(isinstance(o, Saved | AttemptEnded) for o in saves), saves
    grades = grades_of(state.attempt.id)
    for number, outcome in enumerate(saves, start=1):
        graded = grades[state.questions[number - 1].question.id]
        assert graded == ("CORRECT" if isinstance(outcome, Saved) else "UNANSWERED")


def _report_now(ctx: Ctx, state: AttemptStateView, event_id: UUID) -> object:
    return report_integrity_event(
        ctx,
        attempt_id=state.attempt.id,
        client_id=state.attempt.active_client_id,
        report=IntegrityReport(event_id, IntegrityKind.TAB_HIDDEN, ctx.now, beyond_grace=True),
    )


def test_v1_f29_concurrent_warnings_at_the_limit_end_it_once(frozen_clock: FrozenClock) -> None:
    me = make_student().id
    ctx = as_student(me, now=frozen_clock.now())
    state = begin(ctx, assign([me], now=ctx.now))
    _report_now(ctx, state, uuid4())
    _report_now(ctx, state, uuid4())

    outcomes = run_together(*[lambda: _report_now(ctx, state, uuid4()) for _ in range(10)])

    assert all(isinstance(o, IntegrityAck) for o in outcomes), outcomes
    assert sum(o.counted for o in outcomes if isinstance(o, IntegrityAck)) == 1
    attempt = Attempt.objects.get(pk=state.attempt.id)
    assert (attempt.warning_count, attempt.end_reason) == (3, EndReason.AUTO_SUBMITTED)


def test_the_same_event_five_times_at_once_counts_once_e20(frozen_clock: FrozenClock) -> None:
    me = make_student().id
    ctx = as_student(me, now=frozen_clock.now())
    state = begin(ctx, assign([me], now=ctx.now))
    event = uuid4()

    outcomes = run_together(*[lambda: _report_now(ctx, state, event) for _ in range(5)])

    assert all(isinstance(o, IntegrityAck) and o.warning_count == 1 for o in outcomes), outcomes
    assert Attempt.objects.get(pk=state.attempt.id).warning_count == 1
