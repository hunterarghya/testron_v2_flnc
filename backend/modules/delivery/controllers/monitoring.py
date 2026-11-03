from uuid import UUID

from django.http import HttpRequest
from ninja import Query

from core.http.context import ctx_from
from modules.delivery.dto.monitor import (
    AttemptSummaryOut,
    EndedOut,
    EndForEveryoneIn,
    IntegrityEventOut,
    MonitorFilterIn,
    MonitorOut,
)
from modules.delivery.services.commands import end_for_everyone as ending
from modules.delivery.services.commands import force_submit_attempt as forcing
from modules.delivery.services.queries import get_monitor as monitoring
from modules.delivery.services.queries import list_integrity_events as events


def get_monitor(
    request: HttpRequest, assignment_id: UUID, query: Query[MonitorFilterIn]
) -> MonitorOut:
    monitor = monitoring.get_monitor(
        ctx_from(request), assignment_id=assignment_id, chosen=query.filter
    )
    return MonitorOut.from_monitor(monitor)


def end_for_everyone(
    request: HttpRequest, assignment_id: UUID, payload: EndForEveryoneIn
) -> EndedOut:
    result = ending.end_for_everyone(
        ctx_from(request), assignment_id=assignment_id, confirm=payload.confirm
    )
    return EndedOut.from_result(result)


def force_submit_attempt(request: HttpRequest, attempt_id: UUID) -> AttemptSummaryOut:
    row = forcing.force_submit_attempt(ctx_from(request), attempt_id=attempt_id)
    return AttemptSummaryOut.from_row(row)


def list_integrity_events(request: HttpRequest, attempt_id: UUID) -> list[IntegrityEventOut]:
    found = events.list_integrity_events(ctx_from(request), attempt_id=attempt_id)
    return [IntegrityEventOut.from_row(event) for event in found]
