"""The Test Library (T-02) and question search for Import (T-03): which rows, in what order.
Searching by text also matches the tags on a test's questions ("cell" finds every test with a
question tagged Cell)."""

from collections.abc import Collection, Sequence
from uuid import UUID

from django.db.models import Exists, F, OuterRef, Q, QuerySet
from django.db.models.expressions import OrderBy

from modules.authoring.domain.document import TagLabel
from modules.authoring.domain.library import LibrarySort, QuestionSearchRow, TestFilter
from modules.authoring.domain.values import QuestionType
from modules.authoring.models import Question, QuestionTag, Test
from modules.authoring.repositories.document import TagNames, group_tag_labels


def list_test_ids(
    filters: TestFilter, *, search_tag_ids: Collection[UUID], offset: int, limit: int
) -> tuple[list[UUID], int]:
    tests = Test.objects.filter(archived_at__isnull=not filters.archived)
    if filters.search:
        tests = tests.filter(Q(title__icontains=filters.search) | _has_tag(search_tag_ids))
    if filters.tag_id:
        tests = tests.filter(_has_tag([filters.tag_id]))
    ordered = tests.order_by(*_ordering(filters.sort), "id")
    return list(ordered.values_list("id", flat=True)[offset : offset + limit]), tests.count()


def _has_tag(tag_ids: Collection[UUID]) -> Exists:
    return Exists(QuestionTag.objects.filter(question__test_id=OuterRef("pk"), tag_id__in=tag_ids))


def _ordering(sort: LibrarySort) -> tuple[str | OrderBy, ...]:
    if sort is LibrarySort.TITLE:
        return ("title",)
    if sort is LibrarySort.LAST_USED:
        # Never-used tests last
        return (F("last_assigned_at").desc(nulls_last=True),)
    return ("-updated_at",)


def search_question_ids(
    *,
    search: str | None,
    search_tag_ids: Collection[UUID],
    tag_id: UUID | None,
    exclude_test_id: UUID | None,
    offset: int,
    limit: int,
) -> tuple[list[UUID], int]:
    found: QuerySet[Question] = Question.objects.all()
    if search:
        tagged = Exists(
            QuestionTag.objects.filter(question_id=OuterRef("pk"), tag_id__in=search_tag_ids)
        )
        found = found.filter(Q(search_text__icontains=search) | tagged)
    if tag_id:
        found = found.filter(
            Exists(QuestionTag.objects.filter(question_id=OuterRef("pk"), tag_id=tag_id))
        )
    if exclude_test_id:
        found = found.exclude(test_id=exclude_test_id)
    ordered = found.order_by("-updated_at", "id")
    return list(ordered.values_list("id", flat=True)[offset : offset + limit]), found.count()


def question_rows(question_ids: Sequence[UUID], *, tag_names: TagNames) -> list[QuestionSearchRow]:
    """The found questions with their test's title and tags, in `question_ids` order."""
    found = Question.objects.select_related("test").in_bulk(question_ids)
    pairs = QuestionTag.objects.filter(question_id__in=question_ids).values_list(
        "question_id", "tag_id"
    )
    labels = group_tag_labels(list(pairs), tag_names)
    return [_search_row(found[qid], labels[qid]) for qid in question_ids if qid in found]


def _search_row(question: Question, labels: dict[str, list[TagLabel]]) -> QuestionSearchRow:
    return QuestionSearchRow(
        id=question.id,
        test_id=question.test_id,
        test_title=question.test.title,
        type=QuestionType(question.type),
        stem=question.stem,
        chapter_tags=tuple(labels.get("CHAPTER", [])),
        topic_tags=tuple(labels.get("TOPIC", [])),
    )
