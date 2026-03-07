# Tasks: Chat UX Enhancements — AI Enhance Toggle, Markdown Input Support, File Upload, and Voice Chat

**Input**: Design documents from `/specs/028-chat-ux-enhancements/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/ (api.md, components.md), quickstart.md

**Tests**: Not explicitly requested in the feature specification. Existing tests must continue to pass (Constitution Check IV). No new test tasks are included.

**Organization**: Tasks grouped by user story (P1–P3) for independent implementation and testing. Each story can be delivered as an independently testable increment. User Stories 1 and 2 are both P1 and form the MVP together.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Exact file paths included in descriptions

## Path Conventions

- **Web app**: `frontend/src/` (React/TypeScript), `backend/src/` (Python/FastAPI)
- Frontend components: `frontend/src/components/chat/`
- Frontend hooks: `frontend/src/hooks/`
- Frontend types: `frontend/src/types/`
- Frontend services: `frontend/src/services/`
- Frontend commands: `frontend/src/lib/commands/`
- Backend API: `backend/src/api/`
- Backend services: `backend/src/services/`

---

## Phase 1: Setup

**Purpose**: Verify existing infrastructure, add new TypeScript types and file validation constants shared across multiple user stories.

- [ ] T001 Add `FileAttachment`, `VoiceInputState`, and `ChatPreferences` TypeScript interfaces to frontend/src/types/index.ts per data-model.md definitions
- [ ] T002 [P] Add `FILE_VALIDATION` constants object (maxFileSize, maxFilesPerMessage, allowedImageTypes, allowedDocTypes, allowedArchiveTypes, blockedTypes) and computed `ALLOWED_TYPES` array to frontend/src/types/index.ts per data-model.md validation rules
- [ ] T003 [P] Add `FileUploadResponse`, `FileUploadError`, and `FileValidationConfig` Pydantic models to backend/src/api/chat.py (or a shared models file) per data-model.md backend entity definitions
- [ ] T004 [P] Add file validation constants (`MAX_FILE_SIZE_BYTES`, `MAX_FILES_PER_MESSAGE`, `ALLOWED_IMAGE_TYPES`, `ALLOWED_DOC_TYPES`, `ALLOWED_ARCHIVE_TYPES`, `BLOCKED_TYPES`, `ALLOWED_TYPES`) to backend/src/api/chat.py per data-model.md FileValidationConfig

**Checkpoint**: All shared types and constants are in place. Ready for user story implementation.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Command prefix migration from `#` to `/` — this is a cross-cutting change that MUST be complete before User Story 2 (Markdown input) can be validated, and it also affects the chat interface used by all other stories.

**⚠️ CRITICAL**: User Story 2 (Markdown Input) depends on this phase. Other stories depend on the modified ChatInterface.

- [ ] T005 Update `parseCommand()` in frontend/src/lib/commands/registry.ts to match `/` prefix instead of `#` — change `trimmed.startsWith('#')` to `trimmed.startsWith('/')` and update command name extraction via `trimmed.slice(1)` accordingly
- [ ] T006 [P] Update command autocomplete trigger condition in frontend/src/components/chat/ChatInterface.tsx from `trimmed.startsWith('#')` to `trimmed.startsWith('/')` and update input placeholder text to "Type a message or /command..."
- [ ] T007 [P] Update command display prefix in frontend/src/components/chat/CommandAutocomplete.tsx to show `/commandName` in suggestion list instead of `#commandName`

