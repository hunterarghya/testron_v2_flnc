"""Correcting the answer key (domain_model.md §6.2, G-3): the new entry must fit the paper's
question (database_schema.md §4.3). The paper itself, what students saw, never changes."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import cast
from uuid import UUID

from core.errors import FieldError, FieldsInvalid
from core.text import clean_text_line

Json = Mapping[str, object]
MAX_REASON_LENGTH = 500


@dataclass(frozen=True, slots=True)
class KeyEntry:
    """MCQ/MSQ: the correct options. Numerical: the answer and its ± tolerance."""

    option_ids: tuple[UUID, ...] = ()
    answer: Decimal | None = None
    tolerance: Decimal = Decimal(0)


@dataclass(frozen=True, slots=True)
class Correction:
    """What one correction changed, as kept in answer_key_corrections."""

    question_id: UUID
    before: Json
    after: Json
    reason: str
    version_after: int


def key_entry_json(question: Json, entry: KeyEntry) -> dict[str, object]:
    kind = str(question["type"])
    if kind == "NUMERICAL":
        return _numerical(entry)
    options = {UUID(str(o["id"])) for o in cast("Sequence[Json]", question.get("options", []))}
    picked = list(dict.fromkeys(entry.option_ids))
    too_many = kind == "MCQ" and len(picked) != 1
    if not picked or too_many or not set(picked) <= options or entry.answer is not None:
        message = "Pick one correct option" if kind == "MCQ" else "Pick the correct options"
        raise FieldsInvalid(FieldError("entry", "invalid", message))
    return {"type": kind, "correct_option_ids": [str(o) for o in picked]}


def _numerical(entry: KeyEntry) -> dict[str, object]:
    if entry.answer is None or entry.tolerance < 0 or entry.option_ids:
        raise FieldsInvalid(
            FieldError("entry", "invalid", "Give the answer and a tolerance of 0 or more")
        )
    return {"type": "NUMERICAL", "answer": str(entry.answer), "tolerance": str(entry.tolerance)}


def checked_reason(raw: str) -> str:
    reason = clean_text_line(raw)
    if not reason or len(reason) > MAX_REASON_LENGTH:
        raise FieldsInvalid(
            FieldError("reason", "invalid", f"Say why, in up to {MAX_REASON_LENGTH} characters")
        )
    return reason


def paper_question(paper: Json, question_id: UUID) -> Json | None:
    sections = cast("Sequence[Json]", paper["sections"])
    return next(
        (
            q
            for s in sections
            for q in cast("Sequence[Json]", s["questions"])
            if q["id"] == str(question_id)
        ),
        None,
    )
