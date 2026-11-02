"""The caller's IP address, for per-IP rate limits (api_contract.md §5).

Behind a proxy, REMOTE_ADDR is the proxy itself; the real address is the entry that the
nearest trusted proxy added to X-Forwarded-For. Entries further left were written by the
client and can be faked, so only the configured number of hops is trusted (ADR-052).
"""

from django.http import HttpRequest

from core.config import get_settings

UNKNOWN_IP = "unknown"


def client_ip(request: HttpRequest) -> str:
    return client_ip_from(
        remote_addr=request.META.get("REMOTE_ADDR"),
        forwarded_for=request.headers.get("X-Forwarded-For", ""),
        trusted_hops=get_settings().trusted_proxy_hops,
    )


def client_ip_from(*, remote_addr: object, forwarded_for: str, trusted_hops: int) -> str:
    forwarded = [part.strip() for part in forwarded_for.split(",") if part.strip()]
    if trusted_hops and len(forwarded) >= trusted_hops:
        return forwarded[-trusted_hops]
    return remote_addr if isinstance(remote_addr, str) and remote_addr else UNKNOWN_IP
