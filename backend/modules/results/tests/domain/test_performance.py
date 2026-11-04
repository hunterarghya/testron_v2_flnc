"""The performance table (domain_model.md §6.5; build_phases.md Phase 7 required tests)."""

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from modules.results.domain.performance import TagPerformance, percent, tag_performance

CELL, GENE = uuid4(), uuid4()


@dataclass(frozen=True)
class G:
    outcome: str
    marks_awarded: Decimal
    max_marks: Decimal = Decimal(4)
    tag_ids: tuple[UUID, ...] = (CELL,)


def one(grades: list[G]) -> TagPerformance:
    found = tag_performance(grades)
    assert len(found) == 1
    return found[0]


@pytest.mark.parametrize(
    ("name", "grades", "score", "accuracy", "attempted"),
    [
        (
            "all_correct",
            [G("CORRECT", Decimal(4)), G("CORRECT", Decimal(4))],
            "100.0",
            "100.0",
            "100.0",
        ),
        (
            "one_wrong_one_right",
            [G("CORRECT", Decimal(4)), G("INCORRECT", Decimal(-1))],
            "37.5",
            "50.0",
            "100.0",
        ),
        (
            "partial_counts_half",
            [G("PARTIAL", Decimal(2)), G("CORRECT", Decimal(4))],
            "75.0",
            "75.0",
            "100.0",
        ),
        (
            "unanswered_lowers_attempted_not_accuracy",
            [G("CORRECT", Decimal(4)), G("UNANSWERED", Decimal(0))],
            "50.0",
            "100.0",
            "50.0",
        ),
        ("nothing_answered", [G("UNANSWERED", Decimal(0))], "0.0", "0.0", "0.0"),
        (
            "negative_score_shown_as_is",
            [G("INCORRECT", Decimal(-1)), G("INCORRECT", Decimal(-1))],
            "-25.0",
            "0.0",
            "100.0",
        ),
        ("thirds_round_half_up", [G("CORRECT", Decimal(1), Decimal(3))], "33.3", "100.0", "100.0"),
    ],
)
def test_one_tag(name: str, grades: list[G], score: str, accuracy: str, attempted: str) -> None:
    found = one(grades)
    assert (found.score_pct, found.accuracy_pct, found.attempted_pct) == (
        Decimal(score),
        Decimal(accuracy),
        Decimal(attempted),
    ), name


def test_a_question_counts_for_each_tag_and_the_weakest_comes_first() -> None:
    found = tag_performance(
        [
            G("CORRECT", Decimal(4), tag_ids=(CELL, GENE)),
            G("INCORRECT", Decimal(-1), tag_ids=(GENE,)),
        ]
    )
    assert [(p.tag_id, p.score_pct, p.questions) for p in found] == [
        (GENE, Decimal("37.5"), 2),
        (CELL, Decimal("100.0"), 1),
    ]


def test_untagged_questions_count_nowhere_and_nothing_gives_nothing() -> None:
    assert tag_performance([G("CORRECT", Decimal(4), tag_ids=())]) == []
    assert tag_performance([]) == []
    assert percent(Decimal(1), Decimal(0)) == Decimal("0.0")
