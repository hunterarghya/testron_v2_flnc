"""Inline content: text with marks, hard breaks and inline math (editor_content_spec.md §2)."""

from core.rich_content.normalize import clean_text, merge_text, sorted_marks, text_nodes
from core.rich_content.schema import (
    EXCLUSIVE_MARKS,
    INLINE_NODES,
    MARK_ORDER,
    MAX_LATEX_LENGTH,
    MAX_TEXT_LENGTH,
)
from core.rich_content.walk import At, Json, Walk, as_list, as_object, attrs, fail, node, node_type

_TEXT_KEYS = frozenset({"type", "text", "marks"})
_BREAK_KEYS = frozenset({"type", "marks"})
_MATH_KEYS = frozenset({"type", "attrs"})
_MATH_ATTRS = frozenset({"latex", "display"})
_MARK_KEYS = frozenset({"type", "attrs"})


def inline_content(walk: Walk, raw: object, at: At) -> list[Json]:
    """A paragraph's content, checked, then tidied: lines split, neighbours merged."""
    tidied: list[Json] = []
    for index, item in enumerate(as_list(raw, at)):
        tidied.extend(_inline(walk, item, at.child(index)))
    return merge_text(tidied)


def _inline(walk: Walk, raw: object, at: At) -> list[Json]:
    kind = node_type(raw, at)
    if kind not in INLINE_NODES:
        raise fail(at.key("type"), f"{kind!r} is not allowed inside a paragraph")
    if kind == "text":
        return _text(walk, raw, at)
    if kind == "hardBreak":
        found = node(walk, raw, at, _BREAK_KEYS)
        # A break may carry the marks around it; they mean nothing on a break
        _marks(found.get("marks"), at.key("marks"))
        return [{"type": "hardBreak"}]
    return [math(walk, raw, at, display=False)]


def _text(walk: Walk, raw: object, at: At) -> list[Json]:
    found = node(walk, raw, at, _TEXT_KEYS)
    text = found.get("text")
    if not isinstance(text, str) or len(text) > MAX_TEXT_LENGTH:
        raise fail(at.key("text"), f"must be text of at most {MAX_TEXT_LENGTH} characters")
    return text_nodes(clean_text(text), _marks(found.get("marks"), at.key("marks")))


def _marks(raw: object, at: At) -> list[str]:
    names = []
    for index, item in enumerate(as_list(raw, at)):
        mark_at = at.key(index)
        mark = as_object(item, mark_at)
        unknown = sorted(set(mark) - _MARK_KEYS)
        if unknown or attrs(mark, mark_at, frozenset()):
            raise fail(mark_at, "marks have no settings")
        name = mark.get("type")
        if name not in MARK_ORDER:
            raise fail(mark_at.key("type"), f"{name!r} is not an allowed mark")
        names.append(str(name))
    if set(names) >= EXCLUSIVE_MARKS:
        raise fail(at, "subscript and superscript can't be on the same text")
    return sorted_marks(names)


def math(walk: Walk, raw: object, at: At, *, display: bool) -> Json:
    """An equation: inline inside a paragraph, or displayed on its own line as a block."""
    found = node(walk, raw, at, _MATH_KEYS)
    values = attrs(found, at, _MATH_ATTRS)
    latex = values.get("latex")
    if not isinstance(latex, str) or not latex.strip() or len(latex) > MAX_LATEX_LENGTH:
        raise fail(at.key("attrs").key("latex"), f"must be 1 to {MAX_LATEX_LENGTH} characters")
    if values.get("display", False) is not display:
        where = "on its own line" if display else "inside text"
        raise fail(at.key("attrs").key("display"), f"must be {str(display).lower()} {where}")
    return {"type": "math", "attrs": {"latex": latex, "display": display}}
