# Tasks: Fix Chat Microphone Voice Input — Incorrect Browser Support Detection

**Input**: Design documents from `/specs/036-fix-voice-input/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Not required per constitution (IV. Test Optionality). Manual browser testing covers acceptance scenarios per plan.md.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- All changes are frontend-only (React SPA)

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: CSS animation, tooltip content, and foundational styling required by multiple user stories

- [ ] T001 Add `mic-recording-pulse` keyframes animation and `--animate-mic-recording` custom property to `frontend/src/index.css`
- [ ] T002 [P] Add voice button tooltip content entry (`chat.toolbar.voiceButton`: "Use your microphone to dictate a message instead of typing.") to `frontend/src/constants/tooltip-content.ts`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core type definitions, browser detection utility, and component skeleton that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 Create `frontend/src/hooks/useVoiceInput.ts` with Web Speech API TypeScript type definitions (`SpeechRecognitionEvent`, `SpeechRecognitionErrorEvent`, `SpeechRecognitionInstance`, `UseVoiceInputReturn`) and `getSpeechRecognitionConstructor()` utility that checks `window.SpeechRecognition || window.webkitSpeechRecognition || null`
- [ ] T004 [P] Create `frontend/src/components/chat/VoiceInputButton.tsx` with three visual states: disabled (`MicOff` icon, `text-muted-foreground/50`, `cursor-not-allowed`), ready (`Mic` icon, `text-muted-foreground`), and recording (`Square` icon, `bg-destructive/10 text-destructive`, `mic-recording-pulse` animation) — include `celestial-focus` class and appropriate `aria-label` per contract

**Checkpoint**: Foundation ready — user story implementation can now begin in parallel

---

## Phase 3: User Story 1 — Correct Browser Support Detection Enables Voice Input (Priority: P1) 🎯 MVP

**Goal**: Fix the root cause — browser support detection — so the microphone button is correctly enabled in Firefox 85+, Chrome, Edge, and Safari 14.1+. Eliminate false-negative "not supported" messages.

**Independent Test**: Open the chat interface in Firefox 85+, Chrome, Edge, and Safari. Confirm the microphone button is enabled (not greyed out, no false error message) in all four browsers. Click the button and confirm it initiates voice capture without errors.

### Implementation for User Story 1

- [ ] T005 [US1] Implement `isSupported` state initialization using `getSpeechRecognitionConstructor() !== null` in the `useVoiceInput` hook in `frontend/src/hooks/useVoiceInput.ts`
- [ ] T006 [US1] Export the `useVoiceInput` hook with initial return shape (`isSupported`, `isRecording: false`, `interimTranscript: ''`, `error: null`, `startRecording`, `stopRecording`, `cancelRecording` stubs) in `frontend/src/hooks/useVoiceInput.ts`
- [ ] T007 [US1] Integrate `VoiceInputButton` into `ChatToolbar` with tooltip wiring — show "Voice input is not supported in this browser." tooltip when `isVoiceSupported` is false, dynamic tooltip content for recording/error states, and `contentKey='chat.toolbar.voiceButton'` for idle state in `frontend/src/components/chat/ChatToolbar.tsx`
- [ ] T008 [US1] Wire `useVoiceInput` hook into `ChatInterface` — create `handleVoiceTranscript` callback (appends text to input, clears tokens), create `handleVoiceToggle` toggle handler, pass `isRecording`, `isVoiceSupported`, `onVoiceToggle`, and `voiceError` props to `ChatToolbar` in `frontend/src/components/chat/ChatInterface.tsx`

**Checkpoint**: At this point, the microphone button should be correctly enabled/disabled based on actual browser support. Firefox, Chrome, Edge, and Safari users see an enabled mic button. Unsupported browsers see a disabled button with correct tooltip.

---

## Phase 4: User Story 2 — Voice Capture and Transcription Flow (Priority: P1)

**Goal**: Implement the full voice capture workflow — click mic, speak, see interim transcription, get final text in input field, send to chat agent.

**Independent Test**: In a supported browser, click the microphone button, speak a short sentence, and stop. Confirm the button shows a recording indicator while speaking, interim text appears in the input field during speech, and the final transcription is placed in the input field when speech ends. Press send to deliver the message.

### Implementation for User Story 2

- [ ] T009 [US2] Implement `startRecording()` — create new `SpeechRecognition` instance via `getSpeechRecognitionConstructor()`, configure `continuous: true` and `interimResults: true`, set `lang` to `navigator.language`, call `recognition.start()`, set `isRecording: true`, clear previous error, store instance in `recognitionRef` in `frontend/src/hooks/useVoiceInput.ts`
- [ ] T010 [US2] Implement `stopRecording()` — call `recognitionRef.current.stop()` (waits for final result) in `frontend/src/hooks/useVoiceInput.ts`
- [ ] T011 [US2] Implement `cancelRecording()` — call `recognitionRef.current.abort()`, clear `interimTranscript`, null the ref in `frontend/src/hooks/useVoiceInput.ts`
- [ ] T012 [US2] Implement `onresult` handler — iterate from `event.resultIndex` to `event.results.length`, accumulate non-final results into `interimTranscript` state, invoke `onTranscript(finalText)` callback for final results, clear interim on finalization in `frontend/src/hooks/useVoiceInput.ts`
- [ ] T013 [US2] Implement `onend` handler — set `isRecording: false`, clear `interimTranscript`, null `recognitionRef` in `frontend/src/hooks/useVoiceInput.ts`
- [ ] T014 [US2] Wire `interimTranscript` display into `ChatInterface` — show partial transcription as visual preview in or near the chat input field while recording is active in `frontend/src/components/chat/ChatInterface.tsx`

**Checkpoint**: At this point, the full voice-to-text flow should work — click mic, speak, see interim text, final text appears in input, user can send message.

---

## Phase 5: User Story 3 — Microphone Permission Handling (Priority: P2)

**Goal**: Gracefully handle microphone permission denial and missing hardware, displaying actionable guidance messages.

**Independent Test**: Click the microphone button. When the permission prompt appears, deny it. Confirm a user-friendly message appears explaining the denial and suggesting how to re-enable permissions. Grant permission on retry and confirm voice capture works normally.

### Implementation for User Story 3

- [ ] T015 [US3] Add `getUserMedia` pre-flight permission check in `startRecording()` — call `navigator.mediaDevices.getUserMedia({ audio: true })` before creating `SpeechRecognition` instance, immediately release obtained stream (`stream.getTracks().forEach(t => t.stop())`), guard against missing `navigator.mediaDevices` in `frontend/src/hooks/useVoiceInput.ts`
- [ ] T016 [US3] Handle `getUserMedia` rejection — catch `NotAllowedError` and set error to "Microphone access is required for voice input. Please allow microphone access in your browser settings.", catch `NotFoundError` and other errors with appropriate messages, set error when `navigator.mediaDevices` is unavailable ("Microphone access is not available in this browser.") in `frontend/src/hooks/useVoiceInput.ts`
- [ ] T017 [US3] Handle `SpeechRecognition` `onerror` event — catch `not-allowed` / `permission-denied` errors with permission-specific message, ignore `aborted` errors (intentional cancel), set descriptive error for all other error types in `frontend/src/hooks/useVoiceInput.ts`

**Checkpoint**: Permission denial and missing hardware scenarios now show clear, actionable messages. Users understand what to do to enable voice input.

---

## Phase 6: User Story 4 — Grammatically Correct Error Message (Priority: P2)

**Goal**: Fix the grammatical error in the unsupported browser message ("not support" → "not supported") and ensure it only appears when the browser genuinely lacks the required APIs.

**Independent Test**: Open the chat in a browser that genuinely lacks speech recognition support (or simulate by overriding the API objects). Confirm the displayed error reads "Voice input is not supported in this browser." with correct grammar. Confirm no error appears in supported browsers.

### Implementation for User Story 4

- [ ] T018 [US4] Verify all error messages use correct grammar — confirm "Voice input is not supported in this browser." (not "not support") in disabled button tooltip, `aria-label` value "Voice input not supported", and any other user-facing strings in `frontend/src/hooks/useVoiceInput.ts` and `frontend/src/components/chat/VoiceInputButton.tsx`
- [ ] T019 [US4] Verify unsupported message only displays when `isSupported` is `false` (both `SpeechRecognition` and `webkitSpeechRecognition` absent) — confirm no false-negative messages in `frontend/src/components/chat/ChatToolbar.tsx`

**Checkpoint**: Error messages are grammatically correct and accurately reflect browser capabilities.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Resource cleanup, edge case handling, and final validation across all user stories

- [ ] T020 Add `useEffect` cleanup function in `useVoiceInput` hook to call `recognitionRef.current.abort()` and null the ref on component unmount — ensures zero orphaned audio capture sessions on navigation in `frontend/src/hooks/useVoiceInput.ts`
- [ ] T021 Handle speech recognition runtime errors (network failures, service unavailability) with descriptive fallback messages in `onerror` handler in `frontend/src/hooks/useVoiceInput.ts`
- [ ] T022 Run quickstart.md validation scenarios — verify all 7 error handling conditions, all 3 visual states, and the full voice-to-message flow across Firefox, Chrome, Edge, and Safari

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) — the MVP detection fix
- **User Story 2 (Phase 4)**: Depends on User Story 1 (needs hook skeleton + integration wiring)
- **User Story 3 (Phase 5)**: Depends on User Story 2 (adds permission layer to recording flow)
- **User Story 4 (Phase 6)**: Depends on User Story 1 (verifies messages from detection fix)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — delivers the root cause fix. This IS the MVP.
- **User Story 2 (P1)**: Depends on US1 (needs the hook integration wiring from Phase 3). Delivers the core voice-to-text flow.
- **User Story 3 (P2)**: Depends on US2 (permission check wraps the recording start flow). Can be developed in parallel with US4.
- **User Story 4 (P2)**: Depends on US1 (verifies error messages). Can be developed in parallel with US3.

### Within Each User Story

- Models/types before services/hooks
- Hook logic before component integration
- Core implementation before integration wiring
- Story complete before moving to next priority

### Parallel Opportunities

- T001 and T002 can run in parallel (different files, no dependencies)
- T003 and T004 can run in parallel (different files — hook vs. component)
- Once Phase 2 is complete, US3 (Phase 5) and US4 (Phase 6) can run in parallel (US3 modifies hook internals, US4 verifies messages in component/toolbar — different concerns)
- T018 and T019 can run in parallel (different files)

---

## Parallel Example: Setup Phase

```bash
# Launch both setup tasks together (different files):
Task T001: "Add mic-recording-pulse keyframes animation to frontend/src/index.css"
Task T002: "Add voice button tooltip content entry to frontend/src/constants/tooltip-content.ts"
```

## Parallel Example: Foundational Phase

```bash
# Launch both foundational tasks together (different files):
Task T003: "Create useVoiceInput.ts with type definitions and detection utility"
Task T004: "Create VoiceInputButton.tsx with three visual states"
```

## Parallel Example: User Story 3 + User Story 4

```bash
# After User Story 2 is complete, these can run in parallel:
Task T015-T017: "User Story 3 — Permission handling (modifies hook internals)"
Task T018-T019: "User Story 4 — Error message verification (checks component/toolbar strings)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (CSS animation + tooltip entry)
2. Complete Phase 2: Foundational (hook types + detection + button component)
3. Complete Phase 3: User Story 1 (integration wiring into ChatToolbar + ChatInterface)
4. **STOP and VALIDATE**: Mic button should be enabled in Firefox, Chrome, Edge, Safari. Unsupported browsers show disabled button with correct message.
5. Deploy/demo if ready — this alone fixes the reported bug

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test detection fix across browsers → Deploy/Demo (MVP! Root cause fixed)
3. Add User Story 2 → Test full voice-to-text flow → Deploy/Demo (Core value delivered)
4. Add User Story 3 + 4 in parallel → Test permission handling + error messages → Deploy/Demo (Polish complete)
5. Polish phase → Resource cleanup, edge cases, final validation

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 → User Story 2 (sequential, same integration path)
   - Developer B: User Story 4 (after US1 lands) + User Story 3 (after US2 lands)
3. Polish phase: Any developer

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 22 |
| **Phase 1 (Setup)** | 2 tasks |
| **Phase 2 (Foundational)** | 2 tasks |
| **Phase 3 (US1 — Detection Fix)** | 4 tasks |
| **Phase 4 (US2 — Voice Capture)** | 6 tasks |
| **Phase 5 (US3 — Permissions)** | 3 tasks |
| **Phase 6 (US4 — Error Grammar)** | 2 tasks |
| **Phase 7 (Polish)** | 3 tasks |
| **Parallel opportunities** | 4 groups (Setup, Foundational, US3+US4, within-phase [P] tasks) |
| **MVP scope** | Phases 1–3 (US1 only — 8 tasks, fixes the reported Firefox bug) |
| **Files created** | 2 (`useVoiceInput.ts`, `VoiceInputButton.tsx`) |
| **Files modified** | 4 (`ChatToolbar.tsx`, `ChatInterface.tsx`, `tooltip-content.ts`, `index.css`) |
| **Estimated effort** | ~3 hours (per parent issue) |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- No new external dependencies — uses browser-native Web Speech API
- All changes are frontend-only (TypeScript/React/CSS)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
