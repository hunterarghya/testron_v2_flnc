from uuid import UUID

from django.db import transaction

from core.context import Ctx
from modules.assignments import public as assignments
from modules.delivery.domain.attempt import write_refusal
from modules.delivery.domain.errors import AttemptTakenOver
from modules.delivery.policies import ensure_active_student
from modules.delivery.repositories import attempts
from modules.delivery.services.attempt_views import AttemptClockView, clock_view
from modules.delivery.services.live import open_live


def get_attempt_clock(ctx: Ctx, *, attempt_id: UUID, client_id: UUID | None) -> AttemptClockView:
    """The hall's heartbeat, every 15 s without saves (api_contract.md §4): the clock, so an
    extension, an auto-advance or "end for everyone" reaches the student. An ended attempt
    just says so; another device's heartbeat is refused (§5.9)."""
    student_id = ensure_active_student(ctx.actor)
    with transaction.atomic():
        attempt = attempts.lock_for_student(attempt_id, student_id)
        terms = assignments.get_sitting_terms(attempt.assignment_id, student_id)
        live = open_live(ctx, attempt, terms)
        refusal = write_refusal(live.attempt, client_id)
        if refusal is None:
            attempts.touch(attempt_id, now=ctx.now)
    if isinstance(refusal, AttemptTakenOver):
        raise refusal
    return clock_view(live, now=ctx.now)
