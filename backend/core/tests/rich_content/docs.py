"""Small builders for rich-content documents in tests."""

from core.rich_content import Json

SRC_PREFIX = "https://ik.imagekit.io/acme/tests/"


def allowed_src(src: str) -> bool:
    return src.startswith(SRC_PREFIX)


def doc(*blocks: Json) -> Json:
    return {"v": 1, "type": "doc", "content": list(blocks)}


def para(*inline: Json, **attrs: object) -> Json:
    node: Json = {"type": "paragraph", "content": list(inline)}
    if attrs:
        node["attrs"] = attrs
    return node


def text(value: str, *marks: str) -> Json:
    node: Json = {"type": "text", "text": value}
    if marks:
        node["marks"] = [{"type": mark} for mark in marks]
    return node


def math(latex: str, *, display: bool = False) -> Json:
    return {"type": "math", "attrs": {"latex": latex, "display": display}}


def image(file_id: str = "golgi_01", **attrs: object) -> Json:
    values: Json = {
        "provider": "imagekit",
        "fileId": file_id,
        "src": f"{SRC_PREFIX}2026/11/{file_id}.png",
        "width": 640,
        "height": 420,
        "size": "M",
        "alt": "",
        "caption": "",
    }
    return {"type": "image", "attrs": values | attrs}


def bullets(*items: Json) -> Json:
    return {"type": "bulletList", "content": list(items)}


def item(*content: Json) -> Json:
    return {"type": "listItem", "content": list(content)}


def table(*rows: list[str]) -> Json:
    return {
        "type": "table",
        "content": [
            {
                "type": "tableRow",
                "content": [{"type": "tableCell", "content": [para(text(cell))]} for cell in row],
            }
            for row in rows
        ],
    }
