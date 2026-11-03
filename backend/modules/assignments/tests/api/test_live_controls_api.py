"""HTTP contract of extra time and retakes (api_contract.md §2.6; D-02, D-03)."""

import pytest

from core.clock import FrozenClock
from tests.clients import logged_in, send
from tests.factories.assignments import assign, locked, the_teacher
from tests.factories.students import make_student

pytestmark = pytest.mark.django_db


def test_extensions_and_retake_grants(frozen_clock: FrozenClock) -> None:
    me = make_student().id
    started = assign([me], now=frozen_clock.now())
    waiting = assign([me], now=frozen_clock.now(), window=locked())
    teacher = logged_in(the_teacher().email)

    extended = send(
        teacher, "post", f"/api/v1/admin/assignments/{started}/extensions", {"seconds": 600}
    )
    too_long = send(
        teacher, "post", f"/api/v1/admin/assignments/{started}/extensions", {"seconds": 90_000}
    )
    early = send(
        teacher, "post", f"/api/v1/admin/assignments/{waiting}/extensions", {"seconds": 60}
    )
    grants = send(
        teacher,
        "post",
        f"/api/v1/admin/assignments/{started}/retake-grants",
        {"student_ids": [str(me)]},
    )

    assert extended.json() == {"ends_at": None}
    assert (too_long.status_code, too_long.json()["errors"][0]["field"]) == (422, "seconds")
    assert (early.status_code, early.json()["code"]) == (409, "assignment_not_started")
    assert grants.json() == {"succeeded": [str(me)], "skipped": []}


def test_publish_unpublish_and_change_the_mode(frozen_clock: FrozenClock) -> None:
    started = assign([make_student().id], now=frozen_clock.now())
    waiting = assign([make_student().id], now=frozen_clock.now(), window=locked())
    teacher = logged_in(the_teacher().email)
    base = f"/api/v1/admin/assignments/{started}"

    published = send(
        teacher, "post", f"{base}/publish", {"options": {"content": "ANSWER_REVIEW"}}
    ).json()
    hidden = send(teacher, "post", f"{base}/unpublish").json()
    delayed = send(
        teacher, "patch", f"{base}/publication", {"mode": "AUTO_DELAYED", "delay_s": 600}
    ).json()
    early = send(teacher, "post", f"/api/v1/admin/assignments/{waiting}/publish", {})

    assert (published["mode"], published["content"], published["published_at"]) == (
        "MANUAL",
        "ANSWER_REVIEW",
        "2026-11-12T04:30:00Z",
    )
    assert hidden["published_at"] is None
    assert (delayed["mode"], delayed["delay_s"], delayed["published_at"]) == (
        "AUTO_DELAYED",
        600,
        None,
    )
    assert (early.status_code, early.json()["code"]) == (409, "assignment_not_started")
