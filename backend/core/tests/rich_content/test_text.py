"""plain_text, is_empty and image_refs (editor_content_spec.md §3, helpers)."""

import pytest

from core.rich_content import EMPTY_DOC, Json, image_refs, is_empty, plain_text
from core.tests.rich_content.docs import bullets, doc, image, item, math, para, table, text


def test_plain_text_keeps_words_together_and_adds_math_and_labels() -> None:
    content = doc(
        para(text("Which is "), text("H", "bold"), text("2", "subscript"), text("O?")),
        para(text("Solve "), math("x^2"), text(" now")),
        bullets(item(para(text("listed")))),
        table(["cell"]),
        image(alt="Golgi", caption="body"),
        math("\\frac{a}{b}", display=True),
    )

    assert plain_text(content) == "Which is H2O? Solve x^2 now listed cell Golgi body \\frac{a}{b}"


def test_hard_breaks_separate_words() -> None:
    assert plain_text(doc(para(text("one"), {"type": "hardBreak"}, text("two")))) == "one two"


@pytest.mark.parametrize(
    ("content", "empty"),
    [
        (EMPTY_DOC, True),
        (doc(para()), True),
        (doc(para(text("   ")), para({"type": "hardBreak"})), True),
        (doc(para(text("x"))), False),
        (doc(image()), False),
        (doc(para(math("x"))), False),
    ],
)
def test_is_empty(content: Json, empty: bool) -> None:
    assert is_empty(content) is empty


def test_image_refs_lists_every_image_in_order() -> None:
    content = doc(image("first_1"), table(["x"]), para(text("y")), image("second_2"))

    assert image_refs(content) == ["first_1", "second_2"]
