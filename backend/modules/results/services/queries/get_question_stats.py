from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import cast
from uuid import UUID

from core.context import Ctx
from modules.assignments import public as assignments
from modules.delivery import public as delivery
from modules.grading import public as grading
from modules.results.domain.question_stats import QuestionStat, question_stats
from modules.results.policies import ensure_teacher
from modules.results.services.standings import counts
from modules.tagging import public as tagging

Json = Mapping[str, object]


@dataclass(frozen=True, slots=True)
class QuestionStatView:
    number: int
    question: Json
    stat: QuestionStat
    tags: list[tagging.TagRef]


def get_question_stats(ctx: Ctx, *, assignment_id: UUID) -> list[QuestionStatView]:
    """T-11 Questions: per question, in paper order, over the counted attempts: how many
    answered, got it right or partly right, and the wrong option chosen most. Clicking one
    opens the key correction (D-05). A fixed number of queries."""
    ensure_teacher(ctx.actor)
    keyed = assignments.get_keyed_paper(assignment_id)
    counted = [a.id for a in delivery.rows_of(assignment_id) if counts(a)]
    grades = grading.grades_of(counted)
    answers = delivery.answers_of(counted)
    outcomes = [(g.question_id, g.outcome.value) for rows in grades.values() for g in rows]
    picks = [
        (q, [UUID(o) for o in cast("list[str]", answer["option_ids"])])
        for by_question in answers.values()
        for q, answer in by_question.items()
        if answer and answer.get("kind") == "CHOICE"
    ]
    stats = question_stats(outcomes, picks, cast("Json", keyed.entries["entries"]))
    questions = [
        q
        for s in cast("Sequence[Json]", keyed.paper["sections"])
        for q in cast("Sequence[Json]", s["questions"])
    ]
    tags = tagging.tags_by_ids(
        {UUID(t) for q in questions for t in cast("list[str]", q["tag_ids"])}
    )
    empty = QuestionStat(UUID(int=0), 0, 0, 0, None, 0)
    return [
        QuestionStatView(
            number=n,
            question=q,
            stat=stats.get(UUID(str(q["id"])), empty),
            tags=[tags[UUID(t)] for t in cast("list[str]", q["tag_ids"]) if UUID(t) in tags],
        )
        for n, q in enumerate(questions, start=1)
    ]
