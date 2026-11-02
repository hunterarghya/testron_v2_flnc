"""Which tags to suggest as the teacher types (domain_model.md §4.1, T-03 tag pills)."""

from collections.abc import Mapping, Sequence
from uuid import UUID

from modules.tagging.domain.names import TagRef, normalize_tag_name

MAX_SUGGESTIONS = 8


def rank_suggestions(tags: Sequence[TagRef], typed: str, usage: Mapping[UUID, int]) -> list[TagRef]:
    """Tags whose name starts with what was typed, then those that merely contain it; each
    group by how often the tag is used, then by name. At most 8. "ce" → Cell, Cerebral system.
    """
    query = normalize_tag_name(typed)
    matching = [tag for tag in tags if query in normalize_tag_name(tag.name)]
    matching.sort(
        key=lambda tag: (
            not normalize_tag_name(tag.name).startswith(query),
            -usage.get(tag.id, 0),
            normalize_tag_name(tag.name),
        )
    )
    return matching[:MAX_SUGGESTIONS]
