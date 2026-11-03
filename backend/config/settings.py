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
# The container's own health check calls http://127.0.0.1:8000
ALLOWED_HOSTS = [*env.allowed_hosts, "127.0.0.1"]
CSRF_TRUSTED_ORIGINS = env.csrf_trusted_origins

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.staticfiles",
    "django.contrib.postgres",  # ArrayField (assignments.source_group_ids, ADR-071)
    "ninja",  # templates + static files for the dev-only API docs
    "modules.identity",
    "modules.students",
    "modules.tagging",
    "modules.media",
    "modules.authoring",
    "modules.assignments",
    "modules.delivery",
    "modules.grading",
    "modules.results",
    "modules.audit",
    "modules.housekeeping",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
    },
]

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

# The built SPA (`nuxt generate`), served by WhiteNoise from the API's own origin (ADR-004).
# It exists only inside the image; in `just dev` the SPA is served by Nuxt on :3000.
SPA_BUILD_DIR = BASE_DIR / "spa_build"
WHITENOISE_ROOT = SPA_BUILD_DIR if SPA_BUILD_DIR.is_dir() else None
WHITENOISE_INDEX_FILE = True
# Nuxt puts a content hash in every file name under /_nuxt/, so browsers may keep them forever
WHITENOISE_IMMUTABLE_FILE_TEST = r"/_nuxt/"

# The local dev adapter keeps uploaded images here (MEDIA_BACKEND=local; gitignored)
LOCAL_MEDIA_ROOT = BASE_DIR / ".media"

# Order as in architecture.md §5.1
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "core.http.middleware.security_headers.SecurityHeadersMiddleware",
    "core.http.middleware.request_id.RequestIdMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    # Ninja's views are CSRF-exempt; this checks every unsafe /api/ request itself
    "core.http.middleware.api_csrf.ApiCsrfMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
]

AUTH_USER_MODEL = "identity.User"
# Pending students log in too (to see their status); what they may do is decided by role
# and admission status, not by Django's is_active flag
AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.AllowAllUsersModelBackend"]
PASSWORD_HASHERS = (
    # Hashing on purpose is slow; tests create many users and only need a valid hash
    ["django.contrib.auth.hashers.MD5PasswordHasher"]
    if env.django_env == "test"
    else ["django.contrib.auth.hashers.Argon2PasswordHasher"]
)
# The password rule: 8+ characters, not a common password (api_contract.md §1)
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
]
# Database sessions that also record the user, so all of a user's sessions can be ended
SESSION_ENGINE = "modules.identity.sessions"

# Turns a request into the Actor the area guards check (core.http.areas, ADR-044):
# the login from identity plus the admission status from students
ACTOR_RESOLVER = "modules.students.actors.resolve_actor"
# The coaching centre's name in every email (core.mail, ADR-060): the teacher's branding
MAIL_BRAND_NAME = "modules.authoring.public.get_coaching_name"

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
