"""No student response can carry correctness (CLAUDE.md rule 1, security.md §4.2; V1 F-03,
F-08): every schema reachable from a `/my/*` or `/attempts/*` response is walked, and a
forbidden field name fails the test."""

import re
from collections.abc import Iterator, Mapping
from typing import cast

from config.api import api

Json = Mapping[str, object]
FORBIDDEN = re.compile(r"^(is_correct|correct.*|solutions?|answer_key.*|marks_awarded|score)$")
STUDENT_PATHS = ("/api/v1/my/", "/api/v1/attempts/")


def _refs(node: object) -> Iterator[str]:
    if isinstance(node, Mapping):
        for key, value in node.items():
            if key == "$ref" and isinstance(value, str):
                yield value.rsplit("/", 1)[-1]
            else:
                yield from _refs(value)
    elif isinstance(node, list):
        for item in node:
            yield from _refs(item)


def _student_response_schemas(document: Json) -> set[str]:
    schemas = cast("Json", cast("Json", document["components"])["schemas"])
    paths = cast("Json", document["paths"])
    todo = [
        ref
        for path, item in paths.items()
        if path.startswith(STUDENT_PATHS)
        for operation in cast("Json", item).values()
        for ref in _refs(cast("Json", operation).get("responses", {}))
    ]
    seen: set[str] = set()
    while todo:
        name = todo.pop()
        if name not in seen:
            seen.add(name)
            todo.extend(_refs(schemas[name]))
    return seen


def _properties(schema: object) -> Iterator[str]:
    if isinstance(schema, Mapping):
        yield from cast("Json", schema.get("properties", {}))
        for value in schema.values():
            yield from _properties(value)
    elif isinstance(schema, list):
        for item in schema:
            yield from _properties(item)


def test_student_schemas_have_no_answer_fields() -> None:
    document = cast("Json", api.get_openapi_schema())
    schemas = cast("Json", cast("Json", document["components"])["schemas"])
    reachable = _student_response_schemas(document)

    assert {"AttemptStateOut", "SaveAckOut", "GateStateOut"} <= reachable
    leaks = sorted(
        f"{name}.{field}"
        for name in reachable
        for field in _properties(schemas[name])
        if FORBIDDEN.match(field)
    )
    assert leaks == []
