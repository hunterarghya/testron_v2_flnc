"""HTTP contract of My Tests and the gate (api_contract.md §2.8, §3.4; A-01, A-02)."""

import pytest

from core.clock import FrozenClock
from tests.clients import logged_in, send
from tests.factories.assignments import assign, locked, start
from tests.factories.identity import make_user
from tests.factories.students import make_student

pytestmark = pytest.mark.django_db
ANSWER_FIELDS = ("is_correct", "correct_option_ids", "solution", "score")


def test_my_tests_lists_my_cards(frozen_clock: FrozenClock) -> None:
    me = make_student()
    assignment_id = assign([me.id], now=frozen_clock.now(), title="Genetics", window=locked())

    body = send(logged_in(me.email), "get", "/api/v1/my/tests").json()

    card = body["available"][0]
    assert (card["assignment_id"], card["state"], card["locked"]) == (
        str(assignment_id),
        "JOIN",
        True,
    )
    assert (card["question_count"], card["stage_count"], card["attempt_id"]) == (1, 1, None)
    assert body["upcoming"] == []


def test_the_gate_shows_the_rules_and_opens_after_start(frozen_clock: FrozenClock) -> None:
    me = make_student()
    assignment_id = assign(
        [me.id], now=frozen_clock.now(), window=locked(), password="1234", password_confirm="1234"
    )
    client = logged_in(me.email)
    path = f"/api/v1/my/tests/{assignment_id}/gate"

    waiting = send(client, "get", path)
    start(assignment_id, now=frozen_clock.now())
    ready = send(client, "get", path).json()

    body = waiting.json()
    assert (body["state"], body["requires_password"], body["next_take_number"]) == (
        "WAITING_FOR_TEACHER",
        True,
        1,
    )
    assert body["rules"]["marking"] == {"marks": "4.00", "negative_marks": "1.00"}
    assert body["rules"]["stages"] == [{"title": None, "duration_s": 3600}]
    assert ready["state"] == "READY"
    assert not any(field in waiting.content.decode() for field in ANSWER_FIELDS)
    assert "1234" not in waiting.content.decode()


def test_another_students_gate_is_not_found(frozen_clock: FrozenClock) -> None:
    assignment_id = assign([make_student().id], now=frozen_clock.now())
    outsider = logged_in(make_student().email)

    response = send(outsider, "get", f"/api/v1/my/tests/{assignment_id}/gate")

    assert response.status_code == 404


def test_teachers_cannot_use_the_student_area(frozen_clock: FrozenClock) -> None:
    teacher = logged_in(make_user(teacher=True).email)

    assert send(teacher, "get", "/api/v1/my/tests").status_code == 403
