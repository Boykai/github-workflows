# Implementation Plan: Refactor Codebase for Quality, Best Practices, and UX Improvements

**Branch**: `014-codebase-quality-refactor` | **Date**: 2026-02-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/014-codebase-quality-refactor/spec.md`

## Summary

A targeted refactor addressing 10 independent improvements across the backend, frontend, and Docker configuration. Changes range from critical bug fixes (status name mismatch, admin race condition) to medium-priority reliability improvements (lifespan error handling, Docker healthcheck, cookie security) and low-priority quality-of-life enhancements (BoundedDict completeness, dependency cleanup, settings cache helper, cleanup backoff, env file resolution). All changes are isolated to existing files with no new database migrations or API endpoints required.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript / Node 20 (frontend)
**Primary Dependencies**: FastAPI, Pydantic Settings, aiosqlite (backend); React, Vite, Vitest (frontend)
**Storage**: SQLite via aiosqlite (async), migrations in `backend/src/migrations/`
**Testing**: pytest + pytest-anyio (backend, ~975 tests), Vitest + happy-dom (frontend, ~75 tests)
**Target Platform**: Linux server (Docker), local dev (macOS/Linux)
**Project Type**: Web application (backend + frontend monorepo)
**Performance Goals**: Docker healthcheck < 1s (currently multi-second due to Python/httpx startup)
**Constraints**: No new database migrations; all changes backward-compatible
**Scale/Scope**: 10 independent user stories across ~12 existing files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | `spec.md` exists with 10 prioritized user stories (P1–P3), each with independent test criteria and Given-When-Then acceptance scenarios |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/` |
| III. Agent-Orchestrated Execution | ✅ PASS | Plan phase produces plan.md, research.md, data-model.md, contracts/, quickstart.md — handoff to tasks phase is explicit |
| IV. Test Optionality | ✅ PASS | Tests are included where spec acceptance scenarios require verification (race condition simulation, dict interface completeness). No blanket test mandate. |
| V. Simplicity and DRY | ✅ PASS | All changes are minimal edits to existing files. No new abstractions introduced. `effective_cookie_secure` is a computed property (simplest approach). Exponential backoff uses stdlib `min()` — no new dependencies. |

**Gate result**: ALL PASS — proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/014-codebase-quality-refactor/
├── plan.md              # This file
├── research.md          # Phase 0 output — research decisions
├── data-model.md        # Phase 1 output — entity/model changes
├── quickstart.md        # Phase 1 output — implementation guide
├── contracts/           # Phase 1 output — internal contracts
│   └── internal-contracts.md
└── tasks.md             # Phase 2 output (NOT created by speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   ├── auth.py           # US5: cookie_secure → effective_cookie_secure
│   │   └── chat.py           # US1: uses DEFAULT_STATUS_COLUMNS (no change needed — fallback only)
│   ├── config.py             # US5: add effective_cookie_secure property
│   │                         # US8: add clear_settings_cache()
│   │                         # US10: update env_file to check both paths
│   ├── constants.py          # US1: fix DEFAULT_STATUS_COLUMNS values
│   ├── dependencies.py       # US2: atomic admin promotion
│   ├── main.py               # US3: lifespan try/finally
│   │                         # US9: cleanup loop backoff
│   └── utils.py              # US6: BoundedDict already complete (verified)
├── Dockerfile                # US4: healthcheck command
├── tests/
│   └── unit/
│       ├── test_config.py    # US1: update test assertion
│       └── test_main.py      # US3/US9: existing tests may need updates
│
├── docker-compose.yml        # US4: healthcheck command
│
frontend/
├── package.json              # US7: remove jsdom
└── vitest.config.ts          # US7: already uses happy-dom (no change)
```

**Structure Decision**: Web application (Option 2). All changes target existing files in the `backend/` and `frontend/` directories plus Docker configuration at repository root. No new files or directories added to source code.

## Complexity Tracking

> No constitution violations detected. All changes are minimal, isolated edits to existing files.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none) | — | — |
