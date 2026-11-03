from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from django.db import transaction

from core.context import Ctx
from modules.assignments import public as assignments
from modules.delivery.domain.answers import Answer, answer_json, ensure_answer_fits
from modules.delivery.domain.attempt import write_refusal
from modules.delivery.domain.errors import QuestionNotInStage
from modules.delivery.domain.stages import ensure_answerable
from modules.delivery.policies import ensure_active_student
from modules.delivery.repositories import attempts, responses
from modules.delivery.services.attempt_views import AttemptClockView, clock_view
from modules.delivery.services.live import LiveAttempt, open_live, paper_of


@dataclass(frozen=True, slots=True)
class SaveRequest:
    question_id: UUID
    # None: cleared, and that is saved too
    answer: Answer | None
    marked_for_review: bool
    client_seq: int


@dataclass(frozen=True, slots=True)
class Saved:
    saved_at: datetime
    # False: an older retry, acknowledged and ignored (E-05)
    applied: bool
    clock: AttemptClockView


def save_response(
    ctx: Ctx, *, attempt_id: UUID, client_id: UUID | None, save: SaveRequest
) -> Saved:
    """Every answer change, as it happens [F-2] (domain_model.md §3.6 #4): only into a stage
    open now, in the right shape, from the active device, before the deadline. A save after
    the end is refused with attempt_ended (E-04), and the ending found on the way is kept."""
    student_id = ensure_active_student(ctx.actor)
    applied = False
    with transaction.atomic():
        attempt = attempts.lock_for_save(attempt_id, student_id)
        terms = assignments.get_sitting_terms(attempt.assignment_id, student_id)
        live = open_live(ctx, attempt, terms)
        refusal = write_refusal(live.attempt, client_id)
        if refusal is None:
            applied = _store(ctx, live, save)
    if refusal is not None:
        raise refusal
    return Saved(saved_at=ctx.now, applied=applied, clock=clock_view(live, now=ctx.now))


def _store(ctx: Ctx, live: LiveAttempt, save: SaveRequest) -> bool:
    attempt = live.attempt
    question = paper_of(attempt).questions().get(save.question_id)
    if question is None:
        raise QuestionNotInStage()
    ensure_answerable(live.clock, live.progress, attempt.plan.stage_of(question.id), now=ctx.now)
    ensure_answer_fits(save.answer, question)
    applied = responses.save(
        attempt.id,
        question.id,
        answer=answer_json(save.answer),
        marked_for_review=save.marked_for_review,
        client_seq=save.client_seq,
        now=ctx.now,
    )
    attempts.touch(attempt.id, now=ctx.now)
    return applied
