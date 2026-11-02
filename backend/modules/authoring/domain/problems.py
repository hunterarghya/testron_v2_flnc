"""Validation problems: allowed in a draft, but they block assigning (domain_model.md §3.4,
[C-10]). Questions are numbered 1..n across the test, as the teacher sees them."""

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from core.rich_content import is_empty
from modules.authoring.domain.drafts import QuestionDraft, SectionDraft, TestDraft
from modules.authoring.domain.effective import (
    effective_marks,
    effective_negative_marks,
    effective_time_s,
)
from modules.authoring.domain.values import QuestionType, TimingKind

MIN_OPTIONS = 2
MIN_SECTION_S = 60
MIN_QUESTION_S = 5


@dataclass(frozen=True, slots=True)
class Problem:
    code: str
    message: str
    section_id: UUID | None = None
    question_id: UUID | None = None


def find_problems(test: TestDraft) -> list[Problem]:
    """Every problem, in document order: the test, then each section and its questions."""
    if not test.questions():
        return [Problem("test_empty", "The test has no questions yet.")]
    problems: list[Problem] = []
    number = 0
    sectioned = test.settings.timing.kind is TimingKind.SECTIONED
    for index, section in enumerate(test.sections, start=1):
        if sectioned:
            problems.extend(_section_problems(section, index))
        for question in section.questions:
            number += 1
            problems.extend(_question_problems(test, section.id, question, number))
    return problems


def _section_problems(section: SectionDraft, index: int) -> list[Problem]:
    found = []
    if not section.questions:
        found.append(Problem("section_empty", f"Section {index} has no questions.", section.id))
    if section.duration_s is None or section.duration_s < MIN_SECTION_S:
        message = f"Section {index} needs a duration of at least 1 minute."
        found.append(Problem("section_no_duration", message, section.id))
    return found


def _question_problems(
    test: TestDraft, section_id: UUID, question: QuestionDraft, number: int
) -> list[Problem]:
    codes: list[tuple[str, str]] = []
    if is_empty(question.stem):
        codes.append(("stem_empty", f"Question {number} has no question text."))
    if question.type is QuestionType.NUMERICAL:
        if question.numeric_answer is None:
            codes.append(("numeric_answer_missing", f"Question {number} has no answer value."))
    else:
        codes.extend(_option_problems(question, number))
    codes.extend(_setting_problems(test, question, number))
    return [Problem(code, message, section_id, question.id) for code, message in codes]


def _option_problems(question: QuestionDraft, number: int) -> list[tuple[str, str]]:
    found = []
    if len(question.options) < MIN_OPTIONS:
        found.append(
            ("options_too_few", f"Question {number} needs at least {MIN_OPTIONS} options.")
        )
    if any(is_empty(option.content) for option in question.options):
        found.append(("option_empty", f"Question {number} has an empty option."))
    correct = sum(option.is_correct for option in question.options)
    if correct == 0:
        found.append(("no_correct_option", f"Question {number} has no correct option."))
    elif correct > 1 and question.type is QuestionType.MCQ:
        message = f"Question {number} is single-answer but has {correct} correct options."
        found.append(("mcq_multiple_correct", message))
    return found


def _setting_problems(
    test: TestDraft, question: QuestionDraft, number: int
) -> list[tuple[str, str]]:
    found = []
    seconds = effective_time_s(question, test.settings)
    if seconds is not None and seconds < MIN_QUESTION_S:
        found.append(
            ("time_invalid", f"Question {number} needs at least {MIN_QUESTION_S} seconds.")
        )
    marks = effective_marks(question, test.settings)
    negative = effective_negative_marks(question, test.settings)
    if marks <= 0 or negative < Decimal(0):
        found.append(("marks_invalid", f"Question {number} has invalid marks."))
    return found
