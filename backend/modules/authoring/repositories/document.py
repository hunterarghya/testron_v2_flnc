"""Loading whole tests for the editor and the library: five queries however long the tests are
(the tests, their sections, questions, options and question tags), plus one for tag names."""

from collections import defaultdict
from collections.abc import Callable, Collection, Mapping, Sequence
from uuid import UUID

from core.errors import NotFound
from modules.authoring.domain.document import (
    QuestionView,
    SectionView,
    TagLabel,
    TestDocumentView,
)
from modules.authoring.domain.drafts import OptionDraft
from modules.authoring.domain.values import QuestionType
from modules.authoring.models import Option, Question, QuestionTag, Section, Test
from modules.authoring.repositories.tests_table import settings_of

# tag id -> (kind, name), from the tagging module (its table isn't read here)
TagNames = Callable[[Collection[UUID]], Mapping[UUID, tuple[str, str]]]


def load_document(test_id: UUID, *, tag_names: TagNames) -> TestDocumentView:
    found = load_documents([test_id], tag_names=tag_names)
    if test_id not in found:
        raise NotFound("test")
    return found[test_id]


def load_documents(
    test_ids: Sequence[UUID], *, tag_names: TagNames
) -> dict[UUID, TestDocumentView]:
    """Several whole tests in the same six queries (the library's page of tests)."""
    tests = list(Test.objects.filter(pk__in=test_ids))
    questions = Question.objects.filter(test_id__in=test_ids).order_by("position")
    options = _options_by_question(test_ids)
    tags = _tags_by_question(test_ids, tag_names)
    by_section: dict[UUID, list[QuestionView]] = defaultdict(list)
    for question in questions:
        by_section[question.section_id].append(_question(question, options, tags))
    by_test: dict[UUID, list[SectionView]] = defaultdict(list)
    for section in Section.objects.filter(test_id__in=test_ids).order_by("position"):
        by_test[section.test_id].append(_section(section, by_section[section.id]))
    return {test.id: _document(test, by_test[test.id]) for test in tests}


def _document(test: Test, sections: list[SectionView]) -> TestDocumentView:
    return TestDocumentView(
        id=test.id,
        title=test.title,
        instructions=test.instructions,
        settings=settings_of(test),
        revision=test.revision,
        archived_at=test.archived_at,
        last_assigned_at=test.last_assigned_at,
        updated_at=test.updated_at,
        sections=tuple(sections),
    )


def _section(section: Section, questions: list[QuestionView]) -> SectionView:
    return SectionView(
        id=section.id,
        position=section.position,
        title=section.title,
        instructions=section.instructions,
        duration_s=section.duration_s,
        questions=tuple(questions),
    )


def _question(
    question: Question,
    options: Mapping[UUID, list[OptionDraft]],
    tags: Mapping[UUID, dict[str, list[TagLabel]]],
) -> QuestionView:
    labels = tags.get(question.id, {})
    return QuestionView(
        id=question.id,
        section_id=question.section_id,
        position=question.position,
        type=QuestionType(question.type),
        stem=question.stem,
        solution=question.solution,
        marks_override=question.marks_override,
        negative_marks_override=question.negative_marks_override,
        time_override_s=question.time_override_s,
        options=tuple(options.get(question.id, [])),
        numeric_answer=question.numeric_answer,
        numeric_tolerance=question.numeric_tolerance,
        chapter_tags=tuple(labels.get("CHAPTER", [])),
        topic_tags=tuple(labels.get("TOPIC", [])),
    )


def _options_by_question(test_ids: Sequence[UUID]) -> dict[UUID, list[OptionDraft]]:
    found: dict[UUID, list[OptionDraft]] = defaultdict(list)
    rows = Option.objects.filter(question__test_id__in=test_ids).order_by("question_id", "position")
    for option in rows:
        found[option.question_id].append(OptionDraft(option.id, option.content, option.is_correct))
    return found


def _tags_by_question(
    test_ids: Sequence[UUID], tag_names: TagNames
) -> dict[UUID, dict[str, list[TagLabel]]]:
    pairs = QuestionTag.objects.filter(question__test_id__in=test_ids).values_list(
        "question_id", "tag_id"
    )
    return group_tag_labels(list(pairs), tag_names)


def group_tag_labels(
    pairs: Sequence[tuple[UUID, UUID]], tag_names: TagNames
) -> dict[UUID, dict[str, list[TagLabel]]]:
    """(question id, tag id) pairs -> each question's tags by kind, sorted by name."""
    names = tag_names({tag_id for _, tag_id in pairs})
    found: dict[UUID, dict[str, list[TagLabel]]] = defaultdict(lambda: defaultdict(list))
    for question_id, tag_id in pairs:
        kind, name = names[tag_id]
        found[question_id][kind].append(TagLabel(tag_id, name))
    for kinds in found.values():
        for labels in kinds.values():
            labels.sort(key=lambda label: label.name.casefold())
    return found
