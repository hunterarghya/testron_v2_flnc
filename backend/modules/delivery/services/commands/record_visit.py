from uuid import UUID

from django.db import transaction

from core.context import Ctx
from modules.assignments import public as assignments
from modules.delivery.domain.attempt import write_refusal
from modules.delivery.domain.stages import ensure_answerable
from modules.delivery.policies import ensure_active_student
from modules.delivery.repositories import attempts, responses
from modules.delivery.services.live import open_live


def record_visit(ctx: Ctx, *, attempt_id: UUID, question_id: UUID, client_id: UUID | None) -> None:
    """The student opened a question: the palette's "not answered" state (P-03). It never
    changes an answer, and only a question of a stage open now can be visited."""
    student_id = ensure_active_student(ctx.actor)
    with transaction.atomic():
        attempt = attempts.lock_for_save(attempt_id, student_id)
        terms = assignments.get_sitting_terms(attempt.assignment_id, student_id)
        live = open_live(ctx, attempt, terms)
        refusal = write_refusal(live.attempt, client_id)
        if refusal is None:
            stage = attempt.plan.stage_of(question_id)
            ensure_answerable(live.clock, live.progress, stage, now=ctx.now)
            responses.visit(attempt_id, question_id, now=ctx.now)
    if refusal is not None:
        raise refusal
