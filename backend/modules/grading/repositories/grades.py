from collections.abc import Mapping, Sequence
from uuid import UUID

from modules.grading.domain.grade import QuestionGrade
from modules.grading.models import Grade


def insert_grades(attempt_id: UUID, grades: Sequence[QuestionGrade]) -> None:
    insert_many({attempt_id: grades})


def insert_many(by_attempt: Mapping[UUID, Sequence[QuestionGrade]]) -> None:
    """One statement for every attempt given."""
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
            for attempt_id, grades in by_attempt.items()
            for g in grades
        ]
    )


def delete_grades(attempt_ids: Sequence[UUID]) -> None:
    Grade.objects.filter(attempt_id__in=attempt_ids).delete()
