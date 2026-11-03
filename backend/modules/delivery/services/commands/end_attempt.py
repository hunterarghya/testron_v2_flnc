from dataclasses import replace
from datetime import datetime

from modules.delivery.domain.answers import answer_value, read_answer
from modules.delivery.domain.attempt import AttemptRecord
from modules.delivery.domain.values import AttemptStatus, EndReason
from modules.delivery.repositories import attempts, responses
from modules.grading import public as grading


def end_attempt(
    attempt: AttemptRecord, *, reason: EndReason, ended_at: datetime, now: datetime
) -> AttemptRecord:
    """The one ending path, for every reason (domain_model.md §5.5): the attempt is graded in
    the same transaction, so none is ever ended but ungraded [V1 F-10]. No policy: callers
    are delivery's use cases, holding the attempt's lock."""
    stored = responses.of_attempt(attempt.id)
    given = {q: answer_value(read_answer(r.answer)) for q, r in stored.items()}
    result = grading.grade_attempt(attempt.id, attempt.assignment_id, given)
    attempts.mark_ended(
        attempt.id,
        reason=reason,
        ended_at=ended_at,
        score=result.score,
        answer_key_version=result.answer_key_version,
        graded_at=now,
    )
    return replace(attempt, status=AttemptStatus.ENDED, end_reason=reason, ended_at=ended_at)
