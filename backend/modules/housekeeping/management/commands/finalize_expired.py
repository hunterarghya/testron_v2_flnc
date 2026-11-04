"""`manage.py finalize_expired --all`: end and grade every sitting whose time ran out, now,
instead of when someone next looks (dev_environment_and_deployment.md §8.3). Each ends at
its own deadline instant, exactly as lazy finalization would."""

from argparse import ArgumentParser
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from core.context import system_ctx
from modules.delivery.public import finalize_stale


class Command(BaseCommand):
    help = "End and grade every attempt whose time ran out (normally done lazily)."

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument("--all", action="store_true", help="Every running attempt")

    def handle(self, *args: Any, **options: Any) -> None:
        if not options["all"]:
            raise CommandError("Pass --all to look at every running attempt")
        ended = finalize_stale(system_ctx(), anchored_before=None, limit=None)
        self.stdout.write(f"Ended {ended} attempt(s) whose time had run out.")
