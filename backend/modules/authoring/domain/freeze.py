"""Freezing a test into a paper and its answer key (domain_model.md §4.3, database_schema.md
§4.2-4.3). The paper is built from fields that are not answers, so no answer can leak into it;
the answers and solutions go to the key. Settings are resolved: each question carries its own
marks and time, so later changes to defaults never touch a paper."""

from dataclasses import dataclass, field, replace
from typing import cast
from uuid import UUID

from core.errors import FieldError, FieldsInvalid
from core.rich_content import Json
from modules.authoring.domain.document import QuestionView, SectionView, TestDocumentView
from modules.authoring.domain.drafts import Timing
from modules.authoring.domain.effective import (
    effective_marks,
    effective_negative_marks,
    effective_time_s,
    total_duration_s,
)
from modules.authoring.domain.errors import TestHasProblems
from modules.authoring.domain.values import QuestionType, TimingKind

PAPER_VERSION = 1


@dataclass(frozen=True, slots=True)
class TimingOverride:
    """The wizard's "Timing ✎": applies to this assignment's paper only, never to the test."""

    kind: TimingKind
    duration_s: int | None = None
    default_question_s: int | None = None
    section_durations_s: dict[UUID, int] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class FrozenTest:
    paper: Json
    key_entries: Json
    solutions: Json
    timing_kind: TimingKind
    total_duration_s: int


def freeze(document: TestDocumentView, override: TimingOverride | None = None) -> FrozenTest:
    if override is not None:
        document = with_timing_override(document, override)
    problems = document.problems()
    if problems:
        raise TestHasProblems(
            context={"problems": [{"code": p.code, "message": p.message} for p in problems]}
        )
    total = total_duration_s(document.draft())
    if total is None:  # every part is timed once there are no problems
        raise TestHasProblems(context={"problems": []})
    questions = [q for s in document.sections for q in s.questions]
    return FrozenTest(
        paper=_paper(document, total),
        key_entries={"v": PAPER_VERSION, "entries": {str(q.id): _key_entry(q) for q in questions}},
        solutions={str(q.id): q.solution for q in questions if q.solution is not None},
        timing_kind=document.settings.timing.kind,
        total_duration_s=total,
    )


def with_timing_override(document: TestDocumentView, override: TimingOverride) -> TestDocumentView:
    timing = document.settings.timing
    if override.kind is not timing.kind:
        # Changing the kind belongs to the test itself (api_contract.md §2.6)
        raise FieldsInvalid(
            FieldError("timing_override.kind", "invalid", "Use the test's own timing kind")
        )
    if timing.kind is TimingKind.SECTIONED:
        sections = tuple(
            replace(s, duration_s=override.section_durations_s.get(s.id, s.duration_s))
            for s in document.sections
        )
        return replace(document, sections=sections)
    new_timing: Timing = (
        replace(timing, duration_s=override.duration_s or timing.duration_s)
        if timing.kind is TimingKind.TOTAL
        else replace(
            timing, default_question_s=override.default_question_s or timing.default_question_s
        )
    )
    return replace(document, settings=replace(document.settings, timing=new_timing))


def _paper(document: TestDocumentView, total: int) -> Json:
    settings = document.settings
    return {
        "v": PAPER_VERSION,
        "title": document.title,
        "instructions": document.instructions,
        "timing": {
            "kind": settings.timing.kind.value,
            "allow_return": settings.timing.allow_return,
            "total_duration_s": total,
        },
        "shuffle": {"questions": settings.shuffle_questions, "options": settings.shuffle_options},
        "sections": [_section(document, section) for section in document.sections],
    }


def _section(document: TestDocumentView, section: SectionView) -> Json:
    sectioned = document.settings.timing.kind is TimingKind.SECTIONED
    return {
        "id": str(section.id),
        "title": section.title,
        "instructions": section.instructions,
        "duration_s": section.duration_s if sectioned else None,
        "questions": [_question(document, q) for q in section.questions],
    }


def _question(document: TestDocumentView, question: QuestionView) -> Json:
    draft = question.draft()
    frozen: Json = {
        "id": str(question.id),
        "type": question.type.value,
        "stem": question.stem,
        "marks": str(effective_marks(draft, document.settings)),
        "negative_marks": str(effective_negative_marks(draft, document.settings)),
        "time_s": effective_time_s(draft, document.settings),
        "tag_ids": [str(tag.id) for tag in (*question.chapter_tags, *question.topic_tags)],
    }
    if question.type is not QuestionType.NUMERICAL:
        # Only the option's id and content: never whether it is correct
        frozen["options"] = [{"id": str(o.id), "content": o.content} for o in question.options]
    return frozen


def _key_entry(question: QuestionView) -> Json:
    if question.type is QuestionType.NUMERICAL:
        return {
            "type": "NUMERICAL",
            "answer": str(question.numeric_answer),
            "tolerance": str(question.numeric_tolerance),
        }
    correct = [str(o.id) for o in question.options if o.is_correct]
    return {"type": question.type.value, "correct_option_ids": correct}


def paper_questions(paper: Json) -> list[Json]:
    """Every question of a frozen paper, in paper order."""
    sections = cast("list[Json]", paper["sections"])
    return [q for s in sections for q in cast("list[Json]", s["questions"])]
