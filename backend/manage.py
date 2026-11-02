#!/usr/bin/env python
import os
import sys

from django.core.management import execute_from_command_line

from core.config import ConfigError


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        execute_from_command_line(sys.argv)
    except ConfigError as error:
        # A plain list of what to fix in .env, not a traceback
        sys.stderr.write(f"{error}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
