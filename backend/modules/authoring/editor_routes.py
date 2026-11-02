"""The test editor and library endpoints (T-02 to T-05), mounted by `routes.py` into the one
authoring router (kept apart only for the file size limit). No logic here."""

from ninja import Router

from core.http.areas import TeacherArea
from core.http.pagination import Page
from modules.authoring.controllers import editor, library, tests
from modules.authoring.dto.document import (
    QuestionMutationOut,
    SectionMutationOut,
    TestDocumentOut,
    TestMutationOut,
)
from modules.authoring.dto.library import ImportOut, QuestionSearchRowOut, TestRowOut
from modules.authoring.dto.preview import PreviewOut

router = Router(tags=["authoring"], auth=TeacherArea())

# Before /admin/questions/{question_id}, which would otherwise take "search" as an id
router.add_api_operation(
    "/admin/questions/search",
    ["GET"],
    library.search_questions,
    response={200: Page[QuestionSearchRowOut]},
    summary="Questions from other tests, to import",
)

# The test editor (T-02 New test, T-03, T-04). Every change carries the revision it was based on.
router.add_api_operation(
    "/admin/tests",
    ["POST"],
    tests.create_test,
    response={201: TestDocumentOut},
    summary="A new untitled draft with the teacher's defaults",
)
router.add_api_operation(
    "/admin/tests/{test_id}",
    ["GET"],
    tests.get_test_document,
    response={200: TestDocumentOut},
    summary="The whole test for the editor, with problems and totals",
)
router.add_api_operation(
    "/admin/tests/{test_id}",
    ["PATCH"],
    tests.update_test,
    response={200: TestMutationOut},
    summary="Change the title, instructions or settings",
)
router.add_api_operation(
    "/admin/tests/{test_id}/structure",
    ["PUT"],
    tests.restructure_test,
    response={200: TestMutationOut},
    summary="Reorder sections and questions",
)
router.add_api_operation(
    "/admin/tests/{test_id}/sections",
    ["POST"],
    tests.add_section,
    response={200: SectionMutationOut},
    summary="Add a section after another (sectioned tests)",
)
router.add_api_operation(
    "/admin/tests/{test_id}/questions",
    ["POST"],
    tests.add_question,
    response={200: QuestionMutationOut},
    summary="Add an empty question after another",
)
router.add_api_operation(
    "/admin/sections/{section_id}",
    ["PATCH"],
    editor.update_section,
    response={200: TestMutationOut},
    summary="Change a section's title, instructions or duration",
)
router.add_api_operation(
    "/admin/sections/{section_id}",
    ["DELETE"],
    editor.delete_section,
    response={200: TestMutationOut},
    summary="Remove a section, moving or deleting its questions",
)
router.add_api_operation(
    "/admin/questions/{question_id}",
    ["PATCH"],
    editor.update_question,
    response={200: QuestionMutationOut},
    summary="Save one question as a whole (autosave)",
)
router.add_api_operation(
    "/admin/questions/{question_id}",
    ["DELETE"],
    editor.delete_question,
    response={200: TestMutationOut},
    summary="Remove a question",
)
router.add_api_operation(
    "/admin/questions/{question_id}/duplicate",
    ["POST"],
    editor.duplicate_question,
    response={200: QuestionMutationOut},
    summary="Copy a question right after itself",
)

# The Test Library, import and preview (T-02, T-03 Import, T-05)
router.add_api_operation(
    "/admin/tests",
    ["GET"],
    library.list_tests,
    response={200: Page[TestRowOut]},
    summary="The Test Library: search, filter by tag, sort",
)
router.add_api_operation(
    "/admin/tests/{test_id}/duplicate",
    ["POST"],
    library.duplicate_test,
    response={201: TestDocumentOut},
    summary="Copy a whole test as a new draft",
)
router.add_api_operation(
    "/admin/tests/{test_id}/archive",
    ["POST"],
    library.archive_test,
    response={200: TestRowOut},
    summary="Hide a test from the library",
)
router.add_api_operation(
    "/admin/tests/{test_id}/restore",
    ["POST"],
    library.restore_test,
    response={200: TestRowOut},
    summary="Bring an archived test back",
)
router.add_api_operation(
    "/admin/tests/{test_id}/preview",
    ["GET"],
    library.preview_test,
    response={200: PreviewOut},
    summary="The test as a student sees it",
)
router.add_api_operation(
    "/admin/tests/{test_id}/questions/import",
    ["POST"],
    library.import_questions,
    response={200: ImportOut},
    summary="Copy questions from other tests in at the cursor",
)
