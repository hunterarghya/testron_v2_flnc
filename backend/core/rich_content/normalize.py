"""Normalization: the same content is always stored as the same JSON (editor_content_spec.md §3).

These functions tidy content that has already passed validation. They never repair content
that breaks the rules: that is rejected instead.
"""

import unicodedata
from collections.abc import Iterable, Sequence

from core.rich_content.schema import MARK_ORDER

Json = dict[str, object]

# Only these and control characters (Cc) go. The zero-width joiner and non-joiner (format
# characters, not controls) stay: Bengali conjuncts are shaped by them.
_BYTE_ORDER_MARK = chr(0xFEFF)
# Bidi embeddings, overrides and isolates: they can make text read differently than it is
_BIDI_CONTROLS = frozenset(chr(code) for code in (*range(0x202A, 0x202F), *range(0x2066, 0x206A)))
_KEPT_CONTROLS = frozenset({"\n", "\t"})


def clean_text(raw: str) -> str:
    """NFC, then without control characters, the byte-order mark or bidi controls.
    A tab becomes a space; a newline stays (it becomes a hard break)."""
    text = unicodedata.normalize("NFC", raw).replace("\t", " ")
    return "".join(character for character in text if _is_kept(character))


def _is_kept(character: str) -> bool:
    if character in _KEPT_CONTROLS:
        return True
    if character == _BYTE_ORDER_MARK or character in _BIDI_CONTROLS:
        return False
    return unicodedata.category(character) != "Cc"


def text_nodes(text: str, marks: Sequence[str]) -> list[Json]:
    """One text node per line, with a hard break between lines."""
    nodes: list[Json] = []
    for index, line in enumerate(text.split("\n")):
        if index:
            nodes.append({"type": "hardBreak"})
        nodes.append(text_node(line, marks))
    return nodes


def text_node(text: str, marks: Sequence[str]) -> Json:
    node: Json = {"type": "text", "text": text}
    if marks:
        node["marks"] = [{"type": mark} for mark in sorted_marks(marks)]
    return node


def sorted_marks(marks: Iterable[str]) -> list[str]:
    return sorted(set(marks), key=MARK_ORDER.index)


def merge_text(nodes: Iterable[Json]) -> list[Json]:
    """Neighbouring text with the same marks becomes one node; empty text disappears."""
    merged: list[Json] = []
    for node in nodes:
        if node["type"] == "text" and not node["text"]:
            continue
        previous = merged[-1] if merged else None
        if previous and _same_marks_text(previous, node):
            merged[-1] = {**previous, "text": f"{previous['text']}{node['text']}"}
        else:
            merged.append(node)
    return merged


def _same_marks_text(first: Json, second: Json) -> bool:
    both_text = first["type"] == "text" and second["type"] == "text"
    return both_text and first.get("marks") == second.get("marks")


def trim_empty_paragraphs(blocks: list[Json]) -> list[Json]:
    """Leading and trailing empty paragraphs are removed (editor_content_spec.md §3, rule 6)."""
    start, end = 0, len(blocks)
    while start < end and _is_empty_paragraph(blocks[start]):
        start += 1
    while end > start and _is_empty_paragraph(blocks[end - 1]):
        end -= 1
    return blocks[start:end]


def _is_empty_paragraph(block: Json) -> bool:
    return block["type"] == "paragraph" and not block.get("content")
