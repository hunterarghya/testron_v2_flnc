from dataclasses import dataclass
from typing import cast
from uuid import UUID

from core.rich_content import Json
from modules.assignments.repositories import papers


@dataclass(frozen=True, slots=True)
class AnswerKeyView:
    version: int
    # question id -> {"type", "correct_option_ids"} or {"type", "answer", "tolerance"}
    entries: Json


def get_answer_key(assignment_id: UUID) -> AnswerKeyView:
    """For grading only (domain_model.md §3.6 #7: delivery never reads it). No policy: no
    route reaches this, only grading's use cases."""
    version, stored = papers.answer_key(assignment_id)
    return AnswerKeyView(version=version, entries=cast("Json", stored["entries"]))
