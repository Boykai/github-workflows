# Tasks: Attach User Chat Attachments to GitHub Parent Issue

**Input**: Design documents from `/specs/037-chat-attachment-github-issue/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Included for backend formatter, persistence, and confirmation flows because the plan explicitly calls for regression coverage around attachment serialization and GitHub issue body generation. Existing frontend upload/status coverage should be verified and extended only if gaps remain.

**Organization**: Tasks are grouped by user story so each increment can be implemented and validated independently. The existing upload UI already covers much of the chat-side experience, so the task list emphasizes the missing persistence, formatting, confirmation, and validation work while still reserving targeted verification tasks for the existing frontend paths.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g. US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- **Backend tests**: `backend/tests/unit/`
- **Feature docs**: `specs/037-chat-attachment-github-issue/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No new scaffolding or dependencies are required. The existing chat upload pipeline, workflow confirmation endpoints, and frontend file-preview UI already exist, so implementation can start directly with shared backend attachment infrastructure.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add the shared schema, persistence, and formatting pieces that every user story depends on.

**⚠️ CRITICAL**: No user story work should begin until attachment data can be stored and formatted consistently.

- [ ] T001 Create migration `backend/src/migrations/022_chat_file_urls.sql` to add `file_urls` storage for `chat_proposals` and `chat_recommendations`
- [ ] T002 [P] Add `file_urls` fields, defaults, and schema examples to `backend/src/models/recommendation.py`
- [ ] T003 [P] Update SQLite proposal/recommendation save-load helpers in `backend/src/services/chat_store.py` to persist and hydrate `file_urls`
- [ ] T004 Create shared markdown attachment formatter `backend/src/utils/attachment_formatter.py` with image-vs-link classification and chat-session reference output

**Checkpoint**: Attachment URLs can now survive persistence boundaries and be rendered into a reusable GitHub markdown section.

---

## Phase 3: User Story 1 — Single File Attachment from Chat to GitHub Issue (Priority: P1) 🎯 MVP

**Goal**: Ensure a single uploaded chat file is propagated into the proposal/recommendation flow and attached to the resulting GitHub issue with visible confirmation.

**Independent Test**: Upload one valid file in a chat linked to a GitHub issue, confirm the proposal or recommendation, and verify the resulting GitHub issue body includes the attachment with the expected issue reference and chat-session context.

### Tests for User Story 1

- [ ] T005 [P] [US1] Add formatter unit tests for empty input, one image, one document, and chat-session reference output in `backend/tests/unit/test_attachment_formatter.py`
- [ ] T006 [P] [US1] Extend proposal/recommendation model tests for default and serialized `file_urls` behavior in `backend/tests/unit/test_recommendation_models.py`

### Implementation for User Story 1

- [ ] T007 [US1] Propagate `file_urls` through feature-request and task-proposal creation paths in `backend/src/api/chat.py`
- [ ] T008 [US1] Append formatted attachments to confirmed proposal issue bodies and re-run the GitHub body-length validation after attachment expansion in `backend/src/api/chat.py`
- [ ] T009 [US1] Append formatted attachments when the workflow orchestrator builds recommendation issue bodies in `backend/src/services/workflow_orchestrator/orchestrator.py`
- [ ] T010 [US1] Preserve attachment-aware confirmation, error handling, and issue creation flow in `backend/src/api/workflow.py`

**Checkpoint**: Single-file proposal and recommendation confirmations create GitHub issues whose bodies contain the uploaded file reference and chat provenance.

---

## Phase 4: User Story 2 — Batch Multi-File Attachment (Priority: P1)

**Goal**: Support multiple uploaded files in one chat interaction so every successfully uploaded file appears on the resulting GitHub issue in deterministic order.

**Independent Test**: Select three files, upload them in one chat interaction, confirm the issue flow, and verify each successful file appears in the issue body while preserving ordering and allowing non-failing files to complete.

### Tests for User Story 2

