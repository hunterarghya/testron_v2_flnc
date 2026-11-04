"""What a result is made of (domain_model.md §6.4 "always"): section scores, the chapter and
topic breakdown for this attempt, the time taken, and its label ("Take N", §5.7)."""

from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol, cast
from uuid import UUID
from zoneinfo import ZoneInfo

# Dates are shown in India time (domain_model.md §0)
INDIA = ZoneInfo("Asia/Kolkata")


class GradeLike(Protocol):
    @property
    def section_index(self) -> int: ...
    @property
    def marks_awarded(self) -> Decimal: ...
    @property
    def max_marks(self) -> Decimal: ...
    @property
    def tag_ids(self) -> tuple[UUID, ...]: ...


@dataclass(frozen=True, slots=True)
class PartScore:
    """A section's or a tag's marks out of its maximum."""

    key: str
    score: Decimal
    max: Decimal


def section_scores(grades: Iterable[GradeLike], titles: Sequence[str | None]) -> list[PartScore]:
    """In paper order; an untitled section is "Section n"."""
    totals = _sums((g.section_index, g) for g in grades)
    return [
        PartScore(titles[i] or f"Section {i + 1}", *totals.get(i, (Decimal(0), Decimal(0))))
        for i in range(len(titles))
    ]


def tag_scores(grades: Iterable[GradeLike]) -> dict[UUID, tuple[Decimal, Decimal]]:
    """(score, max) per tag; a question with two tags counts for both."""
    return _sums((tag, g) for g in grades for tag in g.tag_ids)


def _sums[K](pairs: Iterable[tuple[K, GradeLike]]) -> dict[K, tuple[Decimal, Decimal]]:
    found: dict[K, list[Decimal]] = defaultdict(lambda: [Decimal(0), Decimal(0)])
    for key, grade in pairs:
        found[key][0] += grade.marks_awarded
        found[key][1] += grade.max_marks
    return {key: (score, top) for key, (score, top) in found.items()}


def time_taken_s(started_at: datetime, ended_at: datetime | None) -> int:
    return 0 if ended_at is None else max(0, int((ended_at - started_at).total_seconds()))


def attempt_label(title: str, started_at: datetime, take_number: int) -> str:
    """ "Cell Biology — 12 Nov 2026, 10:00 — Take 2" (domain_model.md §5.7)."""
    when = started_at.astimezone(INDIA).strftime("%d %b %Y, %H:%M").lstrip("0")
    return f"{title} — {when} — Take {take_number}"


def section_titles(paper: Mapping[str, object]) -> list[str | None]:
    sections = cast("Sequence[Mapping[str, object]]", paper["sections"])
    return [cast("str | None", section["title"]) for section in sections]
