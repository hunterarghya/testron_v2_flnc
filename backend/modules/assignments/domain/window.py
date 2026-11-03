"""The assignment window (domain_model.md §3.5): one of four kinds, each with only its own
fields, checked when an assignment is created or changed before its start."""

from dataclasses import dataclass
from datetime import datetime, timedelta

from core.errors import FieldError, FieldsInvalid
from modules.assignments.domain.values import WindowKind

# Late entry beyond a day means the window should have been a deadline one
MAX_LATE_ENTRY_S = 24 * 3600


@dataclass(frozen=True, slots=True)
class Window:
    kind: WindowKind
    # MANUAL: shown to students, nothing more
    planned_at: datetime | None = None
    # SCHEDULED
    starts_at: datetime | None = None
    # DEADLINE
    opens_at: datetime | None = None
    closes_at: datetime | None = None
    # MANUAL / SCHEDULED: how long after the start students may still join
    late_entry_s: int | None = None

    @property
    def common_clock(self) -> bool:
        """Everyone shares one clock (MANUAL, SCHEDULED); the others start per student."""
        return self.kind in (WindowKind.MANUAL, WindowKind.SCHEDULED)


def ensure_window_valid(window: Window, *, now: datetime, total_duration_s: int) -> None:
    """Every problem at once (domain_model.md §3.5 #1)."""
    errors = [
        *_late_entry_errors(window),
        *(_scheduled_errors(window, now) if window.kind is WindowKind.SCHEDULED else []),
        *(_deadline_errors(window, total_duration_s) if window.kind is WindowKind.DEADLINE else []),
    ]
    if errors:
        raise FieldsInvalid(*errors)


def _late_entry_errors(window: Window) -> list[FieldError]:
    late = window.late_entry_s
    if late is None:
        return []
    if not window.common_clock:
        return [
            FieldError(
                "window.late_entry_s", "invalid", "Only a locked or scheduled test has late entry"
            )
        ]
    if not 0 <= late <= MAX_LATE_ENTRY_S:
        return [FieldError("window.late_entry_s", "invalid", "Use 0 to 24 hours")]
    return []


def _scheduled_errors(window: Window, now: datetime) -> list[FieldError]:
    if window.starts_at is None or window.starts_at <= now:
        return [FieldError("window.starts_at", "invalid", "Pick a start time in the future")]
    return []


def _deadline_errors(window: Window, total_duration_s: int) -> list[FieldError]:
    if window.opens_at is None or window.closes_at is None:
        return [FieldError("window.closes_at", "invalid", "Pick when it opens and closes")]
    if window.closes_at <= window.opens_at:
        return [FieldError("window.closes_at", "invalid", "It must close after it opens")]
    if window.closes_at - window.opens_at < timedelta(seconds=total_duration_s):
        return [
            FieldError(
                "window.closes_at",
                "invalid",
                "Leave at least the test's duration between open and close",
            )
        ]
    return []
