"""Serve the SPA's shell for app routes such as /admin/tests/123.

The SPA routes in the browser, so a reload or a shared link on any app route must still
get the page that boots it. Real files (/, /_nuxt/*) are served by WhiteNoise before
this view is reached.
"""

from django.conf import settings
from django.http import Http404, HttpRequest, HttpResponse

# `nuxt generate` writes this shell for routes that weren't pre-rendered
SHELL_FILE = "200.html"


def spa_shell(request: HttpRequest) -> HttpResponse:
    shell = settings.SPA_BUILD_DIR / SHELL_FILE
    if not shell.is_file():
        # In `just dev` the SPA runs on Nuxt's own server, not here
        raise Http404("The SPA is not built into this server")
    response = HttpResponse(shell.read_bytes(), content_type="text/html; charset=utf-8")
    # Revalidate every time, so a new release is picked up at once
    response["Cache-Control"] = "no-cache"
    return response
