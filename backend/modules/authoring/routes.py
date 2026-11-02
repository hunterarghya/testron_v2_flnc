"""Every authoring endpoint: path + method -> controller (ADR-030). No logic here."""

from ninja import Router

from core.http.areas import TeacherArea
from modules.authoring.controllers import app_settings, editor, tags, tests
from modules.authoring.dto.app_settings import AppInfoOut, AppSettingsOut
from modules.authoring.dto.document import (
    QuestionMutationOut,
    SectionMutationOut,
    TestDocumentOut,
    TestMutationOut,
)
from modules.authoring.dto.tags import TagDeleteOut, TagOut, TagRenameOut, TagUsageOut

router = Router(tags=["authoring"], auth=TeacherArea())

# Branding for every screen's header, logged in or not (api_contract.md §2.1)
router.add_api_operation(
    "/app",
    ["GET"],
    app_settings.get_app_info,
    response={200: AppInfoOut},
    auth=None,
    summary="The coaching centre's name and logo",
)

# The teacher's settings page, T-19
router.add_api_operation(
    "/admin/settings",
    ["GET"],
    app_settings.get_app_settings,
    response={200: AppSettingsOut},
    summary="The teacher's defaults for new tests and the branding",
)
router.add_api_operation(
    "/admin/settings",
    ["PATCH"],
    app_settings.update_app_settings,
    response={200: AppSettingsOut},
    summary="Change some of the defaults or the branding",
)

# Tags (T-18, T-03 pills). Served here because they also touch question references (ADR-059).
router.add_api_operation(
    "/admin/tags/suggest",
    ["GET"],
    tags.suggest_tags,
    response={200: list[TagOut]},
    summary="Tags matching what is typed (at most 8)",
)
router.add_api_operation(
    "/admin/tags",
    ["GET"],
    tags.list_tags_with_usage,
    response={200: list[TagUsageOut]},
    summary="Every tag with its question and test counts",
)
router.add_api_operation(
    "/admin/tags/{tag_id}",
    ["PATCH"],
    tags.rename_tag,
    response={200: TagRenameOut},
    summary="Rename a tag (merging into an existing one when confirmed)",
)
router.add_api_operation(
    "/admin/tags/{tag_id}",
    ["DELETE"],
    tags.delete_tag,
    response={200: TagDeleteOut},
    summary="Remove a tag from every question, then delete it",
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
