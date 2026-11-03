"""A student's answer and whether it fits the question (domain_model.md §3.6 #4,
database_schema.md §4.5). Correctness is never decided here: delivery has no answer key."""

import re
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import cast
from uuid import UUID

from modules.delivery.domain.errors import AnswerInvalid
from modules.delivery.domain.paper import PaperQuestion

ANSWER_VERSION = 1
# ASCII digits only: "4e2", full-width digits and "12,5" are refused (E-18)
NUMERIC_VALUE = re.compile(r"-?[0-9]{1,8}(\.[0-9]{1,6})?")


@dataclass(frozen=True, slots=True)
class ChoiceAnswer:
    option_ids: frozenset[UUID]


@dataclass(frozen=True, slots=True)
class NumericAnswer:
    # A decimal string, kept as typed
    value: str


Answer = ChoiceAnswer | NumericAnswer


def ensure_answer_fits(answer: Answer | None, question: PaperQuestion) -> None:
    """None (cleared) always fits."""
    if answer is None:
        return
    if isinstance(answer, NumericAnswer):
        if question.type != "NUMERICAL" or not NUMERIC_VALUE.fullmatch(answer.value):
            raise AnswerInvalid()
        return
    if question.type == "NUMERICAL" or not answer.option_ids <= set(question.option_ids):
        raise AnswerInvalid()
    if question.type == "MCQ" and len(answer.option_ids) > 1:
        raise AnswerInvalid("A single-answer question takes one option.")


def answer_json(answer: Answer | None) -> dict[str, object] | None:
    if answer is None:
        return None
    if isinstance(answer, NumericAnswer):
        return {"v": ANSWER_VERSION, "kind": "NUMERIC", "value": answer.value}
    ids = sorted(str(option_id) for option_id in answer.option_ids)
    return {"v": ANSWER_VERSION, "kind": "CHOICE", "option_ids": ids}


def read_answer(stored: Mapping[str, object] | None) -> Answer | None:
    if stored is None:
        return None
    if stored["kind"] == "NUMERIC":
        return NumericAnswer(str(stored["value"]))
    return ChoiceAnswer(frozenset(UUID(o) for o in cast("list[str]", stored["option_ids"])))


def answer_value(answer: Answer | None) -> frozenset[UUID] | Decimal | None:
    """What grading marks: the options picked, the number given, or nothing."""
    if isinstance(answer, NumericAnswer):
        return Decimal(answer.value)
    return None if answer is None else answer.option_ids
