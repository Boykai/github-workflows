# Tasks: Projects Page — Upload GitHub Parent Issue Description & Select Agent Pipeline Config

**Input**: Design documents from `/specs/032-issue-upload-pipeline-config/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/ (api.md, components.md), quickstart.md

**Tests**: Not explicitly requested in the feature specification. Existing frontend validation commands must continue to pass. No new test tasks are included.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently. User Story 1 is the MVP. User Story 3 is also P1 and follows immediately because it is tightly coupled to the core launch form.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `frontend/src/` (React/TypeScript), `backend/src/` (Python/FastAPI)
- Frontend board components: `frontend/src/components/board/`
- Frontend pages: `frontend/src/pages/`
- Frontend services: `frontend/src/services/`
- Frontend shared types: `frontend/src/types/`
- Backend API contracts: `backend/src/api/`
- Backend models: `backend/src/models/`

---

## Phase 1: Setup

**Purpose**: Establish the launch-panel module and confirm the shared contracts this feature reuses.

- [x] T001 Create the launch-form scaffold, local state, and helper constants in `frontend/src/components/board/ProjectIssueLaunchPanel.tsx`
- [x] T002 [P] Verify `PipelineIssueLaunchRequest`, `PipelineConfigSummary`, and `WorkflowResult` exports used by the panel in `frontend/src/types/index.ts`
- [x] T003 [P] Confirm the existing list/seed/launch contract surface in `frontend/src/services/api.ts`, `backend/src/api/pipelines.py`, and `backend/src/models/pipeline.py` will be reused without adding new endpoints

**Checkpoint**: The implementation surface is defined and all shared contracts required by the launch flow are confirmed.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Wire the Projects page data flow that every user story depends on.

**⚠️ CRITICAL**: No user story work should begin until the page passes the launch panel the selected project context and pipeline query state.

- [x] T004 Render `ProjectIssueLaunchPanel` from `frontend/src/pages/ProjectsPage.tsx` with `projectId`, `projectName`, `onLaunched`, and pipeline query props
- [x] T005 Reconcile pipeline loading, refetch, and board-refresh invalidation flows in `frontend/src/pages/ProjectsPage.tsx` so the launch panel receives reactive pipeline data and can refresh the board after success

**Checkpoint**: The Projects page can host the new launch panel and provide all pipeline/query callbacks needed by later stories.

---

## Phase 3: User Story 1 — Paste a GitHub Parent Issue Description and Select Pipeline Config (Priority: P1) 🎯 MVP

**Goal**: Let a user paste an existing GitHub parent issue description, select a saved Agent Pipeline Config, and launch the workflow in one action.

**Independent Test**: On the Projects page, paste a sample issue description, choose an available pipeline config, submit, and verify the request is sent through `pipelinesApi.launch()` and a success state or created issue link is shown.

### Implementation for User Story 1

- [x] T006 [US1] Build the issue-description `<textarea>` and native pipeline `<select>` controls, including labels and project-context copy, in `frontend/src/components/board/ProjectIssueLaunchPanel.tsx`
- [x] T007 [US1] Wire the launch submission mutation in `frontend/src/components/board/ProjectIssueLaunchPanel.tsx` to `pipelinesApi.launch(projectId, { issue_description, pipeline_id })`
- [x] T008 [US1] Add the inline success confirmation state, created-issue link, and reset action in `frontend/src/components/board/ProjectIssueLaunchPanel.tsx`

**Checkpoint**: A user can complete the core launch workflow from pasted text and a selected pipeline config. This is the MVP.

---

## Phase 4: User Story 3 — Inline Validation Prevents Incomplete Submissions (Priority: P1)

**Goal**: Prevent incomplete or oversized submissions and preserve user input when validation or launch errors occur.

**Independent Test**: Attempt to submit with both fields empty, with only the description filled, with only the pipeline selected, and with an oversized description; verify field-level errors appear inline, the submit request is blocked, and previously entered values remain intact.

### Implementation for User Story 3

- [x] T009 [US3] Add trimmed required-field and max-length validation for issue description and pipeline selection in `frontend/src/components/board/ProjectIssueLaunchPanel.tsx`
- [x] T010 [US3] Preserve form values, clear field-specific errors on change, disable duplicate submits while pending, and surface submission failures inline in `frontend/src/components/board/ProjectIssueLaunchPanel.tsx`

**Checkpoint**: The launch form blocks invalid submissions with inline feedback and retains user-entered data on failure.

---

## Phase 5: User Story 2 — Upload an Issue Description from a File (Priority: P2)

**Goal**: Allow users to import a `.md` or `.txt` file into the same issue-description form before launching.

**Independent Test**: Upload a valid `.md` or `.txt` file and confirm the textarea is populated and editable; upload an unsupported file type and confirm the existing textarea content is preserved while an inline file error is shown.

### Implementation for User Story 2

- [x] T011 [US2] Add the hidden file input, upload trigger button, and uploaded-file name display in `frontend/src/components/board/ProjectIssueLaunchPanel.tsx`
- [x] T012 [US2] Implement `isAcceptedIssueFile()` and file-reading logic in `frontend/src/components/board/ProjectIssueLaunchPanel.tsx` to accept `.md`/`.txt`, reject unsupported types, enforce the description size limit, and populate the textarea without losing prior text on failure

**Checkpoint**: Users can bootstrap the launch form from an uploaded issue file instead of manual paste.

---

## Phase 6: User Story 4 — Dynamic Pipeline Config Selection (Priority: P2)

**Goal**: Keep the pipeline selector current and resilient when configs are loading, missing, or fail to load.

**Independent Test**: Load the Projects page and verify the selector lists current configs; verify an informative empty state appears when no configs exist; simulate a fetch failure and verify a retry path is shown without a full page reload.

### Implementation for User Story 4

- [x] T013 [P] [US4] Pass the saved pipeline list, loading state, error state, and retry callback from `frontend/src/pages/ProjectsPage.tsx` into `frontend/src/components/board/ProjectIssueLaunchPanel.tsx`
- [x] T014 [US4] Render loading, empty, and fetch-error states with retry handling for the pipeline selector in `frontend/src/components/board/ProjectIssueLaunchPanel.tsx`

**Checkpoint**: The pipeline selector stays reactive and gracefully handles loading, empty, and error conditions.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final alignment, manual verification, and existing-command validation across the touched surface.

- [x] T015 [P] Run the manual launch, validation, upload, and selector scenarios from `specs/032-issue-upload-pipeline-config/quickstart.md` against `frontend/src/pages/ProjectsPage.tsx` and `frontend/src/components/board/ProjectIssueLaunchPanel.tsx`
- [x] T016 [P] Run `npm run lint`, `npm run type-check`, and `npm run test` from `frontend/package.json` after the UI changes affecting `frontend/src/pages/ProjectsPage.tsx` and `frontend/src/components/board/ProjectIssueLaunchPanel.tsx`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3–6)**: Depend on Foundational completion
  - **US1 (P1)** delivers the MVP and should be completed first
  - **US3 (P1)** should follow US1 because it hardens the same form surface
  - **US2 (P2)** extends the same panel with optional file-upload convenience
  - **US4 (P2)** can start after Foundational because it primarily wires query state and selector states
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational — no dependency on other stories
- **User Story 3 (P1)**: Depends on US1 — validation/error handling hardens the launch form introduced in US1
- **User Story 2 (P2)**: Depends on US1 — file upload extends the same textarea-based launch form
- **User Story 4 (P2)**: Can start after Foundational — depends on the page/query plumbing rather than on file upload

### Within Each User Story

- Shared contracts and page plumbing before UI integration
- Core form controls before mutation wiring
- Mutation wiring before success-state polish
- Validation and error handling before final verification
- Complete each story before moving to later polish tasks

### Parallel Opportunities

- **Phase 1**: T002 and T003 can run in parallel after T001 defines the panel module direction
- **Phase 6**: T013 and T014 can run in parallel once the panel props contract is agreed
- **Phase 7**: T015 and T016 can run in parallel after implementation is complete

---

## Parallel Example: After Foundational Phase Completes

```text
# Track A — Core launch flow
Task T006: Build textarea and select controls in frontend/src/components/board/ProjectIssueLaunchPanel.tsx
Task T007: Wire launch mutation in frontend/src/components/board/ProjectIssueLaunchPanel.tsx
Task T008: Add success confirmation state in frontend/src/components/board/ProjectIssueLaunchPanel.tsx

