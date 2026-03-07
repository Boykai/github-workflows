# Implementation Plan: Simplicity & DRY Refactoring Plan (5 Phases)

**Branch**: `028-simplicity-dry-refactor` | **Date**: 2026-03-07 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/028-simplicity-dry-refactor/spec.md`

## Summary

Eliminate ~1,500+ lines of duplicated code and reduce complexity across the backend and frontend of Project Solune by consolidating repeated patterns into shared abstractions. The approach proceeds in five dependency-ordered phases: (1) backend DRY consolidation of repository resolution, error handling, session validation, and cache patterns; (2) decomposition of the 4,937-line `service.py` monolith into 8 focused modules under 800 LOC each using composition over inheritance with a backward-compatible facade; (3) consolidation of 3 competing initialization patterns into a single `lifespan()` → `app.state` → `Depends()` path; (4) frontend DRY consolidation with a generic CRUD hook factory, shared UI components, centralized query keys, and ChatInterface split; and (5) test mock consolidation.

## Technical Context

**Language/Version**: Python ≥3.12 (targets 3.13) + TypeScript 5.9 / React 19.2
**Primary Dependencies**: FastAPI (backend), React Query / TanStack Query 5.90 (frontend), githubkit (GitHub API), Vite (build)
**Storage**: SQLite via aiosqlite (backend), InMemoryCache (backend), React Query cache (frontend)
**Testing**: pytest (backend: 47+ unit, 3+ integration), Vitest 4.0 (frontend: 29+ unit), Playwright 1.58 (frontend: 9+ E2E)
**Target Platform**: Linux server (Docker), modern browsers
**Project Type**: Web application (backend + frontend monorepo)
**Performance Goals**: No regression — refactoring preserves existing performance characteristics
**Constraints**: All refactoring is behavior-preserving; no new features, no dependency upgrades, no UI redesign
**Scale/Scope**: ~4,937 LOC largest file → <800 LOC; ~1,500+ lines eliminated across codebase

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Specification-First Development ✅

Feature spec exists at `specs/028-simplicity-dry-refactor/spec.md` with 5 prioritized user stories (P1–P3), Given-When-Then acceptance scenarios, clear scope boundaries, and explicit scope exclusions. Requirements checklist at `checklists/requirements.md` is fully passing.

### II. Template-Driven Workflow ✅

All artifacts follow canonical templates from `.specify/templates/`. This plan follows `plan-template.md`. Research, data model, contracts, and quickstart follow their respective templates.

### III. Agent-Orchestrated Execution ✅

This plan is produced by the `speckit.plan` agent with clear inputs (spec.md) and outputs (plan.md, research.md, data-model.md, contracts/, quickstart.md). Hand-off to `speckit.tasks` for task generation is explicit.

### IV. Test Optionality with Clarity ✅

Tests are mandatory for this feature — the spec explicitly requires test suites to pass after every step. Phase 5 specifically addresses test cleanup. The existing test suites (pytest, Vitest, Playwright) serve as the regression gate.

### V. Simplicity and DRY ✅

This feature **is** the simplicity and DRY initiative. Every phase directly serves the principle:
- Phase 1: Eliminates duplicated helpers (~230 lines)
- Phase 2: Decomposes monolith (4,937 LOC → 8 modules, each <800 LOC)
- Phase 3: Eliminates competing initialization patterns (3 → 1)
- Phase 4: Eliminates duplicated frontend patterns (~1,210 lines)
- Phase 5: Consolidates test mocks (~80 lines)

No new complexity is introduced. All changes simplify the codebase.

### Post-Design Re-Check ✅

After Phase 1 design (data-model.md, contracts/), all constitution principles remain satisfied. The composition-over-inheritance decision for service decomposition aligns with Simplicity and DRY. The backward-compatible facade is a transitional measure documented in the contracts, not permanent complexity.

## Project Structure

### Documentation (this feature)

```text
specs/028-simplicity-dry-refactor/
├── plan.md              # This file
├── research.md          # Phase 0 output — research findings
├── data-model.md        # Phase 1 output — module entities and relationships
├── quickstart.md        # Phase 1 output — developer quickstart guide
├── contracts/           # Phase 1 output — module and API contracts
│   ├── backend-helpers.md
│   ├── service-decomposition.md
│   ├── frontend-abstractions.md
│   ├── initialization.md
│   └── test-cleanup.md
├── checklists/
│   └── requirements.md  # Specification quality checklist (pre-existing)
└── tasks.md             # Phase 2 output (created by /speckit.tasks — NOT this command)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/                    # 18 route files (chat.py 29K, workflow.py 28K)
│   ├── services/
│   │   ├── github_projects/    # TARGET: decompose service.py (4,937 LOC)
│   │   │   ├── __init__.py     # Facade + re-exports
│   │   │   ├── service.py      # Monolith → decomposed into 8 modules
│   │   │   ├── client.py       # NEW: HTTP infrastructure (~600 LOC)
│   │   │   ├── projects.py     # NEW: Project queries (~500 LOC)
│   │   │   ├── issues.py       # NEW: Issue CRUD (~600 LOC)
│   │   │   ├── pull_requests.py # NEW: PR operations (~500 LOC)
│   │   │   ├── copilot.py      # NEW: Copilot management (~400 LOC)
│   │   │   ├── fields.py       # NEW: Field mutations (~300 LOC)
│   │   │   ├── board.py        # NEW: Board queries (~400 LOC)
│   │   │   └── repository.py   # NEW: Repo operations (~300 LOC)
│   │   ├── cache.py            # MODIFIED: add cached_fetch()
│   │   └── ...
│   ├── dependencies.py         # MODIFIED: add require_selected_project()
│   ├── logging_utils.py        # EXISTING: wire handle_service_error()
│   ├── utils.py                # EXISTING: canonical resolve_repository()
│   └── main.py                 # MODIFIED: lifespan consolidation
└── tests/
    ├── conftest.py             # MODIFIED: absorb mocks from helpers/
    ├── helpers/
    │   └── mocks.py            # REMOVED in Phase 5
    └── ...

