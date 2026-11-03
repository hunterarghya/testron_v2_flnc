"""The teacher's live monitor and its actions (api_contract.md §2.6, §3.3 `Monitor`). The
contract names `AttemptSummary` and `IntegrityEventView` without defining them; their
fields are below (ADR-077)."""

from datetime import datetime
from decimal import Decimal
from typing import Self
from uuid import UUID

from ninja import Schema
from pydantic import ConfigDict, Field

from modules.delivery.domain.monitor import MonitorFilter, MonitorStatus
from modules.delivery.domain.values import AttemptStatus, EndReason, IntegrityKind
from modules.delivery.repositories.attempt_rows import AttemptRow
from modules.delivery.repositories.integrity_events import EventRow
from modules.delivery.services.commands.end_for_everyone import EndedForEveryone
from modules.delivery.services.queries.get_monitor import Monitor, MonitorRow


class _Out(Schema):
    model_config = ConfigDict(extra="forbid")


class MonitorFilterIn(Schema):
    model_config = ConfigDict(extra="forbid")
    filter: MonitorFilter = MonitorFilter.ALL


class MonitorRowOut(_Out):
    student_id: UUID
    name: str
    take_number: int | None
    attempt_id: UUID | None
    status: MonitorStatus
    current_stage_index: int | None
    answered: int
    total_questions: int
    warning_count: int
    last_seen_at: datetime | None
    deadline_at: datetime | None

    @classmethod
    def from_row(cls, row: MonitorRow, total: int) -> Self:
        attempt = row.attempt
        running = row.status is MonitorStatus.IN_PROGRESS
        return cls(
            student_id=row.student_id,
            name=row.name,
            take_number=attempt.take_number if attempt else None,
            attempt_id=attempt.id if attempt else None,
            status=row.status,
            current_stage_index=attempt.current_stage_index if attempt and running else None,
            answered=row.answered,
            total_questions=total,
            warning_count=attempt.warning_count if attempt else 0,
            last_seen_at=attempt.last_seen_at if attempt else None,
            deadline_at=row.deadline_at,
        )


class MonitorOut(_Out):
    title: str
    rows: list[MonitorRowOut]
    summary: dict[MonitorStatus, int]
    ends_at: datetime | None
    server_now: datetime

    @classmethod
    def from_monitor(cls, monitor: Monitor) -> Self:
        return cls(
            title=monitor.title,
            rows=[MonitorRowOut.from_row(row, monitor.total_questions) for row in monitor.rows],
            summary=monitor.summary,
            ends_at=monitor.ends_at,
            server_now=monitor.server_now,
        )


class AttemptSummaryOut(_Out):
    """The teacher's view of one sitting (force submit; overriding later in Phase 6)."""

    attempt_id: UUID
    student_id: UUID
    take_number: int
    status: AttemptStatus
    end_reason: EndReason | None
    ended_at: datetime | None
    score: Decimal | None
    max_score: Decimal

    @classmethod
    def from_row(cls, row: AttemptRow) -> Self:
        return cls(
            attempt_id=row.id,
            student_id=row.student_id,
            take_number=row.take_number,
            status=row.status,
            end_reason=row.end_reason,
            ended_at=row.ended_at,
            score=row.score,
            max_score=row.max_score,
        )


class IntegrityEventOut(_Out):
    kind: IntegrityKind
    left_at: datetime
    returned_at: datetime | None
    counted: bool

    @classmethod
    def from_row(cls, row: EventRow) -> Self:
        return cls(
            kind=row.kind, left_at=row.left_at, returned_at=row.returned_at, counted=row.counted
        )


class EndForEveryoneIn(Schema):
    model_config = ConfigDict(extra="forbid")
    confirm: str = Field(max_length=20)


class EndedOut(_Out):
    ended_at: datetime
    ended_attempts: int

    @classmethod
    def from_result(cls, result: EndedForEveryone) -> Self:
        return cls(ended_at=result.ended_at, ended_attempts=result.ended_attempts)


class OverrideIn(Schema):
    model_config = ConfigDict(extra="forbid")
    reason: str = Field(max_length=1000)
