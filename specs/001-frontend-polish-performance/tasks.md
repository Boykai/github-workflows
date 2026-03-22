# Tasks: Frontend Polish & Performance — Lucide Barrel File, ChoresPanel Bug Fix, Error Recovery Hints

**Input**: Design documents from `/specs/001-frontend-polish-performance/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Existing test suites (`npm run test:coverage`, `npm run lint`, `pytest`) must continue to pass. No new test infrastructure is required — existing Vitest + pytest suites cover changes. Unit tests for `errorHints.ts` and `useAllChoreNames` follow existing patterns.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. The three phases (A, B, C from the plan) map to user stories and can be executed in parallel.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `solune/backend/src/`, `solune/frontend/src/`
- Frontend paths use `@/` alias mapping to `solune/frontend/src/`
- Backend paths are relative to `solune/backend/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No shared setup is required for this feature. All three phases (icon barrel file, ChoresPanel fix, error hints) are independent workstreams modifying existing infrastructure. Proceed directly to Phase 2.

_(No tasks — existing project structure, dependencies, and tooling are already in place.)_

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No foundational blocking tasks exist. Each user story operates on independent files and can begin immediately. The three workstreams (Phase A: Icons, Phase B: ChoresPanel, Phase C: Error Hints) have no cross-dependencies.

_(No tasks — all user stories are self-contained and can start in parallel.)_

**Checkpoint**: Foundation ready — user story implementation can begin immediately in parallel.

---

## Phase 3: User Story 1 — Accurate Chore Template Counts (Priority: P1) 🎯 MVP

**Goal**: Fix the ChoresPanel bug where paginated/filtered chore data causes templates to incorrectly appear as "uncreated" by introducing a lightweight backend endpoint returning ALL chore names and a dedicated frontend hook.

**Independent Test**: Create several chores, apply filters or navigate to a later page, and verify that all previously created chore templates still show as "already created." Verify the endpoint returns all names regardless of UI state.

### Implementation for User Story 1

- [ ] T001 [US1] Add `GET /{project_id}/chore-names` backend endpoint in `solune/backend/src/api/chores.py` that returns `list[str]` of ALL chore names via `SELECT name FROM chores WHERE project_id = ?` — unpaginated, unfiltered, per contract `specs/001-frontend-polish-performance/contracts/chore-names.yaml`
- [ ] T002 [US1] Add API client method `listChoreNames(projectId: string): Promise<string[]>` in the appropriate frontend API service file (e.g., `solune/frontend/src/services/choresApi.ts` or equivalent) to call `GET /api/v1/chores/{project_id}/chore-names`
- [ ] T003 [US1] Add `useAllChoreNames(projectId)` hook in `solune/frontend/src/hooks/useChores.ts` using `useQuery` with `queryKey: ['chore-names', projectId]`, `staleTime: 60_000`, and `enabled: !!projectId`
- [ ] T004 [US1] Update `solune/frontend/src/components/chores/ChoresPanel.tsx` (lines 152–158) to replace the paginated `allItems` membership check with `useAllChoreNames` hook — build a `Set<string>` from the response and use it for template membership filtering; remove the related TODO comment

**Checkpoint**: Chore templates now correctly display creation status regardless of active filters or pagination state.

---

## Phase 4: User Story 2 — Actionable Error Recovery Hints (Priority: P2)

**Goal**: Create an error classification utility that maps HTTP status codes to structured recovery hints, and integrate it into all error surfaces (ErrorBoundary, ProjectBoardErrorBanners, EmptyState) so users see actionable guidance when errors occur.

**Independent Test**: Simulate each error class (401, 403, 404, 422, 429, 500, network failure, CORS error) and verify the correct hint text, icon, and optional action link appear below the error message in every error surface.

### Implementation for User Story 2

