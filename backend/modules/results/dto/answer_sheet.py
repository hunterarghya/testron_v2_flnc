"""The teacher's answer sheet (api_contract.md §3.5 `AnswerSheet`; T-12): a result with every
part, the student, the times they left the test, and a disqualified score."""

from datetime import datetime
from decimal import Decimal
from typing import Literal, Self
from uuid import UUID

from ninja import Schema
from pydantic import ConfigDict

from modules.results.dto.result import ResultOut
from modules.results.services.queries.get_answer_sheet import (
    AnswerSheet,
    SheetFlags,
    disqualified_score,
)

EventKind = Literal["FULLSCREEN_EXIT", "TAB_HIDDEN", "WINDOW_BLUR", "DEVICE_CHANGED"]


class _Out(Schema):
    model_config = ConfigDict(extra="forbid")


class StudentRefOut(_Out):
    id: UUID
    name: str


class SheetEventOut(_Out):
    kind: EventKind
    left_at: datetime
    returned_at: datetime | None
    counted: bool


class SheetFlagsOut(_Out):
    warning_count: int
    max_warnings: int
    action: Literal["AUTO_SUBMIT", "DISQUALIFY"]
    overridden_at: datetime | None
    override_reason: str | None

    @classmethod
    def from_flags(cls, flags: SheetFlags) -> Self:
        return cls(
            warning_count=flags.warning_count,
            max_warnings=flags.max_warnings,
            action="DISQUALIFY" if flags.action == "DISQUALIFY" else "AUTO_SUBMIT",
            overridden_at=flags.overridden_at,
            override_reason=flags.override_reason,
        )


class AnswerSheetOut(ResultOut):
    student: StudentRefOut
    integrity_events: list[SheetEventOut]
    # The computed score shown in brackets beside "Disqualified" (G-2)
    disqualified_score: Decimal | None
    flags: SheetFlagsOut

    @classmethod
    def from_sheet(cls, sheet: AnswerSheet) -> Self:
        base = ResultOut.from_view(sheet.result).model_dump()
        return cls(
            **base,
            student=StudentRefOut(id=sheet.result.attempt.student_id, name=sheet.student_name),
            integrity_events=[
                SheetEventOut(
                    kind=e.kind.value,
                    left_at=e.left_at,
                    returned_at=e.returned_at,
                    counted=e.counted,
                )
                for e in sheet.events
            ],
            disqualified_score=disqualified_score(sheet),
            flags=SheetFlagsOut.from_flags(sheet.flags),
        )
