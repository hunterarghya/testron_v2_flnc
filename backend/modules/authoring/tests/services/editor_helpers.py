"""Shared setup for editor use-case tests: a teacher, a fresh test, and quick edits."""

from uuid import UUID, uuid4

from core.context import Actor, Ctx, Role
from modules.authoring.domain.document import TestDocumentView
from modules.authoring.domain.values import QuestionType
from modules.authoring.services.commands.add_question import add_question
from modules.authoring.services.commands.create_test import create_test
from modules.authoring.services.queries.get_test_document import get_test_document

TEACHER = Actor(user_id=uuid4(), role=Role.TEACHER)


def words(text: str) -> dict[str, object]:
    return {
        "v": 1,
        "type": "doc",
        "content": [{"type": "paragraph", "content": [{"type": "text", "text": text}]}],
    }


def new_test(ctx: Ctx) -> TestDocumentView:
    return create_test(ctx)


def latest(ctx: Ctx, test_id: UUID) -> TestDocumentView:
    return get_test_document(ctx, test_id=test_id)


def add(
    ctx: Ctx, test_id: UUID, kind: QuestionType = QuestionType.MCQ, after: UUID | None = None
) -> UUID:
    """A question at the end of the first section (or right after `after`)."""
    document = latest(ctx, test_id)
    section = document.sections[0]
    last = after or (section.questions[-1].id if section.questions else None)
    result = add_question(
        ctx,
        test_id=test_id,
        revision=document.revision,
        section_id=section.id,
        after_question_id=last,
        question_type=kind,
    )
    return result.made


def question_order(ctx: Ctx, test_id: UUID) -> list[list[UUID]]:
    return [[q.id for q in section.questions] for section in latest(ctx, test_id).sections]
