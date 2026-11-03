from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from modules.assignments import public as assignments
from modules.grading.domain.grade import Given, grade_question, keyed_questions, total
from modules.grading.repositories import grades


@dataclass(frozen=True, slots=True)
class GradeResult:
    score: Decimal
    answer_key_version: int


def grade_attempt(
    attempt_id: UUID, assignment_id: UUID, answers: Mapping[UUID, Given]
) -> GradeResult:
    """Grade an attempt as it ends, inside the caller's transaction (domain_model.md §3.7 #2):
    the caller writes the score with the end. No policy: there is no route to this, only
    delivery's ending path."""
    key = assignments.get_answer_key(assignment_id)
    paper = assignments.get_paper_content(assignment_id)
    graded = [grade_question(q, answers.get(q.id)) for q in keyed_questions(paper, key.entries)]
    grades.insert_grades(attempt_id, graded)
    return GradeResult(score=total(graded), answer_key_version=key.version)
