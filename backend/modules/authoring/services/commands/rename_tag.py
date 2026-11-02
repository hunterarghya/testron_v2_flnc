from dataclasses import dataclass
from uuid import UUID

from django.db import transaction

from core.context import Ctx
from core.errors import NotFound
from modules.authoring.domain.errors import TagExists
from modules.authoring.policies import ensure_teacher
from modules.authoring.repositories import tag_usage
from modules.tagging import public as tagging


@dataclass(frozen=True, slots=True)
class RenameTagResult:
    tag: tagging.TagRef
    # The tag that disappeared into `tag`, when the rename was a merge
    merged_from: UUID | None


def rename_tag(ctx: Ctx, *, tag_id: UUID, name: str, merge: bool) -> RenameTagResult:
    """Rename a tag everywhere at once: questions, past results, performance (§3.3 #3, T-18).

    Renaming onto another tag's name ("Genetcs" → "Genetics") is a **merge**: refused as
    `tag_exists` until the teacher confirms with `merge`, then every question moves to the
    existing tag and the old one is removed, in one transaction. Both rows are locked in id
    order, so merges can't deadlock or lose a reference (database_schema.md §5.1).
    """
    ensure_teacher(ctx.actor)
    display = tagging.display_tag_name(name)
    with transaction.atomic():
        kind = tagging.get_tag(tag_id).kind
        target_id = tagging.find_tag_id(kind, tagging.normalize_tag_name(name))
        locked = tagging.lock_tags([tag_id] + ([target_id] if target_id else []))
        if tag_id not in locked:
            raise NotFound("tag")
        if target_id is None or target_id == tag_id:
            return _rename(tag_id, display)
        return _merge(tag_id, locked[target_id], merge=merge)


def _rename(tag_id: UUID, display: str) -> RenameTagResult:
    if not tagging.rename(
        tag_id, name=display, normalized_name=tagging.normalize_tag_name(display)
    ):
        # Another rename took the name a moment ago
        raise TagExists()
    return RenameTagResult(tag=tagging.get_tag(tag_id), merged_from=None)


def _merge(tag_id: UUID, target: tagging.TagRef, *, merge: bool) -> RenameTagResult:
    if not merge:
        question_count = tag_usage.question_counts([target.id])[target.id]
        raise TagExists(
            context={
                "target": {
                    "id": str(target.id),
                    "name": target.name,
                    "question_count": question_count,
                }
            }
        )
    tag_usage.move_references(tag_id, target.id)
    tagging.delete(tag_id)
    return RenameTagResult(tag=target, merged_from=tag_id)
