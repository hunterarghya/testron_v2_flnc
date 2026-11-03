from collections import defaultdict

from ninja import Schema

import config.api  # noqa: F401  # loads every module's routes and their DTOs


def test_no_two_dtos_share_a_name() -> None:
    """OpenAPI names schemas by class name, so two DTOs with one name silently become one
    type in the generated client (it happened once: two TotalTimingIn classes)."""
    homes: dict[str, set[str]] = defaultdict(set)
    for schema in _all_subclasses(Schema):
        if _is_api_dto(schema):
            homes[schema.__name__].add(schema.__module__)
    assert {name: mods for name, mods in homes.items() if len(mods) > 1} == {}


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
