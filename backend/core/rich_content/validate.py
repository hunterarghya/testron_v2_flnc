"""`validate`: check rich content against the allow-list, then store it in one normal form
(editor_content_spec.md §3). Validation is rejection, not repair: bad content means a client
bug, so it's refused with the path to the first problem, and logged."""

import json
import logging

from core.errors import FieldError, FieldsInvalid
from core.rich_content.blocks import blocks
from core.rich_content.normalize import trim_empty_paragraphs
from core.rich_content.schema import MAX_BYTES, VERSION, Profile
from core.rich_content.walk import (
    At,
    ImageSrcCheck,
    Json,
    RichContentInvalid,
    Walk,
    as_object,
    fail,
)

logger = logging.getLogger(__name__)
_DOC_KEYS = frozenset({"v", "type", "content"})
EMPTY_DOC: Json = {"v": VERSION, "type": "doc", "content": []}


def validate(raw: object, profile: Profile, *, image_src_allowed: ImageSrcCheck) -> Json:
    """The normalized document, or RichContentInvalid naming the first broken rule.

    `image_src_allowed` says whether an image address may be used (media's check; core
    can't import modules).
    """
    root = At("", depth=0)
    doc = as_object(raw, root)
    _ensure_size(doc, profile)
    unknown = sorted(set(doc) - _DOC_KEYS)
    if unknown:
        raise fail(root.key(unknown[0]), "is not allowed")
    if doc.get("v") != VERSION:
        raise fail(root.key("v"), f"must be {VERSION}")
    if doc.get("type") != "doc":
        raise fail(root.key("type"), "must be doc")
    walk = Walk(profile, image_src_allowed)
    content = blocks(walk, doc.get("content"), root.key("content"))
    return {"v": VERSION, "type": "doc", "content": trim_empty_paragraphs(content)}


def validate_field(
    field: str, raw: object, profile: Profile, *, image_src_allowed: ImageSrcCheck
) -> Json:
    """`validate` for a use case: a broken rule becomes `422 validation_error` on `field`
    with code `rich_content_invalid` (api_contract.md §1)."""
    try:
        return validate(raw, profile, image_src_allowed=image_src_allowed)
    except RichContentInvalid as error:
        # The editor can't produce this, so it's a client bug worth seeing
        logger.warning("rich_content.rejected", extra={"field": field, "pointer": error.pointer})
        raise FieldsInvalid(FieldError(field, "rich_content_invalid", str(error))) from error


def _ensure_size(doc: Json, profile: Profile) -> None:
    size = len(json.dumps(doc, ensure_ascii=False, separators=(",", ":")).encode())
    limit = MAX_BYTES[profile]
    if size > limit:
        raise RichContentInvalid("/", f"is {size} bytes; the limit is {limit}")
