from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from core.context import Ctx
from modules.assignments import public as assignments
from modules.delivery import public as delivery
from modules.results.domain.breakdown import attempt_label
from modules.results.domain.ranking import Placing, placings
from modules.results.policies import ensure_active_student
from modules.results.services.standings import is_disqualified, is_visible, scored


@dataclass(frozen=True, slots=True)
class PastTest:
    assignment_id: UUID
    attempt_id: UUID | None
    label: str
    # AWAITING_RESULTS, PUBLISHED, MISSED or DISQUALIFIED
    state: str
    at: datetime | None
    score: Decimal | None = None
    max_score: Decimal | None = None
    placing: Placing | None = None


def list_my_past_tests(ctx: Ctx) -> list[PastTest]:
    """P-08: one card per ended take, newest first [D-9, Q-13], and a "Missed" card for a
    closed test never sat. A score shows only once the result is visible; rank only if the
    teacher chose it [H-2]. Sittings whose time ran out end first. Fixed queries."""
    student_id = ensure_active_student(ctx.actor)
    delivery.finalize_student(ctx, student_id=student_id)
    frames = {
        f.row.record.id: f
        for f in assignments.list_results_frames_for_student(student_id, now=ctx.now)
    }
    every = delivery.rows_of_student(student_id)
    mine = [a for a in every if a.ended_at and a.assignment_id in frames]
    ranked = _placings(mine, frames, ctx.now)
    cards = [_card(a, frames[a.assignment_id], ranked.get(a.id), ctx.now) for a in mine]
    sat = {a.assignment_id for a in every}
    missed = [
        PastTest(f.row.record.id, None, f.row.record.settings.title, "MISSED", f.row.ends_at)
        for f in frames.values()
        if f.row.state.value == "CLOSED" and f.row.record.id not in sat
    ]
    return sorted(cards + missed, key=lambda c: c.at or ctx.now, reverse=True)


def _card(
    attempt: delivery.AttemptRow,
    frame: assignments.ResultsFrame,
    placing: Placing | None,
    now: datetime,
) -> PastTest:
    label = attempt_label(frame.row.record.settings.title, attempt.started_at, attempt.take_number)
    base = PastTest(
        attempt.assignment_id, attempt.id, label, "AWAITING_RESULTS", attempt.started_at
    )
    if not is_visible(frame, attempt, now=now):
        return base
    if is_disqualified(attempt) and attempt.disqualification_overridden_at is None:
        return PastTest(base.assignment_id, base.attempt_id, label, "DISQUALIFIED", base.at)
    return PastTest(
        base.assignment_id,
        base.attempt_id,
        label,
        "PUBLISHED",
        base.at,
        attempt.score,
        attempt.max_score,
        placing,
    )


def _placings(
    mine: list[delivery.AttemptRow], frames: dict[UUID, assignments.ResultsFrame], now: datetime
) -> dict[UUID, Placing]:
    """Ranks only where the teacher shows them, from every attempt of those tests (one query)."""
    wanted = [
        a.assignment_id
        for a in mine
        if frames[a.assignment_id].row.record.settings.publication.show_rank_and_stats
        and is_visible(frames[a.assignment_id], a, now=now)
    ]
    if not wanted:
        return {}
    return placings(scored(delivery.rows_of_assignments(list(dict.fromkeys(wanted)))))
