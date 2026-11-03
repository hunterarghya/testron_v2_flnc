"""What the exam hall receives (api_contract.md §3.4): the clock on every reply, and the whole
attempt on load and resume. Never anything about correctness [V1 F-03, F-08]."""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from modules.assignments import public as assignments
from modules.delivery.domain.answers import Answer, read_answer
from modules.delivery.domain.attempt import AttemptRecord
from modules.delivery.domain.paper import Json, PaperQuestion, PaperView
from modules.delivery.domain.plan import PlanStage
from modules.delivery.domain.stages import deadline_at, stage_state
from modules.delivery.domain.timeline import attempt_deadline
from modules.delivery.domain.values import AttemptStatus, EndReason, Notice, StageKind, StageState
from modules.delivery.repositories.responses import StoredResponse
from modules.delivery.services.live import LiveAttempt


class Titled(Protocol):
    """A SittingTerms or a StudentAssignment: the title and integrity rules the hall shows."""

    @property
    def title(self) -> str: ...
    @property
    def integrity(self) -> assignments.Integrity: ...


@dataclass(frozen=True, slots=True)
class StageClock:
    index: int
    state: StageState
    deadline_at: datetime | None


@dataclass(frozen=True, slots=True)
class AttemptClockView:
    status: AttemptStatus
    end_reason: EndReason | None
    ended_at: datetime | None
    server_now: datetime
    attempt_deadline: datetime
    current_stage_index: int
    stages: tuple[StageClock, ...]
    warning_count: int
    notice: Notice | None


@dataclass(frozen=True, slots=True)
class OptionView:
    id: UUID
    label: str
    content: Json


@dataclass(frozen=True, slots=True)
class QuestionView:
    question: PaperQuestion
    # The display number in the student's order
    number: int
    options: tuple[OptionView, ...]


@dataclass(frozen=True, slots=True)
class StageMeta:
    stage: PlanStage
    title: str | None
    instructions: Json | None


@dataclass(frozen=True, slots=True)
class ResponseView:
    answer: Answer | None
    marked_for_review: bool
    visited: bool
    client_seq: int


@dataclass(frozen=True, slots=True)
class AttemptStateView:
    clock: AttemptClockView
    attempt: AttemptRecord
    title: str
    integrity: assignments.Integrity
    paper: PaperView
    stage_meta: tuple[StageMeta, ...]
    questions: tuple[QuestionView, ...]
    responses: dict[UUID, ResponseView]


def clock_view(live: LiveAttempt, *, now: datetime) -> AttemptClockView:
    attempt, progress = live.attempt, live.progress
    indexes = range(len(progress.stages))
    return AttemptClockView(
        status=attempt.status,
        end_reason=attempt.end_reason,
        ended_at=attempt.ended_at,
        server_now=now,
        attempt_deadline=attempt.ended_at or attempt_deadline(live.clock),
        current_stage_index=progress.current,
        stages=tuple(
            StageClock(
                index=i,
                state=stage_state(live.clock, progress, i, now=now),
                deadline_at=deadline_at(live.clock, progress, i),
            )
            for i in indexes
        ),
        warning_count=attempt.warning_count,
        notice=live.notice,
    )


def state_view(  # keyword-only after the live attempt (CLAUDE.md limits)
    live: LiveAttempt,
    *,
    terms: Titled,
    paper: PaperView,
    stored: dict[UUID, StoredResponse],
    now: datetime,
) -> AttemptStateView:
    clock = clock_view(live, now=now)
    return AttemptStateView(
        clock=clock,
        attempt=live.attempt,
        title=terms.title,
        integrity=terms.integrity,
        paper=paper,
        stage_meta=_stage_meta(live, paper),
        questions=_visible_questions(live, paper, clock),
        responses={
            q: ResponseView(read_answer(r.answer), r.marked_for_review, r.visited, r.client_seq)
            for q, r in stored.items()
        },
    )


def _stage_meta(live: LiveAttempt, paper: PaperView) -> tuple[StageMeta, ...]:
    """Sections show their title and instructions; a whole test or one question shows none."""
    sections = {s.id: s for s in paper.sections}
    meta = []
    for stage in live.attempt.plan.stages:
        section = sections.get(stage.section_id) if stage.section_id else None
        if stage.kind is StageKind.SECTION and section is not None:
            meta.append(StageMeta(stage, section.title, section.instructions))
        else:
            meta.append(StageMeta(stage, None, None))
    return tuple(meta)


def _visible_questions(
    live: LiveAttempt, paper: PaperView, clock: AttemptClockView
) -> tuple[QuestionView, ...]:
    """Only stages the student may answer now: the open one, and those they may return to.
    Rapid fire shows one question at a time [V1 F-11]; an ended attempt shows none."""
    if clock.status is AttemptStatus.ENDED:
        return ()
    plan = live.attempt.plan
    numbers = {q: n for n, q in enumerate(plan.question_ids(), start=1)}
    questions = paper.questions()
    shown = [
        q
        for stage in plan.stages
        if clock.stages[stage.index].state in (StageState.OPEN, StageState.LEFT)
        for q in stage.question_ids
    ]
    return tuple(_question(questions[q], numbers[q], plan.option_order.get(q, ())) for q in shown)


def _question(question: PaperQuestion, number: int, order: tuple[UUID, ...]) -> QuestionView:
    options = tuple(
        OptionView(option_id, chr(ord("A") + position), question.options[option_id])
        for position, option_id in enumerate(order)
    )
    return QuestionView(question=question, number=number, options=options)
