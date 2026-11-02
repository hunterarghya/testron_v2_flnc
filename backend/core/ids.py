"""Time-ordered UUIDs (RFC 9562 version 7) for every primary key.

New rows get ids that sort by creation time, so inserts land at the end of the
index instead of all over it. Python 3.13 has no uuid7(), so it is built here.
"""

import os
import time
from uuid import UUID

_TIMESTAMP_BITS = 48
_RANDOM_BITS = 74  # 12 bits after the version + 62 bits after the variant
_VERSION_7 = 0x7
_VARIANT_RFC = 0b10


def uuid7() -> UUID:
    # The id embeds wall-clock milliseconds by definition, so it reads the system time
    # directly; ids must never repeat, even under a frozen test clock
    return uuid7_from(time.time_ns() // 1_000_000, os.urandom(10))


def uuid7_from(unix_ms: int, random: bytes) -> UUID:
    """Build a version 7 UUID from a millisecond timestamp and 10 random bytes."""
    random_bits = int.from_bytes(random) & ((1 << _RANDOM_BITS) - 1)
    rand_a = random_bits >> 62  # 12 bits
    rand_b = random_bits & ((1 << 62) - 1)
    value = (unix_ms & ((1 << _TIMESTAMP_BITS) - 1)) << 80
    value |= _VERSION_7 << 76 | rand_a << 64 | _VARIANT_RFC << 62 | rand_b
    return UUID(int=value)


def uuid7_unix_ms(value: UUID) -> int:
    """The creation time (in milliseconds) stored in a version 7 UUID."""
    return value.int >> 80
