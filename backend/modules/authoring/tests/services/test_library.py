"""list_tests, duplicate/archive/restore, search_questions, import_questions, preview_test
(T-02, T-03 Import, T-05)."""

from collections.abc import Sequence
from datetime import timedelta
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from pytest_django import DjangoAssertNumQueries

from conftest import MakeCtx
from core.clock import FrozenClock
from core.context import Ctx
from core.errors import FieldsInvalid, NotFound
from modules.authoring.domain.library import LibrarySort, TestFilter
from modules.authoring.domain.question_patch import OptionInput
from modules.authoring.domain.settings_patch import SettingsPatch, TimingPatch
from modules.authoring.domain.values import QuestionType, TimingKind
from modules.authoring.models import Test
from modules.authoring.services.commands.archive_test import archive_test
from modules.authoring.services.commands.duplicate_test import duplicate_test
from modules.authoring.services.commands.import_questions import import_questions
from modules.authoring.services.commands.restore_test import restore_test
from modules.authoring.services.commands.update_question import update_question
from modules.authoring.services.commands.update_test import update_test
from modules.authoring.services.queries.list_tests import list_tests
from modules.authoring.services.queries.preview_test import preview_test
from modules.authoring.services.queries.search_questions import search_questions
from modules.authoring.tests.services.editor_helpers import (
    TEACHER,
    add,
    latest,
    new_test,
    question_order,
    words,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def ctx(make_ctx: MakeCtx) -> Ctx:
    return make_ctx(TEACHER)


def titled(
    ctx: Ctx, title: str, *, tags: Sequence[str] = (), text: str = "Which organelle?"
) -> UUID:
    """A test with one complete MCQ, tagged as asked."""
    test_id = new_test(ctx).id
    update_test(ctx, test_id=test_id, revision=1, changes={"title": title})
    question_id = add(ctx, test_id)
    options = [
        OptionInput(None, words("Mitochondria"), True),
        OptionInput(None, words("Golgi"), False),
    ]
    update_question(
        ctx,
        question_id=question_id,
        revision=latest(ctx, test_id).revision,
        changes={"stem": words(text), "options": options, "chapter_tags": list(tags)},
    )
    return test_id


def titles(ctx: Ctx, filters: TestFilter) -> list[str]:
    return [row.title for row in list_tests(ctx, filters=filters, offset=0, limit=50).rows]


def test_the_library_finds_tests_by_title_or_by_their_tags(ctx: Ctx) -> None:
    titled(ctx, "Cell Biology")
    titled(ctx, "Revision 1", tags=["Cell"])
    titled(ctx, "Genetics")

    assert titles(ctx, TestFilter(search="cell", sort=LibrarySort.TITLE)) == [
        "Cell Biology",
        "Revision 1",
    ]
    assert titles(ctx, TestFilter(search="  GENE ")) == ["Genetics"]


def test_rows_show_counts_and_problems(ctx: Ctx) -> None:
    test_id = titled(ctx, "Cell Biology")
    add(ctx, test_id)

    [row] = list_tests(ctx, filters=TestFilter(), offset=0, limit=50).rows

    assert (row.question_count, row.total_marks, row.problem_count, row.timing_kind) == (
        2,
        Decimal(8),
        3,
        TimingKind.TOTAL,
    )


def test_the_library_takes_the_same_queries_for_any_page(
    ctx: Ctx, django_assert_num_queries: DjangoAssertNumQueries
) -> None:
    for title in ("A", "B", "C", "D"):
        titled(ctx, title, tags=["Cell"])

    # tests page + count, then the six document queries
    with django_assert_num_queries(8):
        list_tests(ctx, filters=TestFilter(), offset=0, limit=50)


def test_never_used_tests_come_last_when_sorting_by_use(
    ctx: Ctx, frozen_clock: FrozenClock
) -> None:
    old, recent = titled(ctx, "Old"), titled(ctx, "Recent")
    titled(ctx, "Never")
    Test.objects.filter(pk=old).update(last_assigned_at=frozen_clock.now() - timedelta(days=9))
    Test.objects.filter(pk=recent).update(last_assigned_at=frozen_clock.now())

    assert titles(ctx, TestFilter(sort=LibrarySort.LAST_USED)) == ["Recent", "Old", "Never"]


def test_archive_hides_and_restore_brings_back(ctx: Ctx) -> None:
    test_id = titled(ctx, "Cell Biology")

    first = archive_test(ctx, test_id=test_id)
    again = archive_test(ctx, test_id=test_id)

    assert first.archived_at == again.archived_at is not None
    assert titles(ctx, TestFilter()) == []
    assert titles(ctx, TestFilter(archived=True)) == ["Cell Biology"]
    assert restore_test(ctx, test_id=test_id).archived_at is None
    with pytest.raises(NotFound):
        archive_test(ctx, test_id=uuid4())


def test_a_duplicate_is_an_independent_copy(ctx: Ctx) -> None:
    source = titled(ctx, "Cell Biology", tags=["Cell"])

    copy = duplicate_test(ctx, test_id=source)

    original = latest(ctx, source)
    assert (copy.title, copy.revision, copy.last_assigned_at) == ("Cell Biology (copy)", 1, None)
    assert copy.question(copy.sections[0].questions[0].id).chapter_tags[0].name == "Cell"
    assert copy.problems() == original.problems() == []
    assert copy.sections[0].questions[0].id != original.sections[0].questions[0].id


def test_question_search_finds_text_and_tags_in_other_tests(ctx: Ctx) -> None:
    here = titled(ctx, "Here", text="Mitochondria quiz")
    titled(ctx, "Elsewhere", text="Mitochondria again")
    titled(ctx, "Tagged", tags=["Mitochondrion"], text="Energy")

    found = search_questions(
        ctx, search="mitochond", tag_id=None, exclude_test_id=here, offset=0, limit=20
    )

    assert sorted(row.test_title for row in found.rows) == ["Elsewhere", "Tagged"]
    assert found.total == 2


def test_import_copies_in_at_the_cursor_in_order(ctx: Ctx) -> None:
    source = titled(ctx, "Source")
    second_source = add(ctx, source)
    first_source = latest(ctx, source).sections[0].questions[0].id
    target = new_test(ctx).id
    a, b = add(ctx, target), add(ctx, target)

    result = import_questions(
        ctx,
        test_id=target,
        revision=latest(ctx, target).revision,
        source_question_ids=[second_source, first_source],
        section_id=latest(ctx, target).sections[0].id,
        after_question_id=a,
    )

    assert question_order(ctx, target) == [[a, *result.made, b]]
    assert latest(ctx, target).question(result.made[1]).stem == words("Which organelle?")


@pytest.mark.parametrize("sources", [[], "same twice"])
def test_import_needs_different_questions(ctx: Ctx, sources: object) -> None:
    target = titled(ctx, "Target")
    question = latest(ctx, target).sections[0].questions[0].id
    picked = [question, question] if sources == "same twice" else []

    with pytest.raises(FieldsInvalid):
        import_questions(
            ctx,
            test_id=target,
            revision=1,
            source_question_ids=picked,
            section_id=uuid4(),
            after_question_id=None,
        )


def test_preview_shows_the_paper_and_answers_only_when_asked(ctx: Ctx) -> None:
    test_id = titled(ctx, "Cell Biology")
    numerical = add(ctx, test_id, QuestionType.NUMERICAL)

    hidden = preview_test(ctx, test_id=test_id, show_answers=False)
    shown = preview_test(ctx, test_id=test_id, show_answers=True)

    assert [(q.number, q.type) for q in hidden.questions] == [
        (1, QuestionType.MCQ),
        (2, QuestionType.NUMERICAL),
    ]
    assert [o.label for o in hidden.questions[0].options] == ["A", "B"]
    assert [(s.kind, s.duration_s, len(s.question_ids)) for s in hidden.stages] == [
        ("WHOLE", 3600, 2)
    ]
    assert hidden.answers == ()
    assert [len(a.correct_option_ids) for a in shown.answers] == [1, 0]
    assert shown.answers[1].question_id == numerical


@pytest.mark.parametrize(
    ("timing", "stages"),
    [
        (
            TimingPatch(TimingKind.PER_QUESTION, default_question_s=45),
            [("QUESTION", 45), ("QUESTION", 45)],
        ),
        (TimingPatch(TimingKind.SECTIONED), [("SECTION", 3600)]),
    ],
)
def test_preview_stages_follow_the_timing(
    ctx: Ctx, timing: TimingPatch, stages: list[tuple[str, int]]
) -> None:
    test_id = titled(ctx, "Cell Biology")
    add(ctx, test_id)
    update_test(
        ctx,
        test_id=test_id,
        revision=latest(ctx, test_id).revision,
        changes={"settings": SettingsPatch(timing=timing)},
    )

    paper = preview_test(ctx, test_id=test_id, show_answers=False)

    assert [(s.kind, s.duration_s) for s in paper.stages] == stages
