"""Saving one question as a whole (api_contract.md §2.5, editor save model): which changes are
allowed, what a type switch does, and how the sent option list replaces the stored one."""

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import TypedDict
from uuid import UUID

from core.errors import FieldError, FieldsInvalid
from core.rich_content import Json
from modules.authoring.domain.settings_patch import QUESTION_SECONDS
from modules.authoring.domain.settings_rules import marks_error, range_error
from modules.authoring.domain.values import QuestionType

MAX_OPTIONS = 10
MAX_TAGS_PER_KIND = 20


@dataclass(frozen=True, slots=True)
class OptionInput:
    # Present: keep that option (same id); absent: a new option
    id: UUID | None
    content: Json
    is_correct: bool


class QuestionChanges(TypedDict, total=False):
    """Only the fields sent. A sent None clears an override, the solution or the answer."""

    type: QuestionType
    stem: Json
    solution: Json | None
    marks_override: Decimal | None
    negative_marks_override: Decimal | None
    time_override_s: int | None
    numeric_answer: Decimal | None
    numeric_tolerance: Decimal
    options: list[OptionInput]
    chapter_tags: list[str]
    topic_tags: list[str]


def ensure_changes_valid(final_type: QuestionType, changes: QuestionChanges) -> None:
    """Every broken field at once. Rich content is checked separately (core.rich_content)."""
    errors = [*_number_errors(changes), *_shape_errors(final_type, changes)]
    if errors:
        raise FieldsInvalid(*errors)


def _number_errors(changes: QuestionChanges) -> list[FieldError]:
    found: list[FieldError | None] = []
    marks, negative = changes.get("marks_override"), changes.get("negative_marks_override")
    if marks is not None:
        found.append(marks_error("marks_override", marks, zero_allowed=False))
    if negative is not None:
        found.append(marks_error("negative_marks_override", negative, zero_allowed=True))
    seconds = changes.get("time_override_s")
    if seconds is not None:
        found.append(range_error("time_override_s", seconds, QUESTION_SECONDS))
    if changes.get("numeric_tolerance", Decimal(0)) < 0:
        found.append(FieldError("numeric_tolerance", "invalid", "Use 0 or more"))
    return [error for error in found if error is not None]


def _shape_errors(final_type: QuestionType, changes: QuestionChanges) -> list[FieldError]:
    found = []
    options = changes.get("options", [])
    if final_type is QuestionType.NUMERICAL and options:
        found.append(FieldError("options", "invalid", "A numerical question has no options"))
    if len(options) > MAX_OPTIONS:
        found.append(FieldError("options", "invalid", f"Use at most {MAX_OPTIONS} options"))
    numeric_sent = changes.get("numeric_answer") is not None or changes.get("numeric_tolerance")
    if final_type is not QuestionType.NUMERICAL and numeric_sent:
        found.append(
            FieldError("numeric_answer", "invalid", "Only a numerical question has an answer value")
        )
    tag_lists = {
        "chapter_tags": changes.get("chapter_tags", []),
        "topic_tags": changes.get("topic_tags", []),
    }
    for kind, names in tag_lists.items():
        if len(names) > MAX_TAGS_PER_KIND:
            found.append(FieldError(kind, "invalid", f"Use at most {MAX_TAGS_PER_KIND} tags"))
    return found


@dataclass(frozen=True, slots=True)
class OptionsPlan:
    # (id or None for a new option, position, content, is_correct), in the new order
    rows: list[tuple[UUID | None, int, Json, bool]]
    removed: set[UUID]


def plan_options(existing_ids: set[UUID], sent: Sequence[OptionInput]) -> OptionsPlan:
    """Sent options replace the stored list; a sent id must be one of this question's, once."""
    seen: set[UUID] = set()
    for index, option in enumerate(sent):
        if option.id is None:
            continue
        if option.id not in existing_ids or option.id in seen:
            raise FieldsInvalid(
                FieldError(f"options.{index}.id", "invalid", "Not an option of this question")
            )
        seen.add(option.id)
    rows = [(o.id, position, o.content, o.is_correct) for position, o in enumerate(sent)]
    return OptionsPlan(rows=rows, removed=existing_ids - seen)
