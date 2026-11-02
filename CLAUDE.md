# CLAUDE.md

Instructions for Claude (and any developer) working in this repo. **Short by design:** the full rules live in `docs/`, and this file says which doc to read and which rules are never broken.

## What this is

A private online test platform for **one coaching center**: one teacher (super admin) and their students. Biology; MCQ, MSQ and numerical questions; Bengali content.
- **Backend:** Django 6 + Django Ninja, a modular monolith.
- **Frontend:** a Nuxt 4 SPA (`ssr:false`) + Nuxt UI.
- **Database:** PostgreSQL (Neon in prod).
- **Images:** ImageKit.
- **Runtime:** one container. No worker, no Redis, no WebSockets.

## Read before you change

| You're changing | Read first |
| :--- | :--- |
| Any business rule (timing, marking, visibility, attempts) | `docs/domain_model.md` (**the source of truth**: if code disagrees, the code is wrong) |
| Tables, columns, constraints | `docs/database_schema.md` |
| Endpoints, DTOs, error codes | `docs/api_contract.md` |
| Where a file goes, naming, size limits | `docs/project_structure.md` |
| Editor or rich content | `docs/editor_content_spec.md` |
| Exam hall, frontend behaviour | `docs/frontend_spec.md` |
| Authorization, anything security-sensitive | `docs/security.md` |
| Tests | `docs/testing_strategy.md` |
| What to build next and the definition of done | `docs/build_phases.md` |
| Why something is the way it is | `docs/decisions.md` (ADRs) |

## Non-negotiable rules

1. **Never send correctness to a student before publication.** No `is_correct`, correct answers, solutions, marks or scores in any `/my/*` or `/attempts/*` response unless `result_visible()` says so. Student DTOs must not even have such fields.
2. **The server owns time.** Every deadline is checked on the server with `ctx.now`. Domain functions take `now` as an argument and never read the clock.
3. **Every use case calls a policy.** Not yours → `NotFound` (404). Wrong role → `Forbidden`. Two gates: the router area guard **and** the use-case policy.
4. **No implicit endpoints.** Every path is registered in its module's `routes.py`. No DRF, no generic viewsets, no `fields="__all__"`, no Django signals, no logic in `save()` or middleware.
5. **No raw HTML from data.** Rich content is validated JSON. `v-html` is forbidden. The only exception is KaTeX output in `renderMath.ts`.
6. **Never lose an answer.** Saves are idempotent by `client_seq`. Attempts end at their **deadline instant**. Ending and grading happen in **one transaction**.
7. **Decimals, not floats**, for marks and numerical answers. JSON carries decimal strings.
8. **The paper is immutable.** Test edits never change an assignment's paper. Key fixes go through `correct_answer_key` (audited + regrade).

## Code quality (the standard every change must meet)

The code should be a **textbook example of clean code**: modular, readable, single responsibility, compact, optimized where it matters, and free of regressions. In practice:

- **One function does one thing.** If you need "and" to describe it, split it.
- **Never write a second function that does what an existing one does.** Search first, then reuse. Shared logic belongs in `domain/`, `core/` or the frontend's `shared/`.
- **Files are compact, and functions are only as long as they need to be** (limits below).
- **Optimize what matters:** no N+1 queries, no repeated work, indexes that match the queries. Don't trade readability for cleverness.
- **No regressions:** never edit a failing test just to make it pass. Fix the code, or explain why the rule changed.
- **Comments are short, meaningful and in plain, everyday language.** A non-programmer should understand them. Explain why, not what.
- **Frontend:**
  - Use Nuxt UI's built-in components for everything they cover.
  - Build a custom component only when Nuxt UI has nothing for the job. Put it in `shared/components/` and reuse it everywhere.
  - **Never use inline CSS** (`style=` or `:style`). Use Nuxt UI props, the theme and Tailwind classes.

Full rules: `docs/project_structure.md` §1.

## Where code goes (backend module layout)

```
modules/<module>/
  routes.py            path → controller (router.add_api_operation); no logic
  controllers/         parse request → call ONE service → map to DTO; no ORM, no decisions
  dto/                 Pydantic <Name>In / <Name>Out, extra="forbid"
  services/commands/   one file = one state-changing use case = one public function of the same name
  services/queries/    one file = one read for a screen (get_x / list_x)
  policies.py          ensure_<actor>_can_<action>(actor, obj)
  domain/              PURE functions + frozen dataclasses + errors (no Django, no I/O, no clock)
  repositories/        ALL ORM access, named functions (get_x_for_update, list_x_by_y)
  models/              Django models + Meta.constraints only
  public.py            the ONLY thing other modules may import
  tests/{domain,services,api}/
core/                  shared kernel (config, errors, clock, ctx, http, rich_content, rate_limit, mail); imports no module
```

