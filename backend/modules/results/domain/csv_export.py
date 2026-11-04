"""The gradebook as CSV (domain_model.md §6.6): a byte-order mark so Excel reads Bengali names
correctly, and cells that could start a spreadsheet formula made harmless."""

import csv
import io
from collections.abc import Iterable, Sequence

BOM = "﻿"
# A cell starting with one of these is run as a formula by spreadsheet programs
_FORMULA_START = ("=", "+", "-", "@", "\t", "\r")
# Characters Windows or macOS refuse in a file name
_NOT_IN_NAMES = frozenset('<>:"/\\|?*')
MAX_NAME_LENGTH = 150


def safe_cell(value: object) -> str:
    """Numbers stay numbers ("-1.00"); text that looks like a formula gets a leading quote."""
    text = "" if value is None else str(value)
    if text.startswith(_FORMULA_START) and not _is_number(text):
        return "'" + text
    return text


def _is_number(text: str) -> bool:
    try:
        float(text)
    except ValueError:
        return False
    return True


def to_csv(header: Sequence[str], rows: Iterable[Sequence[object]]) -> str:
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\r\n")
    writer.writerow(header)
    writer.writerows([safe_cell(value) for value in row] for row in rows)
    return BOM + out.getvalue()


def csv_file_name(title: str, date: str) -> str:
    """ "{Title} - {YYYY-MM-DD} - Gradebook.csv", with characters no file system accepts
    removed and the name kept to 150 characters (domain_model.md §6.6)."""
    clean = "".join(c for c in title if c not in _NOT_IN_NAMES and c.isprintable()).strip()
    suffix = f" - {date} - Gradebook.csv"
    return clean[: MAX_NAME_LENGTH - len(suffix)] + suffix
