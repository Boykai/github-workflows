# Implementation Plan: Fix 'Every X Issues' Chore Counter to Only Count GitHub Parent Issues

**Branch**: `030-fix-chore-issue-counter` | **Date**: 2026-03-08 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/030-fix-chore-issue-counter/spec.md`

## Summary

Fix the "Every X Issues" Chore counter so it counts only qualifying GitHub Parent Issues — excluding Chores (issues with the `chore` label) and Sub-Issues (issues with a parent-child relationship). The current frontend `parentIssueCount` computation in `ChoresPage.tsx` already excludes Sub-Issues but does **not** exclude Chore-labelled issues, causing the counter to be inflated. The counter logic in `counter.py` and the display logic in `ChoreCard.tsx` / `FeaturedRitualsPanel.tsx` both depend on this single `parentIssueCount` value. The fix requires adding a label-based filter to the `parentIssueCount` computation to exclude items with the `chore` label, ensuring the same filtered count is used for both tile display and trigger evaluation. The backend `evaluate_triggers()` endpoint also needs the corrected count passed from the caller. No schema changes or new API endpoints are needed — this is a filtering fix in existing code paths.

## Technical Context

**Language/Version**: TypeScript ~5.9 (frontend), Python 3.13 (backend)
**Primary Dependencies**: React 19.2, TanStack Query v5.90, Tailwind CSS v4, lucide-react (frontend); FastAPI 0.135, aiosqlite 0.22, Pydantic v2.12 (backend)
**Storage**: SQLite with WAL mode (aiosqlite) — no schema changes required. Existing `chores` table fields (`last_triggered_count`, `schedule_value`, `schedule_type`) are sufficient.
**Testing**: Vitest 4 + Testing Library (frontend), pytest + pytest-asyncio (backend). Existing unit tests in `backend/tests/unit/test_chores_counter.py`.
**Target Platform**: Desktop browsers, 1024px minimum viewport width; Linux server (Docker)
**Project Type**: Web application (frontend/ + backend/)
**Performance Goals**: Counter accuracy on page load — the counter must reflect only qualifying Parent Issues with zero discrepancy between tile display and trigger evaluation.
**Constraints**: No new UI libraries; must not break existing Chore CRUD, trigger evaluation, or template commit flow. The "chore" label is the authoritative marker for Chore-generated issues (used in `service.py:372`). Sub-Issues are identified by GitHub's parent-child relationship metadata (already handled in the board data pipeline).
**Scale/Scope**: ~2 modified frontend files, ~1 modified backend file (counter.py docstring only), ~1 modified test file. Minimal, surgical change.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | spec.md complete with 4 prioritized user stories (P1–P2), Given-When-Then acceptance scenarios, 10 functional requirements (FR-001–FR-010), 6 success criteria, 6 edge cases, 3 key entities |
| **II. Template-Driven** | ✅ PASS | All artifacts follow canonical templates in `.specify/templates/` |
| **III. Agent-Orchestrated** | ✅ PASS | Sequential phase execution (specify → plan → tasks → implement) |
| **IV. Test Optionality** | ✅ PASS | Existing `test_chores_counter.py` tests remain valid; adding a test for chore-label filtering is optional but recommended |
| **V. Simplicity/DRY** | ✅ PASS | Fix is a single-line label filter addition to the existing `parentIssueCount` computation. No new abstractions, no new components, no new endpoints. Reuses existing `BoardItem.labels` data already fetched by `useProjectBoard()`. |

### Post-Phase 1 Re-Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | All design decisions trace to spec FR-001 through FR-010 and SC-001 through SC-006 |
| **II. Template-Driven** | ✅ PASS | plan.md, research.md, data-model.md, contracts/, quickstart.md all follow prior spec structure |
| **III. Agent-Orchestrated** | ✅ PASS | Plan hands off to `/speckit.tasks` for Phase 2 task decomposition |
| **IV. Test Optionality** | ✅ PASS | No additional tests mandated; existing counter.py tests remain green |
| **V. Simplicity/DRY** | ✅ PASS | Minimal change — adding one label filter to existing computation. Single source of truth maintained: `parentIssueCount` computed once in `ChoresPage.tsx`, passed to both `ChoreCard` and `FeaturedRitualsPanel` |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/030-fix-chore-issue-counter/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── api.md           # REST API contract changes
│   └── components.md    # Component interface contracts
└── tasks.md             # Phase 2 output (/speckit.tasks command — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── services/
│   │   └── chores/
│   │       └── counter.py               # UNCHANGED (logic already correct; docstring clarified)
│   └── models/
│       └── chores.py                    # UNCHANGED (model already has all needed fields)
└── tests/
    └── unit/
        └── test_chores_counter.py       # UNCHANGED (existing tests pass; optional new test)

frontend/
├── src/
│   ├── pages/
│   │   └── ChoresPage.tsx               # MODIFIED: Add chore-label exclusion to parentIssueCount
│   ├── components/
│   │   └── chores/
│   │       ├── ChoreCard.tsx            # UNCHANGED (already uses parentIssueCount correctly)
│   │       └── FeaturedRitualsPanel.tsx  # UNCHANGED (already uses parentIssueCount correctly)
│   └── types/
│       └── index.ts                     # UNCHANGED (BoardItem.labels already available)
```

**Structure Decision**: Web application (frontend/ + backend/). The fix is localized to the frontend `parentIssueCount` computation in `ChoresPage.tsx`. The downstream consumers (`ChoreCard.tsx`, `FeaturedRitualsPanel.tsx`) and the backend counter logic (`counter.py`) already consume the count correctly — they just need the correct value. No new files or components are needed.

## Complexity Tracking

> No constitution violations. No complexity justifications needed.

| Decision | Rationale | Alternative Considered |
|----------|-----------|----------------------|
| Filter by `chore` label in frontend `parentIssueCount` memo | The `chore` label is the authoritative classification for Chore-generated issues (applied in `service.py:372`). Board items already include `labels` array from the GraphQL query. Adding a label check to the existing filter is the minimal change. | Backend-computed count (rejected: adds API latency, the frontend already has all data needed; violates YAGNI) |
| Keep Sub-Issue filtering via `sub_issues` array cross-reference | Already implemented correctly in the existing `parentIssueCount` computation. Sub-Issues are identified by their presence in any parent item's `sub_issues` array. | GitHub API sub-issue endpoint (rejected: already handled by board data pipeline; would add N API calls) |
| No schema changes | The existing `last_triggered_count` and `schedule_value` fields on the `Chore` model are sufficient. The counter logic in `counter.py` correctly computes `issues_since = current_count - last_triggered_count`. | Add a dedicated "qualifying_issue_count" column (rejected: over-engineered; the counter is computed dynamically) |
