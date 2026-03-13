# Implementation Plan: Codebase Modernization & Technical Debt Reduction

**Branch**: `038-code-quality-overhaul` | **Date**: 2026-03-12 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/038-code-quality-overhaul/spec.md`

## Summary

Consolidate duplicated backend patterns (error handling, repository resolution, caching), decompose the monolithic chat module and wire in existing-but-unused SQLite persistence, auto-generate frontend TypeScript types from the backend OpenAPI schema, decompose oversized frontend hooks, and fill test coverage gaps — all targeting measurable LOC reduction, zero behavior regressions, and improved developer velocity.

## Technical Context

**Language/Version**: Python >=3.12 (backend), TypeScript 5.9 (frontend)
**Primary Dependencies**: FastAPI >=0.135, React 19.2, Vite 7.3, TanStack Query 5.90, Tailwind CSS 4.2, Radix UI
**Storage**: SQLite via aiosqlite (WAL mode), 22 existing migrations
**Testing**: pytest >=9.0 / pytest-asyncio / pytest-cov (backend), Vitest 4.0 / RTL / Playwright 1.58 (frontend)
**Target Platform**: Docker containers (Linux) — backend:8000, frontend nginx:5173, signal-api:8080
**Project Type**: Web application (frontend + backend)
**Performance Goals**: Zero performance regression — all existing tests pass without modification after consolidation
**Constraints**: SQLite remains the database; no external monitoring services (Sentry, Datadog); no new user-facing features
**Scale/Scope**: ~17 API endpoint files, ~27 service modules, 46 frontend hooks, 7 pages, 55+ unit tests, 4 integration tests

### Pre-existing Infrastructure (Already Built)

The codebase already has several components that this overhaul leverages rather than builds from scratch:

| Component | Location | Status |
|-----------|----------|--------|
| `handle_service_error()` | `logging_utils.py` | ✅ Built, used in 4/17 API files — needs wider adoption |
| `handle_github_errors()` decorator | `logging_utils.py` | ✅ Built — needs wider adoption |
| `StructuredJsonFormatter` | `logging_utils.py` | ✅ Built — needs to be activated for production |
| `RequestIDMiddleware` | `middleware/request_id.py` | ✅ Built and registered in `main.py` |
| `CSPMiddleware` | `middleware/csp.py` | ✅ Built and registered in `main.py` |
| CSP headers in nginx | `frontend/nginx.conf` | ✅ Already configured |
| `resolve_repository()` | `utils.py` | ✅ Canonical function exists — `chat.py` has a duplicate `_resolve_repository()` |
| `require_selected_project()` | `dependencies.py` | ✅ Already a FastAPI dependency |
| `cached_fetch()` | `utils.py` | ✅ Generic cache wrapper exists |
| `InMemoryCache` | `services/cache.py` | ✅ Full TTL/ETag cache implementation |
| `chat_store.py` | `services/chat_store.py` | ✅ Built, zero imports (dead code) — needs wiring |
| `012_chat_persistence.sql` | `migrations/` | ✅ Tables created — chat_messages, chat_proposals, chat_recommendations |
| `AppException` hierarchy | `exceptions.py` | ✅ 11 exception classes with proper HTTP status codes |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Evaluation

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Specification-First | ✅ PASS | `spec.md` complete with 6 prioritized user stories, 21 FRs, 12 SCs, acceptance scenarios, scope boundaries |
| II. Template-Driven Workflow | ✅ PASS | Using canonical `spec-template.md` and `plan-template.md` via speckit commands |
| III. Agent-Orchestrated Execution | ✅ PASS | Executing via `speckit.specify` → `speckit.plan` → `speckit.tasks` pipeline |
| IV. Test Optionality with Clarity | ✅ PASS | Tests explicitly requested in spec: FR-016 (page tests), FR-017 (component tests), FR-018 (chat persistence integration test). TDD not mandated. |
| V. Simplicity and DRY | ✅ PASS | Feature purpose IS DRY/simplicity. Leverages existing infrastructure (13 pre-built components). No premature abstractions. |

**Gate Result**: ✅ ALL GATES PASS — proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/038-code-quality-overhaul/
├── plan.md              # This file
├── research.md          # Phase 0: Technology decisions and best practices
├── data-model.md        # Phase 1: Entity definitions and relationships
├── quickstart.md        # Phase 1: Developer quickstart guide
├── contracts/           # Phase 1: API contract definitions
│   ├── error-response.md
│   └── type-generation.md
└── tasks.md             # Phase 2 output (NOT created by speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   ├── chat.py              # MODIFY: decompose into sub-modules, adopt shared error helpers
│   │   ├── chat/                # NEW: chat sub-module package
│   │   │   ├── __init__.py      # Router aggregation
│   │   │   ├── commands.py      # Agent command handling
│   │   │   ├── messaging.py     # Core message CRUD
│   │   │   ├── proposals.py     # Proposal confirm/cancel flow
│   │   │   └── uploads.py       # File upload handling
│   │   ├── *.py                 # MODIFY: adopt handle_service_error() across all 13 remaining files
│   ├── middleware/
│   │   ├── csp.py               # EXISTS: no changes needed
│   │   └── request_id.py        # EXISTS: no changes needed
│   ├── models/                  # MODIFY: ensure all route definitions declare response_model
│   ├── services/
│   │   ├── chat_store.py        # EXISTS: wire into chat sub-modules
│   │   └── ...
│   ├── logging_utils.py         # EXISTS: activate StructuredJsonFormatter for production
│   ├── utils.py                 # EXISTS: canonical resolve_repository(), cached_fetch()
│   ├── dependencies.py          # EXISTS: require_selected_project() already present
│   └── migrations/              # EXISTS: 012_chat_persistence.sql tables ready
└── tests/
    ├── unit/                    # MODIFY: add tests for new chat sub-modules
    └── integration/
        └── test_chat_persistence.py  # NEW: restart-survival integration test

frontend/
├── src/
│   ├── hooks/
│   │   ├── usePipelineConfig.ts      # MODIFY: decompose into sub-hooks
│   │   ├── usePipelineOrchestration.ts  # NEW: orchestration concern
│   │   ├── usePipelineCrud.ts        # NEW: CRUD operations
│   │   └── usePipelineDirtyState.ts  # NEW: dirty-state tracking
│   ├── pages/                        # MODIFY: add test files for untested pages
│   ├── components/pipeline/          # MODIFY: add test files for key components
│   ├── types/
│   │   ├── index.ts                  # MODIFY: replace manual types with generated
│   │   └── generated.ts              # NEW: auto-generated from OpenAPI schema
│   └── constants/
│       └── generated.ts              # NEW: auto-generated status/label constants
├── scripts/
│   └── generate-types.sh             # NEW: OpenAPI → TypeScript generation script
└── tests/                            # Vitest tests co-located with source or in __tests__/
```

