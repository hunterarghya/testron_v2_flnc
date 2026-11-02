"""Admission, end to end over HTTP (testing_strategy.md §3.7, screens.md §5.1): sign up →
verify the email → wait as Pending → the teacher approves → the student is Active."""

import pytest
from django.test import Client

from conftest import AfterCommit, last_emailed_code
from core.clock import FrozenClock
from tests.clients import logged_in, send
from tests.factories.identity import make_user

pytestmark = pytest.mark.django_db
EMAIL = "rina@example.com"


def test_a_new_student_is_admitted(frozen_clock: FrozenClock, after_commit: AfterCommit) -> None:
    student = Client()
    form = {"name": "Rina Das", "email": EMAIL, "password": "a-long-passphrase"}

    # S-02: sign up; the code arrives by email
    with after_commit():
        assert send(student, "post", "/api/v1/auth/sign-up", form).status_code == 202

    # S-03: verify; the student is logged in and waiting
    verified = send(
        student,
        "post",
        "/api/v1/auth/email-verification",
        {"email": EMAIL, "code": last_emailed_code()},
    ).json()
    assert verified["status"] == "PENDING"
    # S-05: the student area stays closed while waiting
    assert student.get("/api/v1/admin/students").json()["code"] == "forbidden"

    # T-14: the teacher finds the request and approves it
    teacher = logged_in(make_user(teacher=True).email)
    pending = teacher.get("/api/v1/admin/students", {"status": "PENDING"}).json()["items"]
    assert [row["email"] for row in pending] == [EMAIL]
    approved = send(
        teacher, "post", "/api/v1/admin/students/approve", {"student_ids": [pending[0]["id"]]}
    )
    assert approved.json()["succeeded"] == [pending[0]["id"]]

    # "Check again": the same session now shows an active student
    session = student.get("/api/v1/auth/session").json()["user"]
    assert session["status"] == "ACTIVE"
    active = teacher.get("/api/v1/admin/students", {"status": "ACTIVE"}).json()["items"]
    assert [row["email"] for row in active] == [EMAIL]
