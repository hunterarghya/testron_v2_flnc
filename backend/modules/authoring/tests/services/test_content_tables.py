"""The database rules of the authoring tables (database_schema.md §3.4)."""

import pytest
from django.db import IntegrityError, connection, transaction

from conftest import MakeCtx
from modules.authoring.models import Question, QuestionTag, Section
from modules.tagging.public import TagKind, delete, ensure_tags_by_name
from tests.factories.authoring import make_question, make_section, make_test

pytestmark = pytest.mark.django_db


def check_deferred_now() -> None:
    """Deferred uniques are checked at commit; tests never commit, so ask for the check now."""
    with connection.cursor() as cursor:
        cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")


def test_positions_can_swap_inside_one_transaction() -> None:
    test = make_test()
    first, second = make_section(test, 0), make_section(test, 1)

    Section.objects.filter(pk=first.pk).update(position=1)
    Section.objects.filter(pk=second.pk).update(position=0)
    check_deferred_now()

    assert list(test.sections.order_by("position").values_list("id", flat=True)) == [
        second.id,
        first.id,
    ]


def test_two_sections_cannot_keep_one_position() -> None:
    test = make_test()
    make_section(test, 0)

    # Inside a block that is rolled back, so the duplicate doesn't outlive the test
    with transaction.atomic():
        make_section(test, 0)
        with pytest.raises(IntegrityError):
            check_deferred_now()
        transaction.set_rollback(True)


def test_only_numerical_questions_have_an_answer_value() -> None:
    question = make_question(make_section(make_test()))

    with pytest.raises(IntegrityError), transaction.atomic():
        Question.objects.filter(pk=question.pk).update(numeric_answer=5)


def test_timing_columns_match_the_timing_kind() -> None:
    with pytest.raises(IntegrityError), transaction.atomic():
        make_test(timing_kind="PER_QUESTION", duration_s=3600)


def test_deleting_a_tag_untags_its_questions(make_ctx: MakeCtx) -> None:
    tag = ensure_tags_by_name(make_ctx(), kind=TagKind.CHAPTER, names=["Cell"])[0]
    make_question(make_section(make_test()), tag_ids=[tag.id])

    delete(tag.id)

    assert not QuestionTag.objects.exists()
