"""Validation problems (domain_model.md §3.4, [C-10]): one row per rule."""

from decimal import Decimal

import pytest

from core.rich_content import EMPTY_DOC
from modules.authoring.domain.drafts import QuestionDraft, Timing
from modules.authoring.domain.problems import find_problems
from modules.authoring.domain.values import QuestionType, TimingKind
from modules.authoring.tests.domain.drafts import draft_of, mcq, option, section

SECTIONED = Timing(TimingKind.SECTIONED)
PER_QUESTION = Timing(TimingKind.PER_QUESTION, default_question_s=30)


def codes_of(question: QuestionDraft, timing: Timing | None = None) -> list[str]:
    return [problem.code for problem in find_problems(draft_of(section(question), timing=timing))]


def test_a_complete_question_has_no_problems() -> None:
    assert codes_of(mcq()) == []


def test_an_empty_test_has_one_problem() -> None:
    assert [p.code for p in find_problems(draft_of(section()))] == ["test_empty"]


@pytest.mark.parametrize(
    ("question", "codes"),
    [
        (mcq(stem=EMPTY_DOC), ["stem_empty"]),
        (mcq(options=(option(correct=True),)), ["options_too_few"]),
        (mcq(options=(option(correct=True), option(""))), ["option_empty"]),
        (mcq(options=(option(), option())), ["no_correct_option"]),
        (mcq(options=(option(correct=True), option(correct=True))), ["mcq_multiple_correct"]),
        (mcq(type=QuestionType.MSQ, options=(option(correct=True), option(correct=True))), []),
        (mcq(type=QuestionType.NUMERICAL, options=()), ["numeric_answer_missing"]),
        (mcq(type=QuestionType.NUMERICAL, options=(), numeric_answer=Decimal("6.02")), []),
        (mcq(marks_override=Decimal(0)), ["marks_invalid"]),
        (mcq(negative_marks_override=Decimal(-1)), ["marks_invalid"]),
        (mcq(options=()), ["options_too_few", "no_correct_option"]),
    ],
)
def test_each_question_rule(question: QuestionDraft, codes: list[str]) -> None:
    assert codes_of(question) == codes


def test_question_time_counts_only_per_question() -> None:
    assert codes_of(mcq(time_override_s=3), PER_QUESTION) == ["time_invalid"]
    assert codes_of(mcq(time_override_s=3)) == []


def test_sections_need_questions_and_a_duration_only_when_sectioned() -> None:
    test = draft_of(section(mcq(), duration_s=600), section(duration_s=30), timing=SECTIONED)

    problems = find_problems(test)

    assert [(p.code, p.section_id) for p in problems] == [
        ("section_empty", test.sections[1].id),
        ("section_no_duration", test.sections[1].id),
    ]
    assert problems[0].message == "Section 2 has no questions."


def test_questions_are_numbered_across_sections() -> None:
    broken = mcq(stem=EMPTY_DOC)
    test = draft_of(
        section(mcq(), duration_s=600), section(mcq(), broken, duration_s=600), timing=SECTIONED
    )

    [problem] = find_problems(test)

    assert (problem.message, problem.question_id, problem.section_id) == (
        "Question 3 has no question text.",
        broken.id,
        test.sections[1].id,
    )
