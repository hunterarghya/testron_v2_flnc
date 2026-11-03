"""Leaving the test (domain_model.md §5.8). The browser detects it, because only it can; the
server records each departure and decides the count and what happens. A departure costs at
most one warning however often it is reported (E-20), and the last allowed warning ends the
attempt as the assignment says: auto-submitted or disqualified."""

from dataclasses import dataclass
from enum import StrEnum

from modules.delivery.domain.values import EndReason


class WarningAction(StrEnum):
    # Nothing to show: a short absence within the grace period
    NONE = "NONE"
    # Show the warning overlay (P-06)
    WARN = "WARN"
    # The attempt has ended (P-07)
    ENDED = "ENDED"


@dataclass(frozen=True, slots=True)
class WarningDecision:
    # This report makes the departure count
    counts_now: bool
    warning_count: int
    # The warning limit is reached: end the attempt with this reason
    ends_with: EndReason | None


_ENDINGS = {"AUTO_SUBMIT": EndReason.AUTO_SUBMITTED, "DISQUALIFY": EndReason.DISQUALIFIED}


def decide_warning(  # keyword-only (CLAUDE.md limits)
    *,
    warning_count: int,
    max_warnings: int,
    action: str,
    already_counted: bool,
    beyond_grace: bool,
) -> WarningDecision:
    if already_counted or not beyond_grace:
        return WarningDecision(counts_now=False, warning_count=warning_count, ends_with=None)
    count = warning_count + 1
    ends = _ENDINGS[action] if count >= max_warnings else None
    return WarningDecision(counts_now=True, warning_count=count, ends_with=ends)


def warning_action(*, in_progress: bool, counted: bool) -> WarningAction:
    """What the student's screen does with the reply. A repeated report answers the same."""
    if not in_progress:
        return WarningAction.ENDED
    return WarningAction.WARN if counted else WarningAction.NONE
