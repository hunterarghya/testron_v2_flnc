"""Counted attempts, rank and stats (domain_model.md §6.3), worked out on read from scores, so
nothing goes stale after a regrade.

    counted = ended, graded, and not disqualified (unless the teacher overrode it)
    pool    = counted attempts of the same assignment with the same take number (DM-1)
    rank    = standard competition ranking by score, highest first: 1, 2, 2, 4
"""

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

CENT = Decimal("0.01")


@dataclass(frozen=True, slots=True)
class Scored:
    attempt_id: UUID
    take_number: int
    score: Decimal | None
    counted: bool


@dataclass(frozen=True, slots=True)
class Placing:
    rank: int
    pool: int


@dataclass(frozen=True, slots=True)
class Stats:
    count: int
    mean: Decimal
    highest: Decimal
    lowest: Decimal


def is_counted(*, ended: bool, graded: bool, disqualified: bool, overridden: bool) -> bool:
    return ended and graded and (not disqualified or overridden)


def placings(attempts: Iterable[Scored]) -> dict[UUID, Placing]:
    """Each counted attempt's rank within its take's pool."""
    found: dict[UUID, Placing] = {}
    for pool in _pools(attempts).values():
        scores = sorted((a.score or Decimal(0) for a in pool), reverse=True)
        for attempt in pool:
            # Equal scores share the rank of the first of them: 1, 2, 2, 4
            rank = scores.index(attempt.score or Decimal(0)) + 1
            found[attempt.attempt_id] = Placing(rank=rank, pool=len(scores))
    return found


def pool_stats(attempts: Iterable[Scored], take_number: int = 1) -> Stats | None:
    """Over the pool of one take (the first, unless asked); None when it is empty."""
    scores = [a.score or Decimal(0) for a in _pools(attempts).get(take_number, [])]
    if not scores:
        return None
    mean = (sum(scores, Decimal(0)) / len(scores)).quantize(CENT, rounding=ROUND_HALF_UP)
    return Stats(count=len(scores), mean=mean, highest=max(scores), lowest=min(scores))


def _pools(attempts: Iterable[Scored]) -> dict[int, list[Scored]]:
    pools: dict[int, list[Scored]] = defaultdict(list)
    for attempt in attempts:
        if attempt.counted and attempt.score is not None:
            pools[attempt.take_number].append(attempt)
    return pools
