from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from core.context import Ctx
from modules.assignments.domain.entry import is_joined
from modules.assignments.domain.values import LifecycleState
from modules.assignments.policies import ensure_teacher
from modules.assignments.repositories import assignments, audience, presence
from modules.assignments.services.views import assignment_rows
from modules.students import public as students


@dataclass(frozen=True, slots=True)
class LobbyStudent:
    student_id: UUID
    name: str


@dataclass(frozen=True, slots=True)
class JoinedStudent:
    student_id: UUID
    name: str
    last_seen_at: datetime


@dataclass(frozen=True, slots=True)
class Lobby:
    joined: list[JoinedStudent]
    not_joined: list[LobbyStudent]
    state: LifecycleState
    server_now: datetime


def get_lobby(ctx: Ctx, *, assignment_id: UUID) -> Lobby:
    """Who has the gate open right now, and who doesn't (T-09, polled every 5 s)."""
    ensure_teacher(ctx.actor)
    record = assignments.get_record(assignment_id)
    state = assignment_rows([record], now=ctx.now)[0].state
    seen = presence.last_seen(assignment_id)
    people = students.describe_students(audience.member_ids(assignment_id))
    joined = [
        JoinedStudent(p.student_id, p.name, seen[p.student_id])
        for p in people
        if p.student_id in seen and is_joined(seen[p.student_id], now=ctx.now)
    ]
    joined_ids = {s.student_id for s in joined}
    not_joined = [
        LobbyStudent(p.student_id, p.name) for p in people if p.student_id not in joined_ids
    ]
    return Lobby(joined=joined, not_joined=not_joined, state=state, server_now=ctx.now)
