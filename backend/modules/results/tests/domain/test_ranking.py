"""Rank and stats (domain_model.md §6.3; DM-1, E-29): a table of pools."""

from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from modules.results.domain.ranking import Placing, Scored, Stats, is_counted, placings, pool_stats

A, B, C, D, E = (uuid4() for _ in range(5))


def scored(attempt: UUID, score: str | None, *, take: int = 1, counted: bool = True) -> Scored:
    return Scored(attempt, take, None if score is None else Decimal(score), counted)


@pytest.mark.parametrize(
    ("name", "attempts", "expected"),
    [
        ("one_student", [scored(A, "10")], {A: Placing(1, 1)}),
        ("highest_first", [scored(A, "5"), scored(B, "9")], {B: Placing(1, 2), A: Placing(2, 2)}),
        (
            "ties_share_a_rank_1_2_2_4",
            [scored(A, "9"), scored(B, "7"), scored(C, "7"), scored(D, "3")],
            {A: Placing(1, 4), B: Placing(2, 4), C: Placing(2, 4), D: Placing(4, 4)},
        ),
        (
            "negative_scores_rank_too",
            [scored(A, "-2"), scored(B, "0")],
            {B: Placing(1, 2), A: Placing(2, 2)},
        ),
        (
            "disqualified_is_left_out",
            [scored(A, "9", counted=False), scored(B, "5")],
            {B: Placing(1, 1)},
        ),
        ("still_sitting_has_no_score", [scored(A, None), scored(B, "5")], {B: Placing(1, 1)}),
        (
            "each_take_ranks_on_its_own_dm1",
            [scored(A, "9"), scored(B, "5"), scored(C, "4", take=2), scored(D, "8", take=2)],
            {A: Placing(1, 2), B: Placing(2, 2), D: Placing(1, 2), C: Placing(2, 2)},
        ),
        (
            "all_equal",
            [scored(A, "6"), scored(B, "6"), scored(C, "6")],
            {A: Placing(1, 3), B: Placing(1, 3), C: Placing(1, 3)},
        ),
        ("nothing_counted", [scored(A, "6", counted=False)], {}),
    ],
)
def test_placings(name: str, attempts: list[Scored], expected: dict[UUID, Placing]) -> None:
    assert placings(attempts) == expected, name


def test_stats_over_the_first_take_by_default() -> None:
    attempts = [
        scored(A, "9"),
        scored(B, "4"),
        scored(C, "6"),
        scored(D, "1", take=2),
        scored(E, "9", counted=False),
    ]
    assert pool_stats(attempts) == Stats(
        count=3, mean=Decimal("6.33"), highest=Decimal(9), lowest=Decimal(4)
    )
    assert pool_stats(attempts, 2) == Stats(1, Decimal("1.00"), Decimal(1), Decimal(1))
    assert pool_stats(attempts, 3) is None


@pytest.mark.parametrize(
    ("ended", "graded", "disqualified", "overridden", "counted"),
    [
        (True, True, False, False, True),
        (False, False, False, False, False),
        (True, True, True, False, False),
        # E-29: an overridden disqualification joins the pool
        (True, True, True, True, True),
    ],
)
def test_is_counted(
    ended: bool, graded: bool, disqualified: bool, overridden: bool, counted: bool
) -> None:
    assert (
        is_counted(ended=ended, graded=graded, disqualified=disqualified, overridden=overridden)
        is counted
    )
