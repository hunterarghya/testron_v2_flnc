from uuid import UUID

from django.http import HttpRequest

from core.http.context import ctx_from
from modules.assignments.dto.lobby import ActivationOut, LobbyOut
from modules.assignments.services.commands import activate_assignment as activating
from modules.assignments.services.queries import get_lobby as lobby


def activate_assignment(request: HttpRequest, assignment_id: UUID) -> ActivationOut:
    activation = activating.activate_assignment(ctx_from(request), assignment_id=assignment_id)
    return ActivationOut.from_activation(activation)


def get_lobby(request: HttpRequest, assignment_id: UUID) -> LobbyOut:
    return LobbyOut.from_lobby(lobby.get_lobby(ctx_from(request), assignment_id=assignment_id))
