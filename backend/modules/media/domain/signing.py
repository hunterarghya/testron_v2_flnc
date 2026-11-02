"""ImageKit's upload signature (client-side upload API v1). The local dev adapter uses the
same scheme, so the browser code is identical for both."""

import hashlib
import hmac


def upload_signature(private_key: str, *, token: str, expire: int) -> str:
    """HMAC-SHA1 of `token + expire`, as hex. SHA-1 is ImageKit's choice, not ours; inside
    an HMAC it is still sound."""
    message = f"{token}{expire}".encode()
    return hmac.new(private_key.encode(), message, hashlib.sha1).hexdigest()


def is_signature_valid(private_key: str, *, token: str, expire: int, signature: str) -> bool:
    expected = upload_signature(private_key, token=token, expire=expire)
    return hmac.compare_digest(expected, signature)
