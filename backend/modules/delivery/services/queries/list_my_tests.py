from dataclasses import dataclass
from datetime import datetime

from core.context import Ctx
from modules.assignments import public as assignments
from modules.delivery.domain.gate import CardState, card_state
from modules.delivery.policies import ensure_active_student
from modules.delivery.repositories import attempt_facts
from modules.delivery.services.gate_views import GateView, gate_view


@dataclass(frozen=True, slots=True)
class MyTestCard:
    view: GateView
    state: CardState


@dataclass(frozen=True, slots=True)
class MyTests:
    available: list[MyTestCard]
    upcoming: list[MyTestCard]
    server_now: datetime


def list_my_tests(ctx: Ctx) -> MyTests:
    """P-01: the student's assignments they can start, join or resume now, and those still
    to open (soonest first). Only their own, never cancelled ones (A-01). Missed and used-up
    ones are left out: Past Tests shows them. Five queries."""
    student_id = ensure_active_student(ctx.actor)
    mine = assignments.list_student_assignments(student_id)
    sittings = attempt_facts.sittings_by_assignment(student_id, [a.assignment_id for a in mine])
    cards = [
        MyTestCard(view, state)
        for view in (gate_view(a, sittings[a.assignment_id], now=ctx.now) for a in mine)
        if (state := card_state(view.gate)) is not None
    ]
    upcoming = [card for card in cards if card.state is CardState.STARTS_IN]
    upcoming.sort(key=lambda card: card.view.assignment.entry.opens_at or ctx.now)
    available = [card for card in cards if card.state is not CardState.STARTS_IN]
    return MyTests(available=available, upcoming=upcoming, server_now=ctx.now)
