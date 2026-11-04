"""One attempt's result as P-09 and T-12 show it (domain_model.md §6.4): always the score,
time, sections and tags; the rest only as the publication options allow, or everything in
the teacher's view. Built here for get_my_result, get_answer_sheet and list_answer_sheets."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import cast
from uuid import UUID

from modules.assignments import public as assignments
from modules.delivery import public as delivery
from modules.grading import public as grading
from modules.results.domain.breakdown import (
    PartScore,
    attempt_label,
    section_scores,
    section_titles,
    tag_scores,
    time_taken_s,
)
from modules.results.domain.ranking import Placing, Stats
from modules.tagging import public as tagging

Json = Mapping[str, object]


@dataclass(frozen=True, slots=True)
class Shown:
    """Which optional parts a result carries."""

    questions: bool = False
    review: bool = False
    solutions: bool = False
    rank: bool = False

    @classmethod
    def everything(cls) -> "Shown":
        return cls(questions=True, review=True, solutions=True, rank=True)

    @classmethod
    def by_options(cls, publication: assignments.Publication) -> "Shown":
        review = publication.content.value == "ANSWER_REVIEW"
        return cls(
            questions=publication.show_paper or review,
            review=review,
            solutions=review and publication.show_solutions,
            rank=publication.show_rank_and_stats,
        )


@dataclass(frozen=True, slots=True)
class TagPart:
    tag: tagging.TagRef
    score: Decimal
    max: Decimal


@dataclass(frozen=True, slots=True)
class ResultQuestion:
    number: int
    question: Json
    option_order: tuple[UUID, ...]
    your_answer: Json | None = None
    correct: Json | None = None
    grade: grading.QuestionGrade | None = None
    solution: Json | None = None


@dataclass(frozen=True, slots=True)
class ResultView:
    attempt: delivery.AttemptRow
    label: str
    time_taken_s: int
    sections: list[PartScore]
    tags: list[TagPart]
    placing: Placing | None
    stats: Stats | None
    questions: list[ResultQuestion] | None


@dataclass(frozen=True, slots=True)
class Ranked:
    placing: Placing | None
    stats: Stats | None


def result_view(  # keyword-only after the attempt (CLAUDE.md limits)
    attempt: delivery.AttemptRow,
    *,
    frame: assignments.ResultsFrame,
    grades: Sequence[grading.QuestionGrade],
    ranked: Ranked,
    shown: Shown,
) -> ResultView:
    title = frame.row.record.settings.title
    return ResultView(
        attempt=attempt,
        label=attempt_label(title, attempt.started_at, attempt.take_number),
        time_taken_s=time_taken_s(attempt.started_at, attempt.ended_at),
        sections=section_scores(grades, section_titles(frame.paper)),
        tags=_tags(grades),
        placing=ranked.placing if shown.rank else None,
        stats=ranked.stats if shown.rank else None,
        questions=_questions(attempt, frame, grades, shown) if shown.questions else None,
    )


def _tags(grades: Sequence[grading.QuestionGrade]) -> list[TagPart]:
    totals = tag_scores(grades)
    names = tagging.tags_by_ids(list(totals))
    return [TagPart(names[t], s, m) for t, (s, m) in totals.items() if t in names]


def _questions(
    attempt: delivery.AttemptRow,
    frame: assignments.ResultsFrame,
    grades: Sequence[grading.QuestionGrade],
    shown: Shown,
) -> list[ResultQuestion]:
    """In the student's order, with their option order (P-09 "as they saw it")."""
    plan = delivery.plan_of(attempt.id)
    by_id = {
        UUID(str(q["id"])): q
        for s in cast("Sequence[Json]", frame.paper["sections"])
        for q in cast("Sequence[Json]", s["questions"])
    }
    keyed = assignments.get_keyed_paper(attempt.assignment_id) if shown.review else None
    answers = delivery.answers_of([attempt.id])[attempt.id] if shown.review else {}
    graded = {g.question_id: g for g in grades}
    return [
        ResultQuestion(
            number=n,
            question=by_id[q],
            option_order=plan.option_order.get(q, ()),
            your_answer=answers.get(q) if shown.review else None,
            correct=_entry(keyed, q) if keyed else None,
            grade=graded.get(q) if shown.review else None,
            solution=_solution(keyed, q) if keyed and shown.solutions else None,
        )
        for n, q in enumerate(plan.question_ids(), start=1)
    ]


def _entry(keyed: assignments.KeyedPaper, question_id: UUID) -> Json:
    return cast("Json", cast("Json", keyed.entries["entries"])[str(question_id)])


def _solution(keyed: assignments.KeyedPaper, question_id: UUID) -> Json | None:
    return cast("Json | None", keyed.solutions.get(str(question_id)))
