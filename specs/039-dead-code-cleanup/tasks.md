# Tasks: Dead Code & Technical Debt Cleanup

**Input**: Design documents from `/specs/039-dead-code-cleanup/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Not required. Existing test suites (pytest, Vitest) are run after each phase for regression verification only. No new tests are written — all decompositions keep sub-functions private and preserve existing public API contracts.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/` at repository root
- **Docs**: `docs/` at repository root
- **Specs**: `specs/039-dead-code-cleanup/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify baseline codebase state and confirm all cleanup targets exist

- [ ] T001 Verify baseline codebase metrics (465 files, 4653 functions, 803 classes per CGC) and confirm all target files listed in plan.md project structure exist in the repository
- [ ] T002 [P] Review error-handling, deprecation-policy, and complexity-budget contracts in specs/039-dead-code-cleanup/contracts/ to confirm migration patterns before implementation

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Confirm shared utilities that US3 (DRY consolidation) depends on are functional and match expected signatures

**⚠️ CRITICAL**: US3 error handler migration and cache consolidation depend on these utilities existing with expected APIs

- [ ] T003 Confirm handle_service_error(exc, operation, error_cls) utility exists and matches expected signature in backend/src/logging_utils.py (expected at lines 224–261)
- [ ] T004 [P] Confirm require_selected_project validation helper exists in backend/src/dependencies.py and raises ValidationError when session.selected_project_id is missing
- [ ] T005 [P] Confirm InMemoryCache class exposes get(), get_stale(), set(), get_entry(), and refresh_ttl() methods in backend/src/services/cache.py

**Checkpoint**: Foundation verified — user story implementation can now begin

---

## Phase 3: User Story 1 — Remove Dead Code and Build Artifacts (Priority: P1) 🎯 MVP

**Goal**: Remove build artifacts and dead code from the codebase so the code index is accurate, search results are uncluttered, and the project maintains a clean footprint.

**Independent Test**: Verify that `backend/htmlcov/`, `frontend/coverage/`, `frontend/e2e-report/`, and `frontend/test-results/` are removed from the working tree, and that the duplicate `formatTimeAgo` in `DynamicDropdown.tsx` is replaced with the shared utility import. Dead code scanning should return no results for removed artifacts.

### Implementation for User Story 1

- [ ] T006 [US1] Remove gitignored build artifact directories from working tree: backend/htmlcov/, frontend/coverage/, frontend/e2e-report/, frontend/test-results/ (skip any that do not exist — cleanup must be idempotent)
- [ ] T007 [US1] Replace local formatTimeAgo function with import from @/utils/formatTime in frontend/src/components/settings/DynamicDropdown.tsx, adding `new Date(isoString)` conversion at the call site to adapt for the string-to-Date signature difference
- [ ] T008 [US1] Run frontend test suite (`npx vitest run`) to verify zero regressions after DynamicDropdown.tsx change

**Checkpoint**: User Story 1 complete — build artifacts removed and duplicate function eliminated

---

## Phase 4: User Story 2 — Annotate and Document Legacy Code Paths (Priority: P1)

**Goal**: Annotate legacy code paths with deprecation timelines and migration tracking so the team knows what is safe to remove and when.

**Independent Test**: Search for `DEPRECATED(` annotations in affected files and verify each legacy code path has a documented removal timeline or migration plan. Verify `@deprecated` and `@internal` JSDoc annotations on frontend fields and test utilities.

### Implementation for User Story 2

- [ ] T009 [P] [US2] Add `DEPRECATED(v2.0): Remove after all tracked issues use 5-column format. See issue #XXXX` annotation to `_ROW_RE_OLD` regex (L61–62) and its fallback usage (L206) in backend/src/services/agent_tracking.py
- [ ] T010 [P] [US2] Add `DEPRECATED(v2.0)` annotations with linked tracking issues to all legacy pipeline references at L2075+ in backend/src/services/copilot_polling/pipeline.py
- [ ] T011 [P] [US2] Add deprecation timeline annotations to `agents` field (L44) and `execution_mode` field (L46) in backend/src/models/pipeline.py with removal condition: "Remove once all pipelines use groups-based format"
- [ ] T012 [P] [US2] Add legacy format encounter logging (`logger.info("legacy_format_encountered", extra={"format_type": ..., "context": ..., "issue_number": ...})`) at normalization points L215, L238, L300 in backend/src/services/pipelines/service.py
- [ ] T013 [P] [US2] Add `@deprecated` JSDoc annotations to `old_status` (L97), `agents` (L1072), and `execution_mode` (L1075) fields in frontend/src/types/index.ts; audit `old_status` in StatusUpdateActionData and confirm whether any backend code sends it
- [ ] T014 [P] [US2] Add `@internal Test-only reset function. Do not use in production code.` JSDoc annotation to `_resetForTesting` export in frontend/src/hooks/useScrollLock.ts
- [ ] T015 [P] [US2] Audit `clearLegacyStorage` function (L40–47) in frontend/src/hooks/useChatHistory.ts — if localStorage is still used for security cleanup, add `@internal` annotation explaining its purpose; if no longer needed, remove the function
- [ ] T016 [P] [US2] Update `AITaskProposal` docstring to reflect permanent entity status (remove "Temporary entity" language) in backend/src/models/recommendation.py
- [ ] T017 [US2] Update docs/configuration.md to reflect correct migration count (001 through 022) and annotate blocking migrations (017, 018, 021) as historical/removed per research R8 findings
- [ ] T018 [US2] Run backend (`python -m pytest tests/ -v --tb=short`) and frontend (`npx vitest run`) test suites to verify zero regressions after annotation changes

**Checkpoint**: User Story 2 complete — all 8+ legacy code paths annotated with deprecation timelines and migration tracking active

---

## Phase 5: User Story 3 — Consolidate Duplicate Patterns (DRY) (Priority: P2)

**Goal**: Extract repeated code patterns into shared utilities so bug fixes and improvements only need to happen in one place.

**Independent Test**: Verify `handle_service_error` is used in all applicable API endpoints (14 migrated, 4 intentional exceptions preserved), `cached_fetch` replaces repeated cache patterns in 3 files, and `require_selected_project` replaces repeated validation checks — with all backend tests passing.

### Error Handler Migration (per contracts/error-handling.md)

- [ ] T019 [P] [US3] Migrate 5 inline error handlers to `handle_service_error` in backend/src/api/projects.py — replace `except Exception as e: logger.error(...); raise FooError(...)` patterns with `handle_service_error(e, "operation", ErrorClass)` calls
- [ ] T020 [P] [US3] Migrate 4 inline error handlers to `handle_service_error` in backend/src/api/webhooks.py per error-handling contract
- [ ] T021 [P] [US3] Migrate 2 inline error handlers to `handle_service_error` in backend/src/api/signal.py per error-handling contract
- [ ] T022 [P] [US3] Migrate 1 inline error handler to `handle_service_error` in backend/src/api/auth.py per error-handling contract
- [ ] T023 [P] [US3] Migrate 1 inline error handler to `handle_service_error` in backend/src/api/chores.py per error-handling contract
- [ ] T024 [P] [US3] Migrate 1 inline error handler at L952 to `handle_service_error` in backend/src/api/chat.py — skip L167 (silent-fail), L249/389/437 (error-response patterns per contract exceptions)

### Cache Pattern Extraction

- [ ] T025 [US3] Create `cached_fetch` async utility in backend/src/services/cache.py with signature: `cached_fetch(cache: InMemoryCache, key: str, fetch_fn: Callable[..., Awaitable[T]], ttl_seconds: int = 300, refresh: bool = False, stale_fallback: bool = False) -> T` per research R2 design
- [ ] T026 [P] [US3] Adopt `cached_fetch` replacing inline cache check/get/set pattern in backend/src/api/board.py (use `stale_fallback=True` for rate-limit/5xx scenarios)
- [ ] T027 [P] [US3] Adopt `cached_fetch` replacing inline cache check/get/set pattern in backend/src/api/projects.py
- [ ] T028 [US3] Adopt `cached_fetch` replacing inline cache check/get/set pattern in backend/src/api/chat.py

### Validation and Audit

- [ ] T029 [P] [US3] Adopt `require_selected_project` validation helper at 5+ repeated `if not session.selected_project_id` validation sites in backend/src/api/workflow.py
- [ ] T030 [P] [US3] Verify `pipeline_source` field end-to-end usage across backend models and frontend components; mark `@deprecated` if frontend does not consume the field
- [ ] T031 [US3] Address temporary file upload storage in backend/src/api/chat.py — add lifecycle management (cleanup on restart or TTL) or document as intentional for self-hosted single-instance deployments
- [ ] T032 [US3] Run backend test suite (`python -m pytest tests/ -v --tb=short`) and type check (`python -m pyright src/`) to verify zero regressions after DRY consolidation

**Checkpoint**: User Story 3 complete — 14 inline error handlers migrated, cache pattern consolidated into `cached_fetch`, validation helpers adopted

---

## Phase 6: User Story 4 — Reduce Function Complexity (Priority: P2)

**Goal**: Decompose high-complexity functions into smaller, focused sub-functions so the code is easier to understand, test, and maintain.

**Independent Test**: Measure cyclomatic complexity of each refactored function and verify the target CC is met, with all unit and integration tests passing. All extracted sub-functions must have `_` prefix (private) and remain co-located in the same module.

### Backend Decomposition (per contracts/complexity-budget.md)

- [ ] T033 [P] [US4] Decompose `post_agent_outputs_from_pr` (CC=123) into private sub-functions `_get_active_pipeline_tasks`, `_detect_agent_pr_completion`, `_extract_pr_markdown_files`, `_post_agent_comments`, `_update_tracking_after_output` in backend/src/services/copilot_polling/agent_output.py (target: each sub-function CC < 30)
- [ ] T034 [P] [US4] Decompose `assign_agent_for_status` (CC=91) into private sub-functions `_resolve_agent_for_status`, `_validate_assignment_context`, `_create_or_update_pipeline_state`, `_execute_agent_assignment` in backend/src/services/workflow_orchestrator/orchestrator.py (target: each sub-function CC < 25)
- [ ] T035 [P] [US4] Decompose `recover_stalled_issues` (CC=72) into private sub-functions `_bootstrap_recovery_config`, `_detect_stalled_issue`, `_check_recovery_cooldown`, `_execute_recovery_reassignment` in backend/src/services/copilot_polling/recovery.py (target: each sub-function CC < 20)

### Frontend Decomposition

- [ ] T036 [P] [US4] Verify `GlobalSettings` component CC in frontend/src/components/settings/GlobalSettings.tsx — if the form orchestration (excluding already-extracted subcomponents) exceeds CC=30, extract `useGlobalSettingsForm` custom hook for submit/reset logic
- [ ] T037 [P] [US4] Decompose `LoginPage` into co-located sub-components `HeroSection` (branding, tagline, feature highlights), `ThemeToggle` (dark/light switch), and `AuthPanel` (login button, OAuth callback) in frontend/src/pages/LoginPage.tsx (target: each sub-component CC < 30)

### Verification

- [ ] T038 [US4] Run backend (`python -m pytest tests/ -v`) and frontend (`npx vitest run`) test suites, plus type checks (`python -m pyright src/` and `npm run type-check`), to verify zero regressions after complexity reduction

**Checkpoint**: User Story 4 complete — all 5 complexity hotspots decomposed to meet CC targets, zero functions with CC > 40 remain

---

## Phase 7: User Story 5 — Plan Future Architectural Migrations (Priority: P3)

**Goal**: Document migration plans for singleton removal and in-memory store migration so these larger refactors can be scoped and executed in dedicated specs. Audit backward-compat aliases and legacy settings fields.

**Independent Test**: Verify migration plans exist with complete checklists of affected files and import sites. Verify backward-compat aliases are audited with clear removal criteria or `@deprecated` annotations.

### Migration Planning (documentation only — no implementation)

- [ ] T039 [P] [US5] Create singleton removal migration plan in specs/039-dead-code-cleanup/migration-plan-singleton.md — document all 17+ import sites for `github_projects_service`, provider pattern design with `get_service()` fallback, and a checklist of all files needing migration (reference backend/src/services/github_projects/service.py and agents.py)
- [ ] T040 [P] [US5] Create in-memory store SQLite migration plan in specs/039-dead-code-cleanup/migration-plan-sqlite.md — document all ~15 code paths for `_messages`, `_proposals`, `_recommendations` in backend/src/api/chat.py, reference existing migration 012 tables, and list transaction management requirements

### Backward-Compatibility Alias Audit

- [ ] T041 [P] [US5] Audit backward-compat re-export aliases (L16–18) in backend/src/models/chat.py — grep for all import sites of old names across the codebase; remove aliases if no consumers found, otherwise add `@deprecated` annotation with migration instructions
- [ ] T042 [P] [US5] Audit backward-compat alias (L8) in backend/src/prompts/issue_generation.py — grep for all import sites of old name; remove if no consumers found, otherwise add `@deprecated` annotation
- [ ] T043 [P] [US5] Audit backward-compat alias (L94) in backend/src/api/auth.py — grep for all import sites of old name; remove if no consumers found, otherwise add `@deprecated` annotation

### Settings Audit

- [ ] T044 [US5] Audit `agent_pipeline_mappings` deprecation status in backend/src/services/workflow_orchestrator/config.py and frontend/src/components/settings/ProjectSettings.tsx — if no project uses the old format, remove UI editing and auto-backfill code; otherwise document removal criteria

### Verification

- [ ] T045 [US5] Run backend (`python -m pytest tests/ -v`) and frontend (`npx vitest run`) test suites to verify zero regressions after alias removal and settings audit

**Checkpoint**: User Story 5 complete — migration plans documented, backward-compat aliases audited, all planning artifacts produced

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final sweep and validation across all user stories

- [ ] T046 [P] Run final cleanup sweep removing orphaned imports across backend/src/ and frontend/src/ (use linting tools: `python -m ruff check src/ --fix` for backend, `npm run lint -- --fix` for frontend)
- [ ] T047 [P] Update project structure documentation in docs/ if any file paths changed during cleanup; verify README.md references are still accurate
- [ ] T048 Run full regression suite: backend pytest (`python -m pytest tests/ -v`), frontend vitest (`npx vitest run`), backend type check (`python -m pyright src/`), frontend type check (`npm run type-check`), frontend lint (`npm run lint`), and validate all success criteria from specs/039-dead-code-cleanup/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — confirms shared utilities for US3
- **US1 (Phase 3)**: Can start after Setup — no dependency on Foundational
- **US2 (Phase 4)**: Can start after Setup — no dependency on Foundational or US1
- **US3 (Phase 5)**: Depends on Foundational (Phase 2) — uses confirmed shared utilities
- **US4 (Phase 6)**: Depends on US1, US2, US3 — avoids merge conflicts on shared files (agent_output.py, chat.py, projects.py)
- **US5 (Phase 7)**: Can start after Setup — produces planning artifacts only; may run in parallel with US1/US2
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Independent — can start immediately after Setup
- **US2 (P1)**: Independent — can start immediately after Setup; can run in parallel with US1
- **US3 (P2)**: Depends on Foundational phase — uses confirmed `handle_service_error`, `require_selected_project`, `InMemoryCache`
- **US4 (P2)**: Depends on US1–US3 completion — avoids conflicts on files modified in earlier stories (per spec: "depends on earlier cleanup being complete to avoid conflicts")
- **US5 (P3)**: Independent — produces documentation/planning artifacts only; can run in parallel with US1/US2

### Within Each User Story

- Tasks marked [P] can run in parallel (different files, no inter-dependencies)
- Error handler migration tasks (T019–T024) MUST complete before cache adoption on same files (T027 for projects.py, T028 for chat.py)
- `cached_fetch` creation (T025) MUST complete before all adoption tasks (T026–T028)
- File upload lifecycle (T031) should run after other chat.py modifications (T024, T028)
- Decomposition tasks (T033–T037) are fully independent — different files, different functions
- Backward-compat alias audits (T041–T043) are fully independent — different files

### Parallel Opportunities

- **US1 + US2**: Can run fully in parallel (no overlapping files)
- **US1 + US5**: Can run in parallel (no overlapping files)
- **US2 + US5**: Can run in parallel (no overlapping files)
- **T009–T016** (US2 annotations): 8 tasks across 8 different files — full parallelism
- **T019–T025** (US3 error handlers + cache creation): 7 tasks across 7 different files — full parallelism
- **T026–T027** (US3 cache adoption): board.py and projects.py — parallel after T025 completes
- **T033–T037** (US4 decomposition): 5 tasks across 5 different files — full parallelism
- **T039–T043** (US5 planning + audits): 5 tasks across 5 different files — full parallelism

---

## Parallel Example: User Story 2

```bash
# Launch all annotation tasks in parallel (8 different files):
Task T009: "DEPRECATED annotation for _ROW_RE_OLD in agent_tracking.py"
Task T010: "DEPRECATED annotations for legacy pipeline in pipeline.py"
Task T011: "Deprecation annotations for model fields in models/pipeline.py"
Task T012: "Legacy format encounter logging in pipelines/service.py"
Task T013: "@deprecated JSDoc for TS fields in types/index.ts"
Task T014: "@internal JSDoc for _resetForTesting in useScrollLock.ts"
Task T015: "clearLegacyStorage audit in useChatHistory.ts"
Task T016: "AITaskProposal docstring update in recommendation.py"
# Then sequential:
Task T017: "Update docs/configuration.md"
Task T018: "Run regression tests"
```

## Parallel Example: User Story 3

```bash
# Group 1 — Launch all error handler migrations + cache utility creation in parallel:
Task T019: "Migrate 5 handlers in projects.py"
Task T020: "Migrate 4 handlers in webhooks.py"
Task T021: "Migrate 2 handlers in signal.py"
Task T022: "Migrate 1 handler in auth.py"
Task T023: "Migrate 1 handler in chores.py"
Task T024: "Migrate 1 handler in chat.py"
Task T025: "Create cached_fetch in cache.py"

# Group 2 — After Group 1 completes, launch cache adoption + validation in parallel:
Task T026: "Adopt cached_fetch in board.py"
Task T027: "Adopt cached_fetch in projects.py"
Task T029: "Adopt require_selected_project in workflow.py"
Task T030: "Verify pipeline_source usage"

# Group 3 — After Group 2 completes for chat.py dependencies:
Task T028: "Adopt cached_fetch in chat.py"
Task T031: "File upload lifecycle in chat.py"
Task T032: "Run regression tests"
```

## Parallel Example: User Story 4

```bash
# Launch all decomposition tasks in parallel (5 different files):
Task T033: "Decompose post_agent_outputs_from_pr in agent_output.py"
Task T034: "Decompose assign_agent_for_status in orchestrator.py"
Task T035: "Decompose recover_stalled_issues in recovery.py"
Task T036: "Verify/extract GlobalSettings in GlobalSettings.tsx"
Task T037: "Decompose LoginPage in LoginPage.tsx"
# Then:
Task T038: "Run regression tests + type checks"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup — verify baseline
2. Complete Phase 3: User Story 1 — remove build artifacts and duplicate function
3. **STOP and VALIDATE**: Run frontend tests, confirm artifacts removed
4. Immediate impact: cleaner code index, uncluttered search results

### Incremental Delivery

1. Complete Setup → Baseline confirmed
2. Add US1 (dead code removal) → Test → Immediate cleanup (**MVP!**)
3. Add US2 (deprecation annotations) → Test → Legacy code documented with timelines
4. Add US3 (DRY consolidation) → Test → Error handling and caching unified
5. Add US4 (complexity reduction) → Test → All functions under CC targets
6. Add US5 (migration planning) → Test → Architectural roadmap complete
7. Each story adds maintainability improvements without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team verifies Setup + Foundational together
2. Once verified:
   - Developer A: US1 (dead code removal — fast, high-impact)
   - Developer B: US2 (deprecation annotations — many parallel tasks)
   - Developer C: US5 (migration planning — can start early, documentation only)
3. After US1 + US2 complete:
   - Developer A: US3 (DRY consolidation — largest task count)
   - Developer B: US4 preparation (review complexity-budget contract, plan decompositions)
4. After US3 completes:
   - Developer A + B: US4 (complexity reduction — 5 parallel decompositions)
5. Polish phase: All developers collaborate on final sweep

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- CGC checkpoints (per quickstart.md) should be run after completing each user story phase
- Constraint: Zero test regressions, zero type-check errors, no new external dependencies, no behavioral changes
- Total inline error handler migration: 14 direct candidates across 6 files (4 intentional exceptions preserved)
- Total complexity targets: 5 functions decomposed to CC < 30 (with stricter targets for 2)
- Total migration plans: 2 planning artifacts (singleton removal, SQLite migration)
