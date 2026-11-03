"""A student's answer on the wire (api_contract.md §3.4 `Answer`): picked options, or a
numerical value as a decimal string. The shape rules are the domain's (answer_invalid)."""

from typing import Annotated, Literal
from uuid import UUID

from ninja import Schema
from pydantic import ConfigDict, Field

from modules.delivery.domain.answers import Answer, ChoiceAnswer, NumericAnswer

# More options than any question has; the domain checks they belong to the question
MAX_OPTIONS = 26


class _Strict(Schema):
    model_config = ConfigDict(extra="forbid")


class ChoiceAnswerIn(_Strict):
    v: Literal[1] = 1
    kind: Literal["CHOICE"]
    option_ids: list[UUID] = Field(max_length=MAX_OPTIONS)

    def to_answer(self) -> Answer:
        return ChoiceAnswer(frozenset(self.option_ids))


class NumericAnswerIn(_Strict):
    v: Literal[1] = 1
    kind: Literal["NUMERIC"]
    value: str = Field(max_length=32)

    def to_answer(self) -> Answer:
        return NumericAnswer(self.value)


AnswerIn = Annotated[ChoiceAnswerIn | NumericAnswerIn, Field(discriminator="kind")]


class ChoiceAnswerOut(_Strict):
    v: Literal[1] = 1
    kind: Literal["CHOICE"] = "CHOICE"
    option_ids: list[UUID]


class NumericAnswerOut(_Strict):
    v: Literal[1] = 1
    kind: Literal["NUMERIC"] = "NUMERIC"
    value: str


AnswerOut = Annotated[ChoiceAnswerOut | NumericAnswerOut, Field(discriminator="kind")]


def answer_out(answer: Answer | None) -> ChoiceAnswerOut | NumericAnswerOut | None:
    if answer is None:
        return None
    if isinstance(answer, NumericAnswer):
        return NumericAnswerOut(value=answer.value)
    return ChoiceAnswerOut(option_ids=sorted(answer.option_ids, key=str))
