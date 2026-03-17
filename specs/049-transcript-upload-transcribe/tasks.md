# Tasks: Transcript Upload & Transcribe Agent

**Input**: Design documents from `/specs/049-transcript-upload-transcribe/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Included — tests are explicitly requested in the feature specification and are organized throughout implementation phases.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `solune/backend/src/` (Python/FastAPI), `solune/frontend/src/` (TypeScript/React)
- **Backend tests**: `solune/backend/tests/`
- **Frontend tests**: colocated `*.test.tsx` files

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add new file type support across backend and frontend validation layers

- [x] T001 Add `.vtt` and `.srt` to `ALLOWED_DOC_TYPES` set in `solune/backend/src/api/chat.py`
- [x] T002 [P] Add `'.vtt'` and `'.srt'` to `FILE_VALIDATION.allowedDocTypes` array in `solune/frontend/src/types/index.ts`
- [x] T003 [P] Update file input `accept` attribute to include `.vtt,.srt` in `solune/frontend/src/components/chat/ChatToolbar.tsx`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create the transcript detection utility and Transcribe agent prompt — core infrastructure that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Create `TranscriptDetectionResult` dataclass with `is_transcript`, `format`, and `confidence` fields in `solune/backend/src/services/transcript_detector.py`
- [x] T005 Implement extension-based detection (`.vtt` → always transcript with confidence 1.0, `.srt` → always transcript with confidence 1.0) in `solune/backend/src/services/transcript_detector.py`
- [x] T006 Implement content-based regex patterns (speaker labels `^\s*(?:\[?\w[\w\s]{0,30}\]?\s*:\s)`, timestamps `\d{1,2}:\d{2}:\d{2}(?:[.,]\d{1,3})?`, VTT header `^WEBVTT\b`, SRT arrows `\d+:\d{2}:\d{2}[.,]?\d*\s*-->\s*\d+:\d{2}:\d{2}`) in `solune/backend/src/services/transcript_detector.py`
- [x] T007 Implement `detect_transcript(filename, content)` function with priority-ordered checks (extension → VTT markers → SRT markers → speaker labels ≥3 → timestamps ≥5 → not transcript) in `solune/backend/src/services/transcript_detector.py`
- [x] T008 [P] Create `TRANSCRIPT_ANALYSIS_SYSTEM_PROMPT` constant following `issue_generation.py` pattern (role definition, task description, JSON output schema matching `IssueRecommendation` fields) in `solune/backend/src/prompts/transcript_analysis.py`
- [x] T009 Implement `create_transcript_analysis_prompt(transcript_content, project_name, metadata_context)` factory function returning `list[dict]` with system and user messages in `solune/backend/src/prompts/transcript_analysis.py`
- [x] T010 Add `analyze_transcript(self, transcript_content, project_name, session_id, github_token, metadata_context=None)` async method to `AIAgentService` that calls `create_transcript_analysis_prompt()` → `self._call_completion(temperature=0.7, max_tokens=8000)` → `self._parse_issue_recommendation_response()` and sets `original_input` to `transcript_content[:500]` in `solune/backend/src/services/ai_agent.py`

**Checkpoint**: Foundation ready — transcript detection utility, Transcribe agent prompt, and AI service method are all available. User story implementation can now begin.

---

## Phase 3: User Story 1 — Upload Transcript in Chat to Generate Requirements (Priority: P1) 🎯 MVP

**Goal**: A user uploads a transcript file in Chat and receives a structured issue recommendation with extracted requirements, which they can confirm to create a GitHub Parent Issue with sub-issues.

**Independent Test**: Upload a `.vtt` or `.srt` transcript file in Chat → `IssueRecommendationPreview` appears with extracted requirements → confirm → parent issue + sub-issues created per pipeline.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T011 [P] [US1] Create test file `solune/backend/tests/test_chat_transcript.py` with test cases: upload VTT transcript → recommendation generated with `action_type=ISSUE_CREATE`; upload SRT transcript → recommendation generated; upload speaker-labeled `.txt` → recommendation generated; mock `AIAgentService` for predictable responses
- [x] T012 [P] [US1] Add test case in `solune/backend/tests/test_chat_transcript.py` for non-transcript file upload → falls through to normal flow (returns `None` from transcript handler)

### Implementation for User Story 1

- [x] T013 [US1] Create `_handle_transcript_upload(chat_request, session, user_message, ai_service)` async handler function in `solune/backend/src/api/chat.py` that checks `file_urls`, reads file content, runs `detect_transcript()`, calls `ai_service.analyze_transcript()` if transcript detected, stores `IssueRecommendation`, and returns `ChatMessage` with `action_type=ISSUE_CREATE` (or `None` if no transcript)
- [x] T014 [US1] Insert `_handle_transcript_upload()` call at Priority 0.5 in `send_message()` dispatch chain (after `_handle_agent_command()`, before `_handle_feature_request()`) in `solune/backend/src/api/chat.py`

**Checkpoint**: At this point, User Story 1 should be fully functional — uploading a transcript in Chat generates an issue recommendation via the existing `IssueRecommendationPreview` → confirm → create parent issue + sub-issues pipeline.

---

## Phase 4: User Story 2 — Upload Transcript via Parent Issue Intake (Priority: P2)

**Goal**: A user uploads a transcript file or pastes transcript content in the Parent Issue Intake panel, and the system uses extracted requirements as the GitHub issue body instead of raw transcript text.

**Independent Test**: Upload a speaker-labeled `.txt` file in Parent Issue Intake → select pipeline → submit → GitHub issue body contains structured requirements extracted from transcript.

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T015 [P] [US2] Add test cases in `solune/backend/tests/test_chat_transcript.py` (or a new file) for pipeline integration: transcript description → `analyze_transcript()` called, generated title and formatted body used; non-transcript description → existing behavior unchanged

### Implementation for User Story 2

- [x] T016 [US2] Add transcript detection at start of `launch_pipeline_issue()` in `solune/backend/src/api/pipelines.py` — call `detect_transcript("inline", issue_description)` before creating GitHub issue
- [x] T017 [US2] If transcript detected in `launch_pipeline_issue()`, call `ai_service.analyze_transcript()` and use generated `title` + formatted requirements body for the GitHub issue, then continue normal pipeline flow in `solune/backend/src/api/pipelines.py`
- [x] T018 [P] [US2] Update `isAcceptedIssueFile()` to accept `.vtt` and `.srt` extensions, add `'.vtt'` and `'.srt'` to `ACCEPTED_FILE_EXTENSIONS`, update file input `accept` attribute, and update error message to mention transcript formats in `solune/frontend/src/components/board/ProjectIssueLaunchPanel.tsx`

**Checkpoint**: At this point, User Story 2 should be fully functional — uploading a transcript in Parent Issue Intake creates a GitHub issue with structured requirements.

---

## Phase 5: User Story 3 — Non-Transcript Files Pass Through Normally (Priority: P2)

**Goal**: Regular `.txt` and `.md` files (plain notes, code snippets, documentation) are not falsely detected as transcripts and continue through existing processing flows unchanged.

**Independent Test**: Upload a plain `.txt` file with regular notes (no speaker labels or timestamps) in both Chat and Parent Issue Intake → existing behavior (feature-request detection, normal chat response) is unchanged.

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T019 [P] [US3] Add test cases in `solune/backend/tests/test_transcript_detector.py` for non-transcript detection: plain prose `.txt` → NOT detected, standard markdown `.md` → NOT detected, empty content → NOT detected, `.txt` with exactly 2 speaker labels (below threshold) → NOT detected
- [x] T020 [P] [US3] Add test cases in `solune/backend/tests/test_chat_transcript.py` for passthrough behavior: non-transcript `.txt` upload in Chat → `_handle_transcript_upload()` returns `None`, falls through to `_handle_feature_request()`

### Implementation for User Story 3

- [x] T021 [US3] Verify and validate that `detect_transcript()` returns `TranscriptDetectionResult(is_transcript=False, format=None, confidence=0.0)` for plain prose, standard markdown, empty content, and below-threshold inputs — add any missing edge-case handling in `solune/backend/src/services/transcript_detector.py`
- [x] T022 [US3] Verify that `_handle_transcript_upload()` returns `None` for non-transcript files, allowing fallthrough to existing handlers in `solune/backend/src/api/chat.py`
- [x] T023 [US3] Verify that `launch_pipeline_issue()` in `solune/backend/src/api/pipelines.py` proceeds with existing behavior when `detect_transcript()` returns `is_transcript=False`

**Checkpoint**: At this point, User Story 3 should be verified — all existing non-transcript workflows remain unchanged.

---

## Phase 6: User Story 4 — Transcript Format Detection Across File Types (Priority: P3)

**Goal**: The system reliably detects transcripts across multiple formats (`.vtt`, `.srt`, speaker-labeled `.txt`, timestamped `.txt`) and does not produce false positives on standard documents.

**Independent Test**: Upload a diverse set of transcript files (`.vtt`, `.srt`, speaker-labeled `.txt`, timestamped `.txt`) and verify each is correctly detected. Upload non-transcript `.txt` and `.md` files and confirm they are not falsely detected.

### Tests for User Story 4

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T024 [P] [US4] Create comprehensive test file `solune/backend/tests/test_transcript_detector.py` with detection cases: `.vtt` extension → detected as `format="vtt"` with confidence 1.0; `.srt` extension → detected as `format="srt"` with confidence 1.0; `.txt` with speaker labels → detected as `format="speaker_labeled"` with confidence 0.8; `.txt` with timestamps → detected as `format="timestamped"` with confidence 0.7; `.txt` with VTT markers → detected as `format="vtt"` with confidence 0.95; `.txt` with SRT arrows → detected as `format="srt"` with confidence 0.95
- [x] T025 [P] [US4] Add edge case tests in `solune/backend/tests/test_transcript_detector.py`: mixed format content (multiple patterns match → highest-priority pattern wins per detection order in T007), malformed VTT/SRT files, empty filename, content with exactly threshold-boundary counts

### Implementation for User Story 4

- [x] T026 [US4] Validate all detection patterns work correctly for diverse real-world transcript formats and edge cases — refine regex patterns if any test cases fail in `solune/backend/src/services/transcript_detector.py`

**Checkpoint**: All transcript detection formats are verified with comprehensive test coverage.

---

## Phase 7: Testing & Verification

**Purpose**: Complete test coverage for all new components

### Backend Tests

- [x] T027 [P] Create prompt construction tests in `solune/backend/tests/test_transcript_analysis_prompt.py`: verify `create_transcript_analysis_prompt()` returns 2-message list with system and user roles; verify system prompt contains JSON schema instructions; verify user message includes project name, date, and transcript content; verify metadata_context is included when provided; follow pattern from existing `test_issue_generation.py`
- [x] T028 [P] Add `analyze_transcript()` integration test in `solune/backend/tests/test_chat_transcript.py`: mock `CompletionProvider` with predictable JSON response → verify `IssueRecommendation` is correctly populated with `original_input` truncated to 500 chars

### Frontend Tests

- [x] T029 [P] Update `useFileUpload` tests (if they exist) to verify `.vtt` and `.srt` are accepted by file validation in `solune/frontend/`
- [x] T030 [P] Add test cases for `isAcceptedIssueFile()` with `.vtt` and `.srt` extensions in `solune/frontend/src/components/board/ProjectIssueLaunchPanel.test.tsx` (if test file exists)

### Regression Verification

- [x] T031 Run full backend test suite: `cd solune/backend && pytest --cov=src --cov-report=term-missing --durations=20` — verify no regressions
- [x] T032 Run backend linting: `cd solune/backend && ruff check src tests && ruff format --check src tests && bandit -r src/ -ll -ii --skip B104,B608`
- [x] T033 [P] Run frontend type check and linting: `cd solune/frontend && npm run type-check && npm run lint`

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final cleanup and cross-cutting improvements

- [x] T034 Run quickstart.md verification checklist end-to-end
- [x] T035 Verify `.vtt` and `.srt` files are visible in file pickers for both Chat and Parent Issue Intake (manual verification)
- [x] T036 Code cleanup: ensure all new functions have docstrings, type hints, and follow existing code conventions

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) — core MVP
- **User Story 2 (Phase 4)**: Depends on Foundational (Phase 2) — can run in parallel with US1
- **User Story 3 (Phase 5)**: Depends on Foundational (Phase 2) — validation of passthrough behavior
- **User Story 4 (Phase 6)**: Depends on Foundational (Phase 2) — comprehensive detection testing
- **Testing (Phase 7)**: Depends on all user stories being implemented
- **Polish (Phase 8)**: Depends on all testing complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories. **This is the MVP.**
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) — Independent of US1. Backend pipeline integration + frontend intake panel updates.
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) — Validates passthrough. Can run in parallel with US1 and US2.
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) — Detection accuracy testing. Can run in parallel with other stories.

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Detection utility before service integration
- Service integration before API endpoint integration
- Backend before frontend (for US2)
- Core implementation before edge-case handling

### Parallel Opportunities

- **Phase 1**: T002 and T003 can run in parallel (different files). T001 is independent.
- **Phase 2**: T008-T009 (prompt) can run in parallel with T004-T007 (detection utility) — different files, no dependencies.
- **Phase 3-6**: All user stories can start in parallel after Phase 2 — they modify different files.
- **Phase 7**: T027, T028, T029, T030 are all [P] — different test files.
- **Cross-phase**: Frontend tasks (T002, T003, T018, T029, T030, T033) can run in parallel with backend tasks.

---

## Parallel Example: Phase 2 (Foundational)

```bash
# These can run in parallel — different files:
Task: T004-T007 "Implement transcript detection utility in solune/backend/src/services/transcript_detector.py"
Task: T008-T009 "Create Transcribe agent prompt in solune/backend/src/prompts/transcript_analysis.py"

