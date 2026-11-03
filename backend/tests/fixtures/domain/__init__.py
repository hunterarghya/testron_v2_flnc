"""Domain rule tables shared with the product version (testing_strategy.md §3.1): plain JSON,
so both implementations are checked against the same cases."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import cast

Row = dict[str, object]
_HERE = Path(__file__).parent


def load_table(name: str) -> dict[str, object]:
    return cast("dict[str, object]", json.loads((_HERE / f"{name}.json").read_text("utf-8")))


def rows(table: dict[str, object], key: str) -> list[Row]:
    return cast("list[Row]", table[key])


def at(base: datetime, seconds: object) -> datetime | None:
    """A table time: seconds after the base, or None."""
    return None if seconds is None else base + timedelta(seconds=cast("int", seconds))
