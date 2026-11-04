"""T-11's Questions tab: how each question went across the counted attempts, and the wrong
option chosen most often (a hint that the key, or the question, may be wrong: D-05)."""

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import cast
from uuid import UUID

Json = Mapping[str, object]


@dataclass(frozen=True, slots=True)
class QuestionStat:
    question_id: UUID
    answered: int
    correct: int
    partial: int
    # The wrong option picked most, and by how many; None for numerical or when none was
    top_wrong_option: UUID | None
    top_wrong_count: int


def question_stats(
    outcomes: Iterable[tuple[UUID, str]],
    picks: Iterable[tuple[UUID, Iterable[UUID]]],
    key_entries: Json,
) -> dict[UUID, QuestionStat]:
    """`outcomes`: (question, outcome) per graded answer; `picks`: (question, options picked)
    per stored choice answer."""
    tally: dict[UUID, Counter[str]] = {}
    for question_id, outcome in outcomes:
        tally.setdefault(question_id, Counter())[outcome] += 1
    wrong: dict[UUID, Counter[UUID]] = {}
    for question_id, options in picks:
        correct = _correct(key_entries, question_id)
        wrong.setdefault(question_id, Counter()).update(o for o in options if o not in correct)
    return {q: _stat(q, counts, wrong.get(q, Counter())) for q, counts in tally.items()}


def _stat(question_id: UUID, counts: Counter[str], wrong: Counter[UUID]) -> QuestionStat:
    top = wrong.most_common(1)
    return QuestionStat(
        question_id=question_id,
        answered=sum(counts.values()) - counts["UNANSWERED"],
        correct=counts["CORRECT"],
        partial=counts["PARTIAL"],
        top_wrong_option=top[0][0] if top else None,
        top_wrong_count=top[0][1] if top else 0,
    )


def _correct(key_entries: Json, question_id: UUID) -> set[UUID]:
    entry = cast("Json", key_entries.get(str(question_id), {}))
    return {UUID(o) for o in cast("list[str]", entry.get("correct_option_ids", []))}