**Checkpoint**: Command prefix migrated to `/`. Typing `# Heading` no longer triggers command detection. Typing `/help` still works. Markdown characters (`#`, `*`, `-`, `` ` ``, `>`) are all treated as plain text.

---

## Phase 3: User Story 1 — AI Enhance Toggle for Issue Description Control (Priority: P1) 🎯 MVP

**Goal**: Add an "AI Enhance" toggle to the chat toolbar that lets users choose between AI-rewritten or verbatim issue descriptions while always getting auto-generated metadata.

**Independent Test**: Toggle "AI Enhance" OFF → submit a chat message with specific formatting → verify the resulting GitHub Parent Issue description contains the user's exact verbatim input alongside auto-generated metadata (title, labels, estimates) and Agent Pipeline configuration details. Toggle ON → verify existing flow is unchanged.

### Implementation for User Story 1

- [ ] T008 [US1] Create ChatToolbar component in frontend/src/components/chat/ChatToolbar.tsx with AI Enhance pill toggle (left section) — read initial state from `localStorage.getItem('chat-ai-enhance')` defaulting to `true`, persist on change via `localStorage.setItem`, use Sparkles icon from lucide-react, style consistently with AddAgentPopover border/hover pattern (`border border-dashed hover:bg-muted`)
- [ ] T009 [US1] Integrate ChatToolbar into ChatInterface — import and render ChatToolbar above the chat input area in frontend/src/components/chat/ChatInterface.tsx, pass `aiEnhance` state and `onAiEnhanceChange` handler, capture `aiEnhance` value at submission time per FR-017
- [ ] T010 [US1] Modify chat message API client method in frontend/src/services/api.ts to accept and send `ai_enhance` boolean parameter (default `true`) in the `POST /api/v1/chat/messages` request body as `ai_enhance` field
- [ ] T011 [US1] Add `ai_enhance: bool = True` field to the `ChatMessageRequest` Pydantic model in backend/src/api/chat.py and pass the value through to the AI agent service
- [ ] T012 [US1] Add conditional description bypass in backend/src/services/ai_agent.py — when `ai_enhance=False`, use the raw user `message` text as the GitHub Parent Issue description body, skip AI description rewriting, still run metadata inference pipeline (title, labels, estimates, assignees, milestones), and append Agent Pipeline configuration section to the issue body per the template in contracts/api.md

**Checkpoint**: AI Enhance toggle is functional. Toggle OFF → exact user text in issue body + auto-generated metadata. Toggle ON → existing flow unchanged. Toggle state persists in localStorage across page refreshes.

---

## Phase 4: User Story 2 — Markdown Input Without Command Conflicts (Priority: P1) 🎯 MVP

**Goal**: Ensure the chat input field accepts all raw Markdown syntax without triggering command detection errors — only explicit `/commandName` tokens are treated as commands.

**Independent Test**: Type `# Heading`, `**bold**`, `- list item`, `` `code` ``, `> blockquote`, and `[link](url)` into the chat input → confirm none trigger an error or are interpreted as commands. Type `/help` → confirm it is still recognized as a command.

### Implementation for User Story 2

- [ ] T013 [US2] Verify end-to-end that Markdown input (`# Heading`, `**bold**`, `- list`, `` `code` ``, `> quote`, `[link](url)`) is accepted without errors in the chat by tracing the parsing flow through frontend/src/lib/commands/registry.ts and frontend/src/components/chat/ChatInterface.tsx — this is a validation task, no code changes expected if T005–T007 are correct
- [ ] T014 [US2] If the chat input has any additional Markdown-sensitive parsing or filtering logic beyond `parseCommand()` (e.g., message preprocessing, content sanitization), audit and update those code paths in frontend/src/components/chat/ChatInterface.tsx and frontend/src/hooks/useChat.ts to only treat `/`-prefixed tokens as commands

**Checkpoint**: All Markdown syntax accepted as plain text content. Only `/command` tokens trigger command parsing. US1 + US2 together form the complete MVP.

---

## Phase 5: User Story 3 — File Upload Attached to GitHub Issues (Priority: P2)

**Goal**: Allow users to attach files from the chat toolbar, preview them as chips, and have them linked in the resulting GitHub Parent Issue.

**Independent Test**: Click the file upload button (paperclip icon) → select a valid image file → preview chip appears with filename, size, and remove (×) button → submit chat message → verify the file URL is embedded as a Markdown image link in the GitHub Parent Issue body. Select a 15 MB file → error message shown. Select an .exe → error shown.

### Implementation for User Story 3

- [ ] T015 [P] [US3] Create useFileUpload hook in frontend/src/hooks/useFileUpload.ts with `addFiles(fileList)` (client-side validation against FILE_VALIDATION constants for size ≤ 10 MB, allowed types, max 5 files), `removeFile(fileId)`, `uploadAll()` (sequential uploads to POST /api/v1/chat/upload returning file URL array), and `clearAll()` per contracts/components.md UseFileUploadReturn interface
- [ ] T016 [P] [US3] Create FilePreviewChips component in frontend/src/components/chat/FilePreviewChips.tsx rendering a horizontal scrollable row of chips — each chip shows file icon, truncated filename (~20 chars), formatted file size (KB/MB), upload status indicator (spinner/check/warning), and remove (×) button calling `onRemove(fileId)` per contracts/components.md
- [ ] T017 [US3] Add file upload button (Paperclip icon from lucide-react) to ChatToolbar right section in frontend/src/components/chat/ChatToolbar.tsx — click triggers hidden `<input type="file" multiple accept="...">` element with the accept string from data-model.md, show badge with `fileCount` when > 0
- [ ] T018 [US3] Add `chat.uploadFile(file: File)` method to frontend/src/services/api.ts — POST multipart/form-data to `/api/v1/chat/upload`, return `FileUploadResponse`, throw `FileUploadError` on failure per contracts/api.md
- [ ] T019 [US3] Add `file_urls: list[str] = []` field to `ChatMessageRequest` in backend/src/api/chat.py and pass file URLs through to the issue body embedding logic
- [ ] T020 [US3] Implement `POST /api/v1/chat/upload` endpoint in backend/src/api/chat.py — accept multipart/form-data file, validate size (≤ 10 MB) and type (ALLOWED_TYPES), upload images to GitHub via Contents API (`PUT /repos/{owner}/{repo}/contents/uploads/{filename}`) and documents via Gist API (`POST /gists`), return `FileUploadResponse` with accessible URL per contracts/api.md
- [ ] T021 [US3] Add file URL embedding in the issue body in backend/src/services/ai_agent.py — when `file_urls` is non-empty, append an "Attachments" section with Markdown image links (`![filename](url)`) for images and Markdown links (`[filename](url)`) for documents per the issue body template in contracts/api.md
- [ ] T022 [US3] Integrate FilePreviewChips and useFileUpload into ChatInterface — render FilePreviewChips between ChatToolbar and input area in frontend/src/components/chat/ChatInterface.tsx, wire file upload button from ChatToolbar via `onFileSelect`, call `uploadAll()` before message submission, include returned URLs in the `file_urls` array sent with the message, handle upload errors gracefully per FR-018

**Checkpoint**: File upload fully functional. Files validated client-side and server-side. Preview chips show with remove action. Uploaded files linked in GitHub Issue body. Invalid files rejected with clear error messages.

---

## Phase 6: User Story 4 — Voice Chat via Microphone (Priority: P3)

**Goal**: Enable speech-to-text transcription via the Web Speech API, populating the chat input with transcribed text in real time.

**Independent Test**: Click the microphone button → allow permission → speak a test phrase → transcribed text appears in the chat input → click stop → edit text → submit. Deny permission → error message shown → chat continues working. In Firefox (unsupported) → mic button shows disabled state with tooltip.

### Implementation for User Story 4

- [ ] T023 [P] [US4] Create useVoiceInput hook in frontend/src/hooks/useVoiceInput.ts — check `window.SpeechRecognition || window.webkitSpeechRecognition` on mount for `isSupported`, implement `startRecording()` (request mic permission via `getUserMedia`, create SpeechRecognition with `continuous: true`, `interimResults: true`, `lang: 'en-US'`, stream interim results to `interimTranscript`, call `onTranscript(finalText)` on final result), `stopRecording()`, `cancelRecording()`, handle permission denial with user-friendly error message per FR-014/FR-015, cleanup on unmount per contracts/components.md UseVoiceInputReturn interface
- [ ] T024 [P] [US4] Create VoiceInputButton component in frontend/src/components/chat/VoiceInputButton.tsx — idle state shows Mic icon button (lucide-react), recording state shows pulsing red mic icon with `animate-pulse` CSS and red background plus stop control (Square icon), unsupported state shows disabled MicOff icon with tooltip "Voice input not supported in this browser", error state shows brief red flash with toast notification per contracts/components.md VoiceInputButtonProps
- [ ] T025 [US4] Add microphone button to ChatToolbar right section (after file upload button) in frontend/src/components/chat/ChatToolbar.tsx — render VoiceInputButton, pass `isSupported`, `isRecording`, `onVoiceToggle` (start/stop), and `error` props
- [ ] T026 [US4] Integrate useVoiceInput into ChatInterface in frontend/src/components/chat/ChatInterface.tsx — wire the hook's `onTranscript` callback to append transcribed text to the chat input field, display `interimTranscript` as a visual hint (e.g., grayed text) below or within the input, ensure the user can freely edit transcribed text before submission per FR-016

**Checkpoint**: Voice input works in supported browsers (Chrome, Edge, Safari). Mic button shows correct states. Transcribed text appears in input in real time. Permission denial handled gracefully. Unsupported browsers show disabled state. User can edit text before submitting.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Validate all changes work together, ensure type safety, and verify no regressions.

- [ ] T027 Run existing frontend linting and type checking: `cd frontend && npx eslint src/ && npx tsc --noEmit`
- [ ] T028 [P] Run existing frontend tests: `cd frontend && npx vitest run` — all must pass without modification
- [ ] T029 [P] Run existing backend tests: `cd backend && python -m pytest tests/` — all must pass without modification
- [ ] T030 Run quickstart.md verification steps — verify all 13 test scenarios pass (Markdown input, AI Enhance ON/OFF, toggle persistence, file upload, file validation, file remove, voice input in Chrome, voice permission denied, voice unsupported browser, rapid toggle edge case, files without text edge case, network error edge case)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Can start after Setup — BLOCKS User Story 2 validation
- **US1 (Phase 3)**: Depends on Setup (Phase 1) for shared types — can proceed in parallel with Foundational
- **US2 (Phase 4)**: Depends on Foundational (Phase 2) for command prefix migration
- **US3 (Phase 5)**: Depends on Setup (Phase 1) for types/constants — can proceed in parallel with US1 and US2
- **US4 (Phase 6)**: Depends on Setup (Phase 1) for types — can proceed in parallel with US1, US2, US3
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Setup. Adds ChatToolbar and backend ai_enhance flag. **Part of MVP.**
- **US2 (P1)**: Depends on Foundational (Phase 2) command prefix migration. Primarily validation. **Part of MVP.**
- **US3 (P2)**: Can start after Setup. Adds file upload to ChatToolbar, new hook, new component, backend endpoint. Independent of US1/US2.
- **US4 (P3)**: Can start after Setup. Adds voice input to ChatToolbar, new hook, new component. Independent of US1/US2/US3.

### Within Each User Story

- Types/constants before hooks
- Hooks before components
- Components before integration into ChatInterface
- Frontend before backend (or in parallel if different developers)
- API client methods before backend endpoints (for contract clarity)

### Parallel Opportunities

- **Phase 1**: T001 must precede T002 (types before constants); T003 and T004 can run in parallel with T001/T002 (different files: backend vs frontend)
- **Phase 2**: T005 is the core change; T006 and T007 can run in parallel (different files)
- **Phase 3**: T008 (ChatToolbar) → T009 (integrate into ChatInterface) are sequential; T010 (api.ts) can parallel with T008
- **Phase 5**: T015 (hook) and T016 (component) can run in parallel; T017 adds to ChatToolbar, T018 adds to api.ts — both can parallel; T020 (backend endpoint) can parallel with frontend tasks
- **Phase 6**: T023 (hook) and T024 (component) can run in parallel; T025 (add to toolbar) sequential after T024
- **Phase 7**: T028 and T029 (frontend/backend tests) can run in parallel
- **Cross-story**: US1 and US3 and US4 can all proceed in parallel after Phase 1 (different files). US2 validation waits for Phase 2.

---

## Parallel Example: User Story 1

```bash
# These can run in parallel (different files):
Task T008: "Create ChatToolbar.tsx" in frontend/src/components/chat/ChatToolbar.tsx
Task T010: "Modify API client" in frontend/src/services/api.ts

# Then sequentially:
Task T009: "Integrate ChatToolbar into ChatInterface" in frontend/src/components/chat/ChatInterface.tsx (depends on T008)

# Backend tasks can parallel with frontend:
Task T011: "Add ai_enhance to ChatMessageRequest" in backend/src/api/chat.py
Task T012: "Conditional description bypass" in backend/src/services/ai_agent.py (depends on T011)
```

## Parallel Example: User Story 3

```bash
# These can run in parallel (different files):
Task T015: "Create useFileUpload hook" in frontend/src/hooks/useFileUpload.ts
Task T016: "Create FilePreviewChips component" in frontend/src/components/chat/FilePreviewChips.tsx
Task T018: "Add uploadFile API method" in frontend/src/services/api.ts
Task T020: "Implement upload endpoint" in backend/src/api/chat.py

# Then sequentially:
Task T017: "Add file upload button to ChatToolbar" in frontend/src/components/chat/ChatToolbar.tsx (depends on T015)
Task T022: "Integrate into ChatInterface" in frontend/src/components/chat/ChatInterface.tsx (depends on T015, T016, T017, T018)

# Backend embedding (depends on T020):
Task T021: "Add file URL embedding in issue body" in backend/src/services/ai_agent.py
```

## Parallel Example: User Story 4

```bash
# These can run in parallel (different files):
Task T023: "Create useVoiceInput hook" in frontend/src/hooks/useVoiceInput.ts
Task T024: "Create VoiceInputButton component" in frontend/src/components/chat/VoiceInputButton.tsx

# Then sequentially:
Task T025: "Add mic button to ChatToolbar" in frontend/src/components/chat/ChatToolbar.tsx (depends on T024)
Task T026: "Integrate into ChatInterface" in frontend/src/components/chat/ChatInterface.tsx (depends on T023, T025)
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2)

1. Complete Phase 1: Setup (shared types and constants)
2. Complete Phase 2: Foundational (command prefix `#` → `/` migration)
3. Complete Phase 3: User Story 1 (AI Enhance toggle)
4. Complete Phase 4: User Story 2 (Markdown input validation)
5. **STOP and VALIDATE**: Test AI Enhance toggle ON/OFF + Markdown input acceptance independently
6. Deploy/demo if ready — users can now control issue description rewriting and use Markdown freely

### Incremental Delivery

1. Complete Setup + Foundational → Command prefix migrated, types ready
2. Add User Story 1 → AI Enhance toggle functional → Deploy/Demo (MVP Part 1)
3. Add User Story 2 → Markdown input verified → Deploy/Demo (MVP Complete!)
4. Add User Story 3 → File upload working → Deploy/Demo
5. Add User Story 4 → Voice input working → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Setup is done:
   - Developer A: User Story 1 (AI Enhance toggle — frontend + backend)
   - Developer B: User Story 3 (File upload — frontend hook + component)
   - Developer C: User Story 4 (Voice input — frontend hook + component)
3. Developer A validates User Story 2 after Foundational completes
4. Stories complete and integrate into ChatInterface independently
5. Polish phase: All developers

---

## Summary

| Metric | Count |
|--------|-------|
| **Total tasks** | 30 |
| **Phase 1 — Setup** | 4 |
| **Phase 2 — Foundational (Command Prefix)** | 3 |
| **Phase 3 — US1 (AI Enhance Toggle)** | 5 |
| **Phase 4 — US2 (Markdown Input)** | 2 |
| **Phase 5 — US3 (File Upload)** | 8 |
| **Phase 6 — US4 (Voice Input)** | 4 |
| **Phase 7 — Polish** | 4 |
| **Parallelizable tasks [P]** | 12 |
| **Frontend files created** | 5 (ChatToolbar.tsx, FilePreviewChips.tsx, VoiceInputButton.tsx, useFileUpload.ts, useVoiceInput.ts) |
| **Frontend files modified** | 5 (registry.ts, ChatInterface.tsx, CommandAutocomplete.tsx, api.ts, types/index.ts) |
| **Backend files modified** | 2 (chat.py, ai_agent.py) |
| **New backend endpoints** | 1 (POST /api/v1/chat/upload) |

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Tests are NOT included per spec (Constitution Check IV — test optionality). Existing tests must pass.
- The command prefix migration (`#` → `/`) is in Foundational because it is a prerequisite for Markdown input (US2) and affects all command interactions
- US1 and US2 together form the MVP scope — they deliver the highest-impact changes (user control over descriptions + Markdown support)
- US3 (file upload) is the largest story (8 tasks) due to full-stack changes including a new backend endpoint and GitHub API integration
- US4 (voice input) is frontend-only and uses the native Web Speech API with no new dependencies
- All file validation rules are defined in both frontend (TypeScript constants) and backend (Python constants) per data-model.md — both must be kept in sync
- The ChatToolbar component is created in US1 and extended in US3 (file upload button) and US4 (mic button) — task ordering ensures the component exists before extension
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
