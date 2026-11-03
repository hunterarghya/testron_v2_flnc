"""The teacher's live controls reaching the students (T-10, D-02-D-04; domain_model.md §5.2,
§5.5, §5.7; E-30, E-31, DM-6)."""

from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID

import pytest
from pytest_django import DjangoAssertNumQueries

from core.clock import FrozenClock
from core.errors import ConfirmationMismatch, DomainError, FieldsInvalid, Forbidden
from modules.assignments.domain.window import Window
from modules.assignments.public import WindowKind
from modules.assignments.services.commands.extend_time import extend_time
from modules.assignments.services.commands.grant_retakes import grant_retakes
from modules.delivery.domain.monitor import MonitorFilter, MonitorStatus
from modules.delivery.domain.values import EndReason
from modules.delivery.services.attempt_views import AttemptStateView
from modules.delivery.services.commands.end_for_everyone import end_for_everyone
from modules.delivery.services.commands.force_submit_attempt import force_submit_attempt
from modules.delivery.services.commands.submit_attempt import submit_attempt
from modules.delivery.services.queries.get_attempt_clock import get_attempt_clock
from modules.delivery.services.queries.get_monitor import get_monitor
from tests.factories.assignments import assign, locked, start, teacher_ctx
from tests.factories.delivery import answer, as_student, begin, choice, option_id, stored
from tests.factories.students import make_student

pytestmark = pytest.mark.django_db
MIN = timedelta(minutes=1)


def test_extra_time_for_everyone_reaches_the_student_e30(frozen_clock: FrozenClock) -> None:
    me = make_student().id
    assignment_id = assign([me], now=frozen_clock.now(), window=locked())
    start(assignment_id, now=frozen_clock.now())
    state = begin(as_student(me, now=frozen_clock.now()), assignment_id)

    ends_at = extend_time(
        teacher_ctx(frozen_clock.now()),
        assignment_id=assignment_id,
        seconds=600,
        student_ids=None,
        stage_index=None,
    )

    beat = get_attempt_clock(
        as_student(me, now=frozen_clock.now()),
        attempt_id=state.attempt.id,
        client_id=state.attempt.active_client_id,
    )
    assert beat.attempt_deadline == state.clock.attempt_deadline + 10 * MIN == ends_at


def test_extra_time_for_one_student_only(frozen_clock: FrozenClock) -> None:
    me, other = make_student().id, make_student().id
    assignment_id = assign([me, other], now=frozen_clock.now())
    mine = begin(as_student(me, now=frozen_clock.now()), assignment_id)
    theirs = begin(as_student(other, now=frozen_clock.now()), assignment_id)
    teacher = teacher_ctx(frozen_clock.now())

    extend_time(
        teacher, assignment_id=assignment_id, seconds=300, student_ids=[me], stage_index=None
    )

    def deadline(student: UUID, state: AttemptStateView) -> datetime:
        ctx = as_student(student, now=frozen_clock.now())
        client = state.attempt.active_client_id
        return get_attempt_clock(
            ctx, attempt_id=state.attempt.id, client_id=client
        ).attempt_deadline

    assert deadline(me, mine) == mine.clock.attempt_deadline + 5 * MIN
    assert deadline(other, theirs) == theirs.clock.attempt_deadline
    with pytest.raises(FieldsInvalid):
        extend_time(
            teacher,
            assignment_id=assignment_id,
            seconds=0,
            student_ids=[make_student().id],
            stage_index=4,
        )


def test_live_controls_wait_for_the_start(frozen_clock: FrozenClock) -> None:
    assignment_id = assign([make_student().id], now=frozen_clock.now(), window=locked())
    with pytest.raises(DomainError) as early:
        extend_time(
            teacher_ctx(frozen_clock.now()),
            assignment_id=assignment_id,
            seconds=60,
            student_ids=None,
            stage_index=None,
        )
    assert early.value.code == "assignment_not_started"


def test_a_retake_is_a_new_take_on_its_own_clock(frozen_clock: FrozenClock) -> None:
    me = make_student().id
    deadline = frozen_clock.now() + 2 * timedelta(hours=1)
    assignment_id = assign(
        [me],
        now=frozen_clock.now(),
        window=Window(WindowKind.DEADLINE, opens_at=frozen_clock.now(), closes_at=deadline),
    )
    ctx = as_student(me, now=frozen_clock.now())
    first = begin(ctx, assignment_id)
    submit_attempt(ctx, attempt_id=first.attempt.id, client_id=first.attempt.active_client_id)
    outcome = grant_retakes(
        teacher_ctx(ctx.now), assignment_id=assignment_id, student_ids=[me, make_student().id]
    )
    assert (len(outcome.applied), [s.reason for s in outcome.skipped]) == (1, ["not_found"])

    # After the window closed: a granted sitting ignores the close
    frozen_clock.advance(hours=3)
    retake = begin(as_student(me, now=frozen_clock.now()), assignment_id)
    assert (retake.attempt.take_number, retake.attempt.is_granted) == (2, True)
    assert retake.clock.attempt_deadline == frozen_clock.now() + timedelta(hours=1)


