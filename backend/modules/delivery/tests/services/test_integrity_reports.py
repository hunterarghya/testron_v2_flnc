"""report_integrity_event (domain_model.md §5.8; E-20, E-21; P-06)."""

from datetime import timedelta
from uuid import UUID, uuid4

import pytest

from core.clock import FrozenClock
from core.context import Ctx
from core.errors import DomainError, NotFound
from modules.delivery.domain.integrity import WarningAction
from modules.delivery.domain.values import EndReason, IntegrityKind
from modules.delivery.services.attempt_views import AttemptStateView
from modules.delivery.services.commands.report_integrity_event import (
    IntegrityAck,
    IntegrityReport,
    report_integrity_event,
)
from tests.factories.assignments import assign
from tests.factories.delivery import as_student, begin, stored
from tests.factories.students import make_student

pytestmark = pytest.mark.django_db


def _sitting(clock: FrozenClock) -> tuple[Ctx, AttemptStateView]:
    me = make_student().id
    ctx = as_student(me, now=clock.now())
    return ctx, begin(ctx, assign([me], now=ctx.now))


def _report(
    ctx: Ctx, state: AttemptStateView, event_id: UUID, *, beyond: bool, back: bool = False
) -> IntegrityAck:
    return report_integrity_event(
        ctx,
        attempt_id=state.attempt.id,
        client_id=state.attempt.active_client_id,
        report=IntegrityReport(
            event_id=event_id,
            kind=IntegrityKind.TAB_HIDDEN,
            left_at=ctx.now - timedelta(seconds=8),
            beyond_grace=beyond,
            returned_at=ctx.now if back else None,
        ),
    )


def test_a_brief_absence_is_recorded_but_not_counted(frozen_clock: FrozenClock) -> None:
    ctx, state = _sitting(frozen_clock)

    ack = _report(ctx, state, uuid4(), beyond=False, back=True)

    assert (ack.counted, ack.warning_count, ack.action) == (False, 0, WarningAction.NONE)


def test_one_departure_costs_one_warning_however_often_reported_e20(
    frozen_clock: FrozenClock,
) -> None:
    ctx, state = _sitting(frozen_clock)
    event = uuid4()

    first = _report(ctx, state, event, beyond=False)
    counted = _report(ctx, state, event, beyond=True)
    again = _report(ctx, state, event, beyond=True, back=True)

    assert first.action is WarningAction.NONE
    assert (counted.counted, counted.warning_count, counted.action) == (True, 1, WarningAction.WARN)
    assert (again.counted, again.warning_count) == (True, 1)
    assert stored(state.attempt.id).warning_count == 1


def test_the_last_warning_ends_the_attempt(frozen_clock: FrozenClock) -> None:
    ctx, state = _sitting(frozen_clock)

    acks = [_report(ctx, state, uuid4(), beyond=True) for _ in range(3)]

    assert [a.action for a in acks] == [WarningAction.WARN, WarningAction.WARN, WarningAction.ENDED]
    assert acks[-1].max_warnings == 3
    attempt = stored(state.attempt.id)
    assert (attempt.end_reason, attempt.warning_count) == (EndReason.AUTO_SUBMITTED, 3)
    late = _report(ctx, state, uuid4(), beyond=True)
    assert (late.counted, late.action, late.warning_count) == (False, WarningAction.ENDED, 3)


def test_an_event_from_another_attempt_is_not_found(frozen_clock: FrozenClock) -> None:
    ctx, state = _sitting(frozen_clock)
    other_ctx, other = _sitting(frozen_clock)
    event = uuid4()
    _report(other_ctx, other, event, beyond=False)

    with pytest.raises(NotFound):
        _report(ctx, state, event, beyond=True)


def test_only_the_active_device_reports(frozen_clock: FrozenClock) -> None:
    ctx, state = _sitting(frozen_clock)
    with pytest.raises(DomainError) as refused:
        report_integrity_event(
            ctx,
            attempt_id=state.attempt.id,
            client_id=uuid4(),
            report=IntegrityReport(uuid4(), IntegrityKind.WINDOW_BLUR, ctx.now, beyond_grace=True),
        )
    assert refused.value.code == "attempt_taken_over"