frontend/
├── src/
│   ├── hooks/
│   │   ├── useCrudResource.ts  # NEW: generic CRUD hook factory
│   │   ├── queryKeys.ts        # NEW: centralized query key registry
│   │   ├── useAgents.ts        # MODIFIED: use factory + registry
│   │   ├── useChores.ts        # MODIFIED: use factory + registry
│   │   ├── useSettings.ts      # MODIFIED: use generic pattern + registry
│   │   └── ...
│   ├── components/
│   │   ├── chat/
│   │   │   ├── ChatInterface.tsx     # MODIFIED: orchestrator only (~150 LOC)
│   │   │   ├── ChatMessageList.tsx   # NEW: extracted from ChatInterface
│   │   │   ├── ChatInput.tsx         # NEW: extracted from ChatInterface
│   │   │   ├── PreviewCard.tsx       # NEW: shared preview card
│   │   │   ├── TaskPreview.tsx       # MODIFIED: uses PreviewCard
│   │   │   ├── StatusChangePreview.tsx # MODIFIED: uses PreviewCard
│   │   │   └── IssueRecommendationPreview.tsx # MODIFIED: uses PreviewCard
│   │   └── common/
│   │       ├── Modal.tsx             # NEW: shared modal
│   │       └── ErrorAlert.tsx        # NEW: shared error alert
│   └── ...
└── ...
```

**Structure Decision**: Web application (backend + frontend). Both sides are modified independently — frontend changes (Phase 4) have no cross-dependencies with backend changes (Phases 1–3). The monorepo structure is preserved.

## Implementation Phases

### Phase 1: Backend Quick Wins — DRY Consolidation

**Priority**: P1 | **Dependencies**: None | **Steps are parallel**

| Step | Action | Files Modified | Lines Saved | Gate |
|------|--------|---------------|-------------|------|
| 1.1 | Unify repository resolution → `resolve_repository()` | `workflow.py`, `main.py`, `projects.py`, `tasks.py`, `chat.py`, `chores.py` | ~100 | `pytest` green; `grep _get_repository_info` = 0 |
| 1.2 | Wire `handle_service_error()` + `safe_error_response()` | `board.py`, `workflow.py`, `projects.py`, `auth.py` | ~50 | `pytest` green; 80%+ endpoints use shared helpers |
| 1.3 | Create `require_selected_project()` in `dependencies.py` | `dependencies.py`, `chat.py`, `workflow.py`, `tasks.py`, `chores.py` | ~20 | `pytest` green; `grep` inline guards = 0 |
| 1.4 | Create `cached_fetch()` in `cache.py` | `cache.py`, `projects.py`, `board.py`, `chat.py` | ~60 | `pytest` green |

**Total Lines Saved**: ~230

### Phase 2: Service Decomposition

**Priority**: P2 | **Dependencies**: Phase 1 complete

**Extraction Order** (follows dependency DAG — extract leaves first):

| Order | Module | Depends On | ~LOC | Gate |
|-------|--------|-----------|------|------|
| 1 | `client.py` | None | 600 | `pytest` + `ruff check` |
| 2 | `fields.py` | `client.py` | 300 | Same |
| 3 | `projects.py` | `client.py` | 500 | Same |
| 4 | `copilot.py` | `client.py` | 400 | Same |
| 5 | `repository.py` | `client.py` | 300 | Same |
| 6 | `pull_requests.py` | `client.py` | 500 | Same |
| 7 | `issues.py` | `client.py`, `fields.py` | 600 | Same |
| 8 | `board.py` | `client.py`, `fields.py` | 400 | Same |
| 9 | Update `__init__.py` facade | All modules | — | Same |
| 10 | Remove `service.py` | Facade working | — | Same + no circular imports |
| 11 | Replace singleton with DI | `dependencies.py`, 17+ callers | — | Same |

**Key Decisions**:
- **Composition over inheritance**: Each module receives `GitHubClient` via constructor, not via inheritance.
- **Facade for backward compatibility**: `__init__.py` re-exports all 79 public methods through a composite `GitHubProjectsService` class.
- **One extraction per commit**: Each module extraction is independently testable and mergeable.

### Phase 3: Initialization Consolidation

**Priority**: P3 | **Dependencies**: Phase 2 complete

| Step | Action | Files Modified | Gate |
|------|--------|---------------|------|
| 3.1 | Audit all initialization patterns | — (analysis only) | List of all instances documented |
| 3.2 | Ensure all services created in `lifespan()` | `main.py` | `pytest` green |
| 3.3 | Remove module-level singletons | `service.py`/`__init__.py`, service files | `pytest` green |
| 3.4 | Update all direct imports to use `Depends()` | 17+ API files | `pytest` green |
| 3.5 | Verify full stack | — | `docker compose up`, health check, OAuth flow |

### Phase 4: Frontend DRY Consolidation

**Priority**: P2 | **Dependencies**: None (parallel with Phases 2–3)

| Step | Action | Files Created/Modified | Lines Saved | Gate |
|------|--------|----------------------|-------------|------|
| 4.1 | Generic CRUD hook factory | `useCrudResource.ts`, `useAgents.ts`, `useChores.ts` | ~600 | `npm run test` |
| 4.2 | Consolidate settings hooks | `useSettings.ts` | ~110 | `npm run test` |
| 4.3 | Shared UI components | `PreviewCard.tsx`, `Modal.tsx`, `ErrorAlert.tsx` + consumers | ~500 | `npm run test` |
| 4.4 | Centralize query keys | `queryKeys.ts` + all hook files | — (organization) | `npm run test` |
| 4.5 | Split ChatInterface | `ChatMessageList.tsx`, `ChatInput.tsx`, `ChatInterface.tsx` | — (organization) | `npm run test` |

**Total Lines Saved**: ~1,210

### Phase 5: Test Cleanup

**Priority**: P3 | **Dependencies**: Phases 1–3 complete

| Step | Action | Files Modified | Lines Saved | Gate |
|------|--------|---------------|-------------|------|
| 5.1 | Consolidate mock factories into `conftest.py` | `conftest.py`, `tests/helpers/mocks.py` | ~40 | `pytest` green |
| 5.2 | Replace inline patches with shared fixtures | `test_api_e2e.py` + others | ~40 | `pytest` green |
| 5.3 | Delete `tests/helpers/mocks.py` | Delete file | — | `pytest --collect-only` succeeds |

**Total Lines Saved**: ~80

---

## Dependency Graph

```
Phase 1 (Backend DRY)
    │
    ├──→ Phase 2 (Service Decomposition)
    │       │
    │       └──→ Phase 3 (Init Consolidation)
    │               │
    │               └──→ Phase 5 (Test Cleanup)
    │
