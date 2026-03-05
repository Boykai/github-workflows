# Tasks: Add File Upload and Voice Input Support to App Chat Experience

**Input**: Design documents from `/specs/018-chat-upload-voice/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/api.yaml ✅, quickstart.md ✅

**Tests**: Not explicitly requested in the feature specification. Test tasks are omitted per Constitution Principle IV (Test Optionality with Clarity).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization — create new files and directories needed for the feature, install any new dependencies

- [x] T001 Create upload storage directory and add to .gitignore at project root
- [x] T002 [P] Add `UploadStatus` enum and `FileAttachment` / `FileAttachmentResponse` models to backend/src/models/chat.py per data-model.md
- [x] T003 [P] Extend `ChatMessage` model with optional `attachments` field and `ChatMessageRequest` with optional `attachment_ids` field in backend/src/models/chat.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core backend service and endpoints that MUST be complete before ANY frontend user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Create file upload service with validation (size ≤ 25 MB, MIME allowlist), UUID-based local filesystem storage, and in-memory metadata registry in backend/src/services/file_upload.py
- [x] T005 Add `POST /api/v1/chat/upload` endpoint (multipart/form-data) returning `FileAttachmentResponse` in backend/src/api/chat.py per contracts/api.yaml
- [x] T006 [P] Add `GET /api/v1/chat/upload/{file_id}` endpoint to serve uploaded file content in backend/src/api/chat.py per contracts/api.yaml
- [x] T007 [P] Add `DELETE /api/v1/chat/upload/{file_id}` endpoint to remove queued files in backend/src/api/chat.py per contracts/api.yaml
- [x] T008 Extend existing chat message send endpoint to accept `attachment_ids` and associate `FileAttachment` references with the message in backend/src/api/chat.py per contracts/api.yaml
- [x] T009 [P] Add file upload API client functions (`uploadFile`, `getFileUrl`, `deleteFile`) in frontend/src/services/api.ts

**Checkpoint**: Backend upload/retrieval/deletion pipeline functional; frontend API client ready — user story implementation can now begin

---

## Phase 3: User Story 1 — Upload Files in Chat (Priority: P1) 🎯 MVP

**Goal**: Users can attach files to chat messages using a button click, drag-and-drop, or clipboard paste, preview them inline, remove them, and send them with the message

**Independent Test**: Click the attachment button → select a file → see thumbnail/chip preview → dismiss or send → file delivered in message

### Implementation for User Story 1

- [x] T010 [P] [US1] Create `useFileUpload` hook (file selection, client-side validation, upload state, queue management) in frontend/src/hooks/useFileUpload.ts
- [x] T011 [P] [US1] Create `useDragDrop` hook (dragenter/dragleave/dragover/drop event handling with counter pattern) in frontend/src/hooks/useDragDrop.ts
- [x] T012 [P] [US1] Create `FileUploadButton` component (paperclip icon via lucide-react, hidden `<input type="file">` with accept attribute) in frontend/src/components/chat/FileUploadButton.tsx
- [x] T013 [P] [US1] Create `FilePreviewItem` component (image thumbnail via `URL.createObjectURL` or file-name chip with type icon, dismiss button) in frontend/src/components/chat/FilePreviewItem.tsx
- [x] T014 [P] [US1] Create `FilePreviewArea` component (container rendering list of `FilePreviewItem` components) in frontend/src/components/chat/FilePreviewArea.tsx
- [x] T015 [P] [US1] Create `DragDropOverlay` component (dashed border overlay with "Drop files here" text, visible during drag) in frontend/src/components/chat/DragDropOverlay.tsx
- [x] T016 [US1] Integrate `FileUploadButton` into chat input toolbar, `FilePreviewArea` above text input, drag-and-drop handlers on chat container, and clipboard paste handler in frontend/src/components/chat/ChatInterface.tsx
- [x] T017 [US1] Wire message send flow to upload queued files, collect attachment IDs, and include them in the message payload in frontend/src/components/chat/ChatInterface.tsx

**Checkpoint**: File upload feature fully functional — button select, drag-and-drop, clipboard paste, preview, dismiss, and send with attachments all work end-to-end

---

## Phase 4: User Story 2 — Voice Input for Chat Messages (Priority: P2)

**Goal**: Users can dictate messages via microphone button, see a recording indicator, and review/edit transcribed text before sending

**Independent Test**: Click microphone button → speak a phrase → recording indicator visible → stop recording → transcription appears in text input → edit if needed → send

### Implementation for User Story 2

- [x] T018 [P] [US2] Create `useVoiceInput` hook (Web Speech API `SpeechRecognition`/`webkitSpeechRecognition` wrapper, recording state, interim/final transcription, browser support detection, permission error handling) in frontend/src/hooks/useVoiceInput.ts
- [x] T019 [P] [US2] Create `RecordingIndicator` component (animated pulsing mic icon or waveform indicator) in frontend/src/components/chat/RecordingIndicator.tsx
- [x] T020 [US2] Create `VoiceInputButton` component (microphone icon via lucide-react, toggles recording, hidden/disabled with tooltip when browser unsupported) in frontend/src/components/chat/VoiceInputButton.tsx
- [x] T021 [US2] Integrate `VoiceInputButton` into chat input toolbar, append transcribed text to input field on completion, show `RecordingIndicator` when recording in frontend/src/components/chat/ChatInterface.tsx
- [x] T022 [US2] Handle microphone permission denial by displaying informative guidance message in frontend/src/components/chat/VoiceInputButton.tsx

**Checkpoint**: Voice input feature fully functional — record, transcribe, review, edit, and send all work; permission denial handled gracefully; unsupported browsers show disabled state

---

## Phase 5: User Story 3 — File Validation and Error Handling (Priority: P2)

**Goal**: Users receive clear, actionable error messages when file uploads fail validation (size, type) or encounter network errors, with retry options

**Independent Test**: Attempt to upload a file > 25 MB → inline error shown; attempt unsupported file type → error with accepted formats listed; simulate network error → retry option displayed

### Implementation for User Story 3

- [x] T023 [US3] Add inline error message display for file size exceeded (>25 MB) and unsupported file type with accepted formats list in frontend/src/hooks/useFileUpload.ts
- [x] T024 [US3] Add max attachment count enforcement (≤10 files per message) with error message in frontend/src/hooks/useFileUpload.ts
- [x] T025 [US3] Add network/server error handling with retry option for failed uploads in frontend/src/hooks/useFileUpload.ts
- [x] T026 [US3] Display validation and upload error messages inline in the `FilePreviewArea` component in frontend/src/components/chat/FilePreviewArea.tsx

**Checkpoint**: All validation errors surface immediately with clear messaging; retry available for transient failures; user is never blocked from continuing to use chat

---

## Phase 6: User Story 4 — Accessibility for File Upload and Voice Controls (Priority: P2)

**Goal**: All new controls are fully keyboard-navigable and screen-reader compatible with proper ARIA labels, roles, and live region announcements

**Independent Test**: Navigate to attachment and microphone buttons via Tab key → activate via Enter/Space → screen reader announces button purpose, state changes ("Recording started", "File attached: report.pdf"), and errors

### Implementation for User Story 4

- [x] T027 [P] [US4] Add `aria-label`, `role`, keyboard focus styles (`focus-visible:` Tailwind utilities) to `FileUploadButton` in frontend/src/components/chat/FileUploadButton.tsx
- [x] T028 [P] [US4] Add `aria-label`, `role`, keyboard focus styles, and `aria-pressed` for recording toggle to `VoiceInputButton` in frontend/src/components/chat/VoiceInputButton.tsx
- [x] T029 [P] [US4] Add accessible labels and keyboard-focusable dismiss buttons with `aria-label` to `FilePreviewItem` in frontend/src/components/chat/FilePreviewItem.tsx
- [x] T030 [US4] Add ARIA live region (`role="status"`, `aria-live="polite"`) for recording state changes ("Recording started", "Recording stopped", "Transcription complete") and file attachment announcements ("File attached: filename", "File removed") in frontend/src/components/chat/ChatInterface.tsx

**Checkpoint**: All new controls pass keyboard-only navigation test; screen readers announce all state changes within 2 seconds of the event

---

## Phase 7: User Story 5 — Mobile-Optimized File and Voice Input (Priority: P3)

**Goal**: File upload leverages native camera/photo library/files on mobile; voice input uses native microphone seamlessly

**Independent Test**: On mobile device — tap file upload → camera, photo library, and files options available; tap microphone → native microphone activates with visible recording indicator

### Implementation for User Story 5

- [x] T031 [US5] Add `accept` attribute with image and document MIME types and optional `capture` attribute for mobile camera access on the file input element in frontend/src/components/chat/FileUploadButton.tsx
- [x] T032 [US5] Verify voice input hook triggers native microphone on mobile browsers and recording indicator is visible on small screens in frontend/src/hooks/useVoiceInput.ts and frontend/src/components/chat/RecordingIndicator.tsx
- [x] T033 [US5] Ensure touch-friendly sizing (min 44×44px tap targets) and responsive layout for all new toolbar buttons and preview areas in frontend/src/components/chat/ChatInterface.tsx

**Checkpoint**: Mobile users can access camera, photo library, files via native picker and use device microphone for voice input

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T034 [P] Revoke `URL.createObjectURL` references (created in the hook for preview display) on file removal and component unmount to prevent memory leaks in frontend/src/hooks/useFileUpload.ts
- [x] T035 [P] Stop active voice recording and clean up `SpeechRecognition` instance on component unmount or navigation away in frontend/src/hooks/useVoiceInput.ts
- [x] T036 [P] Add server-side filename sanitization (strip path components, limit length) and defense-in-depth MIME type re-validation in backend/src/services/file_upload.py
- [x] T037 Run quickstart.md validation checklist against completed implementation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup (Phase 1) completion — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational (Phase 2) completion
- **US2 (Phase 4)**: Depends on Foundational (Phase 2) completion — independent of US1
- **US3 (Phase 5)**: Depends on US1 (Phase 3) completion (extends file upload error handling)
- **US4 (Phase 6)**: Depends on US1 (Phase 3) and US2 (Phase 4) completion (adds accessibility to existing components)
- **US5 (Phase 7)**: Depends on US1 (Phase 3) and US2 (Phase 4) completion (adds mobile optimization to existing components)
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 — Upload Files (P1)**: Can start after Foundational — No dependencies on other stories
- **US2 — Voice Input (P2)**: Can start after Foundational — Independent of US1
- **US3 — Validation & Errors (P2)**: Depends on US1 (extends the file upload pipeline with validation UX)
- **US4 — Accessibility (P2)**: Depends on US1 and US2 (adds ARIA attributes to components created in those stories)
- **US5 — Mobile Optimization (P3)**: Depends on US1 and US2 (adds mobile attributes to components created in those stories)

### Within Each User Story

- Models/hooks before components
- Components before integration into ChatInterface
- Core functionality before error handling and polish

### Parallel Opportunities

- T002, T003 can run in parallel (different model sections)
- T006, T007 can run in parallel (independent endpoints)
- T009 can run in parallel with T006/T007 (frontend vs backend)
- T010, T011, T012, T013, T014, T015 can all run in parallel (separate new files)
- T018, T019 can run in parallel (separate new files)
- T027, T028, T029 can run in parallel (different component files)
- T034, T035, T036 can run in parallel (independent cleanup tasks)
- **US1 and US2 can be developed in parallel** by separate developers after Foundational phase

---

## Parallel Example: User Story 1

```bash
# Launch all hooks and components in parallel (all separate files):
Task T010: "Create useFileUpload hook in frontend/src/hooks/useFileUpload.ts"
Task T011: "Create useDragDrop hook in frontend/src/hooks/useDragDrop.ts"
Task T012: "Create FileUploadButton in frontend/src/components/chat/FileUploadButton.tsx"
Task T013: "Create FilePreviewItem in frontend/src/components/chat/FilePreviewItem.tsx"
Task T014: "Create FilePreviewArea in frontend/src/components/chat/FilePreviewArea.tsx"
Task T015: "Create DragDropOverlay in frontend/src/components/chat/DragDropOverlay.tsx"