# T010 depends on T008-T009 completing first:
Task: T010 "Add analyze_transcript() to AIAgentService in solune/backend/src/services/ai_agent.py"
```

## Parallel Example: User Stories (Phases 3-6)

```bash
# After Phase 2 completes, these can all start in parallel:
Developer A: Phase 3 — US1 Chat transcript upload (T011-T014)
Developer B: Phase 4 — US2 Pipeline intake (T015-T018)
Developer C: Phase 5 — US3 Non-transcript passthrough (T019-T023)
Developer D: Phase 6 — US4 Detection accuracy (T024-T026)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T010) — CRITICAL, blocks all stories
3. Complete Phase 3: User Story 1 (T011-T014)
4. **STOP and VALIDATE**: Upload a `.vtt` transcript in Chat → recommendation appears → confirm → issue created
5. Deploy/demo if ready — core value delivered

### Incremental Delivery

1. Setup + Foundational → Foundation ready (T001-T010)
2. Add User Story 1 → Test independently → Deploy/Demo (**MVP!**) (T011-T014)
3. Add User Story 2 → Test independently → Deploy/Demo (T015-T018)
4. Add User Story 3 → Validate passthrough → Deploy/Demo (T019-T023)
5. Add User Story 4 → Comprehensive detection testing → Deploy/Demo (T024-T026)
6. Full testing + polish → Production ready (T027-T036)

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (Phase 1-2)
2. Once Foundational is done:
   - Developer A: User Story 1 (Chat path — P1 MVP)
   - Developer B: User Story 2 (Pipeline path — P2)
   - Developer C: User Story 3 + 4 (Passthrough + Detection — P2/P3)
3. Stories complete and integrate independently
4. Final testing and polish as a team

---

## Notes

- [P] tasks = different files, no dependencies — safe to run in parallel
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable after Phase 2
- No new database migrations required — `TranscriptDetectionResult` is an in-memory dataclass
- `IssueRecommendation` model is reused as-is — no changes to existing model
- Existing UI component `IssueRecommendationPreview.tsx` renders transcript recommendations — no new UI components needed
- Commit after each task or logical group
- Stop at any checkpoint to validate the story independently
