"""The student's Past Tests (api_contract.md §3.5 `PastTestRow`; P-08)."""

from datetime import datetime
from decimal import Decimal
from typing import Literal, Self, cast
from uuid import UUID

from ninja import Schema
from pydantic import ConfigDict

from modules.results.services.queries.list_my_past_tests import PastTest


class PastTestOut(Schema):
    model_config = ConfigDict(extra="forbid")
    attempt_id: UUID | None
    assignment_id: UUID
    label: str
    state: Literal["AWAITING_RESULTS", "PUBLISHED", "MISSED", "DISQUALIFIED"]
    at: datetime | None
    # Only once the result is visible; rank only if the teacher shows it
    score: Decimal | None
    max_score: Decimal | None
    rank: int | None
    rank_pool: int | None

    @classmethod
    def from_card(cls, card: PastTest) -> Self:
        return cls(
            attempt_id=card.attempt_id,
            assignment_id=card.assignment_id,
            label=card.label,
            state=cast(
                "Literal['AWAITING_RESULTS', 'PUBLISHED', 'MISSED', 'DISQUALIFIED']", card.state
            ),
            at=card.at,
            score=card.score,
            max_score=card.max_score,
            rank=card.placing.rank if card.placing else None,
            rank_pool=card.placing.pool if card.placing else None,
        )
