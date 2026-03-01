# Implementation Plan: Add 'Clean Up' Button to Delete Stale Branches and PRs

**Branch**: `015-stale-cleanup-button` | **Date**: 2026-03-01 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/015-stale-cleanup-button/spec.md`

## Summary

Add a 'Clean Up' button that allows project maintainers to remove stale branches and pull requests from a GitHub repository while preserving `main` and any branch/PR linked to an open issue on the associated GitHub Projects v2 board. The implementation adds a backend API endpoint that performs a preflight fetch (all branches, open PRs, open project board issues), computes deletion/preservation lists with cross-referencing, and executes sequential deletions with rate-limit-aware batching. The frontend adds a button with tooltip, a confirmation modal displaying categorized items, a progress indicator during execution, and a post-operation summary/audit trail. See [research.md](./research.md) for decision rationale.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript 5.4 / React 18 (frontend)
**Primary Dependencies**: FastAPI, httpx, aiosqlite, Pydantic v2 (backend); React 18, Vite 5.4, TailwindCSS 3.4, React Query 5 (frontend)
**Storage**: SQLite (WAL mode) via aiosqlite — new `cleanup_audit_logs` table for audit trail (migration 008)
**Testing**: pytest + pytest-asyncio (backend), Vitest + React Testing Library (frontend)
**Target Platform**: Linux server (Docker), modern browsers
**Project Type**: Web application (frontend + backend)
**Performance Goals**: Preflight fetch and confirmation modal displayed within 10 seconds for up to 200 branches (SC-001); permission error within 3 seconds (SC-006)
**Constraints**: Sequential or batched deletions to respect GitHub secondary rate limits; OAuth required with `repo` scope; `main` branch unconditionally protected
**Scale/Scope**: 1 new backend service module, 1 new API endpoint group, 1 new DB migration, 3 new frontend components (button, modal, summary), 1 new hook, up to 200 branches per repository

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Research Check (Phase 0 Gate)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | `spec.md` exists with 6 prioritized user stories (P1×2, P2×3, P3×1), Given-When-Then scenarios, 14 FRs, and 7 edge cases |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates |
| III. Agent-Orchestrated Execution | ✅ PASS | `speckit.plan` agent produces plan.md and Phase 0/1 artifacts |
| IV. Test Optionality | ✅ PASS | Tests not mandated in spec; will follow existing test patterns if present |
| V. Simplicity and DRY | ✅ PASS | Reuses existing `GitHubProjectsService` methods (`delete_branch`, `_request_with_retry`), existing auth patterns, existing modal UI patterns |

**Gate Result**: ALL PASS — proceed to Phase 0

### Post-Design Check (Phase 1 Gate)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | All FR items (FR-001 through FR-014) have corresponding design artifacts in data-model.md and contracts/ |
| II. Template-Driven Workflow | ✅ PASS | plan.md, research.md, data-model.md, contracts/, quickstart.md all generated |
| III. Agent-Orchestrated Execution | ✅ PASS | Plan ready for handoff to `speckit.tasks` |
| IV. Test Optionality | ✅ PASS | No test mandate; tests optional per constitution |
| V. Simplicity and DRY | ✅ PASS | Reuses existing `GitHubProjectsService` for all GitHub API calls, existing `_request_with_retry` for rate limiting, existing `get_session_dep` for auth, existing modal patterns from `IssueDetailModal`. No new frameworks or abstractions. |

**Gate Result**: ALL PASS — proceed to Phase 2 (tasks)

## Project Structure

### Documentation (this feature)

```text
specs/015-stale-cleanup-button/
├── plan.md              # This file
├── research.md          # Phase 0: Technical decisions and rationale
├── data-model.md        # Phase 1: Entity definitions and migration SQL
├── quickstart.md        # Phase 1: Development setup and testing guide
├── contracts/
│   └── cleanup-api.md   # Phase 1: REST API contract (POST preflight, POST execute)
├── checklists/
│   └── requirements.md  # Requirements checklist
└── tasks.md             # Phase 2 output (NOT created by speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── migrations/
│   │   └── 008_cleanup_audit_logs.sql          # Audit trail table
│   ├── models/
│   │   └── cleanup.py                          # Pydantic models (request/response)
│   ├── services/
│   │   └── cleanup_service.py                  # Preflight, execution, audit logic
│   └── api/
│       ├── __init__.py                         # Register cleanup router
│       └── cleanup.py                          # REST endpoints (preflight, execute)
└── tests/                                      # Optional: pytest tests

frontend/
├── src/
│   ├── types/
│   │   └── index.ts                            # Add cleanup TypeScript interfaces
│   ├── services/
│   │   └── api.ts                              # Add cleanup API client methods
│   ├── hooks/
│   │   └── useCleanup.ts                       # React hook for cleanup workflow state
│   ├── components/
│   │   └── board/
│   │       ├── CleanUpButton.tsx                # Button with tooltip
│   │       ├── CleanUpConfirmModal.tsx          # Confirmation modal with item lists
│   │       └── CleanUpSummary.tsx               # Post-operation summary/audit trail
│   └── pages/
│       └── BoardPage.tsx                        # Add CleanUpButton to board header (or ProjectBoard)
└── tests/                                      # Optional: Vitest tests
```

**Structure Decision**: Web application structure (Option 2). The repository already uses `backend/` and `frontend/` top-level directories with established patterns for models, services, API routes, components, hooks, and types. All new files follow existing naming conventions. The cleanup service reuses `GitHubProjectsService` for all GitHub API interactions rather than duplicating API call logic.

## Complexity Tracking

> No constitution violations detected. All design decisions follow existing patterns.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *(none)* | — | — |
