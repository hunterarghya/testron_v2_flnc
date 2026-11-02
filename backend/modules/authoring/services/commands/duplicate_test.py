from uuid import UUID

from django.db import transaction

from core.context import Ctx
from modules.authoring.domain.document import TestDocumentView
from modules.authoring.models.test import MAX_TITLE_LENGTH
from modules.authoring.policies import ensure_teacher
from modules.authoring.repositories import questions, sections, tests_table
from modules.authoring.services.editing import read_document

COPY_SUFFIX = " (copy)"


def duplicate_test(ctx: Ctx, *, test_id: UUID) -> TestDocumentView:
    """A new draft with everything the test has: settings, sections, questions, options and
    tags (T-02 `⋯` Duplicate). The copy has never been assigned and starts at revision 1."""
    ensure_teacher(ctx.actor)
    source = read_document(test_id)
    with transaction.atomic():
        copy_id = tests_table.insert_test(
            title=copy_title(source.title), settings=source.settings, now=ctx.now
        )
        tests_table.update_test(copy_id, {"instructions": source.instructions})
        targets = []
        for section in source.sections:
            section_id = sections.insert_section(
                copy_id,
                position=section.position,
                title=section.title,
                duration_s=section.duration_s,
                instructions=section.instructions,
            )
            targets += [
                questions.CopyTo(q.id, copy_id, section_id, q.position) for q in section.questions
            ]
        questions.copy_questions(targets, now=ctx.now)
    return read_document(copy_id)


def copy_title(title: str) -> str:
    """ "Cell Biology (copy)", shortened if needed to stay within the title limit."""
    return title[: MAX_TITLE_LENGTH - len(COPY_SUFFIX)] + COPY_SUFFIX
