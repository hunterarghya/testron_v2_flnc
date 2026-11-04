"""The teacher's results inbox and dashboard (T-13, T-01; api_contract.md §2.2, §2.7)."""

from datetime import datetime
from decimal import Decimal
from typing import Self
from uuid import UUID

from ninja import Schema
from pydantic import ConfigDict

from modules.assignments import public as assignments
from modules.results.services.queries.get_dashboard import Dashboard
from modules.results.services.queries.list_results_inbox import InboxRow


class _Out(Schema):
    model_config = ConfigDict(extra="forbid")


class AssignmentBriefOut(_Out):
    assignment_id: UUID
    title: str
    state: str
    publication_state: str
    ends_at: datetime | None
    audience: int
    ended: int
    in_progress: int
    starts_at: datetime | None

    @classmethod
    def from_row(cls, row: assignments.AssignmentRow) -> Self:
        window = row.record.settings.window
        return cls(
            assignment_id=row.record.id,
            title=row.record.settings.title,
            state=row.state.value,
            publication_state=row.publication_state.value,
            ends_at=row.ends_at,
            audience=row.audience_count,
            ended=row.progress.ended,
            in_progress=row.progress.in_progress,
            starts_at=window.starts_at or window.opens_at or window.planned_at,
        )


class ResultsInboxRowOut(AssignmentBriefOut):
    average_pct: Decimal | None
    flagged: int

    @classmethod
    def from_inbox(cls, row: InboxRow) -> Self:
        brief = AssignmentBriefOut.from_row(row.row).model_dump()
        return cls(**brief, average_pct=row.average_pct, flagged=row.flagged)


class DashboardOut(_Out):
    live: list[AssignmentBriefOut]
    upcoming: list[AssignmentBriefOut]
    recent: list[ResultsInboxRowOut]
    pending_students: int
    results_to_publish: int

    @classmethod
    def from_dashboard(cls, board: Dashboard) -> Self:
        return cls(
            live=[AssignmentBriefOut.from_row(r) for r in board.live],
            upcoming=[AssignmentBriefOut.from_row(r) for r in board.upcoming],
            recent=[ResultsInboxRowOut.from_inbox(r) for r in board.recent],
            pending_students=board.pending_students,
            results_to_publish=board.results_to_publish,
        )
