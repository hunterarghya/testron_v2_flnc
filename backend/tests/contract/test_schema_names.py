from collections import Counter, defaultdict
from collections.abc import Mapping

from ninja import Schema

from config.api import api  # loads every module's routes and their DTOs


def test_no_two_dtos_share_a_name() -> None:
    """OpenAPI names schemas by class name, so two DTOs with one name silently become one
    type in the generated client (it happened once: two TotalTimingIn classes)."""
    homes: dict[str, set[str]] = defaultdict(set)
    for schema in _all_subclasses(Schema):
        if _is_api_dto(schema):
            homes[schema.__name__].add(schema.__module__)
    assert {name: mods for name, mods in homes.items() if len(mods) > 1} == {}


def test_no_two_operations_share_an_id() -> None:
    """OpenAPI names operations by controller function, so two `get_group`s in two modules
    give the generated client one path with the other's response type (it happened once)."""
    paths: Mapping[str, Mapping[str, Mapping[str, object]]] = api.get_openapi_schema()["paths"]
    ids = Counter(str(op["operationId"]) for methods in paths.values() for op in methods.values())
    assert [name for name, count in ids.items() if count > 1] == []


def _is_api_dto(schema: type) -> bool:
    # Private bases (_In, _Out) and classes made inside tests never reach the OpenAPI document
    home = schema.__module__
    return (
        home.startswith(("modules.", "core."))
        and ".tests." not in home
        and schema.__name__[0] != "_"
    )


def _all_subclasses(cls: type) -> set[type]:
    found: set[type] = set(cls.__subclasses__())
    for sub in list(found):
        found |= _all_subclasses(sub)
    return found
