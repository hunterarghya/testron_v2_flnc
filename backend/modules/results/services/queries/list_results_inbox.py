from collections import defaultdict
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from enum import StrEnum
from uuid import UUID

from core.context import Ctx
from modules.assignments import public as assignments
from modules.delivery import public as delivery
from modules.results.domain.ranking import pool_stats
from modules.results.policies import ensure_teacher
from modules.results.services.standings import scored


class InboxTab(StrEnum):
    TO_PUBLISH = "to_publish"
    PUBLISHED = "published"
    ALL = "all"


@dataclass(frozen=True, slots=True)
class InboxRow:
    row: assignments.AssignmentRow
    # The first take's mean as a percentage of the paper's marks
    average_pct: Decimal | None
    # Attempts with at least one counted warning
    flagged: int


def list_results_inbox(ctx: Ctx, *, tab: InboxTab) -> list[InboxRow]:
    """T-13: closed assignments, newest first. "To publish" are those whose results wait for
    the teacher (manual, not published); the menu badge counts them. Fixed queries."""
    ensure_teacher(ctx.actor)
    closed = assignments.list_assignments(
        ctx,
        filters=assignments.AssignmentFilter(tab=assignments.Tab.CLOSED),
        offset=0,
        limit=10_000,
    ).rows
    rows = [r for r in closed if _in_tab(tab, r.publication_state.value)]
    attempts: dict[UUID, list[delivery.AttemptRow]] = defaultdict(list)
    for attempt in delivery.rows_of_assignments([r.record.id for r in rows]):
        attempts[attempt.assignment_id].append(attempt)
    return [_inbox_row(r, attempts[r.record.id]) for r in rows]


def _in_tab(tab: InboxTab, state: str) -> bool:
    if tab is InboxTab.TO_PUBLISH:
        return state == "UNPUBLISHED"
    if tab is InboxTab.PUBLISHED:
        return state != "UNPUBLISHED"
    return True


def _inbox_row(row: assignments.AssignmentRow, attempts: list[delivery.AttemptRow]) -> InboxRow:
    stats = pool_stats(scored(attempts))
    top = attempts[0].max_score if attempts else Decimal(0)
    average = None
    if stats is not None and top > 0:
        average = (stats.mean * 100 / top).quantize(Decimal(1), rounding=ROUND_HALF_UP)
    return InboxRow(row, average, sum(a.warning_count > 0 for a in attempts))
