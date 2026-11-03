"""save_response, record_visit, the heartbeat, submit_attempt and lazy finalization
(domain_model.md §3.6 #4, §5.5; E-03, E-04, E-05, E-39; V1 F-10)."""

from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from pytest_django import DjangoAssertNumQueries

from core.clock import FrozenClock
from core.context import Ctx
from core.errors import DomainError
from modules.delivery.domain.errors import AnswerInvalid, QuestionNotInStage
from modules.delivery.domain.values import AttemptStatus, EndReason
from modules.delivery.models import Response
from modules.delivery.services.attempt_views import AttemptStateView
from modules.delivery.services.commands.record_visit import record_visit
from modules.delivery.services.commands.save_response import SaveRequest, save_response
from modules.delivery.services.commands.submit_attempt import submit_attempt
from modules.delivery.services.queries.get_attempt_clock import get_attempt_clock
from modules.delivery.services.queries.list_my_tests import list_my_tests
from tests.factories.assignments import assign, exam_test
from tests.factories.delivery import (
    answer,
    as_student,
    begin,
    choice,
    grades_of,
    numeric,
    option_id,
    stored,
)
from tests.factories.students import make_student

pytestmark = pytest.mark.django_db


@pytest.fixture
def sitting(frozen_clock: FrozenClock) -> AttemptStateView:
    me = make_student().id
    assignment_id = assign([me], now=frozen_clock.now(), test=exam_test())
    return begin(as_student(me, now=frozen_clock.now()), assignment_id)


def _ctx(state: AttemptStateView, clock: FrozenClock) -> Ctx:
    return as_student(state.attempt.student_id, now=clock.now())


def _answer_of(state: AttemptStateView, number: int) -> object:
    question_id = state.questions[number - 1].question.id
    return Response.objects.get(attempt_id=state.attempt.id, question_id=question_id).answer


def test_a_save_is_stored_and_an_older_retry_ignored_e05(
    sitting: AttemptStateView, frozen_clock: FrozenClock
) -> None:
    ctx = _ctx(sitting, frozen_clock)
    first = answer(ctx, sitting, 1, choice(option_id(sitting, 1, "B")), seq=2)
    late_retry = answer(ctx, sitting, 1, choice(option_id(sitting, 1, "C")), seq=1)

    assert (first.applied, late_retry.applied) == (True, False)
    assert _answer_of(sitting, 1) == {
        "v": 1,
        "kind": "CHOICE",
        "option_ids": [str(option_id(sitting, 1, "B"))],
    }
    answer(ctx, sitting, 1, None, seq=3)
    assert _answer_of(sitting, 1) is None


def test_a_save_must_fit_the_question(sitting: AttemptStateView, frozen_clock: FrozenClock) -> None:
    ctx = _ctx(sitting, frozen_clock)
    both = choice(option_id(sitting, 1, "A"), option_id(sitting, 1, "B"))
    with pytest.raises(AnswerInvalid):
        answer(ctx, sitting, 1, both)
    with pytest.raises(AnswerInvalid):
        answer(ctx, sitting, 3, numeric("4e2"))
    with pytest.raises(QuestionNotInStage):
        save_response(
            ctx,
            attempt_id=sitting.attempt.id,
            client_id=sitting.attempt.active_client_id,
            save=SaveRequest(uuid4(), None, marked_for_review=False, client_seq=1),
        )


def test_an_old_device_can_no_longer_write_e39(
    sitting: AttemptStateView, frozen_clock: FrozenClock
) -> None:
    ctx = _ctx(sitting, frozen_clock)
    with pytest.raises(DomainError) as refused:
        save_response(
            ctx,
            attempt_id=sitting.attempt.id,
            client_id=uuid4(),
            save=SaveRequest(sitting.questions[0].question.id, None, False, 1),
        )
    assert refused.value.code == "attempt_taken_over"


