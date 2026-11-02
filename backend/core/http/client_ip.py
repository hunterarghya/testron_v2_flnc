"""The caller's IP address, for per-IP rate limits (api_contract.md §5)."""

from django.http import HttpRequest

UNKNOWN_IP = "unknown"


def client_ip(request: HttpRequest) -> str:
    # Behind the production proxy every REMOTE_ADDR is the proxy itself (backlog O-10)
    address = request.META.get("REMOTE_ADDR")
    return address if isinstance(address, str) and address else UNKNOWN_IP
