from enum import StrEnum


class WindowKind(StrEnum):
    """When students may sit an assignment (domain_model.md §3.5 AssignmentWindow)."""

    MANUAL = "MANUAL"
    SCHEDULED = "SCHEDULED"
    DEADLINE = "DEADLINE"
    OPEN = "OPEN"


class PublicationMode(StrEnum):
    MANUAL = "MANUAL"
    AUTO_IMMEDIATE = "AUTO_IMMEDIATE"
    AUTO_DELAYED = "AUTO_DELAYED"


class PublishContent(StrEnum):
    SCORE_ONLY = "SCORE_ONLY"
    ANSWER_REVIEW = "ANSWER_REVIEW"


class LifecycleState(StrEnum):
    """Derived, never stored (domain_model.md §3.5, [D-8])."""

    SCHEDULED = "SCHEDULED"
    WAITING = "WAITING"
    LIVE = "LIVE"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"
