# Tasks: Add 'Clean Up' Button to Delete Stale Branches and PRs

**Input**: Design documents from `/specs/015-stale-cleanup-button/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/cleanup-api.md

**Tests**: Tests are OPTIONAL — not explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4, US5, US6)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Database migration, shared backend models, and shared frontend types needed by all user stories

- [ ] T001 Create cleanup audit logs migration in backend/src/migrations/008_cleanup_audit_logs.sql
- [ ] T002 [P] Create cleanup Pydantic models (request/response/row) in backend/src/models/cleanup.py
- [ ] T003 [P] Add cleanup TypeScript interfaces (BranchInfo, PullRequestInfo, CleanupPreflightResponse, CleanupExecuteRequest, CleanupExecuteResponse, CleanupItemResult) to frontend/src/types/index.ts

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Backend cleanup service, API routing, and frontend API client that MUST be complete before ANY user story UI can function

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement cleanup service with preflight logic (fetch all branches via REST, fetch open PRs via REST, fetch open issues on project board via GraphQL, 3-layer cross-referencing strategy, permission check) in backend/src/services/cleanup_service.py
- [ ] T005 Implement cleanup service execute logic for branch deletion (sequential DELETE /repos/{owner}/{repo}/git/refs/heads/{branch} with 200ms delay, main branch server-side rejection) in backend/src/services/cleanup_service.py
- [ ] T006 Implement cleanup service execute logic for PR closure (sequential PATCH /repos/{owner}/{repo}/pulls/{number} with state=closed, 200ms delay between requests) in backend/src/services/cleanup_service.py
- [ ] T007 Implement cleanup service audit trail logic (create audit log row on execute start, update on completion/failure, query history) in backend/src/services/cleanup_service.py
- [ ] T008 Create cleanup API router with POST /cleanup/preflight, POST /cleanup/execute, GET /cleanup/history endpoints (auth via get_session_dep) in backend/src/api/cleanup.py
- [ ] T009 Register cleanup API router with prefix /cleanup and tag "cleanup" in backend/src/api/__init__.py
- [ ] T010 [P] Add cleanup API client methods (cleanupPreflight, cleanupExecute, cleanupHistory) to frontend/src/services/api.ts

**Checkpoint**: Backend API fully functional — preflight, execute, and history endpoints respond correctly with auth

---

## Phase 3: User Story 1 — Review and Confirm Deletion Candidates (Priority: P1) 🎯 MVP

**Goal**: Maintainer clicks 'Clean Up', system fetches all branches/PRs, cross-references against open issues on the project board, and presents a confirmation modal listing items to delete and items to preserve with reasons. Maintainer can confirm or cancel.

**Independent Test**: Click 'Clean Up' on a repository with a mix of stale branches, active branches linked to open issues, and the main branch → verify the modal correctly categorizes every item into deletion or preservation lists with reasons shown.

### Implementation for User Story 1

- [ ] T011 [P] [US1] Create useCleanup React hook with preflight query (POST /cleanup/preflight), workflow state machine (idle → loading → confirming → executing → summary → idle), and error state in frontend/src/hooks/useCleanup.ts
- [ ] T012 [P] [US1] Create CleanUpConfirmModal component displaying branches_to_delete, branches_to_preserve, prs_to_close, prs_to_preserve lists with preservation reasons, confirm/cancel buttons, and empty-state handling (no items to delete → confirm disabled) in frontend/src/components/board/CleanUpConfirmModal.tsx
- [ ] T013 [US1] Create CleanUpButton component with onClick that triggers preflight via useCleanup hook, loading spinner during preflight, and renders CleanUpConfirmModal when confirming state is active in frontend/src/components/board/CleanUpButton.tsx
- [ ] T014 [US1] Add CleanUpButton to the board header area in frontend/src/components/board/ProjectBoard.tsx

**Checkpoint**: User Story 1 complete — maintainer can click 'Clean Up', see the confirmation modal with categorized items, and cancel without deletions

---

## Phase 4: User Story 2 — Execute Clean-Up Operation (Priority: P1)

**Goal**: After confirming deletion, the system deletes branches and closes PRs sequentially, displays a progress indicator, and presents a summary report showing counts and per-item results.

**Independent Test**: Confirm deletion on a repository with known stale branches and PRs → verify progress indicator shows during execution → verify summary report shows correct counts of deleted/closed/preserved items.

### Implementation for User Story 2

- [ ] T015 [US2] Add execute mutation to useCleanup hook (POST /cleanup/execute with confirmed branches_to_delete and prs_to_close, transition to executing state, then to summary state on response) in frontend/src/hooks/useCleanup.ts
- [ ] T016 [US2] Add progress indicator UI to CleanUpButton component (visible during executing state, showing "Cleaning up..." with spinner) in frontend/src/components/board/CleanUpButton.tsx
- [ ] T017 [US2] Create CleanUpSummary component displaying operation results (branches_deleted, prs_closed, branches_preserved, prs_preserved, errors list, per-item results with action/reason/error, dismiss button) in frontend/src/components/board/CleanUpSummary.tsx
- [ ] T018 [US2] Render CleanUpSummary in CleanUpButton when workflow state is summary in frontend/src/components/board/CleanUpButton.tsx

**Checkpoint**: User Stories 1 AND 2 complete — full clean-up workflow (click → review → confirm → progress → summary) functional

---

## Phase 5: User Story 3 — Discover the Clean-Up Feature (Priority: P2)

**Goal**: The 'Clean Up' button has a descriptive tooltip explaining that the operation removes stale branches and PRs while preserving main and items linked to open issues on the project board.

**Independent Test**: Hover over the 'Clean Up' button → verify tooltip text accurately describes the operation scope and preservation behavior.

### Implementation for User Story 3

- [ ] T019 [US3] Add descriptive tooltip to CleanUpButton (text: "Remove stale branches and pull requests while preserving 'main' and items linked to open issues on the project board") in frontend/src/components/board/CleanUpButton.tsx

**Checkpoint**: User Story 3 complete — button tooltip provides clear discoverability

---

## Phase 6: User Story 4 — Handle Errors Gracefully During Clean-Up (Priority: P2)

**Goal**: When deletions fail due to permissions, rate limits, or network issues, the system surfaces actionable error messages per item, continues with remaining items, and includes errors in the summary report.

**Independent Test**: Simulate a permission error on one branch deletion → verify the system reports the error, continues with remaining deletions, and includes the failure with reason in the summary.

### Implementation for User Story 4

- [ ] T020 [US4] Add error handling to useCleanup hook for preflight failures (network errors, 422 invalid project, 429 rate limit) with user-facing error messages and transition back to idle state in frontend/src/hooks/useCleanup.ts
- [ ] T021 [US4] Add inline error display to CleanUpButton for preflight errors (show error message with retry option, no modal opened) in frontend/src/components/board/CleanUpButton.tsx
- [ ] T022 [US4] Enhance CleanUpSummary to distinguish successful deletions, failed deletions (with error reason), and preserved items in separate sections in frontend/src/components/board/CleanUpSummary.tsx

**Checkpoint**: User Story 4 complete — errors are surfaced per-item with actionable messages, no silent failures

---

## Phase 7: User Story 5 — Permission Verification Before Clean-Up (Priority: P2)

**Goal**: When the user lacks delete permissions, the system detects this during preflight and shows a clear permission error before any deletions are attempted.

**Independent Test**: Authenticate as a user without push access → click 'Clean Up' → verify a permission error message is shown within 3 seconds, before the confirmation modal.

### Implementation for User Story 5

- [ ] T023 [US5] Add permission error handling to useCleanup hook (detect has_permission=false in preflight response, set permission error state, do not transition to confirming) in frontend/src/hooks/useCleanup.ts
- [ ] T024 [US5] Add permission error UI to CleanUpButton (display "You need at least push access to this repository to delete branches and close pull requests." when permission error state is set) in frontend/src/components/board/CleanUpButton.tsx

**Checkpoint**: User Story 5 complete — users without permissions see a clear error before any modal or deletion

---

## Phase 8: User Story 6 — Audit Trail of Clean-Up Operations (Priority: P3)

**Goal**: After a clean-up completes, the maintainer can review a detailed audit trail listing every deleted and preserved item with timestamps and reasons, available after dismissing the summary.

**Independent Test**: Perform a clean-up → dismiss the summary → access the audit trail → verify all actions are logged with correct details (item type, action, reason, timestamp).

### Implementation for User Story 6

- [ ] T025 [US6] Add audit history query to useCleanup hook (GET /cleanup/history with owner/repo params, store audit entries in state, expose showAuditHistory toggle) in frontend/src/hooks/useCleanup.ts
- [ ] T026 [US6] Create CleanUpAuditHistory component displaying past cleanup operations (timestamp, counts, status) with per-item detail drill-down, accessible from board after summary is dismissed in frontend/src/components/board/CleanUpAuditHistory.tsx
- [ ] T027 [US6] Add "View Audit History" link in CleanUpSummary dismiss footer and render CleanUpAuditHistory from CleanUpButton when audit history state is active in frontend/src/components/board/CleanUpButton.tsx

**Checkpoint**: User Story 6 complete — audit trail accessible for post-operation review

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T028 [P] Verify main branch is unconditionally protected server-side (reject in execute endpoint even if included in request) in backend/src/api/cleanup.py
- [ ] T029 [P] Verify sequential deletion with 200ms delay respects GitHub secondary rate limits in backend/src/services/cleanup_service.py
- [ ] T030 [P] Verify 3-layer cross-referencing (naming convention, PR body references, timeline events) produces accurate categorization in backend/src/services/cleanup_service.py
- [ ] T031 Run quickstart.md manual validation (start app, click Clean Up, review modal, confirm, view summary, check audit trail) per specs/015-stale-cleanup-button/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (migration + models) — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) — Preflight + confirmation modal
- **User Story 2 (Phase 4)**: Depends on User Story 1 (Phase 3) — Execute builds on confirmation flow
- **User Story 3 (Phase 5)**: Depends on User Story 1 (Phase 3) — Tooltip added to existing button
- **User Story 4 (Phase 6)**: Depends on User Story 2 (Phase 4) — Error handling requires execute flow
- **User Story 5 (Phase 7)**: Depends on User Story 1 (Phase 3) — Permission check in preflight
- **User Story 6 (Phase 8)**: Depends on User Story 2 (Phase 4) — Audit trail requires completed operations
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P1)**: Builds on US1 (useCleanup hook + CleanUpButton already created)
- **User Story 3 (P2)**: Builds on US1 (adds tooltip to existing CleanUpButton)
- **User Story 4 (P2)**: Builds on US2 (adds error handling to existing hook + summary)
- **User Story 5 (P2)**: Builds on US1 (adds permission check to existing hook + button)
- **User Story 6 (P3)**: Builds on US2 (adds audit history to existing hook + summary)

### Within Each User Story

- Hook logic before component UI
- Component rendering before page integration
- Core functionality before error handling

### Parallel Opportunities

- T002 (backend models) and T003 (frontend types) can run in parallel — different files
- T010 (frontend API client) can run in parallel with T004–T009 (backend service/API) — different directories
- T011 (useCleanup hook) and T012 (CleanUpConfirmModal) can run in parallel within US1 — different files
- US3 and US5 could run in parallel once US1 is complete (both modify CleanUpButton but at different layers)
- T028, T029, and T030 (polish verification tasks) can run in parallel — independent validation

---

## Parallel Example: Setup Phase

```bash
# Launch setup tasks in parallel (different files):
Task: T002 "Create cleanup Pydantic models in backend/src/models/cleanup.py"
Task: T003 "Add cleanup TypeScript interfaces to frontend/src/types/index.ts"
```

## Parallel Example: Foundational Phase

```bash
# Launch frontend API client in parallel with backend service:
Task: T004-T009 "Backend cleanup service + API endpoints"
Task: T010 "Frontend cleanup API client methods in frontend/src/services/api.ts"
```

## Parallel Example: User Story 1

```bash
# Launch hook and modal in parallel (different files):
Task: T011 "Create useCleanup hook in frontend/src/hooks/useCleanup.ts"
Task: T012 "Create CleanUpConfirmModal in frontend/src/components/board/CleanUpConfirmModal.tsx"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup (migration, models, types)
2. Complete Phase 2: Foundational (service, API, frontend client)
3. Complete Phase 3: User Story 1 (preflight + confirmation modal)
4. Complete Phase 4: User Story 2 (execute + progress + summary)
5. **STOP and VALIDATE**: Test MVP — click Clean Up, review modal, confirm, view summary
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Backend API ready
2. Add User Story 1 → Confirmation modal works → Deploy/Demo (read-only MVP)
3. Add User Story 2 → Execute + summary works → Deploy/Demo (full MVP!)
4. Add User Story 3 → Tooltip discoverability → Deploy/Demo
5. Add User Story 4 → Error handling → Deploy/Demo
6. Add User Story 5 → Permission verification → Deploy/Demo
7. Add User Story 6 → Audit trail → Deploy/Demo
8. Polish → Verification + validation → Final release

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 → User Story 2 (sequential, same files)
   - Developer B: Can prep US3/US5 logic once US1 merges
   - Developer C: Can prep US6 once US2 merges
