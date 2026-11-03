"""Why a student can't start, answer or move on (api_contract.md §1). Each names its condition."""

from datetime import datetime

from core.errors import Conflict, DomainError, Invalid


class NotOpenYet(Conflict):
    code = "not_open_yet"
    title = "This test hasn't opened yet"

    def __init__(self, *, opens_at: datetime | None, server_now: datetime) -> None:
        super().__init__(context={"opens_at": opens_at, "server_now": server_now})


class WaitingForTeacher(Conflict):
    code = "waiting_for_teacher"
    title = "Your teacher hasn't started the test yet"

    def __init__(self, *, server_now: datetime) -> None:
        super().__init__(context={"server_now": server_now})


class EntryClosed(Conflict):
    code = "entry_closed"
    title = "Entry to this test has closed"

    def __init__(self, *, closed_at: datetime | None) -> None:
        super().__init__(context={"closed_at": closed_at} if closed_at else None)


class NoAttemptsLeft(Conflict):
    code = "no_attempts_left"
    title = "You have used every attempt for this test"


class PasswordRequired(DomainError):
    code = "password_required"
    status = 403
    title = "Enter the password from your teacher"


class PasswordIncorrect(DomainError):
    code = "password_incorrect"
    status = 403
    title = "That password isn't right"

    def __init__(self, *, tries_left: int) -> None:
        super().__init__(context={"tries_left": tries_left})


class AttemptEnded(Conflict):
    """No write reaches an ended attempt (domain_model.md §3.6 #6)."""

    code = "attempt_ended"
    title = "This test has ended"

    def __init__(self, *, ended_at: datetime | None, end_reason: str | None) -> None:
        super().__init__(context={"ended_at": ended_at, "end_reason": end_reason})


class AttemptTakenOver(Conflict):
    """Only the latest device writes (domain_model.md §5.9)."""

    code = "attempt_taken_over"
    title = "This test was opened on another device"


class StageClosed(Conflict):
    code = "stage_closed"
    title = "This part of the test has closed"

    def __init__(self, stage_index: int) -> None:
        super().__init__(context={"stage_index": stage_index})


class QuestionNotInStage(Invalid):
    code = "question_not_in_stage"
    title = "This question isn't open now"


class AnswerInvalid(Invalid):
    code = "answer_invalid"
    title = "This answer doesn't fit the question"


class StageNavigationInvalid(Conflict):
    """Moving on from a stage that isn't the current one, or back where returning isn't allowed."""

    code = "stage_navigation_invalid"
    title = "You can't move to that part of the test now"
