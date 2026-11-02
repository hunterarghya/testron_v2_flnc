"""The API contract as committed JSON (ADR-020).

One renderer, used by `scripts/export_openapi.py` (writes the file) and by the
snapshot test (fails CI when the code and the committed file disagree).
"""

import json

from config.api import api


def render_openapi() -> str:
    return json.dumps(api.get_openapi_schema(), indent=2, ensure_ascii=False) + "\n"
