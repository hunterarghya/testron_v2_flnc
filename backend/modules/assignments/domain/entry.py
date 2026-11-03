"""When a student may begin a regular sitting (domain_model.md §5.4 checks 4-6), and Start
(§3.5, T-09). The attempt-dependent checks are delivery's; these are the assignment's."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta

from core.errors import Conflict
from modules.assignments.domain.errors import AssignmentCancelled
from modules.assignments.domain.lifecycle import (
    ExtensionGrant,
    Timeline,
    assignment_end,
    awaits_start,
    common_anchor,
    needs_start,
    opens_at,
)
from modules.assignments.domain.values import WindowKind

# The lobby counts a student as joined while their gate was open this recently (T-09)
PRESENCE_WINDOW = timedelta(seconds=30)


class ActivationNotRequired(Conflict):
    """Start belongs to locked tests and those that need activation (T-09)."""

    code = "activation_not_required"
    title = "This test doesn't wait for Start"


@dataclass(frozen=True, slots=True)
class Entry:
    # Check 4: not before this
    opens_at: datetime | None
    # Check 5: Start not pressed yet
    awaits_start: bool
    # Check 6: closed from this instant (None: not known yet, or never)
    closes_at: datetime | None
    # The shared clock's start, for MANUAL and SCHEDULED once known
    anchor_at: datetime | None
    ends_at: datetime | None


def entry_window(timeline: Timeline, extensions: Sequence[ExtensionGrant]) -> Entry:
    anchor = common_anchor(timeline)
    end = assignment_end(timeline, extensions)
    return Entry(
        opens_at=opens_at(timeline.window),
        awaits_start=awaits_start(timeline),
        closes_at=_entry_closes_at(timeline, anchor, end),
        anchor_at=anchor,
        ends_at=end,
    )


def _entry_closes_at(
    timeline: Timeline, anchor: datetime | None, end: datetime | None
) -> datetime | None:
    """The earliest of: ended for everyone; a deadline's close; and for a shared clock its
    end (boundary(n)) and the late-entry cut-off."""
    window = timeline.window
    limits = [timeline.ended_at]
    if window.kind is WindowKind.DEADLINE:
        limits.append(window.closes_at)
    if window.common_clock and anchor is not None:
        limits.append(end)
        if window.late_entry_s is not None:
            limits.append(anchor + timedelta(seconds=window.late_entry_s))
    present = [limit for limit in limits if limit is not None]
    return min(present, default=None)


def ensure_activatable(timeline: Timeline) -> None:
    if timeline.cancelled_at is not None:
        raise AssignmentCancelled()
    if not needs_start(timeline):
        raise ActivationNotRequired()


def is_joined(last_seen_at: datetime, *, now: datetime) -> bool:
    return now - last_seen_at <= PRESENCE_WINDOW


def is_locked(timeline: Timeline, *, has_password: bool) -> bool:
    """🔒 on the lists (T-06, P-01): students wait for Start or need a password."""
    return needs_start(timeline) or has_password
