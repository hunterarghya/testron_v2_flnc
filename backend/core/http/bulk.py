"""`BulkResult` (api_contract.md §3.1): what a bulk action on students did."""

from typing import Self
from uuid import UUID

from ninja import Schema
from pydantic import ConfigDict

from core.bulk import BulkOutcome


class SkippedOut(Schema):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    reason: str


class BulkResultOut(Schema):
    """`{succeeded, skipped}`: a student in the wrong status is skipped, not an error."""

    model_config = ConfigDict(extra="forbid")

    succeeded: list[UUID]
    skipped: list[SkippedOut]

    @classmethod
    def from_outcome(cls, outcome: BulkOutcome) -> Self:
        return cls(
            succeeded=list(outcome.applied),
            skipped=[
                SkippedOut(id=skip.student_id, reason=skip.reason) for skip in outcome.skipped
            ],
        )
