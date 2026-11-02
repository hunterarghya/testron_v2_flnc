"""The `tests` rows: settings as columns, and the revision every edit is checked against."""

from datetime import datetime
from uuid import UUID

from core.db.locking import for_update
from core.errors import NotFound
from modules.authoring.domain.drafts import Integrity, Marking, TestSettings, Timing
from modules.authoring.domain.errors import TestChangedElsewhere
from modules.authoring.domain.values import IntegrityAction, TimingKind
from modules.authoring.models import Question, Section, Test


def settings_of(test: Test) -> TestSettings:
    return TestSettings(
        timing=Timing(
            kind=TimingKind(test.timing_kind),
            duration_s=test.duration_s,
            default_question_s=test.default_question_s,
            allow_return=test.allow_return,
        ),
        shuffle_questions=test.shuffle_questions,
        shuffle_options=test.shuffle_options,
        marking=Marking(marks=test.marks, negative_marks=test.negative_marks),
        integrity=Integrity(
            grace_s=test.integrity_grace_s,
            max_warnings=test.integrity_max_warnings,
            action=IntegrityAction(test.integrity_action),
        ),
    )


def settings_columns(settings: TestSettings) -> dict[str, object]:
    timing = settings.timing
    return {
        "timing_kind": timing.kind.value,
        "duration_s": timing.duration_s,
        "default_question_s": timing.default_question_s,
        "allow_return": timing.allow_return,
        "shuffle_questions": settings.shuffle_questions,
        "shuffle_options": settings.shuffle_options,
        "marks": settings.marking.marks,
        "negative_marks": settings.marking.negative_marks,
        "integrity_grace_s": settings.integrity.grace_s,
        "integrity_max_warnings": settings.integrity.max_warnings,
        "integrity_action": settings.integrity.action.value,
    }


def insert_test(*, title: str, settings: TestSettings, now: datetime) -> UUID:
    test = Test.objects.create(
        title=title, created_at=now, updated_at=now, **settings_columns(settings)
    )
    return test.id


def lock_for_edit(test_id: UUID, *, revision: int, now: datetime) -> int:
    """Lock the test for this edit and move it to the next revision. A save based on an
    older revision is refused: another tab changed the test meanwhile (E-34)."""
    stored = for_update(Test.objects.filter(pk=test_id)).values_list("revision", flat=True).first()
    if stored is None:
        raise NotFound("test")
    if stored != revision:
        raise TestChangedElsewhere(context={"revision": stored})
    Test.objects.filter(pk=test_id).update(revision=stored + 1, updated_at=now)
    return stored + 1


def update_test(test_id: UUID, values: dict[str, object]) -> None:
    Test.objects.filter(pk=test_id).update(**values)


def owning_test_of_section(section_id: UUID) -> UUID:
    found = Section.objects.filter(pk=section_id).values_list("test_id", flat=True).first()
    if found is None:
        raise NotFound("section")
    return found


def owning_test_of_question(question_id: UUID) -> UUID:
    found = Question.objects.filter(pk=question_id).values_list("test_id", flat=True).first()
    if found is None:
        raise NotFound("question")
    return found


def set_archived_at(test_id: UUID, archived_at: datetime | None) -> None:
    if not Test.objects.filter(pk=test_id).exists():
        raise NotFound("test")
    Test.objects.filter(pk=test_id).update(archived_at=archived_at)