**Structure Decision**: Web application (Option 2). Backend and frontend are separate Docker services with distinct build pipelines. Chat module decomposition creates a new `api/chat/` package. Frontend type generation adds build-time artifact files.

## Complexity Tracking

> No constitution violations detected. All changes leverage existing infrastructure.

---

## Post-Design Constitution Re-evaluation

*Re-check after Phase 1 design artifacts are complete.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Specification-First | ✅ PASS | All Phase 1 artifacts (data-model.md, contracts/, quickstart.md) trace directly to spec.md FRs. No scope expansion. |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical structure. Plan, research, data-model, contracts, quickstart all present. |
| III. Agent-Orchestrated Execution | ✅ PASS | `speckit.plan` pipeline respected: Phase 0 (research) → Phase 1 (design). Agent context updated via `update-agent-context.sh copilot`. |
| IV. Test Optionality with Clarity | ✅ PASS | Tests defined in data-model.md and quickstart.md only where spec mandates (FR-016 through FR-018). No unnecessary test requirements added. |
| V. Simplicity and DRY | ✅ PASS | data-model.md reuses existing SQLite tables (migration 012). contracts/ leverage existing `AppException` hierarchy and `chat_store.py`. Type generation uses standard `openapi-typescript` — no custom tooling. No new abstractions beyond minimal package structure for chat decomposition. |

**Post-Design Gate Result**: ✅ ALL GATES PASS — ready for Phase 2 (tasks generation).