Phase 4 (Frontend DRY) ← independent, parallel with Phases 2–3
```

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Circular imports during decomposition | Medium | High (app won't start) | Extract in dependency order (leaves first); smoke test imports after each extraction |
| Subtle behavior change in error handling | Low | Medium (different error responses) | Existing tests catch regressions; `handle_service_error` preserves structured error format |
| Frontend shared component doesn't cover edge case | Low | Low (can extend props) | `children` prop pattern allows per-consumer customization |
| Module-level import removal breaks 17+ files | Medium | High (widespread failures) | One caller at a time; `pytest` after each change |
| Cache behavior change from `cached_fetch` wrapper | Low | Medium (stale data) | Wrapper preserves exact TTL and refresh semantics from current inline patterns |

## Complexity Tracking

> No constitution violations exist. All changes reduce complexity — no new complexity is introduced.

| Decision | Justification | Alternative Rejected |
|----------|--------------|---------------------|
| Backward-compatible facade (transitional) | Allows incremental migration; callers update on their schedule | Big-bang migration rejected — too risky for 17+ import sites |
| Composition over inheritance | Clean dependency boundaries; each service testable in isolation | Mixin approach rejected — fragile MRO, hard to reason about |
| `cached_fetch` as standalone function (not class method) | Simpler interface; no class modification needed | Decorator approach rejected — can't easily capture runtime parameters (refresh flag, cache key) |

## Estimated Effort

| Phase | Effort | Parallelism |
|-------|--------|-------------|
| Phase 1: Backend DRY | 1–2 days | Steps 1.1–1.4 are parallel |
| Phase 2: Service Decomposition | 3–5 days | Sequential (dependency order) |
| Phase 3: Initialization Consolidation | 1–2 days | Sequential |
| Phase 4: Frontend DRY | 2–3 days | Steps 4.1–4.5 are mostly parallel; parallel with Phases 2–3 |
| Phase 5: Test Cleanup | 0.5–1 day | After Phases 1–3 |
| **Total** | **7–13 days** | Backend + Frontend can be parallelized |

## Artifacts Generated

| Artifact | Path | Description |
|----------|------|-------------|
| Plan | `specs/028-simplicity-dry-refactor/plan.md` | This file |
| Research | `specs/028-simplicity-dry-refactor/research.md` | 12 research findings resolving all unknowns |
| Data Model | `specs/028-simplicity-dry-refactor/data-model.md` | Module entities, relationships, and state transitions |
| Quickstart | `specs/028-simplicity-dry-refactor/quickstart.md` | Developer guide for executing each phase |
| Contract: Backend Helpers | `specs/028-simplicity-dry-refactor/contracts/backend-helpers.md` | Shared helper signatures and wiring |
| Contract: Service Decomposition | `specs/028-simplicity-dry-refactor/contracts/service-decomposition.md` | Module interfaces and facade |
| Contract: Frontend Abstractions | `specs/028-simplicity-dry-refactor/contracts/frontend-abstractions.md` | CRUD factory, UI components, query keys |
| Contract: Initialization | `specs/028-simplicity-dry-refactor/contracts/initialization.md` | Single initialization pattern |
| Contract: Test Cleanup | `specs/028-simplicity-dry-refactor/contracts/test-cleanup.md` | Mock consolidation plan |
