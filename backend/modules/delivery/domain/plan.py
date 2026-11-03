"""The attempt's plan (domain_model.md §5.4, database_schema.md §4.4): its stages, the order
of questions in each and the order of each question's options. Built once at the start from a
seed and stored, so a later change to this code never reshuffles a running attempt [V1 F-38].

Shuffling keeps sections together: questions move only within their section, so a total-timer
test's section headings still make sense (ADR-074)."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from random import Random
from typing import cast
from uuid import UUID

from modules.delivery.domain.paper import Json, PaperQuestion, PaperSection, PaperView
from modules.delivery.domain.values import StageKind

PLAN_VERSION = 1


@dataclass(frozen=True, slots=True)
class PlanStage:
    index: int
    kind: StageKind
    # The section this stage comes from (None for a total-timer test's single stage)
    section_id: UUID | None
    duration_s: int
    question_ids: tuple[UUID, ...]


@dataclass(frozen=True, slots=True)
class Plan:
    stages: tuple[PlanStage, ...]
    # Only questions with options; the student sees them in this order
    option_order: Mapping[UUID, tuple[UUID, ...]]

    @property
    def durations_s(self) -> tuple[int, ...]:
        return tuple(stage.duration_s for stage in self.stages)

    def stage_of(self, question_id: UUID) -> int | None:
        return next((s.index for s in self.stages if question_id in s.question_ids), None)

    def question_ids(self) -> list[UUID]:
        """Every question, in the student's order: their display numbers follow it."""
        return [q for stage in self.stages for q in stage.question_ids]


def build_plan(paper: PaperView, seed: int) -> Plan:
    rng = Random(seed)  # noqa: S311  # a fair shuffle, not a secret
    sections = [
        (section, _ordered(section.questions, rng, shuffle=paper.shuffle_questions))
        for section in paper.sections
    ]
    order = {
        q.id: _ordered(q.option_ids, rng, shuffle=paper.shuffle_options)
        for _, questions in sections
        for q in questions
        if q.option_ids
    }
    return Plan(stages=_stages(paper, sections), option_order=order)


def _ordered[T](items: Sequence[T], rng: Random, *, shuffle: bool) -> tuple[T, ...]:
    shuffled = list(items)
    if shuffle:
        rng.shuffle(shuffled)
    return tuple(shuffled)


def _stages(
    paper: PaperView, sections: Sequence[tuple[PaperSection, tuple[PaperQuestion, ...]]]
) -> tuple[PlanStage, ...]:
    """One WHOLE stage, one per section, or one per question (§5.1)."""
    if paper.timing_kind == "SECTIONED":
        return tuple(
            PlanStage(i, StageKind.SECTION, s.id, s.duration_s or 0, tuple(q.id for q in qs))
            for i, (s, qs) in enumerate(sections)
        )
    if paper.timing_kind == "PER_QUESTION":
        each = [(s.id, q) for s, qs in sections for q in qs]
        return tuple(
            PlanStage(i, StageKind.QUESTION, sid, q.time_s or 0, (q.id,))
            for i, (sid, q) in enumerate(each)
        )
    every = tuple(q.id for _, qs in sections for q in qs)
    return (PlanStage(0, StageKind.WHOLE, None, paper.total_duration_s, every),)


def plan_json(plan: Plan) -> dict[str, object]:
    return {
        "v": PLAN_VERSION,
        "stages": [
            {
                "index": s.index,
                "kind": s.kind.value,
                "section_id": str(s.section_id) if s.section_id else None,
                "duration_s": s.duration_s,
                "question_ids": [str(q) for q in s.question_ids],
            }
            for s in plan.stages
        ],
        "option_order": {str(q): [str(o) for o in ids] for q, ids in plan.option_order.items()},
    }


def read_plan(stored: Json) -> Plan:
    stages = tuple(
        PlanStage(
            index=cast("int", s["index"]),
            kind=StageKind(str(s["kind"])),
            section_id=UUID(str(s["section_id"])) if s["section_id"] else None,
            duration_s=cast("int", s["duration_s"]),
            question_ids=tuple(UUID(q) for q in cast("list[str]", s["question_ids"])),
        )
        for s in cast("Sequence[Json]", stored["stages"])
    )
    order = cast("Mapping[str, list[str]]", stored["option_order"])
    return Plan(
        stages=stages,
        option_order={UUID(q): tuple(UUID(o) for o in ids) for q, ids in order.items()},
    )
