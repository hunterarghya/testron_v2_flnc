"""The frozen paper as delivery reads it (database_schema.md §4.2). It holds no answers by
construction, so nothing read here can leak one."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import cast
from uuid import UUID

Json = Mapping[str, object]


@dataclass(frozen=True, slots=True)
class PaperQuestion:
    id: UUID
    type: str
    stem: Json
    marks: Decimal
    negative_marks: Decimal
    time_s: int | None
    # In the teacher's order; empty for a numerical question
    option_ids: tuple[UUID, ...]
    options: Mapping[UUID, Json]


@dataclass(frozen=True, slots=True)
class PaperSection:
    id: UUID
    title: str | None
    instructions: Json | None
    duration_s: int | None
    questions: tuple[PaperQuestion, ...]


@dataclass(frozen=True, slots=True)
class PaperView:
    title: str
    timing_kind: str
    allow_return: bool
    total_duration_s: int
    shuffle_questions: bool
    shuffle_options: bool
    sections: tuple[PaperSection, ...]

    def questions(self) -> dict[UUID, PaperQuestion]:
        return {q.id: q for s in self.sections for q in s.questions}


def read_paper(content: Json) -> PaperView:
    timing = cast("Json", content["timing"])
    shuffle = cast("Json", content["shuffle"])
    kind = str(timing["kind"])
    return PaperView(
        title=str(content["title"]),
        timing_kind=kind,
        # Rapid fire never goes back (domain_model.md §5.1)
        allow_return=bool(timing["allow_return"]) and kind == "SECTIONED",
        total_duration_s=cast("int", timing["total_duration_s"]),
        shuffle_questions=bool(shuffle["questions"]),
        shuffle_options=bool(shuffle["options"]),
        sections=tuple(_section(s) for s in cast("Sequence[Json]", content["sections"])),
    )


def _section(section: Json) -> PaperSection:
    return PaperSection(
        id=UUID(str(section["id"])),
        title=cast("str | None", section["title"]),
        instructions=cast("Json | None", section["instructions"]),
        duration_s=cast("int | None", section["duration_s"]),
        questions=tuple(_question(q) for q in cast("Sequence[Json]", section["questions"])),
    )


def _question(question: Json) -> PaperQuestion:
    options = cast("Sequence[Json]", question.get("options", []))
    return PaperQuestion(
        id=UUID(str(question["id"])),
        type=str(question["type"]),
        stem=cast("Json", question["stem"]),
        marks=Decimal(str(question["marks"])),
        negative_marks=Decimal(str(question["negative_marks"])),
        time_s=cast("int | None", question["time_s"]),
        option_ids=tuple(UUID(str(o["id"])) for o in options),
        options={UUID(str(o["id"])): cast("Json", o["content"]) for o in options},
    )
