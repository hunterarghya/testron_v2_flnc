"""Opening an attempt in the hall, on load or resume: the latest device wins
(domain_model.md §5.9). The same device refreshing keeps its id (E-40); any other takes over,
and the teacher sees "device changed" (E-39)."""

from dataclasses import replace
from uuid import UUID

from django.db import transaction

from core.context import Ctx
from core.ids import uuid7
from modules.assignments import public as assignments
from modules.delivery.domain.attempt import AttemptRecord, is_takeover
from modules.delivery.repositories import attempts, integrity_events, responses
from modules.delivery.services.attempt_views import AttemptStateView, state_view
from modules.delivery.services.live import open_live, paper_of


def open_attempt(
    ctx: Ctx, attempt_id: UUID, student_id: UUID, *, client_id: UUID | None, take_over: bool = True
) -> AttemptStateView:
    """`take_over=False` when a start at the same instant created it: both get one device id."""
    with transaction.atomic():
        attempt = attempts.lock_for_student(attempt_id, student_id)
        terms = assignments.get_sitting_terms(attempt.assignment_id, student_id)
        live = open_live(ctx, attempt, terms)
        if take_over and live.attempt.in_progress and is_takeover(live.attempt, client_id):
            live = replace(live, attempt=_take_over(ctx, live.attempt))
        stored = responses.of_attempt(attempt_id)
    return state_view(live, terms=terms, paper=paper_of(attempt), stored=stored, now=ctx.now)


def _take_over(ctx: Ctx, attempt: AttemptRecord) -> AttemptRecord:
    """A new id for this device. Its clock is the same: a takeover gives no extra time."""
    if attempt.active_client_id is not None:
        integrity_events.record_device_change(attempt.id, now=ctx.now)
    client_id = uuid7()
    attempts.set_active_client(attempt.id, client_id)
    return replace(attempt, active_client_id=client_id)