# Then integrate sequentially (same file: ChatInterface.tsx):
Task T016: "Integrate file upload components into ChatInterface"
Task T017: "Wire message send flow with attachment IDs"
```

## Parallel Example: User Story 2

```bash
# Launch hook and indicator in parallel (separate files):
Task T018: "Create useVoiceInput hook in frontend/src/hooks/useVoiceInput.ts"
Task T019: "Create RecordingIndicator in frontend/src/components/chat/RecordingIndicator.tsx"

# Then build button and integrate sequentially:
Task T020: "Create VoiceInputButton in frontend/src/components/chat/VoiceInputButton.tsx"
Task T021: "Integrate voice input into ChatInterface"
Task T022: "Handle microphone permission denial"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1 — Upload Files in Chat
4. **STOP and VALIDATE**: Test file upload independently (button select, drag-and-drop, paste, preview, dismiss, send)
5. Deploy/demo if ready — users can share files in chat

### Incremental Delivery

1. Complete Setup + Foundational → Backend upload pipeline ready
2. Add US1 (Upload Files) → Test independently → Deploy/Demo (**MVP!**)
3. Add US2 (Voice Input) → Test independently → Deploy/Demo
4. Add US3 (Validation & Errors) → Test independently → Deploy/Demo
5. Add US4 (Accessibility) → Test independently → Deploy/Demo
6. Add US5 (Mobile Optimization) → Test independently → Deploy/Demo
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers after Foundational phase:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - **Developer A**: US1 (Upload Files) — P1 MVP
   - **Developer B**: US2 (Voice Input) — P2, independent of US1
3. After US1 and US2 complete:
   - **Developer A**: US3 (Validation) — extends US1
   - **Developer B**: US4 (Accessibility) — extends US1 + US2
4. **Developer A or B**: US5 (Mobile) — extends US1 + US2
5. **Together**: Polish phase

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps each task to its user story for traceability
- Each user story is independently completable and testable after its phase checkpoint
- Commit after each task or logical group
- Stop at any checkpoint to validate the story independently
- No test tasks generated (not requested in spec — Constitution Principle IV)
- Voice input uses browser-native Web Speech API (research.md R3) — hidden/disabled in unsupported browsers
- File storage is local filesystem with UUID naming (research.md R2) — no cloud storage at MVP
- All file previews use `URL.createObjectURL` (research.md R5) — no server round-trip for pre-send previews
