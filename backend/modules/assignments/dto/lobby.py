"""Start and the lobby (api_contract.md §2.6, §3.3 `Lobby`)."""

from datetime import datetime
from typing import Self
from uuid import UUID

from ninja import Schema
from pydantic import ConfigDict

from modules.assignments.domain.values import LifecycleState
from modules.assignments.services.commands.activate_assignment import Activation
from modules.assignments.services.queries.get_lobby import Lobby


class _Out(Schema):
    model_config = ConfigDict(extra="forbid")


class ActivationOut(_Out):
    activated_at: datetime
    anchor_at: datetime | None
    ends_at: datetime | None

    @classmethod
    def from_activation(cls, activation: Activation) -> Self:
        return cls(
            activated_at=activation.activated_at,
            anchor_at=activation.anchor_at,
            ends_at=activation.ends_at,
        )


class JoinedOut(_Out):
    student_id: UUID
    name: str
    last_seen_at: datetime


class NotJoinedOut(_Out):
    student_id: UUID
    name: str


class LobbyCountsOut(_Out):
    joined: int
    audience: int


class LobbyOut(_Out):
    joined: list[JoinedOut]
    not_joined: list[NotJoinedOut]
    counts: LobbyCountsOut
    state: LifecycleState
    server_now: datetime

    @classmethod
    def from_lobby(cls, lobby: Lobby) -> Self:
        return cls(
            joined=[
                JoinedOut(student_id=s.student_id, name=s.name, last_seen_at=s.last_seen_at)
                for s in lobby.joined
            ],
            not_joined=[
                NotJoinedOut(student_id=s.student_id, name=s.name) for s in lobby.not_joined
            ],
            counts=LobbyCountsOut(
                joined=len(lobby.joined), audience=len(lobby.joined) + len(lobby.not_joined)
            ),
            state=lobby.state,
            server_now=lobby.server_now,
        )
