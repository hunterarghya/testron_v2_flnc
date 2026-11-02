"""Reading validated rich content: its text for search, whether it's empty, its images
(editor_content_spec.md §3, helpers)."""

from collections.abc import Iterator

from core.rich_content.walk import Json

_INLINE = frozenset({"text", "hardBreak", "math"})


def plain_text(doc: Json) -> str:
    """Text, equations (as LaTeX) and image labels, space-joined; fills `search_text`.
    Text within a paragraph is kept together, so "H₂O" searches as "H2O"."""
    pieces = (" ".join(_block_text(block).split()) for block in _blocks(doc))
    return " ".join(piece for piece in pieces if piece)


def is_empty(doc: Json) -> bool:
    """No visible text, no equation and no image: drives `stem_empty` / `option_empty`.
    An equation alone is a question, so it counts as content."""
    return not any(_has_content(node) for node in _walk(doc))


def image_refs(doc: Json) -> list[str]:
    """The storage ids of every image, in order (ADR-009: referenced files are never deleted)."""
    return [str(_attrs(node)["fileId"]) for node in _walk(doc) if node["type"] == "image"]


def _blocks(doc: Json) -> Iterator[Json]:
    """Every node that holds text or stands alone: paragraphs, images and displayed math."""
    for node in _walk(doc):
        if node["type"] in ("paragraph", "image") or (
            node["type"] == "math" and _attrs(node)["display"]
        ):
            yield node


def _block_text(block: Json) -> str:
    if block["type"] == "image":
        labels = _attrs(block)
        return f"{labels.get('alt', '')} {labels.get('caption', '')}"
    if block["type"] == "math":
        return str(_attrs(block)["latex"])
    return "".join(_inline_text(node) for node in _children(block))


def _inline_text(node: Json) -> str:
    if node["type"] == "text":
        return str(node["text"])
    if node["type"] == "math":
        return f" {_attrs(node)['latex']} "
    return " "


def _has_content(node: Json) -> bool:
    if node["type"] == "text":
        return bool(str(node["text"]).strip())
    return node["type"] in ("image", "math")


def _walk(node: Json) -> Iterator[Json]:
    for child in _children(node):
        yield child
        if child["type"] not in _INLINE:
            yield from _walk(child)


def _children(node: Json) -> list[Json]:
    content = node.get("content")
    return content if isinstance(content, list) else []


def _attrs(node: Json) -> Json:
    attrs = node.get("attrs")
    return attrs if isinstance(attrs, dict) else {}
