from uuid import UUID

from django.http import HttpRequest
from ninja import Query

from core.http.context import ctx_from
from modules.authoring.dto.tags import (
    TagDeleteOut,
    TagFilterIn,
    TagOut,
    TagRenameIn,
    TagRenameOut,
    TagSuggestIn,
    TagUsageOut,
)
from modules.authoring.services.commands import delete_tag as deleting
from modules.authoring.services.commands import rename_tag as renaming
from modules.authoring.services.queries import list_tags_with_usage as listing
from modules.authoring.services.queries import suggest_tags as suggesting
from modules.tagging.public import TagKind


def suggest_tags(request: HttpRequest, filters: Query[TagSuggestIn]) -> list[TagOut]:
    tags = suggesting.suggest_tags(ctx_from(request), kind=TagKind(filters.kind), typed=filters.q)
    return [TagOut.from_ref(tag) for tag in tags]


def list_tags_with_usage(request: HttpRequest, filters: Query[TagFilterIn]) -> list[TagUsageOut]:
    kind = TagKind(filters.kind) if filters.kind else None
    usages = listing.list_tags_with_usage(ctx_from(request), kind=kind, search=filters.q)
    return [TagUsageOut.from_usage(usage) for usage in usages]


def rename_tag(request: HttpRequest, tag_id: UUID, payload: TagRenameIn) -> TagRenameOut:
    result = renaming.rename_tag(
        ctx_from(request), tag_id=tag_id, name=payload.name, merge=payload.merge
    )
    return TagRenameOut.from_result(result)


def delete_tag(request: HttpRequest, tag_id: UUID) -> TagDeleteOut:
    removed = deleting.delete_tag(ctx_from(request), tag_id=tag_id)
    return TagDeleteOut(removed_from_questions=removed)
