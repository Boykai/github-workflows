# Tasks: Fix 'Every X Issues' Chore Counter to Only Count GitHub Parent Issues

**Input**: Design documents from `/specs/030-fix-chore-issue-counter/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are not explicitly requested in the feature specification. Existing backend tests (`test_chores_counter.py`) should continue to pass without changes. No new test tasks are generated.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. This is a surgical bug fix — the total change footprint is minimal (~1 line of code + 1 docstring clarification).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify the development environment and existing behaviour before making changes.

- [ ] T001 Verify frontend builds cleanly by running `cd frontend && npx tsc --noEmit`
- [ ] T002 [P] Verify existing backend counter tests pass by running `cd backend && python -m pytest tests/unit/test_chores_counter.py -v`
- [ ] T003 [P] Verify existing frontend tests pass by running `cd frontend && npx vitest run`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No foundational/blocking changes needed — this is a filter fix to an existing computation. All required data (`BoardItem.labels`) is already available in the board data pipeline.

**⚠️ CRITICAL**: No new infrastructure is needed. The `labels` array on `BoardItem` is already populated by the GraphQL query (`labels(first:20)`) and available on every board item. The `"chore"` label is applied at issue creation time in `backend/src/services/chores/service.py:372`.

**Checkpoint**: No changes required — proceed to user story implementation.

---

## Phase 3: User Story 1 — Counter Displays Accurate Count of Qualifying Parent Issues (Priority: P1) 🎯 MVP

**Goal**: Add chore-label exclusion filter to the `parentIssueCount` useMemo computation in `ChoresPage.tsx` so the tile counter excludes issues with the `"chore"` label.

**Independent Test**: Set up a Chore with "Every 5 issues" trigger. Create a mix of regular issues, Sub-Issues, and Chore-labelled issues. Verify the tile counter increments only for qualifying Parent Issues (non-Sub-Issue, non-Chore-labelled, content_type=issue).

**Acceptance Scenarios**:
- Counter excludes issues with the `chore` label
- Counter continues to exclude Sub-Issues (existing behaviour preserved)
- Counter continues to exclude non-issue content types (existing behaviour preserved)
- Counter deduplicates by `item_id` (existing behaviour preserved)

### Implementation for User Story 1

- [ ] T004 [US1] Add chore-label exclusion filter to `parentIssueCount` useMemo in `frontend/src/pages/ChoresPage.tsx` — insert `if (item.labels?.some(l => l.name === 'chore')) continue;` after the sub-issue exclusion check (line ~49) so that items with the `"chore"` label are skipped from the count

**Checkpoint**: At this point, the `parentIssueCount` correctly excludes Chore-labelled issues, Sub-Issues, and non-issue content types. The tile counter on every `ChoreCard` and the `FeaturedRitualsPanel` ranking both receive the corrected count.

---

## Phase 4: User Story 2 — Trigger Evaluation Uses Same Filtered Count as Tile Display (Priority: P1)

**Goal**: Ensure the backend trigger evaluation receives the same corrected `parentIssueCount` value as the tile display.

**Independent Test**: Configure a Chore with "Every 3 issues." Create 3 qualifying Parent Issues plus several Sub-Issues and Chore issues. Verify the Chore fires at the counter display value of 3 — not inflated by excluded issue types.

**Acceptance Scenarios**:
- The `evaluate_triggers` endpoint receives the corrected `parentIssueCount` (excluding chores and sub-issues) from the frontend caller
- The trigger evaluation fires at the correct threshold matching the tile display
- No backend code changes needed — the fix in T004 corrects the value passed to the backend

### Implementation for User Story 2

- [ ] T005 [US2] Clarify docstring in `backend/src/services/chores/counter.py` for `evaluate_count_trigger()` to specify that `current_count` must be the count of qualifying Parent Issues (excluding Chore-labelled issues and Sub-Issues) to ensure callers pass the correct filtered value

**Checkpoint**: The backend docstring now explicitly documents that `current_count` must exclude Chore-labelled issues and Sub-Issues. The corrected `parentIssueCount` from T004 flows through to the trigger evaluation via the existing `evaluate_triggers` call path.

---

## Phase 5: User Story 3 — Independent Per-Chore Counter Scoping (Priority: P1)

**Goal**: Verify that each Chore's counter is independently scoped to its own `last_triggered_count` baseline.

**Independent Test**: Create two Chores with different thresholds. Run one Chore. Verify the other Chore's counter is unaffected.

**Acceptance Scenarios**:
- Each Chore tile shows a counter computed from its own `last_triggered_count`
- Triggering one Chore does not reset another Chore's counter
- The formula `remaining = schedule_value - (parentIssueCount - last_triggered_count)` is applied per-Chore

### Implementation for User Story 3

No code changes needed — per-Chore independence is already correctly implemented via the `last_triggered_count` field on each `Chore` record. The counter computation in `ChoreCard.tsx` (`issuesSince = parentIssueCount - chore.last_triggered_count`) and `counter.py` (`issues_since = current_count - chore.last_triggered_count`) both use per-Chore baselines. Research R4 confirms this.

**Checkpoint**: Per-Chore counter scoping is verified as already correct. No changes required.

---

## Phase 6: User Story 4 — Counter Reset After Chore Execution (Priority: P2)

**Goal**: Verify that a Chore's counter resets to zero after successful execution.

**Independent Test**: Let a Chore reach its threshold and fire. Verify the counter resets to 0 and begins accumulating from new qualifying Parent Issues only.

**Acceptance Scenarios**:
- After a Chore fires, `last_triggered_count` is updated to the current `parentIssueCount`
- The counter display shows 0 remaining immediately after execution
- New qualifying Parent Issues created after execution increment the counter from 0

### Implementation for User Story 4

No code changes needed — counter reset is already correctly implemented in `service.py:485-498`. When a Chore triggers, `last_triggered_count` is set to the current `parent_issue_count` via CAS update, effectively resetting the delta to 0. Research R5 confirms this.

**Checkpoint**: Counter reset is verified as already correct. No changes required.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Validation, verification, and documentation.

- [ ] T006 [P] Run frontend type check (`cd frontend && npx tsc --noEmit`) to verify the chore-label filter addition compiles without errors
- [ ] T007 [P] Run existing backend counter tests (`cd backend && python -m pytest tests/unit/test_chores_counter.py -v`) to verify no regressions
- [ ] T008 [P] Run full frontend test suite (`cd frontend && npx vitest run`) to verify no regressions from the filter change
- [ ] T009 Manual verification: Start frontend and backend, navigate to Chores page, verify counter excludes Chore-labelled issues per `quickstart.md` verification steps

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: No work needed — skip to user stories
- **User Story 1 (Phase 3)**: Depends on Setup (T001–T003 passing) — this is the core fix
- **User Story 2 (Phase 4)**: Can run in parallel with Phase 3 (different file: counter.py vs ChoresPage.tsx)
- **User Story 3 (Phase 5)**: Verification only — no code changes
- **User Story 4 (Phase 6)**: Verification only — no code changes
- **Polish (Phase 7)**: Depends on T004 and T005 being complete

### User Story Dependencies

- **User Story 1 (P1)**: Core fix — `parentIssueCount` filter in `ChoresPage.tsx`. No dependencies on other stories. **This is the MVP.**
- **User Story 2 (P1)**: Docstring clarification in `counter.py`. Independent of US1 (different file). Can run in parallel.
- **User Story 3 (P1)**: Already implemented — verification only. No code changes.
- **User Story 4 (P2)**: Already implemented — verification only. No code changes.

### Parallel Opportunities

- T001, T002, T003 can all run in parallel (Setup phase)
- T004 and T005 can run in parallel (different files: frontend vs backend)
- T006, T007, T008 can all run in parallel (Polish phase)

---

## Parallel Example: User Story 1 + User Story 2

```bash
# These two tasks can be executed in parallel since they modify different files:
Task T004: "Add chore-label exclusion filter in frontend/src/pages/ChoresPage.tsx"
Task T005: "Clarify docstring in backend/src/services/chores/counter.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Verify environment (T001–T003)
2. Complete Phase 3: User Story 1 — Add chore-label filter (T004)
3. **STOP and VALIDATE**: Run type check, tests, and manual verification
4. Deploy/demo if ready — counter now excludes Chore-labelled issues

### Incremental Delivery

1. T004 (US1): Add chore-label filter → Test → **MVP complete**
2. T005 (US2): Clarify backend docstring → Enhances developer documentation
3. Phases 5–6: Verify existing behaviour → Confirm no regressions
4. Phase 7: Full validation sweep

### Summary

| Metric | Value |
|--------|-------|
| Total tasks | 9 |
| Code-change tasks | 2 (T004: frontend filter, T005: backend docstring) |
| Verification-only tasks | 7 (T001–T003, T006–T009) |
| User Stories with code changes | 2 (US1, US2) |
| User Stories already correct | 2 (US3, US4) |
| Parallel opportunities | 3 groups (Setup, Implementation, Polish) |
| Files modified | 2 (`ChoresPage.tsx`, `counter.py`) |
| MVP scope | User Story 1 only (T004) |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- US3 and US4 require no code changes — they document verification that existing behaviour is correct
- The `"chore"` label is case-sensitive and matches the label applied in `backend/src/services/chores/service.py:372`
- The `BoardItem.labels` array is already populated by the GraphQL query with `labels(first:20)`
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
