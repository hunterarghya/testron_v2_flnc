"""Django settings. Every value comes from `core.config`, validated once at boot."""

from pathlib import Path

from config.database import database_settings
from config.email import parse_email_url
from core.config import get_settings
from core.logging import logging_config

env = get_settings()
is_prod = env.django_env == "prod"

BASE_DIR = Path(__file__).resolve().parent.parent

# The image build (collectstatic) runs without secrets; every other environment has one
SECRET_KEY = env.secret_key.get_secret_value() if env.secret_key else "image-build-only"
DEBUG = env.debug
ALLOWED_HOSTS = env.allowed_hosts
CSRF_TRUSTED_ORIGINS = env.csrf_trusted_origins

# Auth, sessions and the back office come with the identity module. Django needs our
# custom user model before the very first migration, so they are not installed yet.
INSTALLED_APPS: list[str] = []

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "core.http.middleware.request_id.RequestIdMiddleware",
]

# Turns a request into the Actor the area guards check (core.http.areas).
# Nobody can log in until the identity module provides the real one.
ACTOR_RESOLVER = "core.http.areas.anonymous_actor"

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

DATABASES = (
    database_settings(env.database_url, direct_url=env.database_url_direct)
    if env.database_url
    else {}
)
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Stored and sent in UTC; the browser shows Asia/Kolkata (domain_model.md §0)
USE_TZ = True
TIME_ZONE = "UTC"
LANGUAGE_CODE = "en"
USE_I18N = False

# Production sits behind a TLS proxy (Caddy or Render), which sets X-Forwarded-Proto
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https") if is_prod else None
SECURE_SSL_REDIRECT = is_prod
# The container's own health check calls plain http on 127.0.0.1
SECURE_REDIRECT_EXEMPT = [r"^api/v1/healthz$"]
SECURE_HSTS_SECONDS = 31_536_000 if is_prod else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = is_prod
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SESSION_COOKIE_SECURE = is_prod
CSRF_COOKIE_SECURE = is_prod

_email = parse_email_url(env.email_url)
EMAIL_BACKEND = (
    "django.core.mail.backends.locmem.EmailBackend"
    if env.django_env == "test"
    else "django.core.mail.backends.smtp.EmailBackend"
)
EMAIL_HOST = _email.host
EMAIL_PORT = _email.port
EMAIL_HOST_USER = _email.user
EMAIL_HOST_PASSWORD = _email.password
EMAIL_USE_TLS = _email.use_tls
EMAIL_USE_SSL = _email.use_ssl
# Mail is sent inside the request (there is no worker), so it must never hang it
EMAIL_TIMEOUT = 5
DEFAULT_FROM_EMAIL = env.email_from

LOGGING = logging_config()
