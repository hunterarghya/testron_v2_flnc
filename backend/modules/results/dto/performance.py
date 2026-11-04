"""Performance reports (api_contract.md §3.5 `Performance`; P-10, T-15, T-17)."""

from datetime import datetime
from decimal import Decimal
from typing import Self
from uuid import UUID

from ninja import Schema
from pydantic import ConfigDict

from modules.results.dto.gradebook import TagRefOut
from modules.results.services.performance_view import PerformanceView, TagReport
from modules.results.services.queries.get_group_performance import GroupPerformanceView


class _Out(Schema):
    model_config = ConfigDict(extra="forbid")


class TagPerformanceOut(_Out):
    tag: TagRefOut
    score_pct: Decimal
    accuracy_pct: Decimal
    attempted_pct: Decimal
    questions: int

    @classmethod
    def from_report(cls, report: TagReport) -> Self:
        tag, found = report.tag, report.performance
        return cls(
            tag=TagRefOut(id=tag.id, name=tag.name, kind=tag.kind.value),
            score_pct=found.score_pct,
            accuracy_pct=found.accuracy_pct,
            attempted_pct=found.attempted_pct,
            questions=found.questions,
        )


class TrendPointOut(_Out):
    attempt_id: UUID
    label: str
    ended_at: datetime
    score_pct: Decimal


class PerformanceOut(_Out):
    based_on_attempts: int
    chapters: list[TagPerformanceOut]
    topics: list[TagPerformanceOut]
    trend: list[TrendPointOut]

    @classmethod
    def from_view(cls, view: PerformanceView) -> Self:
        return cls(
            based_on_attempts=view.based_on_attempts,
            chapters=[TagPerformanceOut.from_report(r) for r in view.chapters],
            topics=[TagPerformanceOut.from_report(r) for r in view.topics],
            trend=[
                TrendPointOut(attempt_id=p.key, label=p.label, ended_at=p.at, score_pct=p.score_pct)
                for p in view.trend
            ],
        )


class GroupTrendPointOut(_Out):
    assignment_id: UUID
    label: str
    ended_at: datetime
    # Everyone's marks over everyone's maximum, for this test
    score_pct: Decimal


class GroupPerformanceOut(_Out):
    group_name: str
    students: int
    based_on_attempts: int
    chapters: list[TagPerformanceOut]
    topics: list[TagPerformanceOut]
    trend: list[GroupTrendPointOut]

    @classmethod
    def from_view(cls, view: GroupPerformanceView) -> Self:
        report = view.report
        return cls(
            group_name=view.group_name,
            students=view.students,
            based_on_attempts=report.based_on_attempts,
            chapters=[TagPerformanceOut.from_report(r) for r in report.chapters],
            topics=[TagPerformanceOut.from_report(r) for r in report.topics],
            trend=[
                GroupTrendPointOut(
                    assignment_id=p.key, label=p.label, ended_at=p.at, score_pct=p.score_pct
                )
                for p in report.trend
            ],
        )
