"""Correcting the key regrades everyone at once (domain_model.md §6.2; E-14, G-3), and a
disqualification can be overridden (D-09, G-2)."""

from decimal import Decimal
from uuid import uuid4

import pytest

from core.clock import FrozenClock
from core.errors import FieldsInvalid, Forbidden, NotFound
from modules.assignments.public import KeyEntry
from modules.audit.public import entries_for
from modules.delivery.services.commands.override_disqualification import override_disqualification
from modules.delivery.services.commands.submit_attempt import submit_attempt
from modules.results.services.commands.correct_answer_key import correct_answer_key
from tests.factories.assignments import assign, exam_test, teacher_ctx
from tests.factories.delivery import answer, as_student, begin, choice, numeric, option_id, stored
from tests.factories.students import make_student

pytestmark = pytest.mark.django_db


def test_a_key_correction_regrades_every_ended_attempt_e14(frozen_clock: FrozenClock) -> None:
    me = make_student().id
    assignment_id = assign([me], now=frozen_clock.now(), test=exam_test())
    ctx = as_student(me, now=frozen_clock.now())
    state = begin(ctx, assignment_id)
    answer(ctx, state, 1, choice(option_id(state, 1, "B")))
    answer(ctx, state, 3, numeric("45"))
    submit_attempt(ctx, attempt_id=state.attempt.id, client_id=state.attempt.active_client_id)
    assert stored(state.attempt.id).score == Decimal("-2.00")
    teacher = teacher_ctx(ctx.now)

    first = correct_answer_key(
        teacher,
        assignment_id=assignment_id,
        question_id=state.questions[0].question.id,
        entry=KeyEntry(option_ids=(option_id(state, 1, "B"),)),
        reason="B is right",
    )
    second = correct_answer_key(
        teacher,
        assignment_id=assignment_id,
        question_id=state.questions[2].question.id,
        entry=KeyEntry(answer=Decimal(46), tolerance=Decimal(1)),
        reason="Accept 45 to 47",
    )

    assert (first.version, first.regraded_attempts, second.version) == (2, 1, 3)
    attempt = stored(state.attempt.id)
    assert (attempt.score, attempt.answer_key_version) == (Decimal("8.00"), 3)
    actions = [action for action, _, _ in entries_for("assignment", assignment_id)]
    assert actions.count("answer_key.corrected") == 2


def test_a_correction_must_fit_the_question_and_be_the_teachers(frozen_clock: FrozenClock) -> None:
    me = make_student().id
    assignment_id = assign([me], now=frozen_clock.now(), test=exam_test())
    teacher = teacher_ctx(frozen_clock.now())
    state = begin(as_student(me, now=teacher.now), assignment_id)
    first = state.questions[0].question.id

    with pytest.raises(FieldsInvalid):
        correct_answer_key(
            teacher, assignment_id=assignment_id, question_id=first, entry=KeyEntry(), reason="x"
        )
    with pytest.raises(NotFound):
        correct_answer_key(
            teacher, assignment_id=assignment_id, question_id=uuid4(), entry=KeyEntry(), reason="x"
        )
    with pytest.raises(Forbidden):
        correct_answer_key(
            as_student(me, now=teacher.now),
            assignment_id=assignment_id,
            question_id=first,
            entry=KeyEntry(),
            reason="x",
        )


def test_only_a_disqualified_attempt_can_be_overridden(frozen_clock: FrozenClock) -> None:
    me = make_student().id
    state = begin(as_student(me, now=frozen_clock.now()), assign([me], now=frozen_clock.now()))
    teacher = teacher_ctx(frozen_clock.now())
    with pytest.raises(FieldsInvalid):
        override_disqualification(teacher, attempt_id=state.attempt.id, reason="Network trouble")

    row = stored(state.attempt.id)
    row.status, row.end_reason, row.ended_at = "ENDED", "DISQUALIFIED", teacher.now
    row.score, row.graded_at, row.answer_key_version = Decimal(0), teacher.now, 1
    row.save()
    summary = override_disqualification(
        teacher, attempt_id=state.attempt.id, reason="Network trouble"
    )

    assert summary.end_reason == "DISQUALIFIED"
    assert stored(state.attempt.id).disqualification_overridden_at == teacher.now
    with pytest.raises(FieldsInvalid):
        override_disqualification(teacher, attempt_id=state.attempt.id, reason=" ")
