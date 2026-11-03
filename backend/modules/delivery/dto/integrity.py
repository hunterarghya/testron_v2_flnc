"""Leaving the test, on the wire (api_contract.md §3.4 `IntegrityReport`, `IntegrityAck`)."""

from datetime import datetime
from typing import Literal, Self
from uuid import UUID

from ninja import Schema
from pydantic import ConfigDict

from modules.delivery.domain.integrity import WarningAction
from modules.delivery.domain.values import IntegrityKind
from modules.delivery.dto.attempt_clock import AttemptClockOut
from modules.delivery.services.commands.report_integrity_event import IntegrityAck, IntegrityReport


class IntegrityReportIn(Schema):
    model_config = ConfigDict(extra="forbid")
    # DEVICE_CHANGED is the server's own record, never the browser's
    kind: Literal["FULLSCREEN_EXIT", "TAB_HIDDEN", "WINDOW_BLUR"]
    left_at: datetime
    beyond_grace: bool
    returned_at: datetime | None = None

    def to_report(self, event_id: UUID) -> IntegrityReport:
        return IntegrityReport(
            event_id=event_id,
            kind=IntegrityKind(self.kind),
            left_at=self.left_at,
            beyond_grace=self.beyond_grace,
            returned_at=self.returned_at,
        )


class IntegrityAckOut(AttemptClockOut):
    counted: bool
    max_warnings: int
    action: WarningAction

    @classmethod
    def from_ack(cls, ack: IntegrityAck) -> Self:
        clock = AttemptClockOut.from_view(ack.clock).model_dump()
        return cls(**clock, counted=ack.counted, max_warnings=ack.max_warnings, action=ack.action)
