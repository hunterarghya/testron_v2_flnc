import pytest

from core.http.client_ip import UNKNOWN_IP, client_ip_from


@pytest.mark.parametrize(
    ("remote_addr", "forwarded_for", "hops", "ip"),
    [
        ("203.0.113.9", "", 0, "203.0.113.9"),
        ("203.0.113.9", "198.51.100.7", 0, "203.0.113.9"),
        ("10.0.0.2", "198.51.100.7", 1, "198.51.100.7"),
        ("10.0.0.2", "6.6.6.6, 198.51.100.7", 1, "198.51.100.7"),
        ("10.0.0.3", "198.51.100.7, 10.0.0.2", 2, "198.51.100.7"),
        ("10.0.0.2", "", 1, "10.0.0.2"),
        (None, "", 0, UNKNOWN_IP),
    ],
    ids=[
        "no-proxy",
        "no-proxy-ignores-a-faked-header",
        "behind-one-proxy",
        "client-written-entries-are-not-trusted",
        "behind-two-proxies",
        "proxy-configured-but-no-header",
        "no-address-at-all",
    ],
)
def test_client_ip(remote_addr: str | None, forwarded_for: str, hops: int, ip: str) -> None:
    assert (
        client_ip_from(remote_addr=remote_addr, forwarded_for=forwarded_for, trusted_hops=hops)
        == ip
    )
