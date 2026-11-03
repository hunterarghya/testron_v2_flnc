import hmac
from uuid import UUID

from modules.assignments.repositories import assignments
from modules.assignments.services.password_cipher import decrypt_password


def is_password_correct(assignment_id: UUID, typed: str) -> bool:
    """The gate's check 7 (domain_model.md §5.4). Compared in constant time. No policy: the
    caller is delivery's start, after its audience check; it also limits the tries."""
    token = assignments.get_password_token(assignment_id)
    if token is None:
        return True
    return hmac.compare_digest(decrypt_password(token).encode(), typed.encode())
