# Tasks: Preserve Full User-Provided GitHub Issue Description Without Truncation

**Input**: Design documents from `/specs/014-preserve-issue-description/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Explicitly required by specification (FR-009, SC-002, SC-005). Boundary tests mandated at 256, 1,024, 4,096, 32,768, and 65,536 characters.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- Tests: `backend/tests/unit/`, `frontend/src/test/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add the shared constant that all subsequent phases depend on

- [x] T001 Create `GITHUB_ISSUE_BODY_MAX_LENGTH = 65_536` constant in backend/src/constants.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Fix off-by-one Pydantic model constraints that MUST be corrected before any user story validation can succeed

**⚠️ CRITICAL**: No user story work can begin until these max_length fixes are in place

- [x] T002 Fix `AITaskProposal.proposed_description` max_length from 65535 to 65536 in backend/src/models/recommendation.py
- [x] T003 Fix `ProposalConfirmRequest.edited_description` max_length from 65535 to 65536 in backend/src/models/recommendation.py

**Checkpoint**: Foundation ready — Pydantic models now accept the full GitHub API limit. User story implementation can begin.

---

## Phase 3: User Story 1 — Full Description Preserved on Issue Creation (Priority: P1) 🎯 MVP

**Goal**: Ensure the complete, unmodified user-provided issue description is passed to the GitHub Issues API `body` field, character-for-character, through both the workflow recommendation and task proposal pipelines.

**Independent Test**: Submit a multi-thousand-character description through the chat-to-issue flow and verify the created GitHub Issue body matches the input exactly.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T004 [P] [US1] Add test that `AITaskProposal` accepts a 65,536-character `proposed_description` in backend/tests/unit/test_recommendation_models.py (new file)
- [x] T005 [US1] Add test that `ProposalConfirmRequest` accepts a 65,536-character `edited_description` in backend/tests/unit/test_recommendation_models.py (same file as T004)
- [x] T006 [P] [US1] Add test that `confirm_proposal()` passes the full `final_description` to `create_issue(body=...)` unchanged in backend/tests/unit/test_api_chat.py
- [x] T007 [P] [US1] Add test that `confirm_recommendation()` via `format_issue_body()` passes the full assembled body to `create_issue(body=...)` unchanged in backend/tests/unit/test_api_workflow.py

### Implementation for User Story 1

- [x] T008 [US1] Verify `format_issue_body()` in backend/src/services/workflow_orchestrator/orchestrator.py assembles full body without truncation — add inline comment confirming no truncation
- [x] T009 [US1] Verify `confirm_proposal()` in backend/src/api/chat.py passes `final_description` directly to `create_issue(body=...)` without modification — add inline comment confirming no truncation

**Checkpoint**: User Story 1 complete — descriptions up to 65,536 characters are preserved verbatim through both creation pipelines.

---

## Phase 4: User Story 2 — No Silent Truncation at Any Processing Stage (Priority: P1)

**Goal**: Verify and prove that no stage in the processing pipeline (chat handling, state storage, prompt construction, API payload building) silently shortens, summarizes, or truncates the user-provided description.

**Independent Test**: Submit descriptions at known truncation boundaries (256, 1,024, 4,096, 32,768, 65,536 characters) and assert that the full text is preserved at each pipeline stage.

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T010 [P] [US2] Add parametrized boundary-length tests (256, 1024, 4096, 32768, 65536 chars) for proposal path in backend/tests/unit/test_api_chat.py
- [x] T011 [P] [US2] Add parametrized boundary-length tests (256, 1024, 4096, 32768, 65536 chars) for workflow recommendation path in backend/tests/unit/test_api_workflow.py
- [x] T012 [P] [US2] Add test that `AITaskProposal` rejects descriptions exceeding 65,536 characters (Pydantic validation error) in backend/tests/unit/test_recommendation_models.py

### Implementation for User Story 2

- [x] T013 [US2] Audit `generate_issue_recommendation()` in backend/src/services/ai_agent.py — confirm description fields are not truncated (only title is truncated to 256 chars per research.md)
- [x] T014 [US2] Audit Signal chat pipeline body construction in backend/src/services/signal_chat.py — confirm `body_parts` assembly uses full-length fields, not truncated previews

**Checkpoint**: User Stories 1 AND 2 complete — proven via boundary tests that no truncation occurs at any stage for descriptions up to 65,536 characters.

---

## Phase 5: User Story 3 — User Notification on API Length Limit Exceeded (Priority: P2)

**Goal**: When the assembled issue body exceeds the GitHub API's 65,536-character limit, return an explicit HTTP 422 error with a clear message — never silently truncate.

**Independent Test**: Submit a description that results in a body exceeding 65,536 characters and verify the user receives a 422 error with the current length and the limit.

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T015 [P] [US3] Add test that `create_issue_from_recommendation()` raises `ValidationError`(422) when assembled body exceeds 65,536 chars in `backend/tests/unit/test_workflow_orchestrator.py`
- [x] T016 [P] [US3] Add test that `confirm_proposal()` returns HTTP 422 when description exceeds 65,536 chars in `backend/tests/unit/test_api_chat.py`
- [x] T017 [P] [US3] Add test that body at exactly 65,536 chars succeeds (boundary pass) in `backend/tests/unit/test_api_workflow.py`
- [x] T018 [P] [US3] Add test that body at exactly 65,537 chars fails (boundary fail) in `backend/tests/unit/test_api_chat.py`

### Implementation for User Story 3

