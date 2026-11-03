"""Answer key entries (domain_model.md §6.2, E-15) and publishing (§6.4, E-28)."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from core.errors import FieldsInvalid
from modules.assignments.domain.answer_key import (
    KeyEntry,
    checked_reason,
    key_entry_json,
    paper_question,
)
from modules.assignments.domain.publishing import PublicationChanges, edit, publish, unpublish
from modules.assignments.domain.settings import Publication
from modules.assignments.domain.values import PublicationMode, PublishContent

A, B = uuid4(), uuid4()
OPTIONS = [{"id": str(A)}, {"id": str(B)}]
MCQ = {"id": str(uuid4()), "type": "MCQ", "options": OPTIONS}
MSQ = {"id": str(uuid4()), "type": "MSQ", "options": OPTIONS}
NUM = {"id": str(uuid4()), "type": "NUMERICAL"}


@pytest.mark.parametrize(
    ("question", "entry", "expected"),
    [
        (MCQ, KeyEntry(option_ids=(B,)), {"type": "MCQ", "correct_option_ids": [str(B)]}),
        (
            MSQ,
            KeyEntry(option_ids=(A, B, A)),
            {"type": "MSQ", "correct_option_ids": [str(A), str(B)]},
        ),
        (
            NUM,
            KeyEntry(answer=Decimal(46), tolerance=Decimal("0.5")),
            {"type": "NUMERICAL", "answer": "46", "tolerance": "0.5"},
        ),
    ],
)
def test_entries_that_fit(
    question: dict[str, object], entry: KeyEntry, expected: dict[str, object]
) -> None:
    assert key_entry_json(question, entry) == expected


@pytest.mark.parametrize(
    ("question", "entry"),
    [
        # E-15: an MCQ has exactly one answer
        (MCQ, KeyEntry(option_ids=(A, B))),
        (MCQ, KeyEntry()),
        (MSQ, KeyEntry(option_ids=(uuid4(),))),
        (MSQ, KeyEntry(option_ids=(A,), answer=Decimal(1))),
        (NUM, KeyEntry()),
        (NUM, KeyEntry(answer=Decimal(1), tolerance=Decimal(-1))),
        (NUM, KeyEntry(answer=Decimal(1), option_ids=(A,))),
    ],
)
def test_entries_that_dont_fit(question: dict[str, object], entry: KeyEntry) -> None:
    with pytest.raises(FieldsInvalid):
        key_entry_json(question, entry)


def test_a_reason_is_needed_and_a_question_is_found_by_id() -> None:
    assert checked_reason("  Option B was the right one ") == "Option B was the right one"
    with pytest.raises(FieldsInvalid):
        checked_reason("   ")
    paper = {"sections": [{"questions": [MCQ, NUM]}]}
    assert paper_question(paper, uuid4()) is None
    assert paper_question(paper, UUID(str(NUM["id"]))) == NUM


T = datetime(2026, 11, 12, 6, 0, tzinfo=UTC)
DELAYED = Publication(mode=PublicationMode.AUTO_DELAYED, delay_s=3600)


def test_publishing_shows_everything_now_whatever_the_mode() -> None:
    done = publish(
        DELAYED, PublicationChanges(content=PublishContent.ANSWER_REVIEW, show_paper=True), now=T
    )
    assert (done.publication.mode, done.publication.delay_s, done.published_at) == (
        PublicationMode.MANUAL,
        None,
        T,
    )
    assert (done.publication.content, done.publication.show_paper) == (
        PublishContent.ANSWER_REVIEW,
        True,
    )


def test_unpublishing_hides_everything_again_e28() -> None:
    done = unpublish(DELAYED)
    assert (done.publication.mode, done.publication.delay_s, done.published_at) == (
        PublicationMode.MANUAL,
        None,
        None,
    )


def test_a_new_mode_starts_afresh_other_changes_keep_the_publish_time() -> None:
    published = Publication()
    assert edit(published, T, PublicationChanges(show_solutions=True)).published_at == T
    switched = edit(
        published, T, PublicationChanges(mode=PublicationMode.AUTO_DELAYED, delay_s=600)
    )
    assert (switched.publication.delay_s, switched.published_at) == (600, None)
    kept_delay = edit(DELAYED, None, PublicationChanges(show_paper=True))
    assert kept_delay.publication.delay_s == 3600
    with pytest.raises(FieldsInvalid):
        edit(published, T, PublicationChanges(mode=PublicationMode.AUTO_DELAYED))
