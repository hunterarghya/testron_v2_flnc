from django.http import HttpRequest

from core.http.context import ctx_from
from modules.identity.dto.health import HealthOut
from modules.identity.services.queries import get_health as health_query


def get_health(request: HttpRequest, deep: bool = False) -> HealthOut:
    return HealthOut.from_view(health_query.get_health(ctx_from(request), deep=deep))
