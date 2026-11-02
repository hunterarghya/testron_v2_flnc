from enum import StrEnum


class IntegrityAction(StrEnum):
    """What happens when a student runs out of integrity warnings (domain_model.md §4.2)."""

    AUTO_SUBMIT = "AUTO_SUBMIT"
    DISQUALIFY = "DISQUALIFY"


class TimingKind(StrEnum):
    """How a test is timed (domain_model.md §4.2)."""

    TOTAL = "TOTAL"
    PER_QUESTION = "PER_QUESTION"
    SECTIONED = "SECTIONED"


class QuestionType(StrEnum):
    MCQ = "MCQ"
    MSQ = "MSQ"
    NUMERICAL = "NUMERICAL"
