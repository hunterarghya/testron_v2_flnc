"""The exam hall's clock and replies to writes (api_contract.md §3.4 `AttemptClock`,
`SaveAck`, `SubmitResult`). No correctness, marks awarded or score: these types have no such
fields (rule 1, V1 F-03, F-08)."""

from datetime import datetime
from typing import Self
from uuid import UUID

from ninja import Schema
from pydantic import ConfigDict, Field

from modules.delivery.domain.values import AttemptStatus, EndReason, Notice, StageState
from modules.delivery.dto.answers import AnswerIn
from modules.delivery.services.attempt_views import AttemptClockView
from modules.delivery.services.commands.save_response import Saved, SaveRequest
from modules.delivery.services.commands.submit_attempt import Ending


class _Out(Schema):
    model_config = ConfigDict(extra="forbid")


class StageClockOut(_Out):
    index: int
    state: StageState
    deadline_at: datetime | None


class AttemptClockOut(_Out):
    status: AttemptStatus
    end_reason: EndReason | None
    ended_at: datetime | None
    server_now: datetime
    attempt_deadline: datetime
    current_stage_index: int
    stages: list[StageClockOut]
    warning_count: int
    notice: Notice | None

    @classmethod
    def from_view(cls, view: AttemptClockView) -> Self:
        return cls(
            status=view.status,
            end_reason=view.end_reason,
            ended_at=view.ended_at,
            server_now=view.server_now,
            attempt_deadline=view.attempt_deadline,
            current_stage_index=view.current_stage_index,
            stages=[
                StageClockOut(index=s.index, state=s.state, deadline_at=s.deadline_at)
                for s in view.stages
            ],
            warning_count=view.warning_count,
            notice=view.notice,
        )


class StartAttemptIn(Schema):
    model_config = ConfigDict(extra="forbid")
    password: str | None = Field(default=None, max_length=64)


class SaveResponseIn(Schema):
    model_config = ConfigDict(extra="forbid")
    answer: AnswerIn | None
    marked_for_review: bool = False
    client_seq: int = Field(ge=1, le=2**53)

    def to_request(self, question_id: UUID) -> SaveRequest:
        return SaveRequest(
            question_id=question_id,
            answer=None if self.answer is None else self.answer.to_answer(),
            marked_for_review=self.marked_for_review,
            client_seq=self.client_seq,
        )


class SaveAckOut(AttemptClockOut):
    saved_at: datetime
    # False: an older retry, acknowledged and ignored
    applied: bool

    @classmethod
    def from_saved(cls, saved: Saved) -> Self:
        clock = AttemptClockOut.from_view(saved.clock).model_dump()
        return cls(**clock, saved_at=saved.saved_at, applied=saved.applied)


class SubmitResultOut(_Out):
    status: AttemptStatus
    end_reason: EndReason
    ended_at: datetime
    result_available: bool

    @classmethod
    def from_ending(cls, ending: Ending) -> Self:
        return cls(
            status=AttemptStatus.ENDED,
            end_reason=ending.end_reason,
            ended_at=ending.ended_at,
            result_available=ending.result_available,
        )


class NextStageIn(Schema):
    model_config = ConfigDict(extra="forbid")
    # The stage being left: a retry of the same move then changes nothing
    from_stage_index: int = Field(ge=0, le=10_000)
