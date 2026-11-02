from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from django.db import IntegrityError, transaction

from core.db.locking import for_update
from core.errors import NotFound
from modules.tagging.domain.names import TagKind, TagRef
from modules.tagging.models import Tag


def _ref(tag: Tag) -> TagRef:
    return TagRef(id=tag.id, kind=TagKind(tag.kind), name=tag.name)


def get_tag(tag_id: UUID) -> TagRef:
    tag = Tag.objects.filter(pk=tag_id).first()
    if tag is None:
        raise NotFound("tag")
    return _ref(tag)


def find_tag_id(kind: TagKind, normalized_name: str) -> UUID | None:
    return (
        Tag.objects.filter(kind=kind, normalized_name=normalized_name)
        .values_list("id", flat=True)
        .first()
    )


def lock_tags(tag_ids: Sequence[UUID]) -> dict[UUID, TagRef]:
    """Lock in id order, so two merges in opposite directions can't deadlock (§5.1)."""
    tags = for_update(Tag.objects.filter(pk__in=tag_ids).order_by("id"))
    return {tag.id: _ref(tag) for tag in tags}


def tags_by_normalized_names(kind: TagKind, normalized_names: Sequence[str]) -> dict[str, TagRef]:
    tags = Tag.objects.filter(kind=kind, normalized_name__in=normalized_names)
    return {tag.normalized_name: _ref(tag) for tag in tags}


def insert_missing(kind: TagKind, names: dict[str, str], *, now: datetime) -> None:
    """Create tags for the normalized names given ({normalized: display}); existing ones,
    including ones another request just created, are left as they are."""
    Tag.objects.bulk_create(
        [
            Tag(kind=kind, name=display, normalized_name=normalized, created_at=now)
            for normalized, display in names.items()
        ],
        ignore_conflicts=True,
    )


def rename(tag_id: UUID, *, name: str, normalized_name: str) -> bool:
    """False when another tag of the same kind already has that normalized name."""
    try:
        with transaction.atomic():
            Tag.objects.filter(pk=tag_id).update(name=name, normalized_name=normalized_name)
    except IntegrityError:
        return False
    return True


def delete(tag_id: UUID) -> None:
    Tag.objects.filter(pk=tag_id).delete()


def list_tags(kind: TagKind | None, *, search: str | None) -> list[TagRef]:
    tags = Tag.objects.all()
    if kind is not None:
        tags = tags.filter(kind=kind)
    if search:
        tags = tags.filter(normalized_name__contains=search)
    return [_ref(tag) for tag in tags.order_by("kind", "normalized_name")]
