"""`manage.py run_housekeeping`: one round of cleanup now, without waiting for traffic
(dev_environment_and_deployment.md §8.3). It doesn't move the ten-minute schedule."""

from typing import Any

from django.core.management.base import BaseCommand

from core.context import system_ctx
from modules.housekeeping.public import run_housekeeping


class Command(BaseCommand):
    help = "Run housekeeping now (normally triggered by traffic every 10 minutes)."

    def handle(self, *args: Any, **options: Any) -> None:
        report = run_housekeeping(system_ctx())
        self.stdout.write(
            f"Deleted {report.otps} old codes, {report.rate_limits} rate-limit rows, "
            f"{report.lobby_rows} lobby rows and {report.sessions} expired sessions; "
            f"ended {report.attempts_ended} abandoned attempts."
        )
