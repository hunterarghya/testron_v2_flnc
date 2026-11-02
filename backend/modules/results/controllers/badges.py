from django.http import HttpRequest

from core.http.context import ctx_from
from modules.results.dto.badges import BadgesOut
from modules.results.services.queries import get_badges as badges


def get_badges(request: HttpRequest) -> BadgesOut:
    return BadgesOut.from_badges(badges.get_badges(ctx_from(request)))
