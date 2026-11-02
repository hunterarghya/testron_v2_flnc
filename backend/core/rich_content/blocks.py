"""Block content: paragraphs, lists, tables, images and displayed math (editor_content_spec.md
§2.1). Which blocks a field allows depends on its profile."""

from collections.abc import Callable

from core.rich_content.images import image
from core.rich_content.inline import inline_content, math
from core.rich_content.schema import (
    COMPACT_BLOCKS,
    FULL_BLOCKS,
    MAX_COMPACT_PARAGRAPHS,
    MAX_LIST_DEPTH,
    MAX_LIST_ITEMS,
    MAX_TABLE_COLUMNS,
    MAX_TABLE_ROWS,
)
from core.rich_content.walk import At, Json, Walk, as_list, attrs, fail, is_int, node, node_type

_CONTAINER_KEYS = frozenset({"type", "attrs", "content"})
_CELL_ATTRS = frozenset({"colspan", "rowspan", "colwidth"})
_CELLS = frozenset({"tableHeader", "tableCell"})
_LISTS = frozenset({"bulletList", "orderedList"})


def blocks(walk: Walk, raw: object, at: At) -> list[Json]:
    return [block(walk, item, at.child(index)) for index, item in enumerate(as_list(raw, at))]


def block(walk: Walk, raw: object, at: At) -> Json:
    kind = node_type(raw, at)
    allowed = COMPACT_BLOCKS if walk.compact else FULL_BLOCKS
    if kind not in allowed:
        where = "in an option" if walk.compact and kind in FULL_BLOCKS else "here"
        raise fail(at.key("type"), f"{kind!r} is not allowed {where}")
    return _BLOCKS[kind](walk, raw, at)


def paragraph(walk: Walk, raw: object, at: At) -> Json:
    found = node(walk, raw, at, _CONTAINER_KEYS)
    if walk.count("paragraph") > MAX_COMPACT_PARAGRAPHS and walk.compact:
        raise fail(at, f"an option can have at most {MAX_COMPACT_PARAGRAPHS} paragraphs")
    align = attrs(found, at, frozenset({"textAlign"})).get("textAlign")
    if align not in (None, "left", "center"):
        raise fail(at.key("attrs").key("textAlign"), "must be left or center")
    result: Json = {"type": "paragraph"}
    # Left is the default, so only centring is stored
    if align == "center":
        result["attrs"] = {"textAlign": "center"}
    content = inline_content(walk, found.get("content"), at.key("content"))
    if content:
        result["content"] = content
    return result


def _list(walk: Walk, raw: object, at: At) -> Json:
    found = node(walk, raw, at, _CONTAINER_KEYS)
    kind = str(found["type"])
    inside = at.in_list()
    if inside.list_depth > MAX_LIST_DEPTH:
        raise fail(at, f"lists can be nested at most {MAX_LIST_DEPTH} deep")
    # The editor also sends `type` (the numbering style), which is always the default
    values = attrs(found, at, frozenset({"start", "type"} if kind == "orderedList" else ()))
    start = values.get("start")
    if start is not None and not (is_int(start) and isinstance(start, int) and start >= 0):
        raise fail(at.key("attrs").key("start"), "must be a whole number")
    content_at = inside.key("content")
    items = as_list(found.get("content"), content_at, low=1, high=MAX_LIST_ITEMS)
    result: Json = {
        "type": kind,
        "content": [_list_item(walk, item, content_at.child(i)) for i, item in enumerate(items)],
    }
    if start not in (None, 1):
        result["attrs"] = {"start": start}
    return result


def _list_item(walk: Walk, raw: object, at: At) -> Json:
    found = node(walk, raw, at, _CONTAINER_KEYS)
    attrs(found, at, frozenset())
    content_at = at.key("content")
    items = as_list(found.get("content"), content_at, low=1)
    if node_type(items[0], content_at.child(0)) != "paragraph":
        raise fail(content_at.child(0), "a list item starts with a paragraph")
    content = []
    for index, item in enumerate(items):
        item_at = content_at.child(index)
        if node_type(item, item_at) in _LISTS:
            content.append(_list(walk, item, item_at))
        else:
            content.append(_only(walk, item, item_at, "paragraph", paragraph))
    return {"type": "listItem", "content": content}


def _table(walk: Walk, raw: object, at: At) -> Json:
    found = node(walk, raw, at, _CONTAINER_KEYS)
    attrs(found, at, frozenset())
    rows_at = at.key("content")
    rows = as_list(found.get("content"), rows_at, low=1, high=MAX_TABLE_ROWS)
    return {
        "type": "table",
        "content": [
            _only(walk, row, rows_at.child(i), "tableRow", _row) for i, row in enumerate(rows)
        ],
    }


def _row(walk: Walk, raw: object, at: At) -> Json:
    found = node(walk, raw, at, _CONTAINER_KEYS)
    attrs(found, at, frozenset())
    cells_at = at.key("content")
    cells = as_list(found.get("content"), cells_at, low=1, high=MAX_TABLE_COLUMNS)
    return {
        "type": "tableRow",
        "content": [_cell(walk, cell, cells_at.child(i)) for i, cell in enumerate(cells)],
    }


def _cell(walk: Walk, raw: object, at: At) -> Json:
    kind = node_type(raw, at)
    if kind not in _CELLS:
        raise fail(at.key("type"), "a table row holds only cells")
    found = node(walk, raw, at, _CONTAINER_KEYS)
    values = attrs(found, at, _CELL_ATTRS)
    # Merged cells and set widths are off in the editor (editor_content_spec.md §4.1)
    if (
        values.get("colspan", 1) != 1
        or values.get("rowspan", 1) != 1
        or values.get("colwidth") is not None
    ):
        raise fail(at.key("attrs"), "merged or resized cells are not supported")
    content_at = at.key("content")
    paragraphs = as_list(found.get("content"), content_at, low=1)
    content = [
        _only(walk, item, content_at.child(i), "paragraph", paragraph)
        for i, item in enumerate(paragraphs)
    ]
    return {"type": kind, "content": content}


def _only(
    walk: Walk, raw: object, at: At, kind: str, check: Callable[[Walk, object, At], Json]
) -> Json:
    if node_type(raw, at) != kind:
        raise fail(at.key("type"), f"must be a {kind}")
    return check(walk, raw, at)


def _display_math(walk: Walk, raw: object, at: At) -> Json:
    return math(walk, raw, at, display=True)


_BLOCKS: dict[str, Callable[[Walk, object, At], Json]] = {
    "paragraph": paragraph,
    "bulletList": _list,
    "orderedList": _list,
    "table": _table,
    "image": image,
    "math": _display_math,
}
