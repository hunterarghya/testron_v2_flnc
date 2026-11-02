"""HTTP contract of the teacher's admission endpoints (api_contract.md §2.3, T-14)."""

import pytest
from django.test import Client

from conftest import AfterCommit
from core.clock import FrozenClock
from core.context import StudentStatus as S
from modules.students.models import Student
from tests.clients import logged_in, send
from tests.factories.identity import make_user
from tests.factories.students import make_student

pytestmark = pytest.mark.django_db
STUDENTS = "/api/v1/admin/students"


@pytest.fixture
def teacher(frozen_clock: FrozenClock) -> Client:
    return logged_in(make_user(teacher=True).email)


def test_list_returns_a_page_of_rows(teacher: Client) -> None:
    student = make_student(S.PENDING, name="Rina Das", email="rina@example.com")

    body = teacher.get(STUDENTS, {"status": "PENDING"}).json()

    assert (body["total"], body["page"], body["page_size"]) == (1, 1, 50)
    row = body["items"][0]
    assert (row["id"], row["name"], row["status"]) == (str(student.id), "Rina Das", "PENDING")
    assert row["performance_shared"] is False


@pytest.mark.parametrize(
    "query", [{"status": "UNVERIFIED"}, {"status": "ANONYMIZED"}, {"page": 0}, {"page_size": 201}]
)
def test_list_refuses_unknown_filters(teacher: Client, query: dict[str, str | int]) -> None:
    assert teacher.get(STUDENTS, query).status_code == 422


def test_bulk_approve_reports_each_student(teacher: Client) -> None:
    pending, active = make_student(S.PENDING), make_student(S.ACTIVE)

    response = send(
        teacher, "post", f"{STUDENTS}/approve", {"student_ids": [str(pending.id), str(active.id)]}
    )

    assert response.status_code == 200
    assert response.json() == {
        "succeeded": [str(pending.id)],
        "skipped": [{"id": str(active.id), "reason": "status_active"}],
    }


def test_bulk_needs_at_least_one_student(teacher: Client) -> None:
    assert send(teacher, "post", f"{STUDENTS}/approve", {"student_ids": []}).status_code == 422


def test_deactivating_logs_the_student_out_at_once(teacher: Client) -> None:
    student = make_student(S.ACTIVE, email="rina@example.com")
    student_client = logged_in("rina@example.com")

    send(teacher, "post", f"{STUDENTS}/deactivate", {"student_ids": [str(student.id)]})

    assert student_client.get("/api/v1/auth/session").json()["user"] is None


def test_approved_student_sees_active_on_the_next_session_check(teacher: Client) -> None:
    student = make_student(S.PENDING, email="rina@example.com")
    student_client = logged_in("rina@example.com")

    send(teacher, "post", f"{STUDENTS}/approve", {"student_ids": [str(student.id)]})

    assert student_client.get("/api/v1/auth/session").json()["user"]["status"] == "ACTIVE"


def test_anonymize_needs_the_typed_name(teacher: Client) -> None:
    student = make_student(S.DEACTIVATED, name="Rina Das")
    path = f"{STUDENTS}/{student.id}/anonymize"

    wrong = send(teacher, "post", path, {"confirm_name": "Rina"})
    right = send(teacher, "post", path, {"confirm_name": "Rina Das"})

    assert (wrong.status_code, wrong.json()["code"]) == (422, "confirmation_mismatch")
    assert right.status_code == 204


def test_students_cannot_use_the_admission_endpoints(frozen_clock: FrozenClock) -> None:
    student = make_student(S.ACTIVE, email="rina@example.com")
    student_client = logged_in("rina@example.com")

    response = send(
        student_client, "post", f"{STUDENTS}/approve", {"student_ids": [str(student.id)]}
    )

    assert (response.status_code, response.json()["code"]) == (403, "forbidden")


def test_v1_f30_declined_student_cannot_rerequest(
    teacher: Client, after_commit: AfterCommit
) -> None:
    student = make_student(S.PENDING, email="rina@example.com")
    send(teacher, "post", f"{STUDENTS}/decline", {"student_ids": [str(student.id)]})

    with after_commit():
        again = send(
            Client(),
            "post",
            "/api/v1/auth/sign-up",
            {"name": "Rina", "email": "rina@example.com", "password": "a-long-passphrase"},
        )

    assert again.status_code == 202
    assert Student.objects.get(user_id=student.id).status == S.DECLINED
    assert Student.objects.count() == 1
