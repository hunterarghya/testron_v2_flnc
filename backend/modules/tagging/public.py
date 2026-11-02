"""The only names other modules may import from tagging (R-08).

The T-18 use cases (rename with merge, delete, usage counts, suggestions) live in authoring,
because they also move or count the question references it owns (ADR-059); they build on
these.
"""

from modules.tagging.domain.names import (
    TagKind,
    TagRef,
    display_tag_name,
    normalize_tag_name,
)
from modules.tagging.domain.suggestions import MAX_SUGGESTIONS, rank_suggestions
from modules.tagging.repositories.tags import (
    delete,
    find_tag_id,
    get_tag,
    list_tags,
    lock_tags,
    rename,
    tags_by_ids,
)
from modules.tagging.services.commands.ensure_tags_by_name import ensure_tags_by_name

__all__ = [
    "MAX_SUGGESTIONS",
    "TagKind",
    "TagRef",
    "delete",
    "display_tag_name",
    "ensure_tags_by_name",
    "find_tag_id",
    "get_tag",
    "list_tags",
    "lock_tags",
    "normalize_tag_name",
    "rank_suggestions",
    "rename",
    "tags_by_ids",
]
