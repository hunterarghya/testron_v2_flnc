"""What every node check shares: where it is (a JSON pointer), the running counts, and the
basic shape checks. A broken rule raises RichContentInvalid with the pointer to it."""

from collections.abc import Callable
from dataclasses import dataclass, field

from core.rich_content.schema import MAX_DEPTH, MAX_NODES, Profile

Json = dict[str, object]
ImageSrcCheck = Callable[[str], bool]


class RichContentInvalid(Exception):
    """The first broken rule, at a JSON pointer such as `/content/2/attrs/src`."""

    def __init__(self, pointer: str, reason: str) -> None:
        super().__init__(f"{reason} at {pointer or '/'}")
        self.pointer = pointer or "/"
        self.reason = reason


@dataclass(frozen=True, slots=True)
class At:
    pointer: str
    depth: int
    list_depth: int = 0

    def key(self, name: str | int) -> "At":
        """A value inside this node, at the same depth (`attrs`, `text`, `content`)."""
        return At(f"{self.pointer}/{name}", self.depth, self.list_depth)

    def child(self, index: int) -> "At":
        """A child node, one level deeper."""
        return At(f"{self.pointer}/{index}", self.depth + 1, self.list_depth)

    def in_list(self) -> "At":
        return At(self.pointer, self.depth, self.list_depth + 1)


@dataclass
class Walk:
    profile: Profile
    image_src_allowed: ImageSrcCheck
    nodes: int = 0
    counts: dict[str, int] = field(default_factory=dict)

    @property
    def compact(self) -> bool:
        return self.profile is Profile.COMPACT

    def count(self, kind: str) -> int:
        self.counts[kind] = self.counts.get(kind, 0) + 1
        return self.counts[kind]


def fail(at: At, reason: str) -> RichContentInvalid:
    return RichContentInvalid(at.pointer, reason)


def node(walk: Walk, raw: object, at: At, keys: frozenset[str]) -> Json:
    """An object with only the allowed keys, counted towards the node and depth limits."""
    found = as_object(raw, at)
    unknown = sorted(set(found) - keys)
    if unknown:
        raise fail(at.key(unknown[0]), "is not allowed")
    walk.nodes += 1
    if walk.nodes > MAX_NODES:
        raise fail(at, f"has more than {MAX_NODES} nodes in the document")
    if at.depth > MAX_DEPTH:
        raise fail(at, f"is nested more than {MAX_DEPTH} levels deep")
    return found


def attrs(found: Json, at: At, allowed: frozenset[str]) -> Json:
    """The node's attributes (none given is the same as empty); unknown ones are refused."""
    raw = found.get("attrs")
    if raw is None:
        return {}
    values = as_object(raw, at.key("attrs"))
    unknown = sorted(set(values) - allowed)
    if unknown:
        raise fail(at.key("attrs").key(unknown[0]), "is not allowed")
    return values


def node_type(raw: object, at: At) -> str:
    kind = as_object(raw, at).get("type")
    if not isinstance(kind, str):
        raise fail(at.key("type"), "must be a node type")
    return kind


def as_object(raw: object, at: At) -> Json:
    if not isinstance(raw, dict):
        raise fail(at, "must be an object")
    return raw


def as_list(raw: object, at: At, *, low: int = 0, high: int | None = None) -> list[object]:
    if raw is None:
        raw = []
    if not isinstance(raw, list):
        raise fail(at, "must be a list")
    if len(raw) < low or (high is not None and len(raw) > high):
        limit = f"{low} to {high}" if high is not None else f"at least {low}"
        raise fail(at, f"must have {limit} items")
    return raw


def is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)
