"""`manage.py check_config` (`just check-config`): print the effective settings.

Secrets show only "(set)" or "(not set)". An invalid environment never gets this far:
manage.py stops first with the list of problems.
"""

from typing import Any

from django.core.management.base import BaseCommand

from core.config import get_settings
from core.config_report import describe_settings


class Command(BaseCommand):
    help = "Validate the environment and print the effective settings (secrets hidden)."

    def handle(self, *args: Any, **options: Any) -> None:
        rows = describe_settings(get_settings())
        width = max(len(name) for name, _ in rows)
        for name, value in rows:
            self.stdout.write(f"{name.ljust(width)}  {value}")
        self.stdout.write(self.style.SUCCESS("Configuration is valid"))
