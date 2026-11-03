"""HTTP contract of the live monitor and its actions (api_contract.md §2.6, §3.3; T-10, D-04)."""

from uuid import uuid4

import pytest

from core.clock import FrozenClock
from tests.clients import logged_in, send
from tests.factories.assignments import assign, the_teacher
from tests.factories.delivery import as_student, begin
from tests.factories.students import make_student

pytestmark = pytest.mark.django_db


def test_monitor_end_force_and_events(frozen_clock: FrozenClock) -> None:
    me = make_student(name="Aditi")
    assignment_id = assign([me.id, make_student().id], now=frozen_clock.now())
    state = begin(as_student(me.id, now=frozen_clock.now()), assignment_id)
    teacher = logged_in(the_teacher().email)
    base = f"/api/v1/admin/assignments/{assignment_id}"

    monitor = send(teacher, "get", f"{base}/monitor?filter=in_progress").json()
    events = send(teacher, "get", f"/api/v1/admin/attempts/{state.attempt.id}/integrity-events")
    forced = send(teacher, "post", f"/api/v1/admin/attempts/{state.attempt.id}/force-submit")
    again = send(teacher, "post", f"/api/v1/admin/attempts/{state.attempt.id}/force-submit")
    wrong = send(teacher, "post", f"{base}/end", {"confirm": "end"})
    ended = send(teacher, "post", f"{base}/end", {"confirm": "END"})

    row = monitor["rows"][0]
    assert (row["name"], row["status"], row["take_number"], row["total_questions"]) == (
        "Aditi",
        "IN_PROGRESS",
        1,
        1,
    )
    assert monitor["summary"] == {"IN_PROGRESS": 1, "NOT_STARTED": 1}
    assert events.json() == []
    assert (forced.json()["end_reason"], forced.json()["score"]) == ("FORCE_SUBMITTED", "0.00")
    assert (again.status_code, again.json()["code"]) == (409, "attempt_ended")
    assert (wrong.status_code, wrong.json()["code"]) == (422, "confirmation_mismatch")
    assert ended.json()["ended_attempts"] == 0
    assert send(teacher, "get", f"{base}/monitor?filter=nope").status_code == 422
    assert (
        send(teacher, "get", f"/api/v1/admin/attempts/{uuid4()}/integrity-events").status_code
        == 404
    )
