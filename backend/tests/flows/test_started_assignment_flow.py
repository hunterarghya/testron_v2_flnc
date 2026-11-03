"""The assignment screens read real attempts through delivery (ADR-074, backlog B-17):
cancel and removal are refused once a student has started (E-11), and progress counts."""

import pytest

from core.clock import FrozenClock
from modules.assignments.domain.assignment import Progress
from modules.assignments.domain.errors import AssignmentHasAttempts, AudienceMemberHasAttempt
from modules.assignments.services.commands.cancel_assignment import cancel_assignment
from modules.assignments.services.commands.remove_audience import remove_audience
from modules.assignments.services.queries.get_assignment import get_assignment
from modules.delivery.services.commands.submit_attempt import submit_attempt
from tests.factories.assignments import assign, teacher_ctx
from tests.factories.delivery import as_student, begin
from tests.factories.students import make_student

pytestmark = pytest.mark.django_db


def test_started_students_stay_and_the_test_cant_be_cancelled(frozen_clock: FrozenClock) -> None:
    sitter, waiting, done = make_student().id, make_student().id, make_student().id
    assignment_id = assign([sitter, waiting, done], now=frozen_clock.now())
    begin(as_student(sitter, now=frozen_clock.now()), assignment_id)
    finished = begin(as_student(done, now=frozen_clock.now()), assignment_id)
    submit_attempt(
        as_student(done, now=frozen_clock.now()),
        attempt_id=finished.attempt.id,
        client_id=finished.attempt.active_client_id,
    )
    teacher = teacher_ctx(frozen_clock.now())

    with pytest.raises(AssignmentHasAttempts):
        cancel_assignment(teacher, assignment_id=assignment_id)
    with pytest.raises(AudienceMemberHasAttempt):
        remove_audience(teacher, assignment_id=assignment_id, student_ids=[sitter, waiting])

    detail = get_assignment(teacher, assignment_id=assignment_id)
    assert detail.row.progress == Progress(ended=1, in_progress=1)
    started = {m.student_id for m in detail.audience if m.has_attempt}
    assert started == {sitter, done}
