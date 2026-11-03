from collections.abc import Sequence
from uuid import UUID

from modules.grading.domain.grade import QuestionGrade
from modules.grading.models import Grade


def insert_grades(attempt_id: UUID, grades: Sequence[QuestionGrade]) -> None:
    """One statement for the whole attempt."""
    Grade.objects.bulk_create(
        [
            Grade(
                attempt_id=attempt_id,
                question_id=g.question_id,
                section_index=g.section_index,
                outcome=g.outcome.value,
                marks_awarded=g.marks_awarded,
                max_marks=g.max_marks,
                tag_ids=list(g.tag_ids),
            )
            for g in grades
        ]
    )
