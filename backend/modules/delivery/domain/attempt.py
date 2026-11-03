"""An attempt as the use cases see it, and the rules every write to it obeys
(domain_model.md §3.6 #6 and #8, §5.9)."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from core.errors import DomainError
from modules.delivery.domain.errors import AttemptEnded, AttemptTakenOver
from modules.delivery.domain.plan import Plan
from modules.delivery.domain.values import AttemptStatus, EndReason


@dataclass(frozen=True, slots=True)
class AttemptRecord:
    id: UUID
    assignment_id: UUID
    student_id: UUID
    take_number: int
    is_granted: bool
    status: AttemptStatus
    end_reason: EndReason | None
    started_at: datetime
    anchor_at: datetime
    ended_at: datetime | None
    plan: Plan
    current_stage_index: int
    furthest_stage_index: int
    warning_count: int
    active_client_id: UUID | None

    @property
    def in_progress(self) -> bool:
        return self.status is AttemptStatus.IN_PROGRESS


def write_refusal(attempt: AttemptRecord, presented: UUID | None) -> DomainError | None:
    """Why a write can't reach this attempt, or None when it can: it has ended (§3.6 #6), or
    only the latest device writes and this isn't it (§5.9, E-39). The caller raises it after
    its transaction, so a lazy ending found on the way is kept."""
    if not attempt.in_progress:
        return AttemptEnded(ended_at=attempt.ended_at, end_reason=attempt.end_reason)
    if is_takeover(attempt, presented):
        return AttemptTakenOver()
    return None


def is_takeover(attempt: AttemptRecord, presented: UUID | None) -> bool:
    """Opening the attempt from a device that isn't the active one (or none yet). The same
    device refreshing presents its own id and keeps it (E-40)."""
    return presented is None or presented != attempt.active_client_id


def end_reason_at_deadline(
    ended_at: datetime, *, ended_for_everyone_at: datetime | None
) -> EndReason:
    """Time ran out (TIMED_OUT), or the teacher's "end for everyone" cut it short."""
    if ended_for_everyone_at is not None and ended_at >= ended_for_everyone_at:
        return EndReason.ENDED_BY_TEACHER
    return EndReason.TIMED_OUT
