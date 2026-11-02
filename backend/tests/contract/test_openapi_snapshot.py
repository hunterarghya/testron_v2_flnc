from pathlib import Path

from config.openapi import render_openapi

SNAPSHOT = Path(__file__).resolve().parents[3] / "docs" / "api" / "openapi.json"


def test_openapi_snapshot_matches_the_code() -> None:
    """A contract change must be committed with the code (`just openapi`, ADR-020)."""
    assert SNAPSHOT.read_text(encoding="utf-8") == render_openapi()
