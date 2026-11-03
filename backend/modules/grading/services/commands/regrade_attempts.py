from collections.abc import Mapping
from uuid import UUID

from modules.assignments import public as assignments
from modules.grading.domain.grade import (
    Given,
    QuestionGrade,
    grade_question,
    keyed_questions,
    total,
)
from modules.grading.repositories import grades
from modules.grading.services.commands.grade_attempt import GradeResult


def regrade_attempts(
    assignment_id: UUID, answers_by_attempt: Mapping[UUID, Mapping[UUID, Given]]
) -> dict[UUID, GradeResult]:
    """Grade these ended attempts again with the current answer key (domain_model.md §3.7 #3,
    §6.2), inside the caller's transaction: every grade replaced, a fixed number of queries
    however many attempts. No policy: there is no route to this, only delivery's regrade."""
    key = assignments.get_answer_key(assignment_id)
    questions = keyed_questions(assignments.get_paper_content(assignment_id), key.entries)
    graded: dict[UUID, list[QuestionGrade]] = {
        attempt_id: [grade_question(q, answers.get(q.id)) for q in questions]
        for attempt_id, answers in answers_by_attempt.items()
    }
    grades.delete_grades(list(graded))
    grades.insert_many(graded)
    return {
        attempt_id: GradeResult(score=total(rows), answer_key_version=key.version)
        for attempt_id, rows in graded.items()
    }
