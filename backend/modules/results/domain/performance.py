"""Tag performance (domain_model.md §6.5, I-1, I-2): for each chapter or topic, over a set of
attempts' grades. Tags are counted by id, so a renamed tag keeps its history and a deleted
one simply drops out (the caller finds no name for it).

    score_pct    = sum of marks / sum of maximum marks x 100   (can be negative)
    accuracy_pct = (correct + half of partly correct) / answered x 100
    attempted    = answered / questions x 100
    order        : weakest first, by score_pct
"""

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from typing import Protocol
from uuid import UUID

ONE_PLACE = Decimal("0.1")
HUNDRED = Decimal(100)
HALF = Decimal("0.5")


class GradedQuestion(Protocol):
    @property
    def outcome(self) -> object: ...
    @property
    def marks_awarded(self) -> Decimal: ...
    @property
    def max_marks(self) -> Decimal: ...
    @property
    def tag_ids(self) -> tuple[UUID, ...]: ...


@dataclass(frozen=True, slots=True)
class TagPerformance:
    tag_id: UUID
    score_pct: Decimal
    accuracy_pct: Decimal
    attempted_pct: Decimal
    questions: int


@dataclass(slots=True)
class _Tally:
    marks: Decimal = Decimal(0)
    top: Decimal = Decimal(0)
    questions: int = 0
    answered: int = 0
    right: Decimal = field(default_factory=lambda: Decimal(0))


def percent(part: Decimal, whole: Decimal) -> Decimal:
    """One decimal place, half up; 0 when there is nothing to divide by."""
    if whole == 0:
        return Decimal("0.0")
    return (part / whole * HUNDRED).quantize(ONE_PLACE, rounding=ROUND_HALF_UP)


def tag_performance(grades: Iterable[GradedQuestion]) -> list[TagPerformance]:
    tallies: dict[UUID, _Tally] = defaultdict(_Tally)
    for grade in grades:
        outcome = str(getattr(grade.outcome, "value", grade.outcome))
        for tag in grade.tag_ids:
            tally = tallies[tag]
            tally.marks += grade.marks_awarded
            tally.top += grade.max_marks
            tally.questions += 1
            if outcome != "UNANSWERED":
                tally.answered += 1
                tally.right += {"CORRECT": Decimal(1), "PARTIAL": HALF}.get(outcome, Decimal(0))
    found = [
        TagPerformance(
            tag_id=tag,
            score_pct=percent(t.marks, t.top),
            accuracy_pct=percent(t.right, Decimal(t.answered)),
            attempted_pct=percent(Decimal(t.answered), Decimal(t.questions)),
            questions=t.questions,
        )
        for tag, t in tallies.items()
    ]
    return sorted(found, key=lambda p: (p.score_pct, str(p.tag_id)))
