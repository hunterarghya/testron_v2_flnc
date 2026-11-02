from collections.abc import Sequence

from core.context import Ctx
from modules.tagging.domain.names import TagKind, TagRef, display_tag_name, normalize_tag_name
from modules.tagging.repositories import tags


def ensure_tags_by_name(ctx: Ctx, *, kind: TagKind, names: Sequence[str]) -> list[TagRef]:
    """The tags for these names, creating any that don't exist yet (domain_model.md §3.3 #2,
    §4.1): tags are born when the teacher types a new pill in the editor.

    'Cell' and 'cell' are one tag; a new tag keeps the name as first typed. Safe when two
    saves create the same tag at once. Returned in the order given, each tag once. Runs in
    the caller's transaction (the question save).
    """
    wanted: dict[str, str] = {}
    for raw in names:
        wanted.setdefault(normalize_tag_name(raw), display_tag_name(raw))
    tags.insert_missing(kind, wanted, now=ctx.now)
    found = tags.tags_by_normalized_names(kind, list(wanted))
    return [found[normalized] for normalized in wanted]
