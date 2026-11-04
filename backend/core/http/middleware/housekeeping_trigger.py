"""Housekeeping without a cron (architecture.md §5.6, ADR-083): once a signed-in request has
been answered, ask whether a run is due. The database decides who runs it; this process only
asks once a minute, so most requests cost nothing at all.

The work is named by the HOUSEKEEPING_TRIGGER setting (core imports no module); tests turn
it off so query counts stay exact, and test housekeeping directly."""

import logging
from collections.abc import Callable
from datetime import datetime, timedelta

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.utils.module_loading import import_string

from core import clock
from core.context import Ctx, system_ctx

logger = logging.getLogger(__name__)
ASK_EVERY = timedelta(minutes=1)


class HousekeepingTriggerMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response
        path: str | None = settings.HOUSEKEEPING_TRIGGER
        self._run: Callable[[Ctx], object] | None = import_string(path) if path else None
        self._next_ask_at: datetime | None = None

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        if self._run is not None and request.user.is_authenticated and self._may_ask():
            self._trigger(self._run)
        return response

    def _may_ask(self) -> bool:
        now = clock.now()
        if self._next_ask_at is not None and now < self._next_ask_at:
            return False
        self._next_ask_at = now + ASK_EVERY
        return True

    def _trigger(self, run: Callable[[Ctx], object]) -> None:
        try:
            run(system_ctx())
        # ADR-083: the request was answered already; a failed cleanup is logged, tried later
        except Exception:
            logger.exception("Housekeeping failed")
