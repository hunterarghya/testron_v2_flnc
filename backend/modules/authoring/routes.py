"""Every authoring endpoint: path + method -> controller (ADR-030). No logic here."""

from ninja import Router

from core.http.areas import TeacherArea
from modules.authoring import editor_routes
from modules.authoring.controllers import app_settings, tags
from modules.authoring.dto.app_settings import AppInfoOut, AppSettingsOut
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

# The test editor and library (T-02 to T-05)
router.add_router("", editor_routes.router)
