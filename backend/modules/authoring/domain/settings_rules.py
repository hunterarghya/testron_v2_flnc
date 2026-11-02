"""Rules for marks and integrity settings, shared by the teacher's defaults and every test
(domain_model.md §4.2 TestSettings). Each check returns the problem, or None when fine."""

from decimal import Decimal

from core.errors import FieldError

# numeric(7,2) in the database (database_schema.md §3.4)
MAX_MARKS = Decimal("99999.99")
MARK_DECIMAL_PLACES = 2
GRACE_SECONDS = (0, 60)
MAX_WARNINGS = (1, 20)


def marks_error(field: str, value: Decimal, *, zero_allowed: bool) -> FieldError | None:
    """Marks are positive; negative marks (what a wrong answer costs) may be zero."""
    lowest = "0" if zero_allowed else "more than 0"
    message = f"Use {lowest} to {MAX_MARKS}, with at most {MARK_DECIMAL_PLACES} decimals"
    if not _has_two_decimals_at_most(value) or value > MAX_MARKS:
        return FieldError(field, "invalid", message)
    if value < 0 or (value == 0 and not zero_allowed):
        return FieldError(field, "invalid", message)
    return None


def range_error(field: str, value: int, bounds: tuple[int, int]) -> FieldError | None:
    low, high = bounds
    if low <= value <= high:
        return None
    return FieldError(field, "invalid", f"Use {low} to {high}")


def _has_two_decimals_at_most(value: Decimal) -> bool:
    exponent = value.as_tuple().exponent
    # NaN and infinity have a letter for an exponent
    return isinstance(exponent, int) and exponent >= -MARK_DECIMAL_PLACES
