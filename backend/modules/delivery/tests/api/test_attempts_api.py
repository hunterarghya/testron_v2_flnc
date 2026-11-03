"""HTTP contract of the exam hall (api_contract.md §2.8, §3.4): start and resume, the device
header on writes, save acks, submit; and never an answer field [V1 F-03, F-08]."""

from typing import Any

import pytest
from django.test import Client

from core.clock import FrozenClock
from tests.clients import logged_in, send
from tests.factories.assignments import assign, exam_test, locked, start
from tests.factories.students import make_student

pytestmark = pytest.mark.django_db
ANSWER_FIELDS = ("is_correct", "correct_option_ids", "solution", "score", "marks_awarded")


def _sitting(clock: FrozenClock) -> tuple[Client, Any]:
    me = make_student()
    assignment_id = assign([me.id], now=clock.now(), test=exam_test())
    client = logged_in(me.email)
    started = send(client, "post", f"/api/v1/my/tests/{assignment_id}/attempts")
    assert started.status_code == 201
    return client, started.json()


def test_start_then_resume_201_then_200(frozen_clock: FrozenClock) -> None:
    client, state = _sitting(frozen_clock)
    header = {"X-Exam-Client": str(state["exam_client_id"])}

    again = send(
        client, "post", f"/api/v1/my/tests/{state['assignment_id']}/attempts", headers=header
    )

    assert again.status_code == 200
    assert again.json()["exam_client_id"] == state["exam_client_id"]
    assert [q["number"] for q in state["questions"]] == [1, 2, 3]
    assert state["timing"] == {"kind": "TOTAL", "allow_return": False}
    assert state["stages"] == [  # the clock's stages
        {"index": 0, "state": "OPEN", "deadline_at": state["attempt_deadline"]}
    ]


def test_v1_f08_save_ack_has_no_correctness(frozen_clock: FrozenClock) -> None:
    client, state = _sitting(frozen_clock)
    question = state["questions"][0]
    path = f"/api/v1/attempts/{state['attempt_id']}/responses/{question['id']}"
    body = {
        "answer": {"v": 1, "kind": "CHOICE", "option_ids": [question["options"][0]["id"]]},
        "marked_for_review": True,
        "client_seq": 1,
    }

    saved = send(client, "put", path, body, headers={"X-Exam-Client": str(state["exam_client_id"])})

    assert saved.status_code == 200
    assert saved.json()["applied"] is True
    assert saved.json()["status"] == "IN_PROGRESS"
    for text in (saved.content.decode(), str(state)):
        assert not any(field in text for field in ANSWER_FIELDS)


def test_writes_need_the_active_device(frozen_clock: FrozenClock) -> None:
    client, state = _sitting(frozen_clock)
    question = state["questions"][2]
    path = f"/api/v1/attempts/{state['attempt_id']}/responses/{question['id']}"
    body = {"answer": {"v": 1, "kind": "NUMERIC", "value": "46"}, "client_seq": 1}

    missing = send(client, "put", path, body)
    junk = send(client, "put", path, body, headers={"X-Exam-Client": "not-a-uuid"})

    assert (missing.status_code, missing.json()["code"]) == (409, "attempt_taken_over")
    assert junk.json()["code"] == "attempt_taken_over"


@pytest.mark.parametrize(
    ("body", "status", "code"),
    [
        ({"answer": None, "client_seq": 1, "extra": 1}, 422, "validation_error"),
        ({"answer": None, "client_seq": 0}, 422, "validation_error"),
        (
            {"answer": {"v": 1, "kind": "NUMERIC", "value": "4e2"}, "client_seq": 1},
            422,
            "answer_invalid",
        ),
    ],
)
def test_bad_saves_are_refused(
    frozen_clock: FrozenClock, body: dict[str, object], status: int, code: str
) -> None:
    client, state = _sitting(frozen_clock)
    question = state["questions"][2]
    path = f"/api/v1/attempts/{state['attempt_id']}/responses/{question['id']}"

    response = send(
        client, "put", path, body, headers={"X-Exam-Client": str(state["exam_client_id"])}
    )

    assert (response.status_code, response.json()["code"]) == (status, code)


def test_heartbeat_visit_and_submit(frozen_clock: FrozenClock) -> None:
    client, state = _sitting(frozen_clock)
    header = {"X-Exam-Client": str(state["exam_client_id"])}
    base = f"/api/v1/attempts/{state['attempt_id']}"
    question_id = state["questions"][0]["id"]

    beat = send(client, "post", f"{base}/heartbeat", headers=header)
    visit = send(client, "post", f"{base}/questions/{question_id}/visit", headers=header)
    submitted = send(client, "post", f"{base}/submit", headers=header)
    after = send(client, "get", base, headers=header).json()

    assert beat.json()["status"] == "IN_PROGRESS"
    assert visit.status_code == 204
    assert submitted.json() == {
        "status": "ENDED",
        "end_reason": "SUBMITTED",
        "ended_at": "2026-11-12T04:30:00Z",
        "result_available": False,
    }
    assert (after["status"], after["questions"]) == ("ENDED", [])


def test_start_before_the_teacher_is_a_409_with_server_time(frozen_clock: FrozenClock) -> None:
    me = make_student()
    assignment_id = assign([me.id], now=frozen_clock.now(), window=locked())

    response = send(logged_in(me.email), "post", f"/api/v1/my/tests/{assignment_id}/attempts")

    assert (response.status_code, response.json()["code"]) == (409, "waiting_for_teacher")
    assert "server_now" in response.json()["context"]
    start(assignment_id, now=frozen_clock.now())
