"""Every authoring endpoint: path + method -> controller (ADR-030). No logic here."""

from ninja import Router

from core.http.areas import TeacherArea
from modules.authoring.controllers import tags
from modules.authoring.dto.tags import TagDeleteOut, TagOut, TagRenameOut, TagUsageOut

router = Router(tags=["authoring"], auth=TeacherArea())

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
