# Tasks: Fix Playwright Auth Setup, Mutation-Testing CI Noise, and Deprecated Chores Hook Usage

**Input**: Design documents from `/specs/001-fix-ci-auth-chores/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅ (N/A), contracts/ ✅ (N/A), quickstart.md ✅

**Tests**: No new test infrastructure required. Existing test mocks are updated to match the new hook shapes, and deprecated-hook tests are removed. No TDD was requested.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app monorepo**: `solune/frontend/`, `solune/backend/`, `.github/workflows/`

---

## Phase 1: Setup

**Purpose**: No new project initialization needed — this feature modifies an existing monorepo. Phase 1 is intentionally empty.

_(No setup tasks — all changes target existing files.)_

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No shared foundational infrastructure is needed. All user stories modify independent files and can proceed directly.

**⚠️ NOTE**: This feature has no blocking foundational phase. Each user story targets separate config files, workflow files, or hook files with no cross-story prerequisites.

_(No foundational tasks — user stories are independent.)_

---

## Phase 3: User Story 1 — Isolate Playwright Auth Setup from Default Test Runs (Priority: P1) 🎯 MVP

**Goal**: Exclude `save-auth-state.ts` from default Playwright test discovery, provide a dedicated auth-setup project gated on `AUTH_SETUP=1`, and wire the perf project to depend on auth-setup.

**Independent Test**: Run `npx playwright test --list` and confirm `save-auth-state.ts` does not appear; run `npx playwright test` and confirm all 64 E2E tests pass; run `AUTH_SETUP=1 npx playwright test --project=auth-setup --list` and confirm `save-auth-state.ts` is listed.

### Implementation for User Story 1

- [ ] T001 [US1] Add top-level `testIgnore: ['**/save-auth-state.ts']` to exclude save-auth-state.ts from default discovery in `solune/frontend/playwright.config.ts`
- [ ] T002 [US1] Add conditional `auth-setup` project that runs save-auth-state.ts only when `AUTH_SETUP=1` is set in `solune/frontend/playwright.config.ts`
- [ ] T003 [US1] Add `perf` project with `dependencies: ['auth-setup']` and `testMatch: /project-load-performance/` in `solune/frontend/playwright.config.ts`
- [ ] T004 [US1] Add `testIgnore: ['**/project-load-performance*']` to the `chromium` and `firefox` projects in `solune/frontend/playwright.config.ts`

**Checkpoint**: `save-auth-state.ts` absent from `npx playwright test --list`, all 64 E2E tests pass, `AUTH_SETUP=1` enables the auth-setup project.

---

## Phase 4: User Story 2 — Eliminate Misleading Mutation-Testing CI Failures (Priority: P1)

**Goal**: Make mutation-testing CI jobs appear green even when mutants survive, tune Stryker config for CI, consolidate duplicate workflows, and delete the old `mutation.yml`.

**Independent Test**: Confirm only `mutation-testing.yml` exists in `.github/workflows/`; validate YAML syntax; confirm `stryker.config.mjs` has `concurrency: 4` and `timeoutFactor: 2.5`.

### Implementation for User Story 2

- [ ] T005 [P] [US2] Update `concurrency` from 2 to 4 and add `timeoutFactor: 2.5` in `solune/frontend/stryker.config.mjs`
- [ ] T006 [P] [US2] Replace content of `.github/workflows/mutation-testing.yml` with consolidated workflow: Monday 3am UTC schedule, Node 22, 30-day artifact retention, job-level `continue-on-error: true`, `npm run test:mutate` for frontend
- [ ] T007 [US2] Delete duplicate workflow file `.github/workflows/mutation.yml`

**Checkpoint**: Single `mutation-testing.yml` exists, YAML is valid, Stryker config updated. Mutation jobs will appear green on next scheduled run.

---

## Phase 5: User Story 3 — Migrate Deprecated Chores Hook to Paginated Version (Priority: P2)

**Goal**: Replace all `useChoresList` usage with `useChoresListPaginated` in consumers, update test mocks, and remove the deprecated export.

**Independent Test**: `grep -r "useChoresList" solune/frontend/src/ --include="*.ts" --include="*.tsx" | grep -v Paginated` returns zero results; `npm run type-check` passes; `npm run test` passes.

### Implementation for User Story 3

- [ ] T008 [P] [US3] Update `ChoresPage.tsx` import from `useChoresList` to `useChoresListPaginated` and change data access from `.data` to `.allItems` in `solune/frontend/src/pages/ChoresPage.tsx`
- [ ] T009 [P] [US3] Update `ChoresPage.test.tsx` mock from `useChoresList` to `useChoresListPaginated` with `{ allItems }` return shape in `solune/frontend/src/pages/ChoresPage.test.tsx`
- [ ] T010 [P] [US3] Update `useCommandPalette.ts` import from `useChoresList` to `useChoresListPaginated`, change `.data` to `.allItems`, and update `useMemo` dependency in `solune/frontend/src/hooks/useCommandPalette.ts`
- [ ] T011 [P] [US3] Update `useCommandPalette.test.tsx` mock from `useChoresList` to `useChoresListPaginated` with `{ allItems }` return shape in `solune/frontend/src/hooks/useCommandPalette.test.tsx`
- [ ] T012 [US3] Remove deprecated `useChoresList` function and its JSDoc comment from `solune/frontend/src/hooks/useChores.ts`
- [ ] T013 [US3] Remove `useChoresList` test cases from `solune/frontend/src/hooks/useChores.test.tsx`

**Checkpoint**: Zero references to `useChoresList` in `solune/frontend/src/`; `npm run type-check` passes; all frontend tests pass.

---

## Phase 6: User Story 4 — Document Upstream Vitest Deprecation Warning (Priority: P3)

**Goal**: Add a comment in `vitest.config.ts` explaining that the `vitest/suite` deprecation warning is from `@fast-check/vitest@0.3.0` and cannot be fixed in project code.

**Independent Test**: Open `solune/frontend/vitest.config.ts` and confirm the comment block is present and references `@fast-check/vitest@0.3.0`.

### Implementation for User Story 4

- [ ] T014 [US4] Add explanatory comment block above the config export documenting the `vitest/suite` deprecation warning origin in `solune/frontend/vitest.config.ts`

**Checkpoint**: Comment is present and accurate.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all user stories.

- [ ] T015 Verify `save-auth-state.ts` absent from `npx playwright test --list` per quickstart.md §1
- [ ] T016 Verify only `mutation-testing.yml` exists via `ls .github/workflows/mutation*.yml` per quickstart.md §3
- [ ] T017 Verify zero `useChoresList` references via `grep -r "useChoresList" solune/frontend/src/` per quickstart.md §4
- [ ] T018 Run `npm run lint` in `solune/frontend/` — must pass clean
- [ ] T019 Run `npm run type-check` in `solune/frontend/` — must pass clean
- [ ] T020 Run `npm run test:coverage` in `solune/frontend/` — all 1,364+ tests pass
- [ ] T021 Run `npm run build` in `solune/frontend/` — must succeed
- [ ] T022 Validate mutation-testing.yml YAML syntax via `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/mutation-testing.yml'))"`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Empty — no setup needed
- **Foundational (Phase 2)**: Empty — no blocking prerequisites
- **User Story 1 (Phase 3)**: Independent — can start immediately
- **User Story 2 (Phase 4)**: Independent — can start immediately
- **User Story 3 (Phase 5)**: Independent — T008–T011 (consumer migrations) must complete before T012–T013 (deprecated export removal)
- **User Story 4 (Phase 6)**: Independent — can start immediately
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: No dependencies on other stories. All tasks modify `playwright.config.ts` sequentially.
- **User Story 2 (P1)**: No dependencies on other stories. T005 (Stryker config), T006 (workflow YAML), and T007 (delete file) are independent; T005 and T006 can run in parallel.
- **User Story 3 (P2)**: No dependencies on other stories. T008–T011 (consumer migrations) can all run in parallel. T012–T013 (remove deprecated export + tests) must wait for T008–T011.
- **User Story 4 (P3)**: No dependencies on other stories. Single task.

