"""Everything the editor can produce is accepted and stored in one normal form
(editor_content_spec.md §2, §3, §7)."""

import pytest

from core.rich_content import EMPTY_DOC, Json, Profile, validate
from core.tests.rich_content.docs import (
    allowed_src,
    bullets,
    doc,
    image,
    item,
    math,
    para,
    table,
    text,
)

# Bengali samples, built from code points so no invisible character hides in the source
KA, VIRAMA, SSA, RA, YA = chr(0x0995), chr(0x09CD), chr(0x09B7), chr(0x09B0), chr(0x09AF)
E_SIGN, AA_SIGN, O_SIGN = chr(0x09C7), chr(0x09BE), chr(0x09CB)
ZWJ, ZWNJ = chr(0x200D), chr(0x200C)
RLO, LRI, BOM, BELL = chr(0x202E), chr(0x2066), chr(0xFEFF), chr(0x07)


def full(document: Json) -> Json:
    return validate(document, Profile.FULL, image_src_allowed=allowed_src)


def first_paragraph(document: Json) -> list[Json]:
    content = full(document)["content"]
    assert isinstance(content, list)
    inline = content[0]["content"]
    assert isinstance(inline, list)
    return inline


@pytest.mark.parametrize(
    "block",
    [
        para(
            text("H"),
            text("2", "subscript"),
            text("O"),
            text(" cell ", "bold", "italic", "underline"),
        ),
        para(text("x"), text("2", "superscript"), {"type": "hardBreak"}, math("a^2")),
        para(text("Centred"), textAlign="center"),
        bullets(
            item(para(text("one"))), item(para(text("two")), bullets(item(para(text("nested")))))
        ),
        {"type": "orderedList", "attrs": {"start": 3}, "content": [item(para(text("three")))]},
        table(["Organelle", "Job"], ["Golgi", "Packaging"]),
        image(caption="Golgi body", alt="Golgi"),
        math("\\frac{a}{b}", display=True),
    ],
)
def test_every_allowed_node_and_mark_round_trips(block: Json) -> None:
    once = full(doc(block))

    assert once["content"] == [block]
    assert full(once) == once


def test_the_editors_default_attributes_are_accepted_and_dropped() -> None:
    sent = doc(
        {"type": "paragraph", "attrs": {"textAlign": "left"}, "content": [text("a")]},
        {
            "type": "orderedList",
            "attrs": {"start": 1, "type": None},
            "content": [item(para(text("b")))],
        },
    )

    assert full(sent)["content"] == [
        para(text("a")),
        bullets(item(para(text("b")))) | {"type": "orderedList"},
    ]


def test_bengali_is_nfc_and_keeps_its_joiners() -> None:
    decomposed = KA + E_SIGN + AA_SIGN  # কো typed as two signs
    conjunct = KA + VIRAMA + SSA + " " + RA + ZWJ + VIRAMA + YA + ZWNJ

    stored = first_paragraph(doc(para(text(decomposed + " " + conjunct))))

    assert stored == [text(KA + O_SIGN + " " + conjunct)]


def test_bidi_overrides_and_control_characters_are_removed() -> None:
    stored = first_paragraph(doc(para(text(f"{RLO}cell{LRI} wall{BOM}{BELL}\tok"))))

    assert stored == [text("cell wall ok")]


def test_new_lines_become_hard_breaks() -> None:
    assert first_paragraph(doc(para(text("one\ntwo")))) == [
        text("one"),
        {"type": "hardBreak"},
        text("two"),
    ]


def test_neighbouring_text_merges_and_marks_are_sorted() -> None:
    stored = first_paragraph(
        doc(para(text("a", "italic", "bold"), text("b", "bold", "italic"), text(""), text("c")))
    )

    assert stored == [text("ab", "bold", "italic"), text("c")]


def test_marks_on_a_hard_break_are_dropped() -> None:
    sent = para(text("a"), {"type": "hardBreak", "marks": [{"type": "bold"}]}, text("b"))

    assert first_paragraph(doc(sent)) == [text("a"), {"type": "hardBreak"}, text("b")]


def test_empty_paragraphs_at_either_end_are_trimmed() -> None:
    blank: Json = {"type": "paragraph"}

    assert full(doc(blank, para(), para(text("kept")), blank))["content"] == [para(text("kept"))]
    assert full(doc(blank, para(text("")))) == EMPTY_DOC


def test_image_labels_default_to_empty_and_are_one_line() -> None:
    sent = image()
    del sent["attrs"]["alt"]  # type: ignore[attr-defined]  # the builder's attrs dict
    sent["attrs"]["caption"] = "  Golgi\nbody "  # type: ignore[index]

    attrs = full(doc(sent))["content"][0]["attrs"]  # type: ignore[index]

    assert (attrs["alt"], attrs["caption"]) == ("", "Golgi body")


def test_options_allow_paragraphs_inline_math_and_one_image() -> None:
    option = doc(para(text("Mitochondria "), math("x")), para(text("two")), image())

    assert (
        validate(option, Profile.COMPACT, image_src_allowed=allowed_src)["content"]
        == option["content"]
    )
