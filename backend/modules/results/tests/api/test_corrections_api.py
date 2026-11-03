"""HTTP contract of answer key corrections (api_contract.md §2.7; D-05)."""

import pytest

from core.clock import FrozenClock
from tests.clients import logged_in, send
from tests.factories.assignments import assign, exam_test, the_teacher
from tests.factories.delivery import as_student, begin, option_id
from tests.factories.students import make_student

pytestmark = pytest.mark.django_db


def test_a_correction_returns_the_new_version(frozen_clock: FrozenClock) -> None:
    me = make_student().id
    assignment_id = assign([me], now=frozen_clock.now(), test=exam_test())
    state = begin(as_student(me, now=frozen_clock.now()), assignment_id)
    teacher = logged_in(the_teacher().email)
    path = f"/api/v1/admin/assignments/{assignment_id}/answer-key-corrections"
    question = str(state.questions[0].question.id)
    right = {"option_ids": [str(option_id(state, 1, "B"))]}

    done = send(teacher, "post", path, {"question_id": question, "entry": right, "reason": "B"})
    wrong = send(teacher, "post", path, {"question_id": question, "entry": {}, "reason": "?"})

    assert done.json() == {"version": 2, "regraded_attempts": 0}
    assert (wrong.status_code, wrong.json()["errors"][0]["field"]) == (422, "entry")
