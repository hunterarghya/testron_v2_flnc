"""What a student is told about a paper before starting (P-01 card, P-02 rules), read from
the frozen paper (database_schema.md §4.2). Never anything about answers."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import cast

Json = Mapping[str, object]


@dataclass(frozen=True, slots=True)
class Stage:
    title: str | None
    duration_s: int


@dataclass(frozen=True, slots=True)
class PaperSummary:
    question_count: int
    total_marks: Decimal
    total_duration_s: int
    timing_kind: str
    allow_return: bool
    stages: tuple[Stage, ...]
    # (marks, negative marks) when every question has the same, else None ("MIXED")
    marking: tuple[Decimal, Decimal] | None


def paper_summary(paper: Json) -> PaperSummary:
    timing = cast("Json", paper["timing"])
    kind = str(timing["kind"])
    sections = cast("Sequence[Json]", paper["sections"])
    questions = [q for s in sections for q in cast("Sequence[Json]", s["questions"])]
    marking = [(Decimal(str(q["marks"])), Decimal(str(q["negative_marks"]))) for q in questions]
    total_s = cast("int", timing["total_duration_s"])
    return PaperSummary(
        question_count=len(questions),
        total_marks=sum((marks for marks, _ in marking), Decimal(0)),
        total_duration_s=total_s,
        timing_kind=kind,
        # Rapid fire never goes back (domain_model.md §5.1)
        allow_return=bool(timing["allow_return"]) and kind != "PER_QUESTION",
        stages=_stages(kind, total_s, sections, questions),
        marking=marking[0] if len(set(marking)) == 1 else None,
    )


def _stages(
    kind: str, total_s: int, sections: Sequence[Json], questions: Sequence[Json]
) -> tuple[Stage, ...]:
    """One stage for TOTAL, one per section, or one per question (domain_model.md §5.1)."""
    if kind == "SECTIONED":
        return tuple(
            Stage(cast("str | None", s["title"]), cast("int", s["duration_s"])) for s in sections
        )
    if kind == "PER_QUESTION":
        return tuple(Stage(None, cast("int", q["time_s"])) for q in questions)
    return (Stage(None, total_s),)
