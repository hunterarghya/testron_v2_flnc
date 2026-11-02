"""The image node: one uploaded file, with its size and labels (editor_content_spec.md §2.3)."""

from collections.abc import Callable

from core.rich_content.normalize import clean_text
from core.rich_content.schema import (
    IMAGE_FILE_ID,
    IMAGE_PROVIDERS,
    IMAGE_SIZES,
    MAX_COMPACT_IMAGES,
    MAX_IMAGE_LABEL_LENGTH,
    MAX_IMAGE_SIDE,
)
from core.rich_content.walk import At, Json, Walk, attrs, fail, node

_KEYS = frozenset({"type", "attrs"})
_ATTRS = frozenset({"provider", "fileId", "src", "width", "height", "size", "alt", "caption"})


def _is_side(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and 1 <= value <= MAX_IMAGE_SIDE


def _is_label(value: object) -> bool:
    return isinstance(value, str) and len(value) <= MAX_IMAGE_LABEL_LENGTH


# Each attribute's rule, and what the error says when it's broken
_RULES: dict[str, tuple[Callable[[object], bool], str]] = {
    "provider": (lambda value: value in IMAGE_PROVIDERS, "must be imagekit"),
    "fileId": (
        lambda value: isinstance(value, str) and bool(IMAGE_FILE_ID.match(value)),
        "must be a storage file id",
    ),
    "width": (_is_side, f"must be 1 to {MAX_IMAGE_SIDE} pixels"),
    "height": (_is_side, f"must be 1 to {MAX_IMAGE_SIDE} pixels"),
    "size": (lambda value: value in IMAGE_SIZES, "must be S, M, L or FULL"),
}


def image(walk: Walk, raw: object, at: At) -> Json:
    found = node(walk, raw, at, _KEYS)
    values = attrs(found, at, _ATTRS)
    at_attrs = at.key("attrs")
    for name, (is_valid, message) in _RULES.items():
        if not is_valid(values.get(name)):
            raise fail(at_attrs.key(name), message)
    src = values.get("src")
    if not isinstance(src, str) or not walk.image_src_allowed(src):
        raise fail(at_attrs.key("src"), "must be an image uploaded here")
    if walk.count("image") > MAX_COMPACT_IMAGES and walk.compact:
        raise fail(at, f"an option can have only {MAX_COMPACT_IMAGES} image")
    checked = {name: values[name] for name in _RULES}
    return {"type": "image", "attrs": {**checked, "src": src, **_labels(values, at_attrs)}}


def _labels(values: Json, at: At) -> dict[str, str]:
    labels = {}
    for name in ("alt", "caption"):
        value = values.get(name) or ""
        if not _is_label(value):
            raise fail(at.key(name), f"must be at most {MAX_IMAGE_LABEL_LENGTH} characters")
        # Plain text on one line
        labels[name] = " ".join(clean_text(str(value)).split())
    return labels
