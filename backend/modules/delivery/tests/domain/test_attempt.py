"""Which writes may reach an attempt (domain_model.md §3.6 #6 and #8, §5.9; E-39, E-40), and
what grading is handed for each answer."""

from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from modules.delivery.domain.answers import answer_value
from modules.delivery.domain.attempt import AttemptRecord, is_takeover, write_refusal
from modules.delivery.domain.errors import AttemptEnded, AttemptTakenOver
from modules.delivery.domain.plan import Plan
from modules.delivery.domain.values import AttemptStatus, EndReason
from tests.factories.delivery import choice, numeric

T0 = datetime(2026, 11, 12, 4, 30, tzinfo=UTC)
DEVICE = uuid4()
RUNNING = AttemptRecord(
    id=uuid4(),
    assignment_id=uuid4(),
    student_id=uuid4(),
    take_number=1,
    is_granted=False,
    status=AttemptStatus.IN_PROGRESS,
    end_reason=None,
    started_at=T0,
    anchor_at=T0,
    ended_at=None,
    plan=Plan(stages=(), option_order={}),
    current_stage_index=0,
    furthest_stage_index=0,
    warning_count=0,
    active_client_id=DEVICE,
)
ENDED = replace(RUNNING, status=AttemptStatus.ENDED, end_reason=EndReason.SUBMITTED, ended_at=T0)


def test_the_active_device_may_write_e40() -> None:
    assert write_refusal(RUNNING, DEVICE) is None
    assert not is_takeover(RUNNING, DEVICE)


def test_any_other_device_is_refused_e39() -> None:
    assert isinstance(write_refusal(RUNNING, uuid4()), AttemptTakenOver)
    assert isinstance(write_refusal(RUNNING, None), AttemptTakenOver)
    assert is_takeover(RUNNING, None)


def test_an_ended_attempt_refuses_every_write_with_its_ending() -> None:
    refusal = write_refusal(ENDED, DEVICE)
    assert isinstance(refusal, AttemptEnded)
    assert refusal.context == {"ended_at": T0, "end_reason": EndReason.SUBMITTED}


def test_grading_gets_the_options_the_number_or_nothing() -> None:
    picked = uuid4()
    assert answer_value(choice(picked)) == frozenset({picked})
    assert answer_value(numeric("-12.5")) == Decimal("-12.5")
    assert answer_value(None) is None
