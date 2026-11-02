from django.conf import settings
from django.urls import URLPattern, URLResolver, path, re_path

from config.api import api
from config.spa import spa_shell
from core.config import get_settings
from core.http.problems import api_not_found
from modules.media.routes import local_dev_urlpatterns

# The local stand-in for ImageKit, development only (dev_environment_and_deployment.md §1.6)
_LOCAL_MEDIA = settings.DEBUG and get_settings().media_backend == "local"

urlpatterns: list[URLPattern | URLResolver] = [
    path("api/v1/", api.urls),
    re_path(r"^api/", api_not_found),
    *(local_dev_urlpatterns() if _LOCAL_MEDIA else []),
    # Everything else is an SPA route; the API, static and dev media files keep their real 404s
    re_path(r"^(?!api/|static/|dev-media/).*$", spa_shell),
]
