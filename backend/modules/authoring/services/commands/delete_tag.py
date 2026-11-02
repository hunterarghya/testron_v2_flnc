from uuid import UUID

from django.db import transaction

from core.context import Ctx
from core.errors import NotFound
from modules.authoring.policies import ensure_teacher
from modules.authoring.repositories import tag_usage
from modules.tagging import public as tagging


def delete_tag(ctx: Ctx, *, tag_id: UUID) -> int:
    """Remove a tag from every question, then the tag itself (domain_model.md §3.3 #4, T-18).
    Questions and results stay; past performance for this tag drops out of reports (ADR-017).
    Returns how many questions lost the tag.
    """
    ensure_teacher(ctx.actor)
    with transaction.atomic():
        if tag_id not in tagging.lock_tags([tag_id]):
            raise NotFound("tag")
        removed = tag_usage.remove_references(tag_id)
        tagging.delete(tag_id)
    return removed
