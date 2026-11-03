"""One assignment as a student sees it before starting: the gate, and the card on My Tests.
list_my_tests and get_gate_state both build it here."""

from dataclasses import dataclass, replace
from datetime import datetime

from modules.assignments import public as assignments
from modules.delivery.domain.gate import (
    EntryTimes,
    Gate,
    Sittings,
    SittingTimes,
    gate,
    time_left_if_started_now,
)


@dataclass(frozen=True, slots=True)
class GateView:
    assignment: assignments.StudentAssignment
    gate: Gate
    sittings: Sittings
    time_left_if_started_now_s: int | None
    server_now: datetime


def gate_view(
    assignment: assignments.StudentAssignment, sittings: Sittings, *, now: datetime
) -> GateView:
    sittings = replace(sittings, has_grant=assignment.has_unused_grant)
    entry = assignment.entry
    current = gate(entry_times(assignment), sittings, now=now)
    times = SittingTimes(
        duration_s=assignment.paper.total_duration_s,
        common_clock=assignment.window.common_clock,
        anchor_at=entry.anchor_at,
        ends_at=entry.ends_at,
    )
    return GateView(
        assignment=assignment,
        gate=current,
        sittings=sittings,
        time_left_if_started_now_s=time_left_if_started_now(current, times, now=now),
        server_now=now,
    )


def entry_times(assignment: assignments.StudentAssignment) -> EntryTimes:
    entry = assignment.entry
    return EntryTimes(entry.opens_at, entry.awaits_start, entry.closes_at)
