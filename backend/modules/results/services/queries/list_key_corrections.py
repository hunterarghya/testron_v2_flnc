from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from core.context import Ctx
from modules.assignments import public as assignments
from modules.results.domain.key_history import EntryText, entry_text, numbered_questions
from modules.results.policies import ensure_teacher


@dataclass(frozen=True, slots=True)
class KeyCorrectionView:
    question_id: UUID
    number: int
    before: EntryText
    after: EntryText
    reason: str
    version: int
    corrected_at: datetime


def list_key_corrections(ctx: Ctx, *, assignment_id: UUID) -> list[KeyCorrectionView]:
    """T-11: every answer key correction, newest first, with what it changed and why
    (domain_model.md §6.2; security.md T-05). Teacher only. Three queries."""
    ensure_teacher(ctx.actor)
    frame = assignments.get_results_frame(ctx, assignment_id=assignment_id)
    numbered = numbered_questions(frame.paper)
    views = []
    for record in assignments.list_answer_key_corrections(assignment_id):
        fix = record.correction
        number, question = numbered[str(fix.question_id)]
        views.append(
            KeyCorrectionView(
                question_id=fix.question_id,
                number=number,
                before=entry_text(question, fix.before),
                after=entry_text(question, fix.after),
                reason=fix.reason,
                version=fix.version_after,
                corrected_at=record.corrected_at,
            )
        )
    return views
