# Implementation Plan: Audit & Refactor FastAPI+React GitHub Projects Copilot Codebase

**Branch**: `018-audit-refactor-codebase` | **Date**: 2026-03-04 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/018-audit-refactor-codebase/spec.md`

## Summary

Perform a full-sweep audit and refactor of the FastAPI (Python 3.11+) backend and React 18/TypeScript frontend. The work is organized into three phases: (1) modernize all dependencies to latest stable versions and remove unused packages, (2) DRY-consolidate duplicated patterns (client caching, fallback chains, retry logic, header builders) into shared abstractions, and (3) fix anti-patterns (hardcoded model names, unbounded in-memory caches, dead parameters, dual singleton registration). All refactoring is performed in-place — no new files or modules are created. All existing API contracts and test suites must remain green.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript 5.4 (frontend)
**Primary Dependencies**: FastAPI 0.135.1, httpx 0.28.1, github-copilot-sdk 0.1.29, openai 2.24.0, azure-ai-inference 1.0.0b9, React 18.3.1, @tanstack/react-query 5.90.7, Vite 5.4 (stay on 5.x; 7.x is a major upgrade out of scope)
**Storage**: SQLite via aiosqlite 0.22.1 with WAL mode
**Testing**: pytest + pytest-asyncio (backend), vitest 4.0.18 + @playwright/test 1.58.2 (frontend)
**Target Platform**: Linux server (Docker), browser SPA
**Project Type**: Web application (backend + frontend)
**Performance Goals**: No degradation from current baseline; bounded memory usage for all in-memory caches
**Constraints**: In-place refactoring only (no new files/modules), preserve all API endpoint contracts, ruff formatting with 100-char line length and double quotes, maintain dual AI provider pattern (Copilot SDK primary, Azure OpenAI fallback)
**Scale/Scope**: ~4,755 lines in service.py, ~924 lines in graphql.py, ~311 lines in completion_providers.py, ~443 lines in model_fetcher.py, ~693 lines in frontend/src/services/api.ts

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First Development** | ✅ PASS | spec.md exists with prioritized user stories (P1/P2), Given-When-Then acceptance scenarios, and edge cases |
| **II. Template-Driven Workflow** | ✅ PASS | All artifacts follow canonical templates |
| **III. Agent-Orchestrated Execution** | ✅ PASS | speckit.plan agent produces plan.md, research.md, data-model.md, quickstart.md |
| **IV. Test Optionality with Clarity** | ✅ PASS | Spec explicitly requires existing test suites to pass (SC-001, SC-002); no new test infrastructure mandated. Individual tests may be updated if refactored internals change |
| **V. Simplicity and DRY** | ✅ PASS | The entire purpose of this feature is DRY consolidation and simplification. Shared abstractions are replacing proven duplicated patterns — not premature abstraction |

**Gate Result**: ALL PASS — proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/018-audit-refactor-codebase/
├── plan.md              # This file
├── research.md          # Phase 0: dependency versions, design decisions
├── data-model.md        # Phase 1: key entity definitions for shared abstractions
├── quickstart.md        # Phase 1: step-by-step implementation guide
├── contracts/           # Phase 1: N/A (no new API endpoints; this is a refactor)
└── tasks.md             # Phase 2 output (created by /speckit.tasks, not this command)
```

### Source Code (repository root)

```text
backend/
├── pyproject.toml                          # Dependency manifest (Phase 1 changes)
├── src/
│   ├── main.py                             # Singleton registration (Phase 3E)
│   ├── dependencies.py                     # Dependency injection (Phase 3E)
│   ├── utils.py                            # BoundedDict/BoundedSet (referenced, not changed)
│   ├── api/
│   │   └── chat.py                         # In-memory state documentation (Phase 3B)
│   └── services/
│       ├── completion_providers.py          # CopilotClientPool extraction (Phase 2A)
│       ├── model_fetcher.py                # CopilotClientPool consumer (Phase 2A)
│       ├── github_commit_workflow.py        # delete_files resolution (Phase 3C)
│       ├── github_auth.py                  # OAuth state documentation (Phase 3D)
│       ├── github_projects/
│       │   ├── service.py                  # Fallback helper, retry unification, header consolidation (Phase 2B/2C/2D), hardcoded model fix (Phase 3A)
│       │   └── graphql.py                  # Parameterize ASSIGN_COPILOT_MUTATION model (Phase 3A)
│       ├── workflow_orchestrator/
│       │   └── transitions.py              # Bounded cache audit (Phase 3F)
│       └── copilot_polling/
│           └── state.py                    # Already uses BoundedDict/BoundedSet ✓
└── tests/                                  # Existing tests — must all pass

frontend/
├── package.json                            # Dependency manifest (Phase 1 changes)
└── src/
    └── services/
        └── api.ts                          # No structural changes needed
```

**Structure Decision**: Existing web application layout (backend/ + frontend/) is preserved. All changes are in-place modifications to the files listed above. No new files or directories are created.

## Constitution Check — Post-Design Re-evaluation

*Re-evaluated after Phase 1 design completion.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First Development** | ✅ PASS | Design artifacts (research.md, data-model.md, quickstart.md) fully trace back to spec requirements |
| **II. Template-Driven Workflow** | ✅ PASS | All artifacts follow canonical templates |
| **III. Agent-Orchestrated Execution** | ✅ PASS | Plan artifacts ready for handoff to speckit.tasks |
| **IV. Test Optionality with Clarity** | ✅ PASS | No new test infrastructure required; existing suites validate all changes |
| **V. Simplicity and DRY** | ✅ PASS | New abstractions (CopilotClientPool, _with_fallback) replace proven duplicated patterns. Retry unification was identified as already unified (no unnecessary refactoring). Vite/React major upgrades correctly scoped out as premature. |

**Post-Design Gate Result**: ALL PASS — proceed to task generation.

## Complexity Tracking

> No constitution violations detected. No complexity justifications required.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *(none)* | — | — |
