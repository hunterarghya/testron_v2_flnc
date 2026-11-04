"""Housekeeping end to end (database_schema.md §5.4, architecture.md §5.6; ADR-083): what each
run clears, the abandoned-attempt safety net, the trigger and the management commands."""

from datetime import timedelta
from io import StringIO
from uuid import UUID

import pytest
from django.core.management import CommandError, call_command
from django.test import override_settings

from core.clock import FrozenClock
from core.context import Ctx, system_ctx
from modules.assignments.models import LobbyPresence
from modules.delivery.public import row_of
from modules.housekeeping.public import run_housekeeping, run_housekeeping_if_due
from modules.identity.models import EmailOtp, RateLimitBucket, UserSession
from tests.clients import logged_in, send
from tests.factories.assignments import assign, exam_test, locked, start
from tests.factories.delivery import as_student, begin
from tests.factories.identity import make_user
from tests.factories.students import make_student

pytestmark = pytest.mark.django_db
DAY = timedelta(days=1)


def _otp(clock: FrozenClock, age: timedelta, *, live: bool) -> UUID:
    created = clock.now() - age
    return EmailOtp.objects.create(
        user=make_user(),
        purpose="VERIFY_EMAIL",
        code_hash="x" * 64,
        expires_at=created + timedelta(minutes=15),
        consumed_at=None if live else created,
        created_at=created,
    ).id


def _bucket(
    clock: FrozenClock, key: str, age: timedelta, blocked_for: timedelta | None = None
) -> None:
    started = clock.now() - age
    RateLimitBucket.objects.create(
        key=key,
        window_started_at=started,
        hits=3,
        blocked_until=clock.now() + blocked_for if blocked_for else None,
    )


def _session(clock: FrozenClock, key: str, expires_in: timedelta) -> None:
    UserSession.objects.create(
        session_key=key, session_data="", expire_date=clock.now() + expires_in
    )


def _lobby(clock: FrozenClock, *, started: bool) -> UUID:
    student_id = make_student().id
    assignment_id = assign([student_id], now=clock.now(), window=locked())
    LobbyPresence.objects.create(
        assignment_id=assignment_id, student_id=student_id, last_seen_at=clock.now()
    )
    if started:
        start(assignment_id, now=clock.now())
    return assignment_id


def test_a_run_clears_only_what_is_old_enough(frozen_clock: FrozenClock) -> None:
    old_otp, new_otp = _otp(frozen_clock, 8 * DAY, live=False), _otp(frozen_clock, DAY, live=True)
    _bucket(frozen_clock, "login:ip:old", 2 * DAY)
    _bucket(frozen_clock, "login:ip:blocked", 2 * DAY, blocked_for=timedelta(hours=1))
    _bucket(frozen_clock, "login:ip:fresh", timedelta(minutes=5))
    _session(frozen_clock, "expired" + "x" * 25, -timedelta(seconds=1))
    _session(frozen_clock, "current" + "x" * 25, DAY)
    waiting, started = _lobby(frozen_clock, started=False), _lobby(frozen_clock, started=True)

    report = run_housekeeping(system_ctx())

    assert (report.otps, report.rate_limits, report.lobby_rows, report.sessions) == (1, 1, 1, 1)
    assert list(EmailOtp.objects.values_list("id", flat=True)) == [new_otp]
    assert old_otp != new_otp
    assert set(RateLimitBucket.objects.values_list("key", flat=True)) == {
        "login:ip:blocked",
        "login:ip:fresh",
    }
    assert list(UserSession.objects.values_list("session_key", flat=True)) == ["current" + "x" * 25]
    assert list(LobbyPresence.objects.values_list("assignment_id", flat=True)) == [waiting]
    assert started != waiting


def test_an_abandoned_attempt_ends_at_its_deadline_not_at_the_sweep(
    frozen_clock: FrozenClock,
) -> None:
    student_id = make_student().id
    assignment_id = assign([student_id], now=frozen_clock.now(), test=exam_test())
    state = begin(as_student(student_id, now=frozen_clock.now()), assignment_id)
    deadline = frozen_clock.now() + timedelta(seconds=3600)

    frozen_clock.advance(hours=23)
    assert run_housekeeping(system_ctx()).attempts_ended == 0
    frozen_clock.advance(hours=2)
    assert run_housekeeping(system_ctx()).attempts_ended == 1

    row = row_of(state.attempt.id)
    assert (row.ended_at, row.graded_at is not None) == (deadline, True)


def test_only_one_run_in_ten_minutes(frozen_clock: FrozenClock) -> None:
    assert run_housekeeping_if_due(system_ctx()) is not None
    frozen_clock.advance(minutes=5)
    assert run_housekeeping_if_due(system_ctx()) is None
    frozen_clock.advance(minutes=5)
    assert run_housekeeping_if_due(system_ctx()) is not None


RUNS: list[Ctx] = []


def record_run(ctx: Ctx) -> None:
    RUNS.append(ctx)


def fail_run(ctx: Ctx) -> None:
    raise RuntimeError("cleanup broke")


@override_settings(HOUSEKEEPING_TRIGGER="tests.flows.test_housekeeping_flow.record_run")
def test_signed_in_traffic_triggers_it_at_most_once_a_minute(frozen_clock: FrozenClock) -> None:
    RUNS.clear()
    client = logged_in(make_student().email)
    asked = len(RUNS)

    send(client, "get", "/api/v1/auth/session")
    frozen_clock.advance(seconds=61)
    send(client, "get", "/api/v1/auth/session")

    assert asked == 1
    assert len(RUNS) == 2
    assert RUNS[-1].actor.user_id is None


@override_settings(HOUSEKEEPING_TRIGGER="tests.flows.test_housekeeping_flow.fail_run")
def test_a_failed_run_never_fails_the_request(frozen_clock: FrozenClock) -> None:
    client = logged_in(make_student().email)
    frozen_clock.advance(seconds=61)

    assert send(client, "get", "/api/v1/auth/session").status_code == 200


def run(command: str, *args: str) -> str:
    output = StringIO()
    call_command(command, *args, stdout=output)
    return output.getvalue()


def test_the_management_commands(frozen_clock: FrozenClock) -> None:
    _bucket(frozen_clock, "login:email:rina@example.com", timedelta(minutes=1), timedelta(hours=1))
    _bucket(frozen_clock, "login:ip:10.0.0.1", timedelta(minutes=1))
    _bucket(frozen_clock, "login:ip:10.0.0.2", timedelta(minutes=1))

    assert "Cleared 2" in run("clear_rate_limits", "--key", "login:ip:*")
    assert "Cleared 1" in run("clear_rate_limits", "--key", "login:email:rina@example.com")
    assert "Cleared 0" in run("clear_rate_limits", "--key", "login_ip%")
    with pytest.raises(CommandError, match="narrower"):
        run("clear_rate_limits", "--key", "*")
    assert "ended 0 abandoned attempts" in run("run_housekeeping")
    assert "Ended 0 attempt(s)" in run("finalize_expired", "--all")
    with pytest.raises(CommandError, match="--all"):
        run("finalize_expired")
