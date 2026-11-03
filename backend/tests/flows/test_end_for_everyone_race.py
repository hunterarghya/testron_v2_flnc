"""End for everyone racing the students' saves (testing_strategy.md §3.8): every sitting
ends at the same instant, and no answer is applied after it."""

import pytest

from core.clock import FrozenClock
from modules.delivery.domain.errors import AttemptEnded
from modules.delivery.domain.values import EndReason
from modules.delivery.services.commands.end_for_everyone import EndedForEveryone, end_for_everyone
from modules.delivery.services.commands.save_response import Saved
from tests.concurrency import run_together
from tests.factories.assignments import assign, teacher_ctx
from tests.factories.delivery import answer, as_student, begin, choice, grades_of, option_id, stored
from tests.factories.students import make_student

pytestmark = pytest.mark.django_db(transaction=True)


def test_end_for_everyone_racing_saves(frozen_clock: FrozenClock) -> None:
    students = [make_student().id for _ in range(6)]
    assignment_id = assign(students, now=frozen_clock.now())
    sittings = [(s, begin(as_student(s, now=frozen_clock.now()), assignment_id)) for s in students]
    teacher = teacher_ctx(frozen_clock.now())

    outcomes = run_together(
        lambda: end_for_everyone(teacher, assignment_id=assignment_id, confirm="END"),
        *[
            lambda s=s, state=state: answer(
                as_student(s, now=teacher.now), state, 1, choice(option_id(state, 1, "A"))
            )
            for s, state in sittings
        ],
    )

    assert isinstance(outcomes[0], EndedForEveryone), outcomes[0]
    for (_, state), outcome in zip(sittings, outcomes[1:], strict=True):
        assert isinstance(outcome, Saved | AttemptEnded), outcome
        attempt = stored(state.attempt.id)
        assert (attempt.end_reason, attempt.ended_at) == (EndReason.ENDED_BY_TEACHER, teacher.now)
        graded = grades_of(state.attempt.id)[state.questions[0].question.id]
        assert graded == ("CORRECT" if isinstance(outcome, Saved) else "UNANSWERED")
