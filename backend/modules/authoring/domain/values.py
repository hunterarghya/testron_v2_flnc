from enum import StrEnum


class IntegrityAction(StrEnum):
    """What happens when a student runs out of integrity warnings (domain_model.md §4.2)."""

    AUTO_SUBMIT = "AUTO_SUBMIT"
    DISQUALIFY = "DISQUALIFY"