- [ ] T011 [P] [US2] Add multi-file formatter regression coverage for ordering and mixed file types in `backend/tests/unit/test_attachment_formatter.py`
- [ ] T012 [P] [US2] Add proposal confirmation tests that assert multiple `file_urls` are embedded in the created issue body in `backend/tests/unit/test_api_chat.py`
- [ ] T013 [P] [US2] Add recommendation confirmation tests that assert multiple `file_urls` flow through workflow execution in `backend/tests/unit/test_api_workflow.py`

### Implementation for User Story 2

- [ ] T014 [US2] Ensure batched `file_urls` round-trip through proposal/recommendation persistence in `backend/src/services/chat_store.py`
- [ ] T015 [US2] Verify and adjust multi-file handoff so `frontend/src/hooks/useFileUpload.ts` and `frontend/src/components/chat/ChatInterface.tsx` submit every successful upload URL in a single chat action

**Checkpoint**: Multi-file uploads remain independently tracked in chat and all successful files are attached to the GitHub issue body together.

---

## Phase 5: User Story 3 — Attachment Failure Handling and Retry (Priority: P2)

**Goal**: Tighten validation and failure behavior so empty files, unavailable issues, and upload/confirm failures produce actionable retryable states without breaking successful files.

**Independent Test**: Attempt to upload a zero-byte file and confirm it is rejected immediately, then simulate an unavailable issue or confirmation failure and verify the user can retry without losing other successful attachments.

### Tests for User Story 3

- [ ] T016 [P] [US3] Add upload endpoint regression tests for zero-byte files and structured attachment error responses in `backend/tests/unit/test_api_chat.py`

### Implementation for User Story 3

- [ ] T017 [US3] Reject zero-byte uploads with an `empty_file` error response in `backend/src/api/chat.py`
- [ ] T018 [US3] Preserve retryable confirmation behavior and unavailable-issue error reporting in `backend/src/api/chat.py` and `backend/src/api/workflow.py`
- [ ] T019 [US3] Verify and adjust failed-file messaging and retry affordances in `frontend/src/hooks/useFileUpload.ts` and `frontend/src/components/chat/FilePreviewChips.tsx`

**Checkpoint**: Invalid files fail early, confirmation failures stay recoverable, and the UI continues to show per-file retryable error states.

---

## Phase 6: User Story 4 — Attachment Metadata Display (Priority: P3)

**Goal**: Preserve rich attachment metadata in both the chat UI and the GitHub issue so users can recognize filenames, file types, sizes, and chat provenance.

**Independent Test**: Upload image and document files, verify the chat chips show filename/icon/size, then confirm the issue and verify the attachment markdown uses readable filenames plus the chat-session reference.

### Tests for User Story 4

- [ ] T020 [P] [US4] Add formatter regression tests for filename prefix stripping and metadata-friendly markdown output in `backend/tests/unit/test_attachment_formatter.py`

### Implementation for User Story 4

- [ ] T021 [US4] Render human-readable filenames and chat-session reference text in `backend/src/utils/attachment_formatter.py`
- [ ] T022 [US4] Verify and adjust filename, file-type icon, size, and attached-state presentation in `frontend/src/components/chat/FilePreviewChips.tsx` and `frontend/src/components/chat/ChatInterface.tsx`

**Checkpoint**: Attachment metadata stays readable in both chat and GitHub, completing the end-user experience.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final verification, migration sanity checks, and quickstart validation across all stories.

