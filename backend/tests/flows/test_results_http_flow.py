"""HTTP contract of results (api_contract.md §2.7, §2.9, §3.5; T-11, T-12, P-08, P-09)."""

import pytest

from core.clock import FrozenClock
from modules.assignments.domain.settings import Publication
from modules.assignments.domain.values import PublicationMode, PublishContent
from modules.delivery.services.commands.submit_attempt import submit_attempt
from tests.clients import logged_in, send
from tests.factories.assignments import assign, exam_test, the_teacher
from tests.factories.delivery import answer, as_student, begin, choice, option_id
from tests.factories.students import make_student

pytestmark = pytest.mark.django_db
SHOWN = Publication(mode=PublicationMode.AUTO_IMMEDIATE, content=PublishContent.ANSWER_REVIEW)


def test_teacher_results_endpoints(frozen_clock: FrozenClock) -> None:
    me = make_student(name="Mou")
    assignment_id = assign([me.id], now=frozen_clock.now(), test=exam_test())
    ctx = as_student(me.id, now=frozen_clock.now())
    state = begin(ctx, assignment_id)
    submit_attempt(ctx, attempt_id=state.attempt.id, client_id=state.attempt.active_client_id)
    teacher = logged_in(the_teacher().email)
    base = f"/api/v1/admin/assignments/{assignment_id}"

    book = send(teacher, "get", f"{base}/gradebook").json()
    stats = send(teacher, "get", f"{base}/question-stats").json()
    key = send(teacher, "get", f"{base}/answer-key").json()
    sheet = send(teacher, "get", f"/api/v1/admin/attempts/{state.attempt.id}/sheet").json()
    sheets = send(teacher, "get", f"{base}/answer-sheets?attempt_ids={state.attempt.id}")
    bad_ids = send(teacher, "get", f"{base}/answer-sheets?attempt_ids=nope")
    csv = send(teacher, "get", f"{base}/exports/gradebook.csv")

    assert (book["rows"][0]["name"], book["rows"][0]["status"], book["stats"]["count"]) == (
        "Mou",
        "SUBMITTED",
        1,
    )
    assert [s["number"] for s in stats] == [1, 2, 3]
    assert key["version"] == 1
    assert (sheet["student"]["name"], len(sheet["questions"]), sheet["score"]) == ("Mou", 3, "0.00")
    assert len(sheets.json()) == 1
    assert bad_ids.status_code == 422
    assert csv["Content-Type"] == "text/csv; charset=utf-8"
    assert "attachment; filename*=UTF-8''" in csv["Content-Disposition"]
    assert send(teacher, "get", "/api/v1/admin/results?tab=all").json()["total"] == 0
    assert (
        send(teacher, "get", "/api/v1/admin/dashboard").json()["live"][0]["title"] == "Cell Biology"
    )


def test_student_sees_a_visible_result_and_not_a_hidden_one(frozen_clock: FrozenClock) -> None:
    me = make_student()
    shown_id = assign([me.id], now=frozen_clock.now(), test=exam_test(), publication=SHOWN)
    hidden_id = assign([me.id], now=frozen_clock.now(), test=exam_test())
    ctx = as_student(me.id, now=frozen_clock.now())
    attempts = {}
    for assignment_id in (shown_id, hidden_id):
        state = begin(ctx, assignment_id)
        answer(ctx, state, 1, choice(option_id(state, 1, "A")))
        submit_attempt(ctx, attempt_id=state.attempt.id, client_id=state.attempt.active_client_id)
        attempts[assignment_id] = state.attempt.id
    client = logged_in(me.email)

    shown = send(client, "get", f"/api/v1/my/results/{attempts[shown_id]}").json()
    hidden = send(client, "get", f"/api/v1/my/results/{attempts[hidden_id]}")
    past = send(client, "get", "/api/v1/my/past-tests").json()

    assert (shown["score"], shown["questions"][0]["outcome"]) == ("4.00", "CORRECT")
    assert shown["questions"][0]["solution"] is None
    assert (hidden.status_code, hidden.json()["code"]) == (404, "results_not_published")
    assert sorted(card["state"] for card in past["items"]) == ["AWAITING_RESULTS", "PUBLISHED"]
    assert "Take 1" in past["items"][0]["label"]