def test_a_grant_gives_a_student_who_missed_it_a_late_first_take_dm6(
    frozen_clock: FrozenClock,
) -> None:
    me = make_student().id
    assignment_id = assign([me], now=frozen_clock.now(), window=locked(late_entry_s=60))
    start(assignment_id, now=frozen_clock.now())
    frozen_clock.advance(minutes=30)
    with pytest.raises(DomainError):
        begin(as_student(me, now=frozen_clock.now()), assignment_id)

    grant_retakes(teacher_ctx(frozen_clock.now()), assignment_id=assignment_id, student_ids=[me])
    late = begin(as_student(me, now=frozen_clock.now()), assignment_id)

    assert (late.attempt.take_number, late.attempt.is_granted) == (1, True)
    assert late.clock.attempt_deadline == frozen_clock.now() + timedelta(hours=1)


def test_end_for_everyone_ends_and_grades_every_running_sitting_e31(
    frozen_clock: FrozenClock,
) -> None:
    one, two = make_student().id, make_student().id
    assignment_id = assign([one, two], now=frozen_clock.now())
    states = [begin(as_student(s, now=frozen_clock.now()), assignment_id) for s in (one, two)]
    teacher = teacher_ctx(frozen_clock.now() + MIN)
    with pytest.raises(ConfirmationMismatch):
        end_for_everyone(teacher, assignment_id=assignment_id, confirm="end now")

    result = end_for_everyone(teacher, assignment_id=assignment_id, confirm="END")
    again = end_for_everyone(teacher, assignment_id=assignment_id, confirm="END")

    assert (result.ended_attempts, again.ended_attempts, again.ended_at) == (2, 0, teacher.now)
    for state in states:
        attempt = stored(state.attempt.id)
        assert (attempt.end_reason, attempt.ended_at) == (EndReason.ENDED_BY_TEACHER, teacher.now)
        assert attempt.score is not None
    with pytest.raises(DomainError) as late:
        answer(as_student(one, now=teacher.now), states[0], 1, None, seq=5)
    assert late.value.code == "attempt_ended"


def test_force_submit_ends_one_sitting(frozen_clock: FrozenClock) -> None:
    me = make_student().id
    state = begin(as_student(me, now=frozen_clock.now()), assign([me], now=frozen_clock.now()))
    teacher = teacher_ctx(frozen_clock.now())

    summary = force_submit_attempt(teacher, attempt_id=state.attempt.id)

    assert (summary.end_reason, summary.score) == (EndReason.FORCE_SUBMITTED, Decimal("0.00"))
    with pytest.raises(DomainError) as again:
        force_submit_attempt(teacher, attempt_id=state.attempt.id)
    assert again.value.code == "attempt_ended"
    with pytest.raises(Forbidden):
        force_submit_attempt(as_student(me, now=teacher.now), attempt_id=state.attempt.id)


def test_the_monitor_shows_everyone_and_keeps_to_a_fixed_number_of_queries(
    frozen_clock: FrozenClock, django_assert_max_num_queries: DjangoAssertNumQueries
) -> None:
    sitter, done, waiting = (
        make_student(name="Aditi").id,
        make_student(name="Mou").id,
        make_student(name="Rahul").id,
    )
    assignment_id = assign([sitter, done, waiting], now=frozen_clock.now())
    ctx = as_student(sitter, now=frozen_clock.now())
    state = begin(ctx, assignment_id)
    answer(ctx, state, 1, choice(option_id(state, 1, "A")))
    finished = begin(as_student(done, now=ctx.now), assignment_id)
    submit_attempt(
        as_student(done, now=ctx.now),
        attempt_id=finished.attempt.id,
        client_id=finished.attempt.active_client_id,
    )
    teacher = teacher_ctx(ctx.now)

    # frame (5), lock running, stages, attempts, answered (+ savepoint pair)
    with django_assert_max_num_queries(11):
        monitor = get_monitor(teacher, assignment_id=assignment_id, chosen=MonitorFilter.ALL)

    by_name = {row.name: row for row in monitor.rows}
    assert by_name["Aditi"].status is MonitorStatus.IN_PROGRESS
    assert (by_name["Aditi"].answered, by_name["Aditi"].deadline_at) == (
        1,
        state.clock.attempt_deadline,
    )
    assert by_name["Mou"].status is MonitorStatus.SUBMITTED
    assert by_name["Rahul"].status is MonitorStatus.NOT_STARTED
    assert monitor.summary == {
        MonitorStatus.IN_PROGRESS: 1,
        MonitorStatus.SUBMITTED: 1,
        MonitorStatus.NOT_STARTED: 1,
    }
    waiting_only = get_monitor(
        teacher, assignment_id=assignment_id, chosen=MonitorFilter.NOT_STARTED
    )
    assert [row.name for row in waiting_only.rows] == ["Rahul"]
    with pytest.raises(Forbidden):
        get_monitor(ctx, assignment_id=assignment_id, chosen=MonitorFilter.ALL)
