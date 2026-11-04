# One image: the Django API + the built SPA, served from one origin (ADR-004, ADR-021).
# Multi-arch (amd64 + arm64 for the Oracle A1 VM). Runs as a non-root user.

# 1) Build the SPA to static files
FROM node:22.23.4-slim AS spa
ENV COREPACK_ENABLE_DOWNLOAD_PROMPT=0
WORKDIR /fe
RUN corepack enable
COPY frontend/package.json frontend/pnpm-lock.yaml frontend/pnpm-workspace.yaml ./
# Dependency install scripts stay off here; `nuxt generate` prepares everything it needs
RUN pnpm install --frozen-lockfile --ignore-scripts
COPY frontend/ ./
COPY docs/api/openapi.json /docs/api/openapi.json
RUN pnpm gen:api && pnpm generate

# 2) Install the Python dependencies
FROM python:3.13-slim AS deps
COPY --from=ghcr.io/astral-sh/uv:0.13.6 /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
WORKDIR /app
COPY backend/pyproject.toml backend/uv.lock backend/.python-version ./
RUN uv sync --frozen --no-dev --no-install-project

# 3) Runtime
FROM python:3.13-slim AS runtime
ARG E2E_TEST_HOOKS=0
ARG APP_VERSION=dev
ARG APP_COMMIT=unknown
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    E2E_TEST_HOOKS=${E2E_TEST_HOOKS} \
    APP_VERSION=${APP_VERSION} \
    APP_COMMIT=${APP_COMMIT}
RUN useradd --uid 10001 --create-home app
WORKDIR /app
COPY --from=deps /app/.venv /app/.venv
COPY backend/ ./
COPY --from=spa /fe/.output/public ./spa_build/
RUN DJANGO_ENV=build python manage.py collectstatic --noinput
USER app
EXPOSE 8000
# A start with MIGRATE_ON_START=1 migrates first, so it gets a minute before checks count
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('PORT', '8000') + '/api/v1/healthz', timeout=4)"
CMD ["sh", "/app/start.sh"]
