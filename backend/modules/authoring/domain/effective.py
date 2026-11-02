"""Effective settings: a question's own override, else the test default (domain_model.md §4.2).
Papers store these resolved numbers, so changing a default later never changes a paper."""

from decimal import Decimal

from modules.authoring.domain.drafts import QuestionDraft, TestDraft, TestSettings
from modules.authoring.domain.values import TimingKind


def effective_marks(question: QuestionDraft, settings: TestSettings) -> Decimal:
    return (
        question.marks_override if question.marks_override is not None else settings.marking.marks
    )


def effective_negative_marks(question: QuestionDraft, settings: TestSettings) -> Decimal:
    if question.negative_marks_override is not None:
        return question.negative_marks_override
    return settings.marking.negative_marks


def effective_time_s(question: QuestionDraft, settings: TestSettings) -> int | None:
    """Seconds for this question; only PER_QUESTION tests time questions one by one."""
    if settings.timing.kind is not TimingKind.PER_QUESTION:
        return None
    if question.time_override_s is not None:
        return question.time_override_s
    return settings.timing.default_question_s


def total_marks(test: TestDraft) -> Decimal:
    return sum((effective_marks(q, test.settings) for q in test.questions()), Decimal(0))


def total_duration_s(test: TestDraft) -> int | None:
    """The whole test's time, or None while a part of it is still unset."""
    timing = test.settings.timing
    if timing.kind is TimingKind.TOTAL:
        return timing.duration_s
    if timing.kind is TimingKind.SECTIONED:
        parts = [section.duration_s for section in test.sections]
    else:
        parts = [effective_time_s(q, test.settings) for q in test.questions()]
    return None if any(part is None for part in parts) else sum(p for p in parts if p is not None)
