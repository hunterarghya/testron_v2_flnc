"""Anything outside the allow-list is refused, with a JSON pointer to it (editor_content_spec.md
§2, §7). Nothing is silently repaired."""

import pytest

from core.errors import FieldsInvalid
from core.rich_content import Json, Profile, RichContentInvalid, validate, validate_field
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


def rejected(document: object, profile: Profile = Profile.FULL) -> RichContentInvalid:
    with pytest.raises(RichContentInvalid) as error:
        validate(document, profile, image_src_allowed=allowed_src)
    return error.value


def nested_lists(depth: int) -> Json:
    node = bullets(item(para(text("leaf"))))
    for _ in range(depth - 1):
        node = bullets(item(para(text("x")), node))
    return node


@pytest.mark.parametrize(
    ("document", "pointer"),
    [
        ("not a doc", "/"),
        ({"v": 2, "type": "doc", "content": []}, "/v"),
        ({"v": 1, "type": "paragraph", "content": []}, "/type"),
        ({"v": 1, "type": "doc", "content": [], "html": "<b>x</b>"}, "/html"),
        (doc({"type": "heading", "content": [text("x")]}), "/content/0/type"),
        (doc({"type": "codeBlock"}), "/content/0/type"),
        (doc(para({"type": "image"})), "/content/0/content/0/type"),
        (doc(para(text("x", "link"))), "/content/0/content/0/marks/0/type"),
        (
            doc(
                para(
                    {
                        "type": "text",
                        "text": "x",
                        "marks": [{"type": "bold", "attrs": {"color": "red"}}],
                    }
                )
            ),
            "/content/0/content/0/marks/0/attrs/color",
        ),
        (doc(para(text("x", "subscript", "superscript"))), "/content/0/content/0/marks"),
        (doc(para(text("x" * 5001))), "/content/0/content/0/text"),
        (
            doc(para({"type": "text", "text": "x", "style": "color:red"})),
            "/content/0/content/0/style",
        ),
        (doc(para(text("x"), textAlign="right")), "/content/0/attrs/textAlign"),
        (doc(para(math("x", display=True))), "/content/0/content/0/attrs/display"),
        (doc(math("x")), "/content/0/attrs/display"),
        (doc(math("")), "/content/0/attrs/latex"),
        (doc(image(src="https://evil.example/tests/x.png")), "/content/0/attrs/src"),
        (doc(image(provider="s3")), "/content/0/attrs/provider"),
        (doc(image(file_id="../x")), "/content/0/attrs/fileId"),
        (doc(image(width=0)), "/content/0/attrs/width"),
        (doc(image(height=True)), "/content/0/attrs/height"),
        (doc(image(size="XL")), "/content/0/attrs/size"),
        (doc(image(alt="a" * 301)), "/content/0/attrs/alt"),
        (doc(image(onclick="x")), "/content/0/attrs/onclick"),
        (doc(bullets()), "/content/0/content"),
        (doc(bullets(*[item(para(text("x")))] * 51)), "/content/0/content"),
        (doc(bullets(item(bullets(item(para(text("x"))))))), "/content/0/content/0/content/0"),
        (
            doc(nested_lists(4)),
            "/content/0/content/0/content/1/content/0/content/1/content/0/content/1",
        ),
        (
            doc(
                {"type": "orderedList", "attrs": {"start": -1}, "content": [item(para(text("x")))]}
            ),
            "/content/0/attrs/start",
        ),
        (doc(table(*[["x"]] * 21)), "/content/0/content"),
        (doc(table(["x"] * 9)), "/content/0/content/0/content"),
        (
            doc(
                {
                    "type": "table",
                    "content": [
                        {
                            "type": "tableRow",
                            "content": [
                                {"type": "tableCell", "attrs": {"colspan": 2}, "content": [para()]}
                            ],
                        }
                    ],
                }
            ),
            "/content/0/content/0/content/0/attrs",
        ),
        (
            doc({"type": "table", "content": [{"type": "tableRow", "content": [para()]}]}),
            "/content/0/content/0/content/0/type",
        ),
    ],
)
def test_disallowed_content_is_refused_at_its_path(document: object, pointer: str) -> None:
    assert rejected(document).pointer == pointer


@pytest.mark.parametrize(
    ("option", "pointer"),
    [
        (doc(bullets(item(para(text("x"))))), "/content/0/type"),
        (doc(table(["x"])), "/content/0/type"),
        (doc(math("x", display=True)), "/content/0/type"),
        (doc(para(text("1")), para(text("2")), para(text("3")), para(text("4"))), "/content/3"),
        (doc(image("first_1"), image("second_2")), "/content/1"),
    ],
)
def test_options_have_tighter_limits(option: Json, pointer: str) -> None:
    assert rejected(option, Profile.COMPACT).pointer == pointer


def test_size_node_count_and_depth_are_limited() -> None:
    big_option = doc(para(text("x" * 4000)), para(text("y" * 4000)), para(text("z" * 500)))
    many_nodes = doc(*[para(text("x"), {"type": "hardBreak"})] * 700)

    assert "limit is 8192" in rejected(big_option, Profile.COMPACT).reason
    assert "nodes" in rejected(many_nodes).reason


def test_a_use_case_gets_a_field_error() -> None:
    with pytest.raises(FieldsInvalid) as error:
        validate_field(
            "stem", doc({"type": "heading"}), Profile.FULL, image_src_allowed=allowed_src
        )

    [field_error] = error.value.field_errors()
    assert (field_error.field, field_error.code) == ("stem", "rich_content_invalid")
    assert "/content/0/type" in field_error.message
