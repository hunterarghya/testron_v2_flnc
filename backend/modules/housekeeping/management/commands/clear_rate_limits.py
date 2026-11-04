"""`manage.py clear_rate_limits --key <pattern>`: unblock someone locked out by a rate limit
(dev_environment_and_deployment.md §8.3), e.g. `--key "login:email:rina@example.com"` or
`--key "login:ip:*"`. `*` matches anything; nothing else is special."""

from argparse import ArgumentParser
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from core import rate_limit


class Command(BaseCommand):
    help = "Remove rate-limit counters whose key matches the pattern (* matches anything)."

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument("--key", required=True, help='A key, or a pattern like "login:ip:*"')

    def handle(self, *args: Any, **options: Any) -> None:
        pattern: str = options["key"].strip()
        if not pattern or set(pattern) == {"*"}:
            raise CommandError("Give a key or a narrower pattern; '*' alone would clear them all")
        cleared = rate_limit.clear(pattern)
        self.stdout.write(f"Cleared {cleared} rate-limit counter(s) matching {pattern!r}.")
