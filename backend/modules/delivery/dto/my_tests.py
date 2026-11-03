"""What a student sees before starting (api_contract.md §3.4 `MyTestCard`, `GateState`).
No answers, marks awarded or scores: these types have no such fields (rule 1)."""

from datetime import datetime
from decimal import Decimal
from typing import Literal, Self
from uuid import UUID

from ninja import Schema
from pydantic import ConfigDict

from modules.assignments import public as assignments
from modules.delivery.domain.gate import CardState, GateStatus
from modules.delivery.services.gate_views import GateView
from modules.delivery.services.queries.list_my_tests import MyTestCard, MyTests


class _Out(Schema):
    model_config = ConfigDict(extra="forbid")


class MyTestCardOut(_Out):
    assignment_id: UUID
    title: str
    question_count: int
    total_duration_s: int
    stage_count: int
    timing_kind: str
    locked: bool
    state: CardState
    starts_at: datetime | None
    closes_at: datetime | None
    attempt_id: UUID | None

    @classmethod
    def from_card(cls, card: MyTestCard) -> Self:
        mine, paper = card.view.assignment, card.view.assignment.paper
        return cls(
            assignment_id=mine.assignment_id,
            title=mine.title,
            question_count=paper.question_count,
            total_duration_s=paper.total_duration_s,
            stage_count=len(paper.stages),
            timing_kind=paper.timing_kind,
            locked=mine.locked,
            state=card.state,
            starts_at=mine.entry.opens_at,
            closes_at=mine.window.closes_at,
            attempt_id=card.view.sittings.in_progress_attempt_id,
        )


class MyTestsOut(_Out):
    available: list[MyTestCardOut]
    upcoming: list[MyTestCardOut]
    server_now: datetime

    @classmethod
    def from_tests(cls, tests: MyTests) -> Self:
        return cls(
            available=[MyTestCardOut.from_card(card) for card in tests.available],
            upcoming=[MyTestCardOut.from_card(card) for card in tests.upcoming],
            server_now=tests.server_now,
        )


class StageOut(_Out):
    title: str | None
    duration_s: int


class MarkingOut(_Out):
    marks: Decimal
    negative_marks: Decimal


class RulesOut(_Out):
    question_count: int
    total_marks: Decimal
    total_duration_s: int
    timing_kind: str
    stages: list[StageOut]
    marking: MarkingOut | Literal["MIXED"]
    allow_return: bool
    max_warnings: int
    action: str

    @classmethod
    def from_assignment(cls, mine: assignments.StudentAssignment) -> Self:
        paper = mine.paper
        marking = paper.marking
        return cls(
            question_count=paper.question_count,
            total_marks=paper.total_marks,
            total_duration_s=paper.total_duration_s,
            timing_kind=paper.timing_kind,
            stages=[StageOut(title=s.title, duration_s=s.duration_s) for s in paper.stages],
            marking="MIXED"
            if marking is None
            else MarkingOut(marks=marking[0], negative_marks=marking[1]),
            allow_return=paper.allow_return,
            max_warnings=mine.integrity.max_warnings,
            action=mine.integrity.action,
        )


class GateStateOut(_Out):
    assignment_id: UUID
    title: str
    rules: RulesOut
    state: GateStatus
    requires_password: bool
    opens_at: datetime | None
    # Entry is possible until this instant (late entry, a deadline's close)
    late_entry_until: datetime | None
    time_remaining_if_started_now_s: int | None
    attempt_id: UUID | None
    next_take_number: int
    server_now: datetime

    @classmethod
    def from_view(cls, view: GateView) -> Self:
        mine = view.assignment
        return cls(
            assignment_id=mine.assignment_id,
            title=mine.title,
            rules=RulesOut.from_assignment(mine),
            state=view.gate.status,
            requires_password=mine.has_password,
            opens_at=mine.entry.opens_at,
            late_entry_until=mine.entry.closes_at,
            time_remaining_if_started_now_s=view.time_left_if_started_now_s,
            attempt_id=view.sittings.in_progress_attempt_id,
            next_take_number=view.sittings.used + 1,
            server_now=view.server_now,
        )
