# Implementation Plan: Full Codebase Review & Refactoring

**Branch**: `023-codebase-review-refactor` | **Date**: 2026-03-06 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/023-codebase-review-refactor/spec.md`

## Summary

Systematic refactoring of the GitHub Projects Chat application across 6 phases: dependency audit, DRY consolidation (repository resolution ×3→1, error handling adoption, cache wrapper, validation dependency), service monolith decomposition (4,941 LOC → 7 focused modules <800 LOC each + facade), initialization pattern consolidation (3 patterns → lifespan+DI only), frontend quality pass (5 components >300 LOC, type safety, accessibility), and CI/CD enforcement (coverage artifacts, vulnerability scanning). All changes are internal — zero user-visible behavior changes.

## Technical Context

**Language/Version**: Python 3.12 (pyproject.toml targets ≥3.11, pyright configured for 3.12) + TypeScript ~5.8  
**Primary Dependencies**: FastAPI ≥0.109.0, githubkit ≥0.14.0, httpx ≥0.26.0, pydantic ≥2.5.0, React 18.3, @tanstack/react-query 5.17, Vite 5.4  
**Storage**: SQLite with WAL mode (aiosqlite ≥0.20.0) — sessions, settings, migrations  
**Testing**: Backend: pytest + pytest-asyncio + pytest-cov (10 conftest fixtures, 18+ test classes). Frontend: vitest 4.0 + happy-dom + @testing-library/react (29+ test files) + Playwright 1.58 (E2E)  
**Target Platform**: Linux server (Docker container), browser SPA  
**Project Type**: Web application (FastAPI backend + React/Vite frontend)  
**Performance Goals**: No regression — all refactoring is behavior-preserving. Service facade must add negligible overhead (<1ms per call).  
**Constraints**: All 47+ backend unit tests, 3+ integration tests, 29+ frontend unit tests, 9+ E2E tests must pass after each phase. No breaking changes to API response shapes.  
**Scale/Scope**: Backend: ~15 runtime deps, 4,941 LOC service monolith, 14 API route files, 78 service methods. Frontend: ~54 components, 7,176 total component LOC.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | spec.md complete with 6 prioritized user stories (P1-P4), acceptance scenarios, edge cases |
| II. Template-Driven Workflow | ✅ PASS | Following canonical plan template |
| III. Agent-Orchestrated Execution | ✅ PASS | Following specify → plan → tasks → implement pipeline |
| IV. Test Optionality | ✅ PASS | Existing tests maintained; no new tests mandated (only mock-path updates) |
| V. Simplicity and DRY | ✅ PASS | Core goal IS simplification — the entire spec targets DRY consolidation and complexity reduction |

**Gate result**: PASS — no violations. Proceeding to Phase 0.

### Post-Design Re-evaluation

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | spec.md complete; plan artifacts (research, data-model, contracts, quickstart) all generated |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates |
| III. Agent-Orchestrated Execution | ✅ PASS | specify → plan → tasks → implement pipeline followed |
| IV. Test Optionality | ✅ PASS | No new tests created. Existing tests maintained. Mock-path updates only where decomposition changes import targets. |
| V. Simplicity and DRY | ✅ PASS | Decomposition creates 8 focused modules (each <800 LOC) from 1 monolith (4,941 LOC). Facade preserves simplicity of existing interface. Cache wrapper eliminates 7× duplication. Validation dependency eliminates 5× duplication. |

**Post-design gate result**: PASS — no violations or complexity additions to justify.

## Project Structure

### Documentation (this feature)

```text
specs/023-codebase-review-refactor/
├── plan.md              # This file
├── research.md          # Phase 0: Dependency research, pattern analysis
├── data-model.md        # Phase 1: Service decomposition entity mapping
├── quickstart.md        # Phase 1: Refactoring quickstart guide
├── contracts/           # Phase 1: Internal service interface contracts
│   └── internal-contracts.md
├── checklists/
│   └── requirements.md  # Quality checklist (complete)
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/                       # 14 route files — adopt error handling helpers, validation dependency
│   │   ├── auth.py                # 6 try/except blocks → adopt handle_service_error
│   │   ├── board.py               # 3 try/except blocks
│   │   ├── chat.py                # 8 try/except blocks, 3+ selected_project_id checks
│   │   ├── chores.py              # 3 try/except blocks
│   │   ├── projects.py            # 3 try/except blocks
│   │   ├── tasks.py               # 2 try/except blocks
│   │   ├── webhooks.py            # 3 try/except blocks
│   │   ├── workflow.py            # 4 try/except blocks, _get_repository_info → resolve_repository
│   │   └── ...                    # agents, cleanup, health, mcp, metadata, settings, signal
│   ├── dependencies.py            # Add require_selected_project(), consolidate DI
│   ├── logging_utils.py           # Contains handle_service_error(), safe_error_response() (underutilized)
│   ├── utils.py                   # Canonical resolve_repository() — all sites must use this
│   ├── main.py                    # Remove inline repo resolution, consolidate lifespan
│   ├── services/
│   │   ├── github_projects/
│   │   │   ├── __init__.py        # Backward-compatible facade (re-exports all public methods)
│   │   │   ├── service.py         # DECOMPOSE: 4,941 LOC → coordinator/facade only
│   │   │   ├── client.py          # NEW: HTTP client infra, rate limit, _rest, _graphql (~300 LOC)
│   │   │   ├── projects.py        # NEW: list/get projects, parse (~200 LOC)
│   │   │   ├── board.py           # NEW: board data, reconciliation, draft items, status (~700 LOC)
│   │   │   ├── issues.py          # NEW: create/update/get issues, sub-issues, labels (~600 LOC)
│   │   │   ├── pull_requests.py   # NEW: PR listing, details, merge, review (~700 LOC)
│   │   │   ├── copilot.py         # NEW: copilot assignment, status, polling (~400 LOC)
│   │   │   ├── fields.py          # NEW: field listing, updates, options (~250 LOC)
│   │   │   ├── repository.py      # NEW: repo info, branches, commits, file content (~300 LOC)
│   │   │   └── graphql.py         # Existing: GraphQL query strings (cleanup only)
│   │   ├── cache.py               # Add generic cached_fetch() wrapper
│   │   ├── signal_delivery.py     # tenacity user — keep dependency
│   │   └── ...
│   └── ...
└── tests/
    ├── conftest.py                # Centralized fixtures (already good — consolidate any stragglers)
    ├── unit/
    └── integration/

frontend/
├── src/
│   ├── components/
│   │   ├── chat/
│   │   │   └── ChatInterface.tsx      # 412 LOC → split into sub-components
│   │   ├── settings/
│   │   │   ├── McpSettings.tsx        # 459 LOC → split
│   │   │   └── SignalConnection.tsx   # 349 LOC → split
│   │   ├── chores/
│   │   │   └── AddChoreModal.tsx      # 299 LOC → borderline, evaluate
│   │   ├── board/
│   │   │   └── IssueDetailModal.tsx   # 247 LOC → OK (<300)
│   │   └── ...
│   ├── hooks/                         # DRY review
│   ├── services/api.ts                # DRY review
│   └── types/index.ts                 # 750+ LOC, already well-typed
└── ...

.github/
└── workflows/
    ├── ci.yml                     # Add coverage artifacts upload, vulnerability scanning
    └── branch-issue-link.yml      # Existing (no changes)
```

**Structure Decision**: Existing web application layout. Backend service decomposition creates 8 new module files within the existing `github_projects/` package. Frontend changes are component splits within existing directories. No new top-level directories needed.

## Complexity Tracking

> No constitution violations to justify. The entire feature reduces complexity.