3. Stories complete and integrate independently

---

## Summary

- **Total tasks**: 31
- **Phase 1 (Setup)**: 3 tasks
- **Phase 2 (Foundational)**: 7 tasks
- **Phase 3 (US1 — Review & Confirm)**: 4 tasks
- **Phase 4 (US2 — Execute Clean-Up)**: 4 tasks
- **Phase 5 (US3 — Discover Feature)**: 1 task
- **Phase 6 (US4 — Error Handling)**: 3 tasks
- **Phase 7 (US5 — Permission Verification)**: 2 tasks
- **Phase 8 (US6 — Audit Trail)**: 3 tasks
- **Phase 9 (Polish)**: 4 tasks
- **Parallel opportunities**: 5 identified (Setup, Foundational, US1, US3/US5, Polish)
- **Independent test criteria**: Each user story has a clear independent test defined
- **Suggested MVP scope**: User Stories 1 + 2 (Preflight + Execute — Phases 1–4, 18 tasks)
- **Format validation**: ✅ All 31 tasks follow checklist format (checkbox, ID, labels, file paths)

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Backend follows existing FastAPI + aiosqlite + Pydantic v2 patterns
- Frontend follows existing React 18 + React Query 5 + TailwindCSS patterns
- No test tasks included (tests not explicitly requested in specification)
- Reuses existing GitHubProjectsService for all GitHub API calls (R1, R2, R8)
- Sequential deletion with 200ms delay respects GitHub secondary rate limits (R4)
- Audit trail stored in SQLite cleanup_audit_logs table (R6)
