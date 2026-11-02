"""Marking one response (domain_model.md §6.1): pure, table-tested.

`M` = the question's effective marks, `N` = its effective negative marks (stored >= 0).
MSQ gets proportional partial marks, as NTA does: picking some of the correct options and no
wrong one earns M * picked / correct; any wrong pick takes the full penalty -N (0 when there
is no negative marking). Every score is rounded once, to 0.01 (half up).
"""

from collections.abc import Set
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from enum import StrEnum
from uuid import UUID

CENT = Decimal("0.01")


class Outcome(StrEnum):
    CORRECT = "CORRECT"
    PARTIAL = "PARTIAL"
    INCORRECT = "INCORRECT"
    UNANSWERED = "UNANSWERED"


@dataclass(frozen=True, slots=True)
class Mark:
    outcome: Outcome
    marks: Decimal


def _mark(outcome: Outcome, marks: Decimal) -> Mark:
    return Mark(outcome, marks.quantize(CENT, rounding=ROUND_HALF_UP))


def mark_mcq(selected: Set[UUID], correct: Set[UUID], *, marks: Decimal, negative: Decimal) -> Mark:
    if not selected:
        return _mark(Outcome.UNANSWERED, Decimal(0))
    if selected == correct:
        return _mark(Outcome.CORRECT, marks)
    return _mark(Outcome.INCORRECT, -negative)


def mark_msq(selected: Set[UUID], correct: Set[UUID], *, marks: Decimal, negative: Decimal) -> Mark:
    if not selected:
        return _mark(Outcome.UNANSWERED, Decimal(0))
    if not selected <= correct:
        # Any wrong option: the full penalty, however many correct ones were picked too
        return _mark(Outcome.INCORRECT, -negative)
    if selected == correct:
        return _mark(Outcome.CORRECT, marks)
    return _mark(Outcome.PARTIAL, marks * len(selected) / len(correct))


def mark_numerical(
    value: Decimal | None, answer: Decimal, *, tolerance: Decimal, marks: Decimal, negative: Decimal
) -> Mark:
    if value is None:
        return _mark(Outcome.UNANSWERED, Decimal(0))
    if abs(value - answer) <= tolerance:
        return _mark(Outcome.CORRECT, marks)
    return _mark(Outcome.INCORRECT, -negative)
