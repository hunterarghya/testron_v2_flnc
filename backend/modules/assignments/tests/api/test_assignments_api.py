"""HTTP contract of the teacher's assignment endpoints (api_contract.md §2.6, §3.3)."""

from typing import Any

import pytest
from django.test import Client

from core.clock import FrozenClock
from tests.clients import logged_in, send
from tests.factories.assignments import assignable_test
from tests.factories.identity import make_user
from tests.factories.students import make_student

pytestmark = pytest.mark.django_db
ASSIGNMENTS = "/api/v1/admin/assignments"
PUBLICATION = {
    "mode": "MANUAL",
    "content": "SCORE_ONLY",
    "show_paper": False,
    "show_solutions": False,
    "show_rank_and_stats": False,
}


@pytest.fixture
def teacher(frozen_clock: FrozenClock) -> Client:
    return logged_in(make_user(teacher=True).email)


def create(client: Client, **changes: object) -> Any:
    body = {
        "test_id": str(assignable_test().id),
        "title": "Cell Biology",
        "student_ids": [str(make_student().id)],
        "window": {"kind": "MANUAL"},
        "gate": {"requires_activation": False, "password": "4321", "password_confirm": "4321"},
        "integrity": {"grace_s": 5, "max_warnings": 3, "action": "AUTO_SUBMIT"},
        "publication": PUBLICATION,
    }
    return send(client, "post", ASSIGNMENTS, body | changes)


def test_create_answers_201_with_the_detail(teacher: Client) -> None:
    response = create(teacher, timing_override={"kind": "TOTAL", "duration_s": 1200})

    assert response.status_code == 201
    body = response.json()
    assert (body["state"], body["window_kind"], body["locked"]) == ("WAITING", "MANUAL", True)
    assert body["gate"] == {"requires_activation": False, "has_password": True}
    assert body["timing"] == {"kind": "TOTAL", "total_duration_s": 1200, "allow_return": False}
    assert body["audience"]["count"] == 1
    assert (body["publication"]["mode"], body["publication_state"]) == ("MANUAL", "UNPUBLISHED")
    assert "4321" not in response.content.decode()


def test_create_errors_use_the_contract_codes(teacher: Client) -> None:
    mismatch = create(
        teacher, gate={"requires_activation": False, "password": "1234", "password_confirm": "x"}
    )
    wrong_kind = create(teacher, timing_override={"kind": "PER_QUESTION", "default_question_s": 60})
    unknown_field = create(teacher, colour="red")

    assert mismatch.json()["code"] == "password_mismatch"
    assert wrong_kind.json()["code"] == "validation_error"
    assert unknown_field.status_code == 422


def test_patch_after_the_start_names_the_editable_fields(teacher: Client) -> None:
    assignment = create(teacher, window={"kind": "OPEN"}).json()

    response = send(
        teacher,
        "patch",
        f"{ASSIGNMENTS}/{assignment['id']}",
        {"gate": {"requires_activation": True}},
    )

    assert response.status_code == 409
    assert response.json()["code"] == "assignment_started"
    assert response.json()["context"]["editable_fields"] == ["title", "publication", "password"]


def test_password_set_reveal_and_remove(teacher: Client) -> None:
    path = f"{ASSIGNMENTS}/{create(teacher).json()['id']}/password"

    assert send(teacher, "get", path).json() == {"password": "4321"}
    changed = send(teacher, "put", path, {"password": "9876", "password_confirm": "9876"})
    assert changed.status_code == 204
    assert send(teacher, "get", path).json() == {"password": "9876"}
    assert send(teacher, "put", path, {"password": None}).status_code == 204
    assert send(teacher, "get", path).json() == {"password": None}


def test_audience_add_and_remove_answer_bulk_results(teacher: Client) -> None:
    assignment = create(teacher).json()
    newcomer = str(make_student().id)
    audience = f"{ASSIGNMENTS}/{assignment['id']}/audience"

    added = send(teacher, "post", f"{audience}/add", {"student_ids": [newcomer]}).json()
    removed = send(teacher, "post", f"{audience}/remove", {"student_ids": [newcomer]}).json()

    assert added == {"succeeded": [newcomer], "skipped": []}
    assert removed == {"succeeded": [newcomer], "skipped": []}


def test_list_cancel_and_filters(teacher: Client) -> None:
    assignment_id = create(teacher).json()["id"]

    assert send(teacher, "post", f"{ASSIGNMENTS}/{assignment_id}/cancel").status_code == 204
    cancelled = send(teacher, "get", f"{ASSIGNMENTS}?state=cancelled").json()
    upcoming = send(teacher, "get", f"{ASSIGNMENTS}?state=upcoming&from=2020-01-01T00:00:00Z")

    assert [row["id"] for row in cancelled["items"]] == [assignment_id]
    assert upcoming.json()["total"] == 0
    again = send(teacher, "post", f"{ASSIGNMENTS}/{assignment_id}/cancel")
    assert again.json()["code"] == "assignment_cancelled"


def test_students_are_kept_out(frozen_clock: FrozenClock) -> None:
    student = make_student()
    client = logged_in(student.email)

    assert send(client, "get", ASSIGNMENTS).status_code == 403


def test_start_and_lobby(teacher: Client) -> None:
    assignment_id = create(teacher).json()["id"]
    path = f"{ASSIGNMENTS}/{assignment_id}"

    lobby = send(teacher, "get", f"{path}/lobby").json()
    started = send(teacher, "post", f"{path}/activate")
    again = send(teacher, "post", f"{path}/activate")

    assert (lobby["counts"], lobby["state"], lobby["joined"]) == (
        {"joined": 0, "audience": 1},
        "WAITING",
        [],
    )
    assert started.status_code == 200
    assert started.json() == again.json()
    assert started.json()["anchor_at"] == started.json()["activated_at"]


def test_start_on_an_open_test_is_refused(teacher: Client) -> None:
    assignment_id = create(teacher, window={"kind": "OPEN"}).json()["id"]

    response = send(teacher, "post", f"{ASSIGNMENTS}/{assignment_id}/activate")

    assert (response.status_code, response.json()["code"]) == (409, "activation_not_required")
