"""Grading a whole paper (domain_model.md §3.7 #1): one grade per question, unanswered ones
included, from the paper and its key."""

from decimal import Decimal
from uuid import UUID, uuid4

from modules.grading.domain.grade import grade_question, keyed_questions, total
from modules.grading.domain.marking import Outcome

A, B, C = uuid4(), uuid4(), uuid4()
TAG = uuid4()
MCQ, MSQ, NUM = uuid4(), uuid4(), uuid4()


def _q(qid: UUID, kind: str, marks: str = "4.00", negative: str = "1.00") -> dict[str, object]:
    return {
        "id": str(qid),
        "type": kind,
        "marks": marks,
        "negative_marks": negative,
        "tag_ids": [str(TAG)],
    }


PAPER = {
    "sections": [
        {"questions": [_q(MCQ, "MCQ"), _q(MSQ, "MSQ")]},
        {"questions": [_q(NUM, "NUMERICAL", negative="0.00")]},
    ]
}
KEY = {
    str(MCQ): {"type": "MCQ", "correct_option_ids": [str(A)]},
    str(MSQ): {"type": "MSQ", "correct_option_ids": [str(A), str(B)]},
    str(NUM): {"type": "NUMERICAL", "answer": "46", "tolerance": "0.5"},
}


def test_every_question_is_graded_with_its_section_and_tags() -> None:
    questions = keyed_questions(PAPER, KEY)
    grades = [grade_question(q, None) for q in questions]
    assert [(g.question_id, g.section_index, g.outcome) for g in grades] == [
        (MCQ, 0, Outcome.UNANSWERED),
        (MSQ, 0, Outcome.UNANSWERED),
        (NUM, 1, Outcome.UNANSWERED),
    ]
    assert all(g.tag_ids == (TAG,) and g.max_marks == Decimal(4) for g in grades)
    assert total(grades) == Decimal("0.00")


def test_answers_are_marked_by_type_and_summed() -> None:
    mcq, msq, num = keyed_questions(PAPER, KEY)
    grades = [
        grade_question(mcq, frozenset({C})),
        grade_question(msq, frozenset({A})),
        grade_question(num, Decimal("46.4")),
    ]
    assert [(g.outcome, g.marks_awarded) for g in grades] == [
        (Outcome.INCORRECT, Decimal("-1.00")),
        (Outcome.PARTIAL, Decimal("2.00")),
        (Outcome.CORRECT, Decimal("4.00")),
    ]
    assert total(grades) == Decimal("5.00")


def test_an_answer_of_the_wrong_kind_counts_as_unanswered() -> None:
    mcq, _, num = keyed_questions(PAPER, KEY)
    assert grade_question(mcq, Decimal(1)).outcome is Outcome.UNANSWERED
    assert grade_question(num, frozenset({A})).outcome is Outcome.UNANSWERED
