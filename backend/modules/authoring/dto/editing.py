"""What the editor sends (api_contract.md §2.5). Every change carries the `revision` it was
based on. Rich content arrives as JSON and is checked by the use case (core.rich_content)."""

from decimal import Decimal
from typing import Annotated, Literal, cast
from uuid import UUID

from ninja import Schema
from pydantic import ConfigDict, Field

from modules.authoring.domain import drafts
from modules.authoring.domain.question_patch import OptionInput, QuestionChanges
from modules.authoring.domain.settings_patch import SettingsPatch, TimingPatch
from modules.authoring.domain.values import IntegrityAction, QuestionType, TimingKind
from modules.authoring.services.commands.update_section import SectionChanges
from modules.authoring.services.commands.update_test import TestChanges

RichJson = dict[str, object]
Money = Annotated[Decimal, Field(max_digits=7, decimal_places=2)]
Number = Annotated[Decimal, Field(max_digits=20, decimal_places=6)]
TagName = Annotated[str, Field(max_length=160)]


class _In(Schema):
    model_config = ConfigDict(extra="forbid")

    def _sent(self, clearable: frozenset[str]) -> dict[str, object]:
        """The fields sent. A sent null clears the `clearable` ones and means "leave as is"
        for the rest."""
        names = self.model_fields_set - {"revision"}
        values = {name: getattr(self, name) for name in names}
        return {
            name: value for name, value in values.items() if value is not None or name in clearable
        }


class RevisionIn(_In):
    revision: int


class TotalTimingIn(_In):
    kind: Literal["TOTAL"]
    duration_s: int | None = None


class PerQuestionTimingIn(_In):
    kind: Literal["PER_QUESTION"]
    default_question_s: int | None = None


class SectionedTimingIn(_In):
    kind: Literal["SECTIONED"]
    allow_return: bool | None = None


class MarkingIn(_In):
    marks: Money
    negative_marks: Money


class IntegrityIn(_In):
    grace_s: int
    max_warnings: int
    action: Literal["AUTO_SUBMIT", "DISQUALIFY"]


class TestSettingsPatchIn(_In):
    timing: (
        Annotated[
            TotalTimingIn | PerQuestionTimingIn | SectionedTimingIn, Field(discriminator="kind")
        ]
        | None
    ) = None
    shuffle_questions: bool | None = None
    shuffle_options: bool | None = None
    marking: MarkingIn | None = None
    integrity: IntegrityIn | None = None

    def patch(self) -> SettingsPatch:
        timing = self.timing
        return SettingsPatch(
            timing=TimingPatch(
                kind=TimingKind(timing.kind),
                duration_s=getattr(timing, "duration_s", None),
                default_question_s=getattr(timing, "default_question_s", None),
                allow_return=getattr(timing, "allow_return", None),
            )
            if timing
            else None,
            shuffle_questions=self.shuffle_questions,
            shuffle_options=self.shuffle_options,
            marking=drafts.Marking(self.marking.marks, self.marking.negative_marks)
            if self.marking
            else None,
            integrity=drafts.Integrity(
                self.integrity.grace_s,
                self.integrity.max_warnings,
                IntegrityAction(self.integrity.action),
            )
            if self.integrity
            else None,
        )


class TestPatchIn(RevisionIn):
    title: str | None = Field(default=None, max_length=400)
    # null removes the instructions
    instructions: RichJson | None = None
    settings: TestSettingsPatchIn | None = None

    def changes(self) -> TestChanges:
        sent = self._sent(frozenset({"instructions"}))
        if self.settings is not None:
            sent["settings"] = self.settings.patch()
        return cast("TestChanges", sent)


class SectionIn(RevisionIn):
    after_section_id: UUID | None = None
    title: str = Field(default="", max_length=400)
    duration_s: int | None = None


class SectionPatchIn(RevisionIn):
    title: str | None = Field(default=None, max_length=400)
    instructions: RichJson | None = None
    duration_s: int | None = None

    def changes(self) -> SectionChanges:
        return cast("SectionChanges", self._sent(frozenset({"instructions", "duration_s"})))


class SectionDeleteIn(_In):
    revision: int
    # Needed only when the section still has questions
    questions: Literal["move_to_previous", "delete"] | None = None


class QuestionIn(RevisionIn):
    section_id: UUID
    after_question_id: UUID | None = None
    type: Literal["MCQ", "MSQ", "NUMERICAL"]


class OptionIn(_In):
    # Present: keep that option; absent: a new one
    id: UUID | None = None
    content: RichJson
    is_correct: bool = False


class QuestionPatchIn(RevisionIn):
    """The whole question as the editor holds it; any field left out stays as it is."""

    type: Literal["MCQ", "MSQ", "NUMERICAL"] | None = None
    stem: RichJson | None = None
    solution: RichJson | None = None
    marks_override: Money | None = None
    negative_marks_override: Money | None = None
    time_override_s: int | None = None
    numeric_answer: Number | None = None
    numeric_tolerance: Number | None = None
    options: list[OptionIn] | None = Field(default=None, max_length=10)
    chapter_tags: list[TagName] | None = Field(default=None, max_length=20)
    topic_tags: list[TagName] | None = Field(default=None, max_length=20)

    def changes(self) -> QuestionChanges:
        clearable = frozenset(
            {
                "solution",
                "marks_override",
                "negative_marks_override",
                "time_override_s",
                "numeric_answer",
            }
        )
        sent = self._sent(clearable)
        if self.type is not None:
            sent["type"] = QuestionType(self.type)
        if self.options is not None:
            sent["options"] = [OptionInput(o.id, o.content, o.is_correct) for o in self.options]
        return cast("QuestionChanges", sent)


class SectionLayoutIn(_In):
    id: UUID
    question_ids: list[UUID]


class StructureIn(RevisionIn):
    sections: list[SectionLayoutIn] = Field(max_length=100)

    def layout(self) -> list[tuple[UUID, list[UUID]]]:
        return [(section.id, section.question_ids) for section in self.sections]