def test_submit_grades_at_once_and_is_safe_to_repeat(
    sitting: AttemptStateView, frozen_clock: FrozenClock
) -> None:
    ctx = _ctx(sitting, frozen_clock)
    answer(ctx, sitting, 1, choice(option_id(sitting, 1, "A")))
    answer(ctx, sitting, 2, choice(option_id(sitting, 2, "B")))
    answer(ctx, sitting, 3, numeric("46.00"))
    client = sitting.attempt.active_client_id

    ending = submit_attempt(ctx, attempt_id=sitting.attempt.id, client_id=client)
    again = submit_attempt(ctx, attempt_id=sitting.attempt.id, client_id=client)

    assert ending == again
    assert (ending.end_reason, ending.ended_at) == (EndReason.SUBMITTED, ctx.now)
    attempt = stored(sitting.attempt.id)
    assert (attempt.score, attempt.answer_key_version) == (Decimal("7.00"), 1)
    assert len(grades_of(attempt.id)) == 3
    with pytest.raises(DomainError) as after:
        answer(ctx, sitting, 1, None, seq=9)
    assert after.value.code == "attempt_ended"


def test_v1_f10_a_save_after_the_deadline_ends_it_at_the_deadline_e04(
    sitting: AttemptStateView, frozen_clock: FrozenClock
) -> None:
    deadline = sitting.clock.attempt_deadline
    frozen_clock.advance(hours=1, seconds=30)

    with pytest.raises(DomainError) as refused:
        answer(_ctx(sitting, frozen_clock), sitting, 1, None)

    assert refused.value.code == "attempt_ended"
    attempt = stored(sitting.attempt.id)
    assert (attempt.status, attempt.end_reason, attempt.ended_at) == (
        AttemptStatus.ENDED,
        EndReason.TIMED_OUT,
        deadline,
    )
    assert attempt.score == Decimal("0.00")
    assert set(grades_of(attempt.id).values()) == {"UNANSWERED"}


def test_e03_a_closed_browser_is_finalized_when_my_tests_is_read(
    sitting: AttemptStateView, frozen_clock: FrozenClock
) -> None:
    ctx = _ctx(sitting, frozen_clock)
    answer(ctx, sitting, 1, choice(option_id(sitting, 1, "A")))
    frozen_clock.advance(days=2)

    tests = list_my_tests(_ctx(sitting, frozen_clock))

    assert tests.available == []
    attempt = stored(sitting.attempt.id)
    assert (attempt.end_reason, attempt.ended_at, attempt.score) == (
        EndReason.TIMED_OUT,
        sitting.clock.attempt_deadline,
        Decimal("4.00"),
    )


def test_the_heartbeat_tells_the_clock_and_the_end(
    sitting: AttemptStateView, frozen_clock: FrozenClock
) -> None:
    client = sitting.attempt.active_client_id
    beat = get_attempt_clock(
        _ctx(sitting, frozen_clock), attempt_id=sitting.attempt.id, client_id=client
    )
    assert beat.status is AttemptStatus.IN_PROGRESS
    assert beat.attempt_deadline - beat.server_now == timedelta(hours=1)

    frozen_clock.advance(hours=2)
    over = get_attempt_clock(
        _ctx(sitting, frozen_clock), attempt_id=sitting.attempt.id, client_id=uuid4()
    )
    assert (over.status, over.end_reason) == (AttemptStatus.ENDED, EndReason.TIMED_OUT)


def test_a_visit_marks_the_question_seen_and_keeps_the_answer(
    sitting: AttemptStateView, frozen_clock: FrozenClock
) -> None:
    ctx = _ctx(sitting, frozen_clock)
    answer(ctx, sitting, 1, choice(option_id(sitting, 1, "A")))
    for number in (1, 2):
        record_visit(
            ctx,
            attempt_id=sitting.attempt.id,
            question_id=sitting.questions[number - 1].question.id,
            client_id=sitting.attempt.active_client_id,
        )
    assert _answer_of(sitting, 1) is not None
    assert _answer_of(sitting, 2) is None


def test_a_save_reads_a_fixed_number_of_queries(
    sitting: AttemptStateView,
    frozen_clock: FrozenClock,
    django_assert_max_num_queries: DjangoAssertNumQueries,
) -> None:
    ctx = _ctx(sitting, frozen_clock)
    # attempt (locked), assignment, extensions, stages, the upsert, last seen (+ savepoint pair)
    with django_assert_max_num_queries(8):
        answer(ctx, sitting, 1, None)
