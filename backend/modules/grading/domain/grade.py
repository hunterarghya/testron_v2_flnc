"""Grading a whole attempt (domain_model.md §3.7): one grade per paper question, unanswered
ones included, so a timed-out attempt is scored like any other [V1 F-10]."""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import cast
from uuid import UUID

from modules.grading.domain.marking import Mark, Outcome, mark_mcq, mark_msq, mark_numerical

Json = Mapping[str, object]
# What the student gave: the options picked, a numerical value, or nothing
Given = frozenset[UUID] | Decimal | None


@dataclass(frozen=True, slots=True)
class KeyedQuestion:
    """A paper question with its key entry."""

    id: UUID
    type: str
    section_index: int
    marks: Decimal
    negative_marks: Decimal
    tag_ids: tuple[UUID, ...]
    correct_option_ids: frozenset[UUID] = frozenset()
    answer: Decimal | None = None
    tolerance: Decimal = Decimal(0)


@dataclass(frozen=True, slots=True)
class QuestionGrade:
    question_id: UUID
    section_index: int
    outcome: Outcome
    marks_awarded: Decimal
    max_marks: Decimal
    tag_ids: tuple[UUID, ...]


def keyed_questions(paper: Json, entries: Json) -> list[KeyedQuestion]:
    sections = cast("Sequence[Json]", paper["sections"])
    return [
        _keyed(index, question, cast("Json", entries[str(question["id"])]))
        for index, section in enumerate(sections)
        for question in cast("Sequence[Json]", section["questions"])
    ]


def _keyed(section_index: int, question: Json, entry: Json) -> KeyedQuestion:
    numerical = entry["type"] == "NUMERICAL"
    correct = cast("list[str]", entry.get("correct_option_ids", []))
    return KeyedQuestion(
        id=UUID(str(question["id"])),
        type=str(question["type"]),
        section_index=section_index,
        marks=Decimal(str(question["marks"])),
        negative_marks=Decimal(str(question["negative_marks"])),
        tag_ids=tuple(UUID(t) for t in cast("list[str]", question["tag_ids"])),
        correct_option_ids=frozenset(UUID(o) for o in correct),
        answer=Decimal(str(entry["answer"])) if numerical else None,
        tolerance=Decimal(str(entry.get("tolerance", "0"))),
    )


def grade_question(question: KeyedQuestion, given: Given) -> QuestionGrade:
    mark = _mark(question, given)
    return QuestionGrade(
        question_id=question.id,
        section_index=question.section_index,
        outcome=mark.outcome,
        marks_awarded=mark.marks,
        max_marks=question.marks,
        tag_ids=question.tag_ids,
    )


def _mark(question: KeyedQuestion, given: Given) -> Mark:
    marks, negative = question.marks, question.negative_marks
    if question.answer is not None:
        value = given if isinstance(given, Decimal) else None
        return mark_numerical(
            value, question.answer, tolerance=question.tolerance, marks=marks, negative=negative
        )
    picked = given if isinstance(given, frozenset) else frozenset()
    mark = mark_msq if question.type == "MSQ" else mark_mcq
    return mark(picked, question.correct_option_ids, marks=marks, negative=negative)


def total(grades: Iterable[QuestionGrade]) -> Decimal:
    return sum((grade.marks_awarded for grade in grades), Decimal("0.00"))