- [ ] T023 Run targeted backend unit suites in `backend/tests/unit/test_attachment_formatter.py`, `backend/tests/unit/test_recommendation_models.py`, `backend/tests/unit/test_api_chat.py`, and `backend/tests/unit/test_api_workflow.py`
- [ ] T024 [P] Run backend lint and migration validation for `backend/src/migrations/022_chat_file_urls.sql` via `cd backend && python -m ruff check src/`
- [ ] T025 [P] Run the single-file, batch, failure, and metadata scenarios documented in `specs/037-chat-attachment-github-issue/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No tasks — proceed directly to foundational work
- **Foundational (Phase 2)**: No dependencies — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational — establishes the MVP single-file attach path
- **User Story 2 (Phase 4)**: Depends on Foundational and benefits from US1’s shared formatter/confirmation wiring
- **User Story 3 (Phase 5)**: Depends on Foundational and should be layered after the main upload/confirm path exists
- **User Story 4 (Phase 6)**: Depends on Foundational and should land after attachment formatting/output is stable
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start immediately after Phase 2 — this is the MVP
- **User Story 2 (P1)**: Should start after US1’s formatter and confirmation wiring land, though its tests can be prepared in parallel
- **User Story 3 (P2)**: Can begin after US1, because it hardens the same upload/confirmation code paths
- **User Story 4 (P3)**: Can begin after US1/US2 stabilize, because it depends on final attachment formatting and chat metadata presentation

### Within Each User Story

- Tests must be written before implementation when included
- Shared storage/model changes before endpoint updates
- Endpoint updates before frontend verification/adjustment
- Story-specific validation before polish

### Parallel Opportunities

- T002 and T003 can run in parallel (model vs. persistence layer)
- T005 and T006 can run in parallel (different backend test files)
- T011, T012, and T013 can run in parallel (independent batch regressions)
- T016 can run in parallel with T019 after the main upload flow exists (backend validation vs. frontend failure UX)
- T023, T024, and T025 can be split across team members during final validation

---

## Parallel Example: Foundational Phase

```text
# After T001 starts the migration work, these can run in parallel:
Task T002: "Add file_urls fields to backend/src/models/recommendation.py"
Task T003: "Update attachment persistence in backend/src/services/chat_store.py"
```

## Parallel Example: User Story 2

```text
# Prepare the batch-flow regressions together:
Task T011: "Add multi-file formatter tests in backend/tests/unit/test_attachment_formatter.py"
Task T012: "Add proposal batch confirm tests in backend/tests/unit/test_api_chat.py"
Task T013: "Add recommendation batch confirm tests in backend/tests/unit/test_api_workflow.py"
```

## Parallel Example: Final Validation

```text
# Final verification can be divided by toolchain:
Task T023: "Run targeted backend unit suites"
Task T024: "Run backend lint and migration validation"
Task T025: "Execute quickstart single-file, batch, failure, and metadata scenarios"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 2: Foundational storage + formatter work
2. Complete Phase 3: User Story 1 single-file propagation and confirmation flow
3. **STOP and VALIDATE**: Confirm one uploaded file appears in the resulting GitHub issue body
4. Demo/deploy if needed — this satisfies the core issue request

### Incremental Delivery

1. Complete Foundational phase → attachment infrastructure ready
2. Add User Story 1 → validate single-file attachment flow → MVP
3. Add User Story 2 → validate batch attachments and mixed file types
4. Add User Story 3 → validate zero-byte rejection and retryable failures
5. Add User Story 4 → validate metadata fidelity in chat and GitHub output
6. Finish with Polish phase validation

### Parallel Team Strategy

With multiple developers:

1. Complete Phase 2 together
2. Then split:
   - Developer A: US1 single-file propagation + confirmation path
   - Developer B: US2 batch regressions and persistence hardening
   - Developer C: US3/US4 frontend validation and failure/metadata adjustments once US1 is stable
3. Rejoin for Phase 7 verification

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 25 |
| **Phase 2 (Foundational)** | 4 tasks |
| **US1 — Single-file attach** | 6 tasks |
| **US2 — Batch attach** | 5 tasks |
| **US3 — Failure handling** | 4 tasks |
| **US4 — Metadata display** | 3 tasks |
| **Phase 7 (Polish)** | 3 tasks |
| **Parallel opportunities** | 5 task groups identified |
| **Suggested MVP scope** | Phase 2 + Phase 3 (US1) |

---

## Notes

- All tasks follow the required checklist format: checkbox, task ID, optional `[P]`, required story label for story phases, and explicit file paths
- Existing frontend upload and chip UI should only be changed when verification reveals a gap against the spec
- The most critical shared risks are attachment-body length growth, persistence of `file_urls`, and keeping proposal/recommendation confirmation flows aligned
- Stop after each phase checkpoint and validate the story independently before expanding scope
