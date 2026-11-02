"""Write the API's OpenAPI document to docs/api/openapi.json (ADR-020, `just openapi`).

Runs without secrets (DJANGO_ENV=build), like the image build.

Usage: python scripts/export_openapi.py
"""

import importlib
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BACKEND = REPO / "backend"
OUTPUT = REPO / "docs" / "api" / "openapi.json"


def main() -> int:
    sys.path.insert(0, str(BACKEND))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    os.environ.setdefault("DJANGO_ENV", "build")
    importlib.import_module("django").setup()
    # Imported only after Django is set up: the API module reads settings
    render_openapi = importlib.import_module("config.openapi").render_openapi
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render_openapi(), encoding="utf-8", newline="\n")
    sys.stdout.write(f"Wrote {OUTPUT.relative_to(REPO).as_posix()}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
