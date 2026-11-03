from collections.abc import Sequence
from datetime import datetime
from typing import cast
from uuid import UUID

from core.rich_content import Json
from modules.assignments.domain.answer_key import Correction
from modules.assignments.models import AnswerKey, AnswerKeyCorrection, Paper


def insert_paper(  # keyword-only after the id (CLAUDE.md limits)
    assignment_id: UUID,
    *,
    content: Json,
    content_hash: str,
    key_entries: Json,
    solutions: Json,
    now: datetime,
) -> None:
    """The paper and its answer key, written together (domain_model.md §3.5 #2)."""
    Paper.objects.create(
        assignment_id=assignment_id, content=content, content_hash=content_hash, created_at=now
    )
    AnswerKey.objects.create(
        assignment_id=assignment_id, entries=key_entries, solutions=solutions, updated_at=now
    )


def allow_return(assignment_id: UUID) -> bool:
    """Whether students may go back to earlier questions, as frozen in the paper."""
    found = Paper.objects.filter(pk=assignment_id).values_list(
        "content__timing__allow_return", flat=True
    )
    return bool(found.first())


def contents(assignment_ids: Sequence[UUID]) -> dict[UUID, Json]:
    rows = Paper.objects.filter(pk__in=assignment_ids).values_list("assignment_id", "content")
    return dict(rows)


def content(assignment_id: UUID) -> Json:
    return cast("Json", Paper.objects.values_list("content", flat=True).get(pk=assignment_id))


def answer_key(assignment_id: UUID) -> tuple[int, Json]:
    """The key's version and its entries (database_schema.md §4.3)."""
    version, entries = AnswerKey.objects.values_list("version", "entries").get(pk=assignment_id)
    return version, cast("Json", entries)


def lock_answer_key(assignment_id: UUID) -> tuple[int, Json]:
    """The key and its version, locked: corrections are made one at a time."""
    version, stored = (
        AnswerKey.objects.select_for_update()
        .values_list("version", "entries")
        .get(pk=assignment_id)
    )
    return version, cast("Json", stored)


def save_correction(
    assignment_id: UUID, *, entries: Json, correction: Correction, now: datetime
) -> None:
    """The corrected key and the record of what changed, written together."""
    AnswerKey.objects.filter(pk=assignment_id).update(
        entries=entries, version=correction.version_after, updated_at=now
    )
    AnswerKeyCorrection.objects.create(
        answer_key_id=assignment_id,
        question_id=correction.question_id,
        before=correction.before,
        after=correction.after,
        reason=correction.reason,
        version_after=correction.version_after,
        corrected_at=now,
    )
