"""Delivery's vocabulary (domain_model.md §3.6, §7.3-7.4)."""

from enum import StrEnum


class AttemptStatus(StrEnum):
    IN_PROGRESS = "IN_PROGRESS"
    ENDED = "ENDED"


class EndReason(StrEnum):
    SUBMITTED = "SUBMITTED"
    TIMED_OUT = "TIMED_OUT"
    AUTO_SUBMITTED = "AUTO_SUBMITTED"
    DISQUALIFIED = "DISQUALIFIED"
    FORCE_SUBMITTED = "FORCE_SUBMITTED"
    ENDED_BY_TEACHER = "ENDED_BY_TEACHER"


class StageKind(StrEnum):
    """TOTAL has one WHOLE stage; SECTIONED one per section; PER_QUESTION one per question."""

    WHOLE = "WHOLE"
    SECTION = "SECTION"
    QUESTION = "QUESTION"


class StageState(StrEnum):
    NOT_ENTERED = "NOT_ENTERED"
    OPEN = "OPEN"
    LEFT = "LEFT"
    CLOSED = "CLOSED"
    MISSED = "MISSED"


class IntegrityKind(StrEnum):
    FULLSCREEN_EXIT = "FULLSCREEN_EXIT"
    TAB_HIDDEN = "TAB_HIDDEN"
    WINDOW_BLUR = "WINDOW_BLUR"
    # Recorded by the server on a takeover, never counted as a warning (§5.9)
    DEVICE_CHANGED = "DEVICE_CHANGED"


class Notice(StrEnum):
    """What the hall tells the student with a toast (api_contract.md §3.4)."""

    TIME_EXTENDED = "TIME_EXTENDED"
    ENDED_BY_TEACHER = "ENDED_BY_TEACHER"
    STAGE_ADVANCED = "STAGE_ADVANCED"
