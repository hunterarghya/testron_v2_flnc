from typing import cast
from uuid import UUID

from django.db import transaction

from core.context import Ctx
from core.errors import NotFound
from modules.assignments.domain.answer_key import (
    Correction,
    Json,
    KeyEntry,
    checked_reason,
    key_entry_json,
    paper_question,
)
from modules.assignments.policies import ensure_teacher
from modules.assignments.repositories import papers
from modules.assignments.services.queries.get_paper_content import get_paper_content
from modules.audit import public as audit

CORRECTED_ACTION = "answer_key.corrected"


def correct_answer_key_entry(
    ctx: Ctx, *, assignment_id: UUID, question_id: UUID, entry: KeyEntry, reason: str
) -> int:
    """D-05's first half (domain_model.md §6.2, G-3): one question's answer changes in the
    key, with the reason, audited; the version goes up. Returns the new version. The caller
    regrades in the same transaction (results' correct_answer_key)."""
    ensure_teacher(ctx.actor)
    question = paper_question(get_paper_content(assignment_id), question_id)
    if question is None:
        raise NotFound("question")
    after = key_entry_json(question, entry)
    why = checked_reason(reason)
    with transaction.atomic():
        version, stored = papers.lock_answer_key(assignment_id)
        entries = dict(cast("Json", stored["entries"]))
        correction = Correction(
            question_id=question_id,
            before=cast("Json", entries[str(question_id)]),
            after=after,
            reason=why,
            version_after=version + 1,
        )
        entries[str(question_id)] = after
        papers.save_correction(
            assignment_id,
            entries={**stored, "entries": entries},
            correction=correction,
            now=ctx.now,
        )
        audit.record(
            ctx,
            action=CORRECTED_ACTION,
            target_type="assignment",
            target_id=assignment_id,
            data={"question_id": str(question_id), "version": version + 1, "reason": why},
        )
    return version + 1