- [ ] T005 [US2] Create `solune/frontend/src/utils/errorHints.ts` with `getErrorHint(error: unknown): ErrorHint` function that classifies errors by HTTP status code (401/403 → auth, 404 → not found, 422 → validation, 429 → rate limit with reset time, 500+ → server error, TypeError/fetch failure → connection error, unknown → fallback) and returns `{ title: string; hint: string; action?: { label: string; href: string } }` per data-model.md classification mapping
- [ ] T006 [P] [US2] Integrate `getErrorHint()` into `solune/frontend/src/components/common/ErrorBoundary.tsx` — call `getErrorHint(this.state.error)` in the error fallback render path, display hint as a muted paragraph below the existing error message with an info/lightbulb icon, and render action link if present
- [ ] T007 [P] [US2] Integrate `getErrorHint()` into `solune/frontend/src/components/board/ProjectBoardErrorBanners.tsx` — enhance each error banner variant with contextual hint text; add reset time display and "Open Settings" link to the rate limit banner; add "Go to Login" link to auth error banners
- [ ] T008 [P] [US2] Extend `solune/frontend/src/components/common/EmptyState.tsx` with an optional `hint?: string` prop — when provided, render a muted paragraph below the description; ensure backward compatibility when `hint` is omitted
- [ ] T009 [US2] Update `solune/frontend/src/pages/AgentsPage.tsx` to pass `hint={getErrorHint(error).hint}` when rendering error-variant EmptyState components
- [ ] T010 [P] [US2] Update `solune/frontend/src/pages/ToolsPage.tsx` to pass `hint={getErrorHint(error).hint}` when rendering error-variant EmptyState components
- [ ] T011 [P] [US2] Update `solune/frontend/src/pages/ChoresPage.tsx` to pass `hint={getErrorHint(error).hint}` when rendering error-variant EmptyState components

**Checkpoint**: All error surfaces display contextual, actionable recovery hints. 401 errors link to login, 429 errors show reset time and settings link, network errors suggest connectivity checks.

---

## Phase 5: User Story 3 — Centralized Icon Import System (Priority: P3)

**Goal**: Consolidate all ~85 Lucide icon imports into a single barrel file at `src/lib/icons.ts`, migrate all ~68 import sites, and add a lint rule to prevent future import drift. This is purely organizational — no user-facing visual changes.

**Independent Test**: Run `grep -rn "from 'lucide-react'" solune/frontend/src/` and confirm zero results. Verify ESLint blocks new direct imports. Confirm production build icon-vendor chunk size is unchanged or smaller.

### Implementation for User Story 3

- [ ] T012 [US3] Scan the codebase to identify all unique Lucide icons currently imported across `solune/frontend/src/` — document the complete list of ~85 icons and ~68 import sites
- [ ] T013 [US3] Create barrel file `solune/frontend/src/lib/icons.ts` with named re-exports (`export { Icon1, Icon2, ... } from 'lucide-react'`) for ALL identified Lucide icons, including the `LucideIcon` type if used
- [ ] T014 [US3] Migrate all ~68 import sites across `solune/frontend/src/` to import from `@/lib/icons` instead of `lucide-react` directly — verify with `grep -rn "from 'lucide-react'" solune/frontend/src/` returning zero results (exclude `src/lib/icons.ts` itself)
- [ ] T015 [US3] Add ESLint `no-restricted-imports` rule in `solune/frontend/eslint.config.js` to block direct imports from `lucide-react` with message: "Import icons from @/lib/icons instead of lucide-react directly." — verify `npm run lint` passes with no violations (barrel file itself may need an eslint-disable comment)
- [ ] T016 [US3] Run production build (`npm run build` in `solune/frontend/`) and verify the `icons-vendor` chunk size is unchanged or smaller compared to before migration

**Checkpoint**: All icon imports are centralized. Lint rule prevents drift. Bundle size is unaffected.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final verification across all three workstreams.

