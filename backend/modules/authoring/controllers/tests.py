from uuid import UUID

from django.http import HttpRequest
from ninja import Status

from core.http.context import ctx_from
from modules.authoring.domain.values import QuestionType
from modules.authoring.dto.document import (
    QuestionMutationOut,
    SectionMutationOut,
    TestDocumentOut,
    TestMutationOut,
)
from modules.authoring.dto.editing import QuestionIn, SectionIn, StructureIn, TestPatchIn
from modules.authoring.services.commands import add_question as adding_question
from modules.authoring.services.commands import add_section as adding_section
from modules.authoring.services.commands import create_test as creating
from modules.authoring.services.commands import restructure_test as restructuring
from modules.authoring.services.commands import update_test as updating
from modules.authoring.services.queries import get_test_document as reading


def create_test(request: HttpRequest) -> Status[TestDocumentOut]:
    return Status(201, TestDocumentOut.from_view(creating.create_test(ctx_from(request))))


def get_test_document(request: HttpRequest, test_id: UUID) -> TestDocumentOut:
    return TestDocumentOut.from_view(reading.get_test_document(ctx_from(request), test_id=test_id))


def update_test(request: HttpRequest, test_id: UUID, payload: TestPatchIn) -> TestMutationOut:
    result = updating.update_test(
        ctx_from(request), test_id=test_id, revision=payload.revision, changes=payload.changes()
    )
    return TestMutationOut.from_result(result)


def restructure_test(request: HttpRequest, test_id: UUID, payload: StructureIn) -> TestMutationOut:
    result = restructuring.restructure_test(
        ctx_from(request), test_id=test_id, revision=payload.revision, wanted=payload.layout()
    )
    return TestMutationOut.from_result(result)


def add_section(request: HttpRequest, test_id: UUID, payload: SectionIn) -> SectionMutationOut:
    result = adding_section.add_section(
        ctx_from(request),
        test_id=test_id,
        revision=payload.revision,
        after_section_id=payload.after_section_id,
        title=payload.title,
        duration_s=payload.duration_s,
    )
    return SectionMutationOut.with_section(result)


def add_question(request: HttpRequest, test_id: UUID, payload: QuestionIn) -> QuestionMutationOut:
    result = adding_question.add_question(
        ctx_from(request),
        test_id=test_id,
        revision=payload.revision,
        section_id=payload.section_id,
        after_question_id=payload.after_question_id,
        question_type=QuestionType(payload.type),
    )
    return QuestionMutationOut.with_question(result)
