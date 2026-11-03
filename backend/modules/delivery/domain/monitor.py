"""The live monitor's view of each student (T-10, api_contract.md §3.3 `Monitor`): one status
per audience member, from their latest sitting, and the filters over them."""

from enum import StrEnum

from modules.delivery.domain.values import AttemptStatus, EndReason


class MonitorStatus(StrEnum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    TIMED_OUT = "TIMED_OUT"
    AUTO_SUBMITTED = "AUTO_SUBMITTED"
    DISQUALIFIED = "DISQUALIFIED"
    FORCE_SUBMITTED = "FORCE_SUBMITTED"
    ENDED_BY_TEACHER = "ENDED_BY_TEACHER"


class MonitorFilter(StrEnum):
    ALL = "all"
    IN_PROGRESS = "in_progress"
    NOT_STARTED = "not_started"
    ENDED = "ended"
    # At least one counted warning
    FLAGGED = "flagged"


def monitor_status(status: AttemptStatus | None, end_reason: EndReason | None) -> MonitorStatus:
    """No sitting yet, still sitting, or how the latest one ended."""
    if status is None:
        return MonitorStatus.NOT_STARTED
    if status is AttemptStatus.IN_PROGRESS or end_reason is None:
        return MonitorStatus.IN_PROGRESS
    return MonitorStatus(end_reason.value)


def is_shown(chosen: MonitorFilter, status: MonitorStatus, *, warnings: int) -> bool:
    match chosen:
        case MonitorFilter.IN_PROGRESS:
            return status is MonitorStatus.IN_PROGRESS
        case MonitorFilter.NOT_STARTED:
            return status is MonitorStatus.NOT_STARTED
        case MonitorFilter.ENDED:
            return status not in (MonitorStatus.IN_PROGRESS, MonitorStatus.NOT_STARTED)
        case MonitorFilter.FLAGGED:
            return warnings > 0
        case _:
            return True