- [x] T019 [US3] Add body length validation in `create_issue_from_recommendation()` in backend/src/services/workflow_orchestrator/orchestrator.py — raise AppException(422) if `len(body) > GITHUB_ISSUE_BODY_MAX_LENGTH`
- [x] T020 [US3] Add body length validation in `confirm_proposal()` in backend/src/api/chat.py — raise AppException(422) if `len(body) > GITHUB_ISSUE_BODY_MAX_LENGTH`

**Checkpoint**: User Story 3 complete — exceeding the API limit produces an explicit 422 error. Users are never surprised by silent truncation.

---

## Phase 6: User Story 4 — Formatting Preservation Across All Markdown Elements (Priority: P2)

**Goal**: Ensure all markdown formatting elements (headers, lists, code blocks, blockquotes, tables, links, bold, italic, horizontal rules) are preserved exactly as written through the issue creation pipeline.

**Independent Test**: Submit a description containing every supported markdown element and verify each is present and correctly formatted in the created GitHub Issue body.

### Tests for User Story 4

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T021 [P] [US4] Add test with rich markdown description (headers, lists, fenced code blocks, blockquotes, tables, bold, italic, links) for proposal path in backend/tests/unit/test_api_chat.py
- [x] T022 [P] [US4] Add test with rich markdown description for workflow recommendation path in backend/tests/unit/test_api_workflow.py
- [x] T023 [P] [US4] Add test with Unicode, emoji, and special characters in description in backend/tests/unit/test_recommendation_models.py

### Implementation for User Story 4

- [x] T024 [US4] Verify `format_issue_body()` does not escape or modify markdown characters in backend/src/services/workflow_orchestrator/orchestrator.py — confirm f-string/template assembly preserves raw markdown

**Checkpoint**: All user stories complete — descriptions of any length and formatting are preserved verbatim, with explicit errors for exceeding the API limit.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and documentation

- [x] T025 [P] Update quickstart.md verification checklist in specs/014-preserve-issue-description/quickstart.md
- [x] T026 Run full backend test suite (`cd backend && pytest -v`) to confirm no regressions
- [x] T027 Run full frontend test suite (`cd frontend && npm test`) to confirm no regressions
- [x] T028 Run quickstart.md validation checklist end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (constant must exist) — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Phase 2 (max_length fixes)
- **User Story 2 (Phase 4)**: Depends on Phase 2 (max_length fixes) — can run in parallel with US1
- **User Story 3 (Phase 5)**: Depends on Phase 1 (constant) and Phase 2 (model fixes)
- **User Story 4 (Phase 6)**: Depends on Phase 2 (model fixes) — can run in parallel with US1/US2/US3
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) — Independently testable; complements US1 with boundary tests
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) — Adds validation layer; independent of US1/US2 test results
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) — Independently testable; no implementation changes expected

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Model changes before service changes
- Service changes before API endpoint changes
- Core implementation before cross-story integration

### Parallel Opportunities

- T002, T003 modify different fields in the same file — execute sequentially or coordinate edits
- T004, T006, T007 can all run in parallel (different test files); T005 depends on T004 (same file)
- T010, T011, T012 can all run in parallel (different test files/sections)
- T015, T016, T017, T018 can all run in parallel (different test files/sections)
- T021, T022, T023 can all run in parallel (different test files/sections)
- US1, US2, US3, US4 can all start in parallel after Phase 2 is complete

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Test AITaskProposal accepts 65,536-char description in backend/tests/unit/test_recommendation_models.py"
Task: "Test ProposalConfirmRequest accepts 65,536-char description in backend/tests/unit/test_recommendation_models.py"
Task: "Test confirm_proposal passes full description in backend/tests/unit/test_api_chat.py"
Task: "Test confirm_recommendation passes full body in backend/tests/unit/test_api_workflow.py"
```

## Parallel Example: User Story 3

```bash
# Launch all boundary tests for User Story 3 together:
Task: "Test 422 on oversized body for workflow path in backend/tests/unit/test_api_workflow.py"
Task: "Test 422 on oversized body for proposal path in backend/tests/unit/test_api_chat.py"
Task: "Test 65,536-char body succeeds in backend/tests/unit/test_api_workflow.py"
Task: "Test 65,537-char body fails in backend/tests/unit/test_api_chat.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (add constant)
2. Complete Phase 2: Foundational (fix max_length off-by-one)
3. Complete Phase 3: User Story 1 (verify full description passthrough + tests)
4. **STOP and VALIDATE**: Run boundary tests to confirm descriptions up to 65,536 chars pass through unchanged
5. Deploy/demo if ready — core value proposition delivered

### Incremental Delivery

1. Setup + Foundational → Foundation ready (T001–T003)
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!) (T004–T009)
3. Add User Story 2 → Boundary tests prove no truncation at any stage (T010–T014)
4. Add User Story 3 → Explicit 422 errors for oversized bodies (T015–T020)
5. Add User Story 4 → Markdown fidelity proven via tests (T021–T024)
6. Polish → Full regression validation (T025–T028)

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (T001–T003)
2. Once Foundational is done:
   - Developer A: User Story 1 (T004–T009)
   - Developer B: User Story 2 (T010–T014)
   - Developer C: User Story 3 (T015–T020)
   - Developer D: User Story 4 (T021–T024)
3. Stories complete and integrate independently
4. Polish phase runs after all stories merge

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Tests MUST fail before implementation — TDD approach per spec requirements
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- The research.md audit confirmed no truncation exists in the current API body path — changes are primarily off-by-one fixes and adding pre-validation
- Display-only truncation (chat bubble previews) is intentional and out of scope — only API body truncation matters
