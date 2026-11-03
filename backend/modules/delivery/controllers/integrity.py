from uuid import UUID

from django.http import HttpRequest

from core.http.context import ctx_from
from modules.delivery.controllers.attempts import exam_client
from modules.delivery.dto.integrity import IntegrityAckOut, IntegrityReportIn
from modules.delivery.services.commands import report_integrity_event as reporting


def report_integrity_event(
    request: HttpRequest, attempt_id: UUID, event_id: UUID, payload: IntegrityReportIn
) -> IntegrityAckOut:
    ack = reporting.report_integrity_event(
        ctx_from(request),
        attempt_id=attempt_id,
        client_id=exam_client(request),
        report=payload.to_report(event_id),
    )
    return IntegrityAckOut.from_ack(ack)
