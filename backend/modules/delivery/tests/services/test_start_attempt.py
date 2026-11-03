"""start_attempt and get_attempt_state (domain_model.md §5.4, §5.9; E-01, E-02, E-07, E-08,
E-25, E-39, E-40; A-02, A-03)."""

from datetime import timedelta
from uuid import UUID

import pytest

from core.clock import FrozenClock
from core.context import Ctx
from core.errors import DomainError, Forbidden, NotFound, RateLimited
from modules.delivery.domain.errors import PasswordIncorrect
from modules.delivery.domain.values import AttemptStatus, IntegrityKind, StageState
from modules.delivery.models import IntegrityEvent
from modules.delivery.services.commands.submit_attempt import submit_attempt
from modules.delivery.services.queries.get_attempt_state import get_attempt_state
from tests.factories.assignments import assign, exam_test, locked, scheduled, start, teacher_ctx
from tests.factories.delivery import as_student, begin, grant_retake, grant_used_by, stored
from tests.factories.students import make_student

pytestmark = pytest.mark.django_db
HOUR = timedelta(hours=1)


def _me(clock: FrozenClock) -> tuple[Ctx, UUID]:
    me = make_student().id
    return as_student(me, now=clock.now()), me


def test_a_new_sitting_shows_the_paper_in_order_without_answers(frozen_clock: FrozenClock) -> None:
    ctx, me = _me(frozen_clock)
    assignment_id = assign([me], now=ctx.now, test=exam_test())

    state = begin(ctx, assignment_id)

    attempt = state.attempt
    assert (attempt.take_number, attempt.is_granted, attempt.status) == (
        1,
        False,
        AttemptStatus.IN_PROGRESS,
    )
    assert [q.number for q in state.questions] == [1, 2, 3]
    assert [o.label for o in state.questions[0].options] == ["A", "B", "C", "D"]
    assert state.questions[2].options == ()
    assert state.clock.attempt_deadline == ctx.now + HOUR
    assert state.clock.stages[0].state is StageState.OPEN
    assert stored(attempt.id).max_score == 12


def test_starting_again_resumes_on_the_same_device(frozen_clock: FrozenClock) -> None:
    ctx, me = _me(frozen_clock)
    assignment_id = assign([me], now=ctx.now)
    first = begin(ctx, assignment_id)
    client = first.attempt.active_client_id

    again = begin(ctx, assignment_id, client_id=client)
    reloaded = get_attempt_state(ctx, attempt_id=first.attempt.id, client_id=client)

    assert again.attempt.id == reloaded.attempt.id == first.attempt.id
    assert again.attempt.active_client_id == reloaded.attempt.active_client_id == client
    assert not IntegrityEvent.objects.filter(attempt_id=first.attempt.id).exists()


def test_another_device_takes_over_and_the_teacher_sees_it_e39(frozen_clock: FrozenClock) -> None:
    ctx, me = _me(frozen_clock)
    assignment_id = assign([me], now=ctx.now)
    first = begin(ctx, assignment_id)

    other = get_attempt_state(ctx, attempt_id=first.attempt.id, client_id=None)

    assert other.attempt.active_client_id not in (None, first.attempt.active_client_id)
    event = IntegrityEvent.objects.get(attempt_id=first.attempt.id)
    assert (event.kind, event.counted) == (IntegrityKind.DEVICE_CHANGED, False)
    assert other.clock.attempt_deadline == first.clock.attempt_deadline


@pytest.mark.parametrize(
    ("window", "activate", "minutes_later", "code"),
    [
        (locked(), False, 0, "waiting_for_teacher"),
        (scheduled, False, 0, "not_open_yet"),
        (locked(late_entry_s=60), True, 2, "entry_closed"),
    ],
)
def test_entry_checks_refuse_in_order(
    frozen_clock: FrozenClock, window: object, activate: bool, minutes_later: int, code: str
) -> None:
    me = make_student().id
    chosen = window(frozen_clock.now() + HOUR) if callable(window) else window
    assignment_id = assign([me], now=frozen_clock.now(), window=chosen)
    if activate:
        start(assignment_id, now=frozen_clock.now())
    frozen_clock.advance(minutes=minutes_later)

    with pytest.raises(DomainError) as refused:
        begin(as_student(me, now=frozen_clock.now()), assignment_id)
    assert refused.value.code == code


def test_a_late_joiner_on_a_locked_test_loses_the_time_already_gone(
    frozen_clock: FrozenClock,
) -> None:
    me = make_student().id
    assignment_id = assign([me], now=frozen_clock.now(), window=locked())
    started_at = frozen_clock.now()
    start(assignment_id, now=started_at)
    frozen_clock.advance(minutes=6)

    state = begin(as_student(me, now=frozen_clock.now()), assignment_id)

    assert state.attempt.anchor_at == started_at
    assert state.clock.attempt_deadline == started_at + HOUR


def test_one_sitting_only_unless_the_teacher_grants_another(frozen_clock: FrozenClock) -> None:
    ctx, me = _me(frozen_clock)
    assignment_id = assign([me], now=ctx.now)
    first = begin(ctx, assignment_id)
    submit_attempt(ctx, attempt_id=first.attempt.id, client_id=first.attempt.active_client_id)

    with pytest.raises(DomainError) as used_up:
        begin(ctx, assignment_id)
    assert used_up.value.code == "no_attempts_left"

    grant_retake(assignment_id, me, now=ctx.now)
    retake = begin(ctx, assignment_id)
    assert (retake.attempt.take_number, retake.attempt.is_granted) == (2, True)
    assert grant_used_by(assignment_id, me) == retake.attempt.id


def test_the_password_is_checked_and_tries_are_limited_e25(frozen_clock: FrozenClock) -> None:
    ctx, me = _me(frozen_clock)
    assignment_id = assign([me], now=ctx.now, password="mitosis", password_confirm="mitosis")

    with pytest.raises(DomainError) as missing:
        begin(ctx, assignment_id)
    assert missing.value.code == "password_required"
    with pytest.raises(PasswordIncorrect) as wrong:
        begin(ctx, assignment_id, password="meiosis")
    assert wrong.value.context == {"tries_left": 4}
    for _ in range(4):
        with pytest.raises(PasswordIncorrect):
            begin(ctx, assignment_id, password="meiosis")
    with pytest.raises(RateLimited):
        begin(ctx, assignment_id, password="mitosis")

    frozen_clock.advance(seconds=31)
    assert begin(as_student(me, now=frozen_clock.now()), assignment_id, password="mitosis")


def test_only_the_audience_and_only_their_own_attempts_a02_a03(frozen_clock: FrozenClock) -> None:
    ctx, me = _me(frozen_clock)
    assignment_id = assign([me], now=ctx.now)
    outsider, _ = _me(frozen_clock)
    with pytest.raises(NotFound):
        begin(outsider, assignment_id)

    mine = begin(ctx, assignment_id)
    with pytest.raises(NotFound):
        get_attempt_state(outsider, attempt_id=mine.attempt.id, client_id=None)
    teacher = teacher_ctx(ctx.now)
    with pytest.raises(Forbidden):
        begin(teacher, assignment_id)
