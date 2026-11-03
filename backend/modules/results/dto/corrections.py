"""Answer key corrections (api_contract.md §2.7; D-05)."""

from decimal import Decimal
from typing import Self
from uuid import UUID

from ninja import Schema
from pydantic import ConfigDict, Field

from modules.assignments import public as assignments
from modules.results.services.commands.correct_answer_key import KeyCorrected


class KeyEntryIn(Schema):
    """MCQ/MSQ: `option_ids`. Numerical: `answer` and `tolerance`."""

    model_config = ConfigDict(extra="forbid")
    option_ids: list[UUID] = Field(default_factory=list, max_length=26)
    answer: Decimal | None = Field(default=None, max_digits=20, decimal_places=6)
    tolerance: Decimal = Field(default=Decimal(0), max_digits=20, decimal_places=6)

    def to_entry(self) -> assignments.KeyEntry:
        return assignments.KeyEntry(
            option_ids=tuple(self.option_ids), answer=self.answer, tolerance=self.tolerance
        )


class KeyCorrectionIn(Schema):
    model_config = ConfigDict(extra="forbid")
    question_id: UUID
    entry: KeyEntryIn
    reason: str = Field(max_length=1000)


class KeyCorrectedOut(Schema):
    model_config = ConfigDict(extra="forbid")
    version: int
    regraded_attempts: int

    @classmethod
    def from_result(cls, result: KeyCorrected) -> Self:
        return cls(version=result.version, regraded_attempts=result.regraded_attempts)
