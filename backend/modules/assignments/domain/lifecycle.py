"""Where an assignment is in its life, worked out from its times (domain_model.md §3.5 derived
lifecycle, §5.1 anchor, §5.6 assignment_end). Nothing here is stored."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta

from modules.assignments.domain.values import LifecycleState, WindowKind
from modules.assignments.domain.window import Window


@dataclass(frozen=True, slots=True)
class Timeline:
    window: Window
    requires_activation: bool
    total_duration_s: int
    activated_at: datetime | None = None
    ended_at: datetime | None = None
    cancelled_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class ExtensionGrant:
    seconds: int
    # False: one student's extension
    for_everyone: bool
    # None: the final stage
    stage_index: int | None


def common_anchor(timeline: Timeline) -> datetime | None:
    """When the shared clock starts (MANUAL, SCHEDULED); None until it can be known."""
    window = timeline.window
    if window.kind is WindowKind.MANUAL:
        return timeline.activated_at
    if window.kind is WindowKind.SCHEDULED and window.starts_at is not None:
        if not timeline.requires_activation:
            return window.starts_at
        return max(window.starts_at, timeline.activated_at) if timeline.activated_at else None
    return None


def assignment_end(timeline: Timeline, extensions: Sequence[ExtensionGrant]) -> datetime | None:
    """When no one can be sitting the test any more, except student-specific extensions;
    None for OPEN windows (never over) or a common clock not started yet."""
    if timeline.ended_at:
        return timeline.ended_at
    everyone = [e for e in extensions if e.for_everyone]
    window = timeline.window
    if window.common_clock:
        anchor = common_anchor(timeline)
        added = sum(e.seconds for e in everyone)
        return (
            None
            if anchor is None
            else anchor + timedelta(seconds=timeline.total_duration_s + added)
        )
    if window.kind is WindowKind.DEADLINE and window.closes_at is not None:
        added = sum(e.seconds for e in everyone if e.stage_index is None)
        return window.closes_at + timedelta(seconds=added)
    return None


def lifecycle_state(
    timeline: Timeline,
    extensions: Sequence[ExtensionGrant],
    *,
    now: datetime,
    attempts_in_progress: bool,
) -> LifecycleState:
    if timeline.cancelled_at:
        return LifecycleState.CANCELLED
    if timeline.ended_at:
        return LifecycleState.CLOSED
    opens = opens_at(timeline.window)
    if opens is not None and now < opens:
        return LifecycleState.SCHEDULED
    if awaits_start(timeline):
        return LifecycleState.WAITING
    end = assignment_end(timeline, extensions)
    if end is not None and end <= now and not attempts_in_progress:
        return LifecycleState.CLOSED
    return LifecycleState.LIVE


def opens_at(window: Window) -> datetime | None:
    """When students may first enter: a scheduled start or a deadline's opening."""
    return window.starts_at if window.kind is WindowKind.SCHEDULED else window.opens_at


def needs_start(timeline: Timeline) -> bool:
    """A locked (MANUAL) test always waits for Start; others only if activation is required."""
    return timeline.requires_activation or timeline.window.kind is WindowKind.MANUAL


def awaits_start(timeline: Timeline) -> bool:
    return needs_start(timeline) and timeline.activated_at is None


def has_started(state: LifecycleState, timeline: Timeline) -> bool:
    """After this only the audience (added), password, extensions, publication and the end
    may change (domain_model.md §3.5 #5)."""
    return timeline.activated_at is not None or state in (
        LifecycleState.LIVE,
        LifecycleState.CLOSED,
    )
