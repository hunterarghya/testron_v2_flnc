# Every command anyone needs (dev_environment_and_deployment.md §1.4). `just` lists them.
# Recipes are bash so CI runs the same ones. On Windows they run in Git Bash (ADR-041):
# the plain `bash` on a Windows PATH is the WSL launcher, so its full path is given.
set shell := ["bash", "-cu"]
set windows-shell := ["C:/Program Files/Git/bin/bash.exe", "-cu"]

export COREPACK_ENABLE_DOWNLOAD_PROMPT := "0"

pnpm := "corepack pnpm"

# List the recipes
default:
    @just --list --unsorted

# Install backend and frontend dependencies
setup:
    cd backend && uv sync
    cd frontend && {{pnpm}} install --frozen-lockfile

# Start Postgres and Mailpit (Mailpit UI: http://localhost:8025)
infra:
    docker compose --profile infra up -d --wait

# Stop Postgres and Mailpit (the database volume is kept)
infra-down:
    docker compose --profile infra down

# API on :8000 and the SPA on :3000 (open http://localhost:3000), with hot reload
dev:
    trap 'kill 0' EXIT; just api & just web & wait

# Only the API (Django runserver on :8000)
api:
    cd backend && uv run python manage.py runserver 8000

# Only the SPA (Nuxt on :3000; /api goes to :8000)
web:
    cd frontend && {{pnpm}} dev

# Apply migrations to the local database
migrate:
    cd backend && uv run python manage.py migrate

# Create or update the teacher account from .env (safe to repeat)
seed:
    cd backend && uv run python manage.py seed

# Check .env and print the effective settings (secrets hidden)
check-config:
    cd backend && uv run python manage.py check_config

# Wipe the local database, then migrate and seed it again
[confirm("This deletes ALL data in the local database. Continue?")]
db-reset:
    docker compose --profile infra exec -T postgres psql -U app -d postgres -c "DROP DATABASE IF EXISTS app WITH (FORCE)" -c "CREATE DATABASE app OWNER app"
    just migrate
    just seed

# Create migrations after a model change: just makemigrations add_users
makemigrations name:
    cd backend && uv run python manage.py makemigrations --name {{name}}

# Every static gate CI runs (project_structure.md §4.3)
lint:
    cd backend && uv run ruff format --check . ../scripts
    cd backend && uv run ruff check . ../scripts
    cd backend && DJANGO_ENV=build uv run mypy . ../scripts
    cd backend && uv run lint-imports
    cd backend && uv run python ../scripts/check_module_boundaries.py
    cd backend && uv run python ../scripts/check_file_sizes.py
    cd backend && DJANGO_ENV=build uv run python manage.py makemigrations --check --dry-run
    cd frontend && {{pnpm}} lint
    cd frontend && {{pnpm}} typecheck

# Fix formatting and the auto-fixable lint findings
fmt:
    cd backend && uv run ruff format . ../scripts
    cd backend && uv run ruff check --fix . ../scripts
    cd frontend && {{pnpm}} lint:fix

# All backend and frontend tests, with the coverage gates (needs `just infra`).
# The test database is rebuilt every time, so new migrations are always applied.
test:
    cd backend && uv run pytest -q --cov --cov-report=term --cov-report=json:coverage.json
    cd backend && uv run python ../scripts/check_coverage.py coverage.json
    cd frontend && {{pnpm}} exec vitest run --coverage

# Domain tests of every module + one module's service tests: just test-fast delivery
# Reuses the test database; add --create-db after a migration change.
test-fast module *pytest_args:
    cd backend && uv run pytest --reuse-db -q modules/*/tests/domain modules/{{module}}/tests/services {{pytest_args}}

# Export the API contract and regenerate the TypeScript client (ADR-020)
openapi:
    cd backend && uv run python ../scripts/export_openapi.py
    cd frontend && {{pnpm}} gen:api

# Run the production image locally at http://localhost:8000 (needs .env)
full:
    docker compose --profile full up --build

# Stop the production image and its services
full-down:
    docker compose --profile full down

# Try the production setup on this PC at https://localhost: the real image in prod mode, behind
# Caddy, with local Postgres and Mailpit (docs/hosting_guide.md). Makes its env file the first time.
prod-local:
    test -f deploy/oracle/.env.localprod || uv run --project backend python scripts/make_env.py local-prod
    docker compose -f deploy/oracle/compose.prod.yml -f deploy/oracle/compose.local.yml --env-file deploy/oracle/.env.localprod up --build -d
    @echo "Open https://localhost (accept the local certificate). Emails: http://localhost:8026"

# Stop it (add -v to also delete its database: just prod-local-down -v)
prod-local-down *flags:
    docker compose -f deploy/oracle/compose.prod.yml -f deploy/oracle/compose.local.yml --env-file deploy/oracle/.env.localprod down {{flags}}

# Write deploy/oracle/.env for production with fresh secrets:
#   just env-production tests.example.com teacher@example.com "Mrs Sen"
env-production domain email name:
    uv run --project backend python scripts/make_env.py production --domain {{domain}} --teacher-email {{email}} --teacher-name "{{name}}"
