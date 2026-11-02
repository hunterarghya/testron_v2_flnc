"""A test's settings as the editor reads them (api_contract.md §3.2 TestSettings): the timing
is one of three shapes, told apart by `kind`."""

from decimal import Decimal
from typing import Annotated, Literal, Self

from ninja import Schema
from pydantic import ConfigDict, Field

from modules.authoring.domain.drafts import TestSettings, Timing
from modules.authoring.domain.values import TimingKind


class _Out(Schema):
    model_config = ConfigDict(extra="forbid")


class TotalTiming(_Out):
    kind: Literal["TOTAL"]
    duration_s: int


class PerQuestionTiming(_Out):
    kind: Literal["PER_QUESTION"]
    default_question_s: int


class SectionedTiming(_Out):
    kind: Literal["SECTIONED"]
    allow_return: bool


TimingOut = Annotated[
    TotalTiming | PerQuestionTiming | SectionedTiming, Field(discriminator="kind")
]


class Marking(_Out):
    marks: Decimal
    negative_marks: Decimal


class Integrity(_Out):
    grace_s: int
    max_warnings: int
    action: Literal["AUTO_SUBMIT", "DISQUALIFY"]


class TestSettingsOut(_Out):
    timing: TimingOut
    shuffle_questions: bool
    shuffle_options: bool
    marking: Marking
    integrity: Integrity

    @classmethod
    def from_settings(cls, settings: TestSettings) -> Self:
        return cls(
            timing=_timing(settings.timing),
            shuffle_questions=settings.shuffle_questions,
            shuffle_options=settings.shuffle_options,
            marking=Marking(
                marks=settings.marking.marks, negative_marks=settings.marking.negative_marks
            ),
            integrity=Integrity(
                grace_s=settings.integrity.grace_s,
                max_warnings=settings.integrity.max_warnings,
                action=settings.integrity.action.value,
            ),
        )


def _timing(timing: Timing) -> TotalTiming | PerQuestionTiming | SectionedTiming:
    if timing.kind is TimingKind.TOTAL:
        return TotalTiming(kind="TOTAL", duration_s=timing.duration_s or 0)
    if timing.kind is TimingKind.PER_QUESTION:
        return PerQuestionTiming(
            kind="PER_QUESTION", default_question_s=timing.default_question_s or 0
        )
    return SectionedTiming(kind="SECTIONED", allow_return=timing.allow_return)
