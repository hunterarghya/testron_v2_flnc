"""Section and question endpoints addressed by their own id (T-03)."""

from uuid import UUID

from django.http import HttpRequest
from ninja import Query

from core.http.context import ctx_from
from modules.authoring.dto.document import QuestionMutationOut, TestMutationOut
from modules.authoring.dto.editing import (
    QuestionPatchIn,
    RevisionIn,
    SectionDeleteIn,
    SectionPatchIn,
)
from modules.authoring.services.commands import delete_question as deleting_question
from modules.authoring.services.commands import delete_section as deleting_section
from modules.authoring.services.commands import duplicate_question as duplicating
from modules.authoring.services.commands import update_question as updating_question
from modules.authoring.services.commands import update_section as updating_section


def update_section(
    request: HttpRequest, section_id: UUID, payload: SectionPatchIn
) -> TestMutationOut:
    result = updating_section.update_section(
        ctx_from(request),
        section_id=section_id,
        revision=payload.revision,
        changes=payload.changes(),
    )
    return TestMutationOut.from_result(result)


def delete_section(
    request: HttpRequest, section_id: UUID, params: Query[SectionDeleteIn]
) -> TestMutationOut:
    choice = deleting_section.WithQuestions(params.questions) if params.questions else None
    result = deleting_section.delete_section(
        ctx_from(request), section_id=section_id, revision=params.revision, questions_choice=choice
    )
    return TestMutationOut.from_result(result)


def update_question(
    request: HttpRequest, question_id: UUID, payload: QuestionPatchIn
) -> QuestionMutationOut:
    result = updating_question.update_question(
        ctx_from(request),
        question_id=question_id,
        revision=payload.revision,
        changes=payload.changes(),
    )
    return QuestionMutationOut.with_question(result)


def delete_question(
    request: HttpRequest, question_id: UUID, params: Query[RevisionIn]
) -> TestMutationOut:
    result = deleting_question.delete_question(
        ctx_from(request), question_id=question_id, revision=params.revision
    )
    return TestMutationOut.from_result(result)


def duplicate_question(
    request: HttpRequest, question_id: UUID, payload: RevisionIn
) -> QuestionMutationOut:
    result = duplicating.duplicate_question(
        ctx_from(request), question_id=question_id, revision=payload.revision
    )
    return QuestionMutationOut.with_question(result)
