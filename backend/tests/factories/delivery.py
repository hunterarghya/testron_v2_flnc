"""Students sitting tests, through the real use cases (not the use cases' rules)."""

from datetime import datetime
from uuid import UUID

from core.context import Actor, Ctx, Role, StudentStatus
from modules.assignments.models import RetakeGrant
from modules.delivery.domain.answers import Answer, ChoiceAnswer, NumericAnswer
from modules.delivery.models import Attempt
from modules.delivery.services.attempt_views import AttemptStateView
from modules.delivery.services.commands.save_response import Saved, SaveRequest, save_response
from modules.delivery.services.commands.start_attempt import start_attempt
from modules.grading.models import Grade


def as_student(student_id: UUID, *, now: datetime) -> Ctx:
    actor = Actor(user_id=student_id, role=Role.STUDENT, student_status=StudentStatus.ACTIVE)
    return Ctx(actor, now=now, request_id="hall")


def begin(
    ctx: Ctx, assignment_id: UUID, *, password: str | None = None, client_id: UUID | None = None
) -> AttemptStateView:
    return start_attempt(
        ctx, assignment_id=assignment_id, password=password, client_id=client_id
    ).view


def choice(*option_ids: UUID) -> ChoiceAnswer:
    return ChoiceAnswer(frozenset(option_ids))


def numeric(value: str) -> NumericAnswer:
    return NumericAnswer(value)


def answer(
    ctx: Ctx, state: AttemptStateView, number: int, given: Answer | None, *, seq: int = 1
) -> Saved:
    """Save an answer to question `number` (1-based, the student's order) from the device
    that opened the attempt."""
    question = state.questions[number - 1].question
    return save_response(
        ctx,
        attempt_id=state.attempt.id,
        client_id=state.attempt.active_client_id,
        save=SaveRequest(question.id, given, marked_for_review=False, client_seq=seq),
    )


def option_id(state: AttemptStateView, number: int, label: str) -> UUID:
    found = next(o for o in state.questions[number - 1].options if o.label == label)
    return found.id


def stored(attempt_id: UUID) -> Attempt:
    return Attempt.objects.get(pk=attempt_id)


def grant_retake(assignment_id: UUID, student_id: UUID, *, now: datetime) -> None:
    RetakeGrant.objects.create(assignment_id=assignment_id, student_id=student_id, granted_at=now)


def grades_of(attempt_id: UUID) -> dict[UUID, str]:
    """Each paper question's grade outcome."""
    rows = Grade.objects.filter(attempt_id=attempt_id).values_list("question_id", "outcome")
    return dict(rows)


def grant_used_by(assignment_id: UUID, student_id: UUID) -> UUID | None:
    grant = RetakeGrant.objects.get(assignment_id=assignment_id, student_id=student_id)
    return grant.consumed_by_attempt_id
