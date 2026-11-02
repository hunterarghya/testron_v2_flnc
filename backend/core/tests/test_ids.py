from core.ids import uuid7, uuid7_from, uuid7_unix_ms

MS = 1_794_465_000_000  # 2026-11-12


def test_id_is_version_7_with_rfc_variant() -> None:
    value = uuid7()

    assert value.version == 7
    assert value.variant == "specified in RFC 4122"


def test_id_stores_its_creation_millisecond() -> None:
    assert uuid7_unix_ms(uuid7_from(MS, bytes(10))) == MS


def test_ids_sort_by_creation_time() -> None:
    earlier = uuid7_from(MS, b"\xff" * 10)
    later = uuid7_from(MS + 1, bytes(10))

    assert earlier < later


def test_random_bits_never_touch_version_or_variant() -> None:
    value = uuid7_from(MS, b"\xff" * 10)

    assert value.version == 7
    assert value.variant == "specified in RFC 4122"
    assert uuid7_unix_ms(value) == MS


def test_ids_are_unique() -> None:
    assert len({uuid7() for _ in range(10_000)}) == 10_000