### Within User Story 3

- T008, T009, T010, T011 — all marked [P], can run in parallel (different files)
- T012, T013 — must wait for T008–T011 completion (consumers must be migrated before removing the export)

### Parallel Opportunities

- **Cross-story**: All four user stories target different files and can execute in parallel
- **Within US2**: T005 (stryker.config.mjs) and T006 (mutation-testing.yml) can run in parallel
- **Within US3**: T008, T009, T010, T011 (four different files) can all run in parallel

---

## Parallel Example: User Story 3

```bash
# Launch all consumer migration tasks in parallel (different files):
Task T008: "Update ChoresPage.tsx to useChoresListPaginated"
Task T009: "Update ChoresPage.test.tsx mock to useChoresListPaginated"
Task T010: "Update useCommandPalette.ts to useChoresListPaginated"
Task T011: "Update useCommandPalette.test.tsx mock to useChoresListPaginated"

# Then sequentially (depends on above):
Task T012: "Remove deprecated useChoresList from useChores.ts"
Task T013: "Remove useChoresList tests from useChores.test.tsx"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2)

1. Complete Phase 3: User Story 1 (Playwright auth isolation) — restores CI reliability
2. Complete Phase 4: User Story 2 (Mutation CI fixes) — eliminates misleading failures
3. **STOP and VALIDATE**: CI is green, no misleading failures, auth setup isolated
4. Both P1 stories delivered — highest-impact changes are done

### Incremental Delivery

1. User Stories 1 + 2 → CI reliability restored (MVP!)
2. Add User Story 3 → Deprecated hook removed, codebase consistent
3. Add User Story 4 → Upstream warning documented, contributor confusion eliminated
4. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. No shared setup — all stories can start immediately
2. Developer A: User Story 1 (Playwright config)
3. Developer B: User Story 2 (Stryker + workflows)
4. Developer C: User Story 3 (Hook migration) — note internal dependency: migrate consumers before removing export
5. Developer D: User Story 4 (Vitest comment)
6. All stories complete and integrate independently

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 22 |
| **User Story 1 tasks** | 4 (T001–T004) |
| **User Story 2 tasks** | 3 (T005–T007) |
| **User Story 3 tasks** | 6 (T008–T013) |
| **User Story 4 tasks** | 1 (T014) |
| **Polish/validation tasks** | 8 (T015–T022) |
| **Parallel opportunities** | 8 tasks (T005+T006, T008+T009+T010+T011, cross-story parallelism) |
| **Suggested MVP scope** | User Stories 1 + 2 (P1 priority — CI reliability) |
| **Format validation** | ✅ All 22 tasks follow `- [ ] [TaskID] [P?] [Story?] Description with file path` format |

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- No new test files are created — existing test mocks are updated
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