# Track B — Dynamic selector states
Task T013: Pass pipeline query state from frontend/src/pages/ProjectsPage.tsx
Task T014: Render loading/empty/error selector states in frontend/src/components/board/ProjectIssueLaunchPanel.tsx
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Paste text, select a pipeline, launch, and confirm success feedback
5. Demo/deploy the MVP if ready

### Incremental Delivery

1. Complete Setup + Foundational → launch panel can mount with live project/pipeline data
2. Add User Story 1 → validate the core launch flow (**MVP**)
3. Add User Story 3 → validate inline validation and preserved state
4. Add User Story 2 → validate file-upload convenience
5. Add User Story 4 → validate reactive selector loading/empty/error states
6. Finish with Polish → manual scenarios + existing frontend validation commands

### Parallel Team Strategy

With multiple developers:

1. Complete Setup + Foundational together
2. Then split by surface:
   - Developer A: US1 + US3 in `frontend/src/components/board/ProjectIssueLaunchPanel.tsx`
   - Developer B: US4 query plumbing in `frontend/src/pages/ProjectsPage.tsx`
   - Developer C: Polish/verification once feature work stabilizes

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 16 |
| **Setup tasks** | 3 (T001–T003) |
| **Foundational tasks** | 2 (T004–T005) |
| **US1 tasks** | 3 (T006–T008) |
| **US3 tasks** | 2 (T009–T010) |
| **US2 tasks** | 2 (T011–T012) |
| **US4 tasks** | 2 (T013–T014) |
| **Polish tasks** | 2 (T015–T016) |
| **Parallel opportunities** | 5 tasks marked [P] across setup, dynamic selector wiring, and final verification |
| **MVP scope** | Phases 1–3 (T001–T008) |
| **Primary files** | `frontend/src/pages/ProjectsPage.tsx`, `frontend/src/components/board/ProjectIssueLaunchPanel.tsx`, `frontend/src/services/api.ts`, `frontend/src/types/index.ts` |
| **Backend reuse points** | `backend/src/api/pipelines.py`, `backend/src/models/pipeline.py` |

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] labels map user-story work to `spec.md` priorities for traceability
- Tests are NOT included as implementation tasks because the specification did not request TDD or new automated coverage
- This feature should reuse the existing `POST /api/v1/pipelines/{project_id}/launch` endpoint and existing pipeline list/seed endpoints instead of adding backend routes
- Inline validation must preserve the entered issue description and selected pipeline when launch or validation fails
- File upload support is limited to client-side `.md` and `.txt` intake per research.md and contracts/components.md
