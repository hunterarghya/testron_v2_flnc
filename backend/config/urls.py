from django.urls import URLPattern, URLResolver, path, re_path

from config.api import api
from config.spa import spa_shell
from core.http.problems import api_not_found

urlpatterns: list[URLPattern | URLResolver] = [
    path("api/v1/", api.urls),
    re_path(r"^api/", api_not_found),
    # Everything else is an SPA route; the API and static files keep their real 404s
    re_path(r"^(?!api/|static/).*$", spa_shell),
]