- [ ] T017 Run `npm run lint` in `solune/frontend/` and verify zero errors across all changed files
- [ ] T018 Run `npm run test:coverage` in `solune/frontend/` and verify all tests pass with coverage thresholds met (statements 50%, branches 44%, functions 41%, lines 50%)
- [ ] T019 [P] Run backend tests (`pytest` in `solune/backend/`) to verify the new chore-names endpoint passes
- [ ] T020 Run quickstart.md full verification checklist — confirm all 7 gates pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No tasks — existing infrastructure sufficient
- **Foundational (Phase 2)**: No tasks — no blocking prerequisites
- **User Story 1 / Phase B (Phase 3)**: Can start immediately — independent workstream
- **User Story 2 / Phase C (Phase 4)**: Can start immediately — independent workstream
- **User Story 3 / Phase A (Phase 5)**: Can start immediately — independent workstream
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 — Chore Template Counts (P1)**: Fully independent. Internal order: T001 → T002 → T003 → T004 (backend endpoint → API client → hook → ChoresPanel update)
- **User Story 2 — Error Recovery Hints (P2)**: Fully independent. Internal order: T005 (utility) → T006, T007, T008 (parallel integrations) → T009, T010, T011 (page updates, parallel after T008)
- **User Story 3 — Icon Barrel File (P3)**: Fully independent. Internal order: T012 → T013 → T014 → T015 → T016 (scan → barrel → migrate → lint rule → verify build)

### Within Each User Story

- **US1**: T001 (backend) → T002 (API client) → T003 (hook) → T004 (ChoresPanel)
- **US2**: T005 (errorHints utility) → T006 + T007 + T008 (parallel: ErrorBoundary, Banners, EmptyState) → T009 + T010 + T011 (parallel: page updates)
- **US3**: T012 (scan) → T013 (barrel file) → T014 (migrate imports) → T015 (lint rule) → T016 (verify build)

### Parallel Opportunities

- **Cross-story parallelism**: US1, US2, and US3 are fully independent and can execute in parallel
- **Within US2**: T006, T007, T008 can run in parallel after T005 completes (different files, no dependencies)
- **Within US2**: T009, T010, T011 can run in parallel after T008 completes (different page files)

---

## Parallel Example: All Three User Stories

```bash
# All three phases can start simultaneously:
# Developer A: User Story 1 (ChoresPanel fix)
Task T001: "Add chore-names backend endpoint in solune/backend/src/api/chores.py"
Task T002: "Add API client method in frontend API service"
Task T003: "Add useAllChoreNames hook in solune/frontend/src/hooks/useChores.ts"
Task T004: "Update ChoresPanel.tsx membership check"

# Developer B: User Story 2 (Error Hints)
Task T005: "Create errorHints.ts in solune/frontend/src/utils/errorHints.ts"
Task T006: "Integrate into ErrorBoundary.tsx"     # parallel with T007, T008
Task T007: "Integrate into ProjectBoardErrorBanners.tsx"  # parallel with T006, T008
Task T008: "Extend EmptyState.tsx with hint prop"  # parallel with T006, T007

# Developer C: User Story 3 (Icon Barrel)
Task T012: "Scan codebase for Lucide icon usage"
Task T013: "Create barrel file src/lib/icons.ts"
Task T014: "Migrate all import sites to @/lib/icons"
Task T015: "Add ESLint no-restricted-imports rule"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete T001–T004: ChoresPanel bug fix (P1 — data correctness)
2. **STOP and VALIDATE**: Verify templates show correct status with filters active
3. Deploy/demo — users immediately see accurate chore template counts

### Incremental Delivery

1. User Story 1 (P1) → Accurate chore templates → Immediate user value
2. User Story 2 (P2) → Error recovery hints → Better error UX across all surfaces
3. User Story 3 (P3) → Icon barrel file → Developer experience improvement
4. Polish (Phase 6) → Full verification → Confidence in all changes

### Parallel Team Strategy

With multiple developers:

1. No shared setup needed — all stories start immediately
2. Developer A: US1 (T001–T004) — Backend + frontend fix
3. Developer B: US2 (T005–T011) — Error hints utility + integrations
4. Developer C: US3 (T012–T016) — Icon barrel file + migration
5. All reconvene for Phase 6 polish and full verification

---

## Notes

- [P] tasks = different files, no dependencies — safe to parallelize
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Phases A, B, C from plan.md map to US3, US1, US2 respectively (reordered by user priority from spec.md)
- All changes must pass `npm run lint` and `npm run test:coverage`
- Error hints classify by HTTP status code only — never parse error message strings
- Error hint strings are hardcoded English; i18n is deferred
- Icon barrel file is organizational only — Vite already tree-shakes via `manualChunks`
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
