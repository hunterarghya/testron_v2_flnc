from uuid import UUID

from django.http import HttpRequest

from core.http.context import ctx_from
from modules.delivery.dto.my_tests import GateStateOut, MyTestsOut
from modules.delivery.services.queries import get_gate_state as gate
from modules.delivery.services.queries import list_my_tests as listing


def list_my_tests(request: HttpRequest) -> MyTestsOut:
    return MyTestsOut.from_tests(listing.list_my_tests(ctx_from(request)))


def get_gate_state(request: HttpRequest, assignment_id: UUID) -> GateStateOut:
    view = gate.get_gate_state(ctx_from(request), assignment_id=assignment_id)
    return GateStateOut.from_view(view)
