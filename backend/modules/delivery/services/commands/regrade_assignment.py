from datetime import datetime
from uuid import UUID

from modules.delivery.domain.answers import answer_value, read_answer
from modules.delivery.repositories import attempts, responses
from modules.grading import public as grading


def regrade_assignment(assignment_id: UUID, *, now: datetime) -> int:
    """After an answer key correction (domain_model.md §6.2, E-14): every ended attempt is
    graded again, with its score and key version, inside the caller's transaction. Their
    answers never change, only the marks. Returns how many were regraded. No policy: the
    caller is results' key correction, which checks the teacher."""
    ended = attempts.lock_ended_of(assignment_id)
    if not ended:
        return 0
    stored = responses.answers_of(ended)
    given = {
        attempt_id: {q: answer_value(read_answer(answer)) for q, answer in answers.items()}
        for attempt_id, answers in stored.items()
    }
    results = grading.regrade_attempts(assignment_id, given)
    attempts.set_scores(
        {a: (r.score, r.answer_key_version) for a, r in results.items()}, graded_at=now
    )
    return len(results)
