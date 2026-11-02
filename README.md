# <Coaching Name> Test Platform

A private online test platform for a coaching center: **one teacher** writes and runs tests, and **their students** take them. They take them in the browser, on time, fairly, with nothing lost.

## What it does

**For the teacher** (`/admin`):
- **Admission:** approve student sign-up requests in bulk and organize students into groups.
- **Writing tests:** a document-style editor with Bengali paste, images (in options too), equations and chapter/topic tags. Tests can be sectioned, total-timer or rapid-fire.
- **Running tests:**
  - **Assign** a test to groups or individual students: locked (password + teacher start), scheduled, deadline or open.
  - **Run a live test:** lobby, Start for everyone, live monitor, extend time, end for everyone, retakes.
- **Results:**
  - **Review** results: gradebook, question statistics, answer-key correction with automatic regrade.
  - **Publish** manually or automatically, choosing what students see.
  - **Export** answer sheets and keys (HTML → PDF) and the gradebook (CSV).
- **Performance:** see chapter-wise and topic-wise strengths and weaknesses for each student or group, and share them with students.

**For students:**
- Log in, see assigned tests, wait in the lobby, and take tests fullscreen.
- Autosave works offline too. Refreshing resumes the test. The on-screen numeric keypad is available.
- See past results and shared performance once the teacher publishes them.

## Stack

| Part | Tech |
| :--- | :--- |
| Backend | Python 3.13, Django 6, Django Ninja (Pydantic DTOs), Gunicorn |
| Frontend | Nuxt 4 (SPA), Nuxt UI, Tailwind, TipTap, KaTeX, Pinia (exam session only) |
| Database | PostgreSQL 17 (Neon in production) |
| Media | ImageKit (direct signed uploads) |
| Tooling | uv, pnpm, just, ruff, mypy, import-linter, pytest, Vitest, Playwright, k6 |
| Runtime | One Docker image (API + SPA), on an Oracle Cloud VM (Caddy) or Render |

## Quick start

**Prerequisites:** Docker, uv, Node 22 (with corepack), just. On Windows, also Git for Windows (`just` runs its recipes in Git Bash); WSL is not needed.

```bash
cp .env.example .env
just setup        # install backend + frontend dependencies
just infra        # postgres + mailpit in Docker
just migrate      # create the schema
just seed         # teacher account (from .env) + app settings
just dev          # API :8000, SPA :3000
```

- **App:** http://localhost:3000
- **Emails (OTP codes):** Mailpit at http://localhost:8025
- **API docs (dev only):** http://localhost:8000/api/v1/docs

More commands: `just --list`, or `docs/dev_environment_and_deployment.md`.

## Repository layout

```
backend/     Django project: config/, core/ (shared kernel), modules/<module>/ (one per business area)
frontend/    Nuxt app: pages/, features/<feature>/, engine/ (exam-hall core), shared/, api/
docs/        design docs, decisions, backlog, API contract (docs/api/openapi.json)
scripts/     CI helpers (boundary and file-size checks, OpenAPI export)
```

Each backend module follows the same layers: routes → controllers → DTOs → services (commands/queries) → policies · domain · repositories → models. See `docs/project_structure.md`.

## Documentation

| Doc | Contents |
| :--- | :--- |
| [`docs/prd.md`](docs/prd.md) | Requirements |
| [`docs/screens.md`](docs/screens.md) | Screens, wireframes, user flows |
| [`docs/domain_model.md`](docs/domain_model.md) | Business rules (the source of truth) |
| [`docs/database_schema.md`](docs/database_schema.md) | Tables, constraints, indexes |
| [`docs/api_contract.md`](docs/api_contract.md) | Endpoints, DTOs, error codes |
| [`docs/architecture.md`](docs/architecture.md) | How the system fits together |
| [`docs/project_structure.md`](docs/project_structure.md) | Code layout and coding rules |
| [`docs/editor_content_spec.md`](docs/editor_content_spec.md) | Rich content and the editor |
| [`docs/frontend_spec.md`](docs/frontend_spec.md) | Frontend behaviour and the exam engine |
| [`docs/security.md`](docs/security.md) | Authorization and threat model |
| [`docs/testing_strategy.md`](docs/testing_strategy.md) | Test suites and gates |
| [`docs/dev_environment_and_deployment.md`](docs/dev_environment_and_deployment.md) | Local setup, CI/CD, deployment, runbook |
| [`docs/build_phases.md`](docs/build_phases.md) | Build plan and definition of done |
| [`docs/decisions.md`](docs/decisions.md) | Architecture decision log |
| [`docs/backlog.md`](docs/backlog.md) | Deferred work and known issues |
| [`CLAUDE.md`](CLAUDE.md) | Working rules for AI-assisted and human development |

## Contributing

- **Read `CLAUDE.md`, then follow `docs/build_phases.md`.**
- **Commits** use Conventional Commits, and every change goes through CI (lint, types, layer boundaries, file sizes, tests, OpenAPI snapshot).
- **Deploying:** see `docs/dev_environment_and_deployment.md` §4.3, and **never deploy during a live test**.

## License

Proprietary. All rights reserved.
