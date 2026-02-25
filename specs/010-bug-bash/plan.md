# Implementation Plan: Bug Bash — Codebase Quality & Reliability Sweep

**Branch**: `010-bug-bash` | **Date**: 2026-02-24 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/010-bug-bash/spec.md`

## Summary

Systematic codebase sweep fixing security vulnerabilities (session token in URL, plaintext token storage, unverified webhooks, dev-login in production), pipeline correctness bugs (false-positive completion detection, unretried issue creation), DRY violations (repo resolution, header construction, cache pruning, PR filtering — all duplicated 3-10x), error handling gaps (missing Retry-After header, stub endpoints returning fake success), frontend behavioral issues (dual WebSocket+polling, no reconnection backoff, mutation used for reads), and architectural debt (cross-module private attribute access, circular import hacks) across a FastAPI + React + SQLite web application.

## Technical Context

**Language/Version**: Python ≥3.11 (pyright targets 3.12), TypeScript ~5.4  
**Primary Dependencies**: FastAPI ≥0.109, React 18.3, TanStack Query v5, Vite 5, httpx ≥0.26, pydantic ≥2.5, aiosqlite ≥0.20, socket.io-client 4.7, dnd-kit 6.3  
**Storage**: SQLite (WAL mode) via aiosqlite, file-backed at `/app/data/settings.db`  
**Testing**: pytest ≥7.4 + pytest-asyncio (backend, 926+ tests), vitest ≥4.0 (frontend unit), Playwright ≥1.58 (E2E)  
**Target Platform**: Linux server (Docker Compose), browser SPA  
**Project Type**: Web application (backend + frontend)  
**Performance Goals**: Not explicitly defined; current polling interval configurable (default 60s)  
**Constraints**: Single-tenant deployment, single SQLite writer, in-memory state acceptable for MVP  
**Scale/Scope**: Single-user tool automating GitHub Projects V2 with 4-agent AI pipeline; ~30 backend source files, ~20 frontend source files

### Key Technical Details

**Config**: `Settings` (pydantic-settings) with `debug: bool = False`, `github_webhook_secret: str | None`, `copilot_polling_interval: int = 60`, `database_path`, `cors_origins`, `cookie_secure: bool = False`. Global getter: `@lru_cache get_settings()`.

**Auth Flow**: OAuth callback redirects with `?session_token=...` in URL. Cookie-based session via `SESSION_COOKIE_NAME`. Dev-login at `/auth/dev-login` checks `settings.debug`. Session cleanup loop runs as background task.

**Pipeline**: 4-stage agent pipeline (specify→plan→tasks→implement). Completion detection in `copilot_polling/completion.py` uses 3 signals; Signal 3 can false-positive on agent unassignment without commits. State tracked in 8 module-level mutable globals in `copilot_polling/state.py`.

**DI Pattern**: `dependencies.py` provides 3 FastAPI `Depends()` functions. However, `chat.py` and other modules import singletons directly. `webhooks.py` accesses `github_projects_service._client` (private).

**Existing Utilities**: `src/utils.py` has `resolve_repository()` — the intended shared repo resolver — but 4+ call sites in `workflow.py` and 1 in `projects.py` use inline 3-step resolution instead.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | `spec.md` created with 8 prioritized user stories, GWT acceptance scenarios, clarifications resolved |
| II. Template-Driven | ✅ PASS | Using canonical `plan.md` template, all artifacts follow `.specify/templates/` |
| III. Agent-Orchestrated | ✅ PASS | Plan phase produces plan.md, research.md, data-model.md, contracts/, quickstart.md |
| IV. Test Optionality | ✅ PASS | Tests included — spec mandates test coverage for security and correctness fixes (SC-001 through SC-010) |
| V. Simplicity and DRY | ✅ PASS | Core goal of this feature is DRY consolidation and simplification; no premature abstraction — all changes fix identified issues |

**Gate result: PASS** — no violations, no complexity justification needed.

### Post-Design Re-Evaluation

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | All design artifacts trace back to spec.md FRs. No scope creep in contracts. |
| II. Template-Driven | ✅ PASS | All artifacts (plan.md, research.md, data-model.md, contracts/, quickstart.md) follow canonical templates. |
| III. Agent-Orchestrated | ✅ PASS | Phase 0 and Phase 1 complete with clear handoff to Phase 2 (tasks). |
| IV. Test Optionality | ✅ PASS | Tests mandated by spec success criteria (SC-001–SC-010). Implementation phases (quickstart.md) sequence test verification after each phase. |
| V. Simplicity and DRY | ✅ PASS | Design consolidates duplicated patterns (repo resolver, header builder, PR filter, cache pruning) into single-source-of-truth utilities. New abstractions (`EncryptionService`, `BoundedSet/Dict`, `RequestIDMiddleware`) are minimal, justified by spec requirements, and follow existing project conventions. |

**Post-design gate result: PASS**

## Project Structure

### Documentation (this feature)

```text
specs/010-bug-bash/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   ├── auth.py              # FR-001, FR-002: secure token delivery, gate dev-login
│   │   ├── chat.py              # FR-016: fix direct imports → DI
│   │   ├── projects.py          # FR-011: use shared repo resolver
│   │   ├── settings.py          # FR-005: session-owner auth check
│   │   ├── tasks.py             # FR-010: stub → 501
│   │   ├── webhooks.py          # FR-004, FR-015: verify signatures, eliminate _client access
│   │   └── workflow.py          # FR-011: use shared repo resolver
│   ├── middleware/
│   │   └── request_id.py        # FR-024: new request-ID middleware
│   ├── models/                  # Existing models (minimal changes)
│   ├── services/
│   │   ├── copilot_polling/
│   │   │   ├── completion.py    # FR-007: fix false-positive detection
│   │   │   ├── pipeline.py      # FR-013, FR-022: shared cache pruning, configurable delays
│   │   │   ├── state.py         # FR-023: bounded growth
│   │   │   └── recovery.py      # FR-013: shared cache pruning
│   │   ├── github_projects/
│   │   │   └── service.py       # FR-008, FR-012, FR-014, FR-015, FR-021: retry, headers, filtering, public API, pagination
│   │   ├── workflow_orchestrator/
│   │   │   └── orchestrator.py  # FR-016: resolve circular imports
│   │   ├── crypto.py            # FR-003: new — Fernet encryption utility
│   │   ├── github_auth.py       # FR-003, FR-006: encrypt tokens, expire OAuth states
│   │   └── session_store.py     # FR-003: encrypt/decrypt tokens on read/write
│   ├── config.py                # FR-003: add ENCRYPTION_KEY setting
│   ├── exceptions.py            # FR-009: RateLimitError used for Retry-After
│   ├── main.py                  # FR-009, FR-020, FR-024: error handler, health, middleware
│   └── utils.py                 # FR-011, FR-013: shared repo resolver, cache pruning utility
│
├── tests/
│   ├── unit/                    # New tests for FR-001–FR-024
│   └── integration/             # New tests for security, health, webhook verification

frontend/
├── src/
│   ├── hooks/
│   │   ├── useRealTimeSync.ts   # FR-017, FR-018: stop polling on WS, exponential backoff
│   │   └── useWorkflow.ts       # FR-019: mutation → query for getConfig
│   └── services/                # Existing API service layer (minimal changes)
```

**Structure Decision**: Web application (existing backend/ + frontend/ structure). No new top-level directories. One new file (`backend/src/services/crypto.py`) for encryption utility, one new file (`backend/src/middleware/request_id.py`) for request-ID middleware. All other changes are modifications to existing files.

## Complexity Tracking

> No constitution violations detected. No complexity justification needed.
