from typing import Self

from ninja import Schema
from pydantic import ConfigDict

from modules.results.services.queries.get_badges import Badges


class BadgesOut(Schema):
    model_config = ConfigDict(extra="forbid")

    pending_students: int
    results_to_publish: int

    @classmethod
    def from_badges(cls, badges: Badges) -> Self:
        return cls(
            pending_students=badges.pending_students, results_to_publish=badges.results_to_publish
        )
