"""A performance report (P-10, T-15, T-17; domain_model.md §6.5) from a set of attempts:
chapters and topics weakest first, and how the score went over time. Which attempts count is
the caller's: a student's own visible results, or every counted attempt for the teacher."""

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from modules.assignments import public as assignments
from modules.delivery import public as delivery
from modules.grading import public as grading
from modules.results.domain.breakdown import attempt_label
from modules.results.domain.performance import TagPerformance, percent, tag_performance
from modules.tagging import public as tagging

ZERO = Decimal(0)


@dataclass(frozen=True, slots=True)
class TagReport:
    tag: tagging.TagRef
    performance: TagPerformance


@dataclass(frozen=True, slots=True)
class TrendPoint:
    # The attempt; for a group, the assignment
    key: UUID
    label: str
    at: datetime
    score_pct: Decimal


@dataclass(frozen=True, slots=True)
class PerformanceView:
    based_on_attempts: int
    chapters: list[TagReport]
    topics: list[TagReport]
    trend: list[TrendPoint]


def performance_of(attempts: Sequence[delivery.AttemptRow]) -> PerformanceView:
    """One student's report: the tags, and each attempt's score % oldest first."""
    titles = assignments.list_assignment_titles({a.assignment_id for a in attempts})
    trend = [
        TrendPoint(
            key=a.id,
            label=attempt_label(titles.get(a.assignment_id, ""), a.started_at, a.take_number),
            at=_ended(a),
            score_pct=percent(a.score or ZERO, a.max_score),
        )
        for a in attempts
    ]
    return _report(attempts, trend)


def group_performance_of(attempts: Sequence[delivery.AttemptRow]) -> PerformanceView:
    """A group's report: the tags, and each test's score % over everyone who sat it."""
    by_test: dict[UUID, list[delivery.AttemptRow]] = defaultdict(list)
    for attempt in attempts:
        by_test[attempt.assignment_id].append(attempt)
    titles = assignments.list_assignment_titles(list(by_test))
    trend = [
        TrendPoint(
            key=test,
            label=titles.get(test, ""),
            at=max(_ended(a) for a in rows),
            score_pct=percent(
                sum((a.score or ZERO for a in rows), ZERO), sum((a.max_score for a in rows), ZERO)
            ),
        )
        for test, rows in by_test.items()
    ]
    return _report(attempts, trend)


def _report(attempts: Sequence[delivery.AttemptRow], trend: list[TrendPoint]) -> PerformanceView:
    """Every question of these attempts, by tag id; a deleted tag drops out [DM §3.3]."""
    grades = grading.grades_of([a.id for a in attempts])
    found = tag_performance(g for rows in grades.values() for g in rows)
    names = tagging.tags_by_ids([p.tag_id for p in found])
    reports = [TagReport(names[p.tag_id], p) for p in found if p.tag_id in names]
    return PerformanceView(
        based_on_attempts=len(attempts),
        chapters=[r for r in reports if r.tag.kind is tagging.TagKind.CHAPTER],
        topics=[r for r in reports if r.tag.kind is tagging.TagKind.TOPIC],
        trend=sorted(trend, key=lambda p: p.at),
    )


def _ended(attempt: delivery.AttemptRow) -> datetime:
    # Counted attempts have always ended; the start is only a type-safe fallback
    return attempt.ended_at or attempt.started_at