**Frontend:**
- `pages/` are thin (≤ 80 lines), and screens are built in `features/<feature>/`.
- `engine/` is framework-free TypeScript (clock, save queue, integrity, stage navigator, keyboards).
- `api/schema.d.ts` is generated, never edited.
- Network calls go only through `api/client.ts`.
- The only Pinia store is `stores/examSession.ts`.

## Limits (CI-enforced; never raise them for one file: split by responsibility instead)

| Limit | Value |
| :--- | :--- |
| Function | ≤ 40 lines · complexity ≤ 8 · ≤ 6 params (keyword-only after `ctx, id`) |
| Python files | ≤ 200 lines · service file ≤ 120 · test file ≤ 400 |
| Frontend files | Vue SFC ≤ 200 lines · page ≤ 80 · TS module ≤ 200 |
| Typing | `mypy --strict`, `vue-tsc` strict, no `Any`/`any` in domain, services or app code |

## Naming

- **Commands:** `verb_noun` (`start_attempt`). **Queries:** `get_x` / `list_xs`.
- **Policies:** `ensure_…`. **Predicates:** `is_` / `can_` / `has_`.
- **Domain errors** name the condition (`AttemptEnded`, `StageClosed`), and each declares its `code` and status once.
- **DTOs:** `XIn` / `XOut`. **Service results:** frozen `XResult` / `XView` dataclasses.
- **Tests:** `test_<behaviour>_<when>`. V1 regressions: `test_v1_fNN_<what>`.
- **Vocabulary:** use `docs/domain_model.md` §1 (Test, Assignment, Paper, Attempt, Stage, Response, Grade, …). No synonyms.

## Recipe: adding an endpoint

1. Rule in `domain/` + table tests.
2. Service file in `services/commands|queries/` with a docstring citing the `domain_model.md` section, plus service tests (happy path, each error, policy, idempotency, transaction).
3. DTOs in `dto/`.
4. Controller function.
5. One line in `routes.py`.
6. API tests + a query-count test for lists. Add the route to the area-matrix expectations (`tests/security`).
7. `just openapi` (regenerates `docs/api/openapi.json` + the TS client).
8. Frontend: a feature composable → components → a thin page.
9. Update docs that describe changed behaviour, **in the same commit**.

## Commands

```bash
just infra            # postgres + mailpit (Docker)
just dev              # Django :8000 + Nuxt :3000 (hot reload)
just test             # all backend + frontend unit tests
just test-fast <mod>  # domain + one module's service tests
just lint             # every static gate CI runs
just openapi          # export OpenAPI + regenerate the TS client
just migrate / just makemigrations name=<x>
just full             # run the production image locally
just e2e              # Playwright against the full stack
```

**Before saying a step is done:** run `just lint && just test`. If either fails, the step isn't done. Report failures honestly, with the output.

## Workflow (how we build)

- **Follow `docs/build_phases.md`** phase by phase, step by step. One step = one reviewable change.
- **Order inside a step:** domain + tests → service + tests → API + tests → UI → E2E (when the phase requires it).
- **Don't commit or push.** At the end of each step, **propose a commit message**; the developer reviews and commits. Format (Conventional Commits):
  ```
  <type>(<scope>): <imperative summary ≤ 72 chars>

  <why, 1–5 lines>
  - <notable change>
  Refs: <doc §, ADR-xxx, backlog id>
  ```
  - **Types:** feat, fix, test, refactor, docs, build, ci, chore.
  - **Scope:** the module name, `core`, `ui-<area>`, `infra` or `docs`.
- **New decision** (library choice, pattern, trade-off) → append an ADR to `docs/decisions.md`. Never edit old ADRs: supersede them.
- **Something deferred, or a bug noticed but not fixed** → add it to `docs/backlog.md`.
- **Unclear requirement** → ask; don't guess. If the docs conflict, `domain_model.md` wins, then `api_contract.md`, then the rest. Flag the conflict.

## Never

- Read the clock inside `domain/`; use `datetime.now()` / `timezone.now()` outside `core/clock.py`.
- Import another module's internals (only `modules.<x>.public`).
- Query the DB in a controller, policy or domain function.
- Return `None` to signal failure, or swallow exceptions.
- Add a dependency without an ADR.
- Disable a lint rule inline without a comment linking the ADR or doc section that allows it.
- Use floats for marks, naive datetimes, or `fetch` outside `api/` (or `features/exports/`).
- Put secrets in code, tests, fixtures or logs.
