"""The assignment password is stored encrypted, so the teacher can reveal it (ADR-018,
ADR-070). The first key encrypts; every key decrypts, so keys can be rotated."""

from cryptography.fernet import Fernet, MultiFernet

from core.config import ConfigError, get_settings


def encrypt_password(password: str) -> str:
    return _cipher().encrypt(password.encode()).decode()


def decrypt_password(token: str) -> str:
    return _cipher().decrypt(token.encode()).decode()


def _cipher() -> MultiFernet:
    secret = get_settings().assignment_password_key
    if secret is None:
        raise ConfigError("ASSIGNMENT_PASSWORD_KEY is not set")
    keys = secret.get_secret_value().split(",")
    return MultiFernet([Fernet(key.strip()) for key in keys])
