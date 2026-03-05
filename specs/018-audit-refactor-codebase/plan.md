# Implementation Plan: Audit & Refactor FastAPI + React GitHub Projects V2 Codebase

**Branch**: `018-audit-refactor-codebase` | **Date**: 2026-03-05 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/018-audit-refactor-codebase/spec.md`

## Summary

Full-sweep audit and in-place refactor of the FastAPI (Python 3.11+) backend and React 18 + TypeScript frontend. Three phases: (1) modernize all dependencies to latest stable, removing unused `agent-framework-core`; (2) DRY consolidation — extract shared `CopilotClientPool`, introduce `_with_fallback` helper, unify retry logic, consolidate header builders; (3) fix six identified anti-patterns including hardcoded model values, unpersisted in-memory state, stub file-deletion parameter, undocumented OAuth bounds, inconsistent singleton registration, and unbounded caches. All changes are in-place with no new files or module restructuring.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript 5.4 (frontend)
**Primary Dependencies**: FastAPI ≥0.109.0, httpx ≥0.26.0, github-copilot-sdk ≥0.1.0, openai ≥1.0.0, azure-ai-inference ≥1.0.0b1, React 18, Vite 5, @tanstack/react-query 5
**Storage**: SQLite/WAL via aiosqlite ≥0.20.0 (backend); browser state via React Query (frontend)
**Testing**: pytest + pytest-asyncio (backend), vitest (frontend unit), playwright (frontend e2e)
**Target Platform**: Linux server (backend), modern browsers (frontend)
**Project Type**: Web application (backend + frontend)
**Performance Goals**: Maintain existing performance characteristics; no regression in API response times
**Constraints**: Refactor in-place only (no new files/modules), preserve dual AI provider pattern, maintain full API backward compatibility
**Scale/Scope**: ~30 backend Python files modified, ~0 frontend source files modified (deps only), 12 unbounded caches to bound

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | spec.md complete with 3 prioritized user stories, acceptance scenarios, edge cases |
| **II. Template-Driven** | ✅ PASS | All artifacts follow canonical templates |
| **III. Agent-Orchestrated** | ✅ PASS | speckit.plan phase producing plan.md, research.md, data-model.md, contracts/, quickstart.md |
| **IV. Test Optionality** | ✅ PASS | Tests mandated by spec (FR-018, FR-019): existing tests must pass, affected tests must be updated |
| **V. Simplicity and DRY** | ✅ PASS | The entire feature IS about DRY consolidation; no premature abstraction — all extractions address documented duplication |

**Gate result: PASS** — No violations. Proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/018-audit-refactor-codebase/
├── plan.md              # This file
├── research.md          # Phase 0: dependency research & design decisions
├── data-model.md        # Phase 1: entity model for new/changed abstractions
├── quickstart.md        # Phase 1: developer quickstart for the refactor
├── contracts/           # Phase 1: internal API contracts for new helpers
│   ├── copilot-client-pool.md
│   ├── fallback-helper.md
│   ├── unified-retry.md
│   └── header-builder.md
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── pyproject.toml                          # Phase 1: dependency updates
├── src/
│   ├── utils.py                            # Existing BoundedDict/BoundedSet (unchanged)
│   ├── main.py                             # Phase 3E: singleton registration cleanup
│   ├── dependencies.py                     # Phase 3E: remove module-global fallbacks
│   ├── api/
│   │   ├── chat.py                         # Phase 3B: persist or document in-memory state
│   │   └── workflow.py                     # Phase 3F: bound _recent_requests cache
│   ├── services/
│   │   ├── completion_providers.py         # Phase 2A: use shared CopilotClientPool
│   │   ├── model_fetcher.py               # Phase 2A: use shared CopilotClientPool
│   │   ├── github_auth.py                 # Phase 3D: document OAuth state bounds
│   │   ├── github_commit_workflow.py       # Phase 3C: implement or remove delete_files
│   │   ├── agents/
│   │   │   └── service.py                  # Phase 3F: bound chat session caches
│   │   ├── chores/
│   │   │   └── chat.py                     # Phase 3F: bound _conversations cache
│   │   ├── signal_chat.py                  # Phase 3F: bound _signal_pending cache
│   │   ├── github_projects/
│   │   │   ├── graphql.py                  # Phase 3A: parameterize hardcoded model
│   │   │   └── service.py                  # Phase 2B/2C/2D: fallback, retry, headers
│   │   └── workflow_orchestrator/
│   │       ├── transitions.py              # Phase 3F: bound pipeline state caches
│   │       └── config.py                   # Phase 3F: bound _workflow_configs cache
│   └── ...
└── tests/                                  # Update affected tests

frontend/
├── package.json                            # Phase 1: dependency updates
└── src/                                    # No source changes expected
```

**Structure Decision**: Existing web application structure (backend/ + frontend/) is preserved. All refactoring is in-place within existing files per FR-015.

## Complexity Tracking

> No constitution violations to justify. All changes follow simplicity and DRY principles.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *(none)* | — | — |
