"""What every editor change shares (api_contract.md §2.5): the teacher check, the revision
check and bump, one transaction, and the answer every change returns (the new revision, the
problems and the totals), read from the test as it is after the change."""

from collections.abc import Callable, Collection, Mapping, Sequence
from dataclasses import dataclass
from uuid import UUID

from django.db import transaction

from core.context import Ctx
from core.rich_content import Json, Profile, validate_field
from modules.authoring.domain.document import TestDocumentView, Totals
from modules.authoring.domain.problems import Problem
from modules.authoring.policies import ensure_teacher
from modules.authoring.repositories import tests_table
from modules.authoring.repositories.document import load_document, load_documents
from modules.media import public as media
from modules.tagging import public as tagging


@dataclass(frozen=True, slots=True)
class EditResult[T]:
    revision: int
    problems: list[Problem]
    totals: Totals
    document: TestDocumentView
    # What the change made or touched (a new section's or question's id), if anything
    made: T


def edit[T](ctx: Ctx, test_id: UUID, *, revision: int, change: Callable[[], T]) -> EditResult[T]:
    """Run `change` on the test, if `revision` is still the stored one (E-34)."""
    ensure_teacher(ctx.actor)
    with transaction.atomic():
        new_revision = tests_table.lock_for_edit(test_id, revision=revision, now=ctx.now)
        made = change()
        document = read_document(test_id)
    return EditResult(new_revision, document.problems(), document.totals(), document, made)


def read_document(test_id: UUID) -> TestDocumentView:
    return load_document(test_id, tag_names=tag_names)


def tag_names(tag_ids: Collection[UUID]) -> Mapping[UUID, tuple[str, str]]:
    return {
        tag_id: (tag.kind.value, tag.name) for tag_id, tag in tagging.tags_by_ids(tag_ids).items()
    }


def rich(field: str, raw: object, profile: Profile = Profile.FULL) -> Json:
    """Rich content checked and normalized, images only from our storage (ADR-061)."""
    return validate_field(field, raw, profile, image_src_allowed=media.is_allowed_image_url)


def read_documents(test_ids: Sequence[UUID]) -> dict[UUID, TestDocumentView]:
    return load_documents(test_ids, tag_names=tag_names)


def matching_tag_ids(search: str) -> list[UUID]:
    """Tags whose name contains the search text, so a search finds what is tagged with them."""
    return [tag.id for tag in tagging.list_tags(None, search=tagging.normalize_tag_name(search))]
