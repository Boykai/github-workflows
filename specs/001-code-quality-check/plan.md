# Implementation Plan: Code Quality Check

**Branch**: `001-code-quality-check` | **Date**: 2026-03-11 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-code-quality-check/spec.md`

## Summary

A behavior-preserving code quality initiative spanning the full-stack web application (Python/FastAPI backend + React/TypeScript frontend). The work eliminates silent failures and security risks, consolidates duplicated backend patterns into shared helpers, improves frontend consistency and accessibility, adds explicit type boundaries, migrates stateful services to managed lifecycles, and enforces bounded retention on in-memory stores. The approach is incremental (7 phases, P0–P4 priority), preserving all existing public APIs and user-visible behavior.

## Technical Context

**Language/Version**: Python 3.12+ (Pyright targets 3.13) / TypeScript 5.9 (ES2022 target)
**Primary Dependencies**: FastAPI 0.135+, React 19.2, TanStack React Query 5.90, Vite 7.3, GitHubKit 0.14.6+, aiosqlite 0.22+
**Storage**: SQLite (async via aiosqlite) with numbered SQL migrations (001–020, 21 files)
**Testing**: Backend: pytest 9.0+ (pytest-asyncio, 72 test files). Frontend: Vitest 4.0 (happy-dom, Testing Library, jest-axe, 68 test files). E2E: Playwright 1.58
**Target Platform**: Linux server (Docker) + SPA browser client (nginx)
**Project Type**: Web application (backend + frontend monorepo)
**Performance Goals**: Bounded memory for in-memory caches; memoized frontend renders; request cancellation on navigation
**Constraints**: Behavior-preserving refactor — no public API changes, no user-visible behavior changes. Each PR must leave changed scope in passing, releasable state.
**Scale/Scope**: ~109 Python source files, ~263 TypeScript/TSX files, 20 SQL migrations, 18 API route modules, 50+ React hooks, 7 pages

### Pre-Existing State (Codebase Audit)

Several items from the original issue have already been addressed in prior work:

| Issue Item | Current State |
|------------|---------------|
| 1.3 CORS `allow_methods=["*"]` | ✅ Already fixed: `["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]` |
| 2.1 `resolve_repository()` | ✅ Already exists and is used across call sites |
| 2.2 `handle_service_error()` | ✅ Already exists and is used. Note: `safe_error_response()` does NOT exist in `logging_utils.py` |
| 2.3 `cached_fetch()` | ✅ Already exists in `utils.py` and is used |
| 2.4 `require_selected_project()` | ✅ Already exists in `dependencies.py` and is used |
| 3.1 Split `service.py` (5,150 LOC) | ✅ Already split into 12 modules (service.py now 343 LOC) |
| 4.2 Enable strict TS checks | ✅ Already enabled: `noUnusedLocals: true`, `noUnusedParameters: true` |
| 5.5 Remove jsdom | ✅ Only `happy-dom` is installed (jsdom not present) |
| 5.6 Consolidate test dirs | ✅ Only `frontend/src/test/` exists (no duplicate `tests/` dir) |

### Remaining Work

| Issue Item | Current State | Action Needed |
|------------|---------------|---------------|
| 1.1 Silent exception swallowing | ~143 bare `except Exception:` without `as e`; 2 `except...pass` blocks | Audit and fix |
| 1.2 Exception detail leaks | Needs verification in `signal_chat.py` | Wrap with safe error responses |
| 2.5 Modal/Dialog consolidation | Multiple implementations exist | Standardize on one pattern |
| 2.6 `cn()` usage | Mixed template literals and `cn()` | Standardize all to `cn()` |
| 3.2 Split `api.ts` (1,136 LOC) | Still monolithic | Split into domain modules |
| 3.3 Split large hooks | `useBoardControls.ts` (375 LOC) still large | Extract sub-hooks |
| 4.1 Return type hints | Some functions missing annotations | Add explicit return types |
| 4.3 Unsafe type casts | Needs audit for `as unknown as Record` | Replace with typed shapes |
| 5.1 Module-level singletons → DI | Needs audit | Migrate to FastAPI `Depends()`/`app.state` |
| 5.2 `__import__()` anti-pattern | Needs verification in `template_builder.py` | Replace with standard import |
| 5.3 Duplicate migration prefixes | Confirmed: 013, 014, 015 have duplicates (6 files for 3 numbers) | Fix conflicts, add uniqueness test |
| 5.4 In-memory chat → SQLite | Needs audit (migration 012_chat_persistence.sql exists) | Verify/complete persistence |
| 5.7 TODO/FIXME comments | 4 files with TODOs found | Resolve inline or convert to issues |
| 6.1 `useMemo`/`React.memo` | Needs audit | Add memoization where beneficial |
| 6.2 AbortController | No cancellation on route changes | Add `AbortSignal` support |
| 6.3 Cap in-memory structures | Needs audit | Apply bounded collections |
| 6.4 Bundle analysis | Not yet configured | Add rollup-plugin-visualizer |
| 7.1–7.4 Testing gaps | Ongoing | Expand test coverage |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Specification-First Development ✅ PASS

- Prioritized user stories (P1–P3) with independent testing criteria are defined in `spec.md`
- Given-When-Then acceptance scenarios present for all 5 stories
- Clear scope boundaries and out-of-scope declarations defined

### Principle II: Template-Driven Workflow ✅ PASS

- All artifacts follow canonical templates from `.specify/templates/`
- `plan.md` generated from `plan-template.md` via `setup-plan.sh`
- No custom sections added without justification

### Principle III: Agent-Orchestrated Execution ✅ PASS

- This plan follows the `speckit.plan` agent's single responsibility: generate implementation plan artifacts
- Inputs are well-defined (spec.md, constitution.md, codebase audit)
- Outputs are specific (plan.md, research.md, data-model.md, contracts/, quickstart.md)

### Principle IV: Test Optionality with Clarity ✅ PASS

- Tests are explicitly mandated in the spec (FR-026): "All changed backend and frontend behaviors in scope MUST receive targeted automated tests"
- FR-027 requires existing validations to pass
- This is appropriate for a quality initiative where testing is the deliverable

### Principle V: Simplicity and DRY ✅ PASS

- The initiative itself is a DRY consolidation effort
- No premature abstractions introduced — work consolidates existing proven patterns
- Complexity tracking below documents the scope breadth justification

## Project Structure

### Documentation (this feature)

```text
specs/001-code-quality-check/
├── plan.md              # This file
├── research.md          # Phase 0: Technical research and decision log
├── data-model.md        # Phase 1: Entity definitions and relationships
├── quickstart.md        # Phase 1: Implementation quickstart guide
├── contracts/           # Phase 1: API contract schemas
│   └── error-handling.md
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── main.py                          # FastAPI app entry, CORS config
│   ├── config.py                        # Settings management
│   ├── dependencies.py                  # FastAPI DI helpers (require_selected_project)
│   ├── logging_utils.py                 # Centralized error handling (handle_service_error)
│   ├── utils.py                         # Shared utilities (resolve_repository, cached_fetch, BoundedDict)
│   ├── models/                          # 19 Pydantic model files
│   ├── api/                             # 18 API route modules
│   │   ├── board.py, chat.py, workflow.py, projects.py, tasks.py, chores.py
│   │   ├── agents.py, auth.py, health.py, mcp.py, metadata.py
│   │   ├── pipelines.py, settings.py, signal.py, tools.py, webhooks.py, cleanup.py
│   │   └── ... (other routes)
│   ├── services/
│   │   ├── github_projects/             # 12 modules (already split from monolith)
│   │   │   ├── service.py (343 LOC)     # Orchestration facade
│   │   │   ├── issues.py, pull_requests.py, board.py, copilot.py
│   │   │   ├── agents.py, branches.py, graphql.py, identities.py
│   │   │   ├── projects.py, repository.py
│   │   │   └── __init__.py
│   │   ├── copilot_polling/             # Background polling
│   │   ├── workflow_orchestrator/       # Workflow management
│   │   ├── pipelines/                   # Pipeline orchestration
│   │   ├── agents/                      # Agent logic
│   │   ├── chores/                      # Chore scheduling (template_builder.py)
│   │   ├── tools/                       # Tool implementations
│   │   ├── database.py                  # SQLite async + migration runner
│   │   ├── ai_agent.py                  # AI agent service
│   │   ├── signal_chat.py              # Signal integration (exception leak risk)
│   │   └── ... (other services)
│   └── migrations/                      # 20 SQL migration files (001–020)
└── tests/
    ├── unit/                            # Unit tests
    ├── integration/                     # Integration tests
    └── helpers/                         # Test utilities

frontend/
├── src/
│   ├── services/
│   │   └── api.ts                       # 1,136 LOC monolithic API client (split target)
│   ├── hooks/                           # 50+ custom hooks
│   │   ├── useBoardControls.ts (375 LOC) # Large hook (split target)
│   │   ├── useChat.ts, usePipelineConfig.ts, useProjects.ts, useWorkflow.ts
│   │   └── __tests__/                   # Hook tests
│   ├── components/                      # 12 feature directories
│   │   ├── board/                       # Board components (modal targets)
│   │   ├── chat/                        # Chat components (aria-live target)
│   │   ├── agents/, auth/, chores/, common/, pipeline/, settings/, tools/, ui/
│   │   └── ... (other components)
│   ├── pages/                           # 7 page components (memoization targets)
│   ├── lib/utils.ts                     # cn() helper for class composition
│   ├── test/                            # Shared test utils (setup.ts, a11y-helpers.ts)
│   └── types/                           # Shared TypeScript types
├── tsconfig.json                        # Strict mode enabled
├── vite.config.ts                       # Build configuration (bundle analysis target)
└── eslint.config.js                     # Linting rules
```

**Structure Decision**: Web application monorepo with `backend/` and `frontend/` at root. No structural changes needed — the existing directory layout is well-organized. Changes are behavior-preserving refactors within the existing structure.

## Complexity Tracking

> Justifications for scope breadth of this quality initiative.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| 7 phases spanning full stack | Interconnected quality concerns (e.g., exception handling affects security, testing, and DRY) | Partial fixes leave inconsistent behavior; the spec requires holistic quality improvement |
| Cross-cutting refactors (DRY, typing) | Shared patterns must be consistent across all consumers | Per-file fixes would leave duplicated patterns and inconsistent error behavior |
| New migration for chat persistence | FR-020 requires durable chat history surviving restarts | In-memory storage has unbounded growth and data loss on restart — no simpler path exists |
