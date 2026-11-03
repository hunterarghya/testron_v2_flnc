from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from core.context import Ctx
from modules.assignments.domain.values import LifecycleState
from modules.assignments.policies import ensure_teacher
from modules.assignments.repositories import assignments
from modules.assignments.services.views import AssignmentRow, assignment_rows
from modules.students import public as students


class Tab(StrEnum):
    """T-06's tabs, each a set of lifecycle states."""

    UPCOMING = "upcoming"
    LIVE = "live"
    CLOSED = "closed"
    CANCELLED = "cancelled"


_TAB_STATES = {
    Tab.UPCOMING: {LifecycleState.SCHEDULED, LifecycleState.WAITING},
    Tab.LIVE: {LifecycleState.LIVE},
    Tab.CLOSED: {LifecycleState.CLOSED},
    Tab.CANCELLED: {LifecycleState.CANCELLED},
}


@dataclass(frozen=True, slots=True)
class AssignmentFilter:
    tab: Tab | None = None
    group_id: UUID | None = None
    search: str | None = None
    # When it happens, from (inclusive) and to (exclusive)
    from_at: datetime | None = None
    to_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class AssignmentPage:
    rows: list[AssignmentRow]
    total: int


def list_assignments(
    ctx: Ctx, *, filters: AssignmentFilter, offset: int, limit: int
) -> AssignmentPage:
    """The teacher's assignments, newest first (T-06). The state is worked out from the times,
    so the tab is filtered after the rows are read: one coaching center has hundreds of
    assignments, not millions. Five queries, however many there are."""
    ensure_teacher(ctx.actor)
    members = None if filters.group_id is None else students.list_group_member_ids(filters.group_id)
    records = assignments.list_records(
        search=filters.search, student_ids=members, between=(filters.from_at, filters.to_at)
    )
    rows = assignment_rows(records, now=ctx.now)
    if filters.tab is not None:
        rows = [row for row in rows if row.state in _TAB_STATES[filters.tab]]
    return AssignmentPage(rows=rows[offset : offset + limit], total=len(rows))
