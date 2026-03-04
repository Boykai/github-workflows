# Tasks: Chat Message History Navigation with Up Arrow Key Support

**Input**: Design documents from `/specs/018-chat-history-navigation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are NOT explicitly requested in the feature specification. Test tasks are omitted per the test-optionality principle.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `frontend/src/` — frontend-only feature, no backend changes required

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create new files and establish the storage utility and hook scaffolding that all user stories depend on.

- [ ] T001 Create localStorage wrapper utility with `loadHistory`, `saveHistory`, `clearStoredHistory` functions and `CHAT_HISTORY_STORAGE_KEY` constant in `frontend/src/utils/chatHistoryStorage.ts`
- [ ] T002 Create `useChatHistory` hook scaffold with configuration constant `CHAT_HISTORY_MAX_ENTRIES = 100`, empty return interface (`history`, `addToHistory`, `handleHistoryNavigation`, `clearHistory`, `isNavigating`), and initial state (`historyIndex = -1`, `draft = ""`) in `frontend/src/hooks/useChatHistory.ts`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implement core history storage logic and the `addToHistory` function that ALL user stories depend on. No user story work can begin until this phase is complete.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 Implement `loadHistory()` in `frontend/src/utils/chatHistoryStorage.ts` — read from localStorage key `"chat-message-history"`, JSON.parse the value, return `string[]` or `[]` on error/missing data, wrap in try/catch for graceful degradation (FR-013)
- [ ] T004 Implement `saveHistory(messages: string[])` in `frontend/src/utils/chatHistoryStorage.ts` — JSON.stringify and write to localStorage, no-op on error (FR-013)
- [ ] T005 Implement `clearStoredHistory()` in `frontend/src/utils/chatHistoryStorage.ts` — remove the history key from localStorage, no-op on error (FR-013)
- [ ] T006 Implement `addToHistory(message: string)` in `frontend/src/hooks/useChatHistory.ts` — trim message, reject empty/whitespace-only (FR-012), skip consecutive duplicates by comparing with last entry (FR-007), enforce max cap by removing oldest entry when full (FR-005), persist via `saveHistory()` (FR-006), reset navigation index to -1

**Checkpoint**: Foundation ready — storage utility fully functional, `addToHistory` handles all validation rules. User story implementation can now begin.

---

## Phase 3: User Story 1 — Navigate Sent Message History with Up/Down Arrow Keys (Priority: P1) 🎯 MVP

**Goal**: Users can press Up Arrow to cycle backward through previously sent messages and Down Arrow to cycle forward, with draft preservation when navigating past the newest entry.

**Independent Test**: Send 3+ messages, press Up Arrow to cycle through them in reverse order, press Down Arrow to return forward, verify draft is restored when pressing Down past newest entry.

### Implementation for User Story 1

- [ ] T007 [US1] Implement Up Arrow history navigation in `handleHistoryNavigation` in `frontend/src/hooks/useChatHistory.ts` — on first Up press save current input as draft and load newest history entry (index 0 from end), on subsequent Up presses load next older entry, stop at oldest entry without wrap-around, call `e.preventDefault()` only when navigation occurs (FR-002, FR-004)
- [ ] T008 [US1] Implement Down Arrow history navigation in `handleHistoryNavigation` in `frontend/src/hooks/useChatHistory.ts` — move forward through history on Down press, restore saved draft when pressing Down past newest entry, call `e.preventDefault()` only when navigation occurs, return `false` when not in navigation mode (FR-003, FR-004)
- [ ] T009 [US1] Implement cursor positioning at end of restored text in `handleHistoryNavigation` in `frontend/src/hooks/useChatHistory.ts` — use `setTimeout` to set `selectionStart` and `selectionEnd` to the end of the textarea value after setting input (FR-004)
- [ ] T010 [US1] Handle empty history edge case in `handleHistoryNavigation` in `frontend/src/hooks/useChatHistory.ts` — return `false` when Up Arrow is pressed with no history entries, producing no change to input field (FR-011)
- [ ] T011 [US1] Integrate `useChatHistory` hook into `frontend/src/components/chat/ChatInterface.tsx` — import and call `useChatHistory()`, call `addToHistory(content)` in `doSubmit()` before clearing input, call `handleHistoryNavigation(e, input, setInput)` in `handleKeyDown()` after autocomplete handling and return early if it returns `true`

**Checkpoint**: At this point, User Story 1 should be fully functional — users can navigate history with Up/Down arrows, draft is preserved, cursor is positioned correctly. This is the MVP.

---

## Phase 4: User Story 2 — Persist Message History Across Sessions (Priority: P2)

**Goal**: Message history survives page refresh and browser restart, with bounded storage and consecutive deduplication.

**Independent Test**: Send several messages, refresh the browser, press Up Arrow to verify all previous messages are accessible. Send 101 messages and verify oldest is dropped. Send same message twice consecutively and verify only one entry is stored.

### Implementation for User Story 2

- [ ] T012 [US2] Initialize hook state from persisted storage in `useChatHistory` in `frontend/src/hooks/useChatHistory.ts` — call `loadHistory()` on hook initialization to populate the in-memory history array from localStorage so history is available after page refresh (FR-006)
- [ ] T013 [US2] Verify max-cap enforcement end-to-end in `addToHistory` in `frontend/src/hooks/useChatHistory.ts` — ensure that when history reaches 100 entries (default) and a new message is added, the oldest entry is removed before appending, and the updated array is persisted to localStorage (FR-005)
- [ ] T014 [US2] Verify consecutive deduplication in `addToHistory` in `frontend/src/hooks/useChatHistory.ts` — ensure sending the same message twice in a row results in only one history entry by comparing trimmed new message with `history[history.length - 1]` (FR-007)
- [ ] T015 [US2] Verify graceful degradation when localStorage is unavailable in `frontend/src/utils/chatHistoryStorage.ts` — ensure all storage functions handle exceptions silently, allowing in-memory-only history for the current session (FR-013)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work — history navigation persists across sessions, respects the cap, and deduplicates consecutive messages.

---

## Phase 5: User Story 3 — Multi-Line Input Compatibility (Priority: P2)

**Goal**: Up/Down Arrow keys behave normally for cursor movement within multi-line text, and only trigger history navigation when the cursor is on the first line (Up) or last line (Down).

**Independent Test**: Type a multi-line message using Shift+Enter, verify Up Arrow moves cursor between lines normally when not on the first line, verify history navigation activates only when cursor is on the first line (Up) or last line (Down).

### Implementation for User Story 3

- [ ] T016 [US3] Implement multi-line first-line detection for Up Arrow in `handleHistoryNavigation` in `frontend/src/hooks/useChatHistory.ts` — check if `value.slice(0, selectionStart)` contains `\n`; if yes, return `false` to allow normal cursor movement; if no, proceed with history navigation (FR-008)
- [ ] T017 [US3] Implement multi-line last-line detection for Down Arrow in `handleHistoryNavigation` in `frontend/src/hooks/useChatHistory.ts` — check if `value.slice(selectionEnd)` contains `\n`; if yes, return `false` to allow normal cursor movement; if no, proceed with history navigation (FR-009)

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently — multi-line editing is uninterrupted while history navigation still works from first/last lines.

---

## Phase 6: User Story 4 — Clear Chat History (Priority: P3)

**Goal**: Users can clear their entire message history with a confirmation prompt to prevent accidental deletion.

**Independent Test**: Accumulate history, trigger clear action, verify confirmation dialog appears, confirm and verify history is empty (Up Arrow produces no change), repeat and cancel to verify history remains intact.

### Implementation for User Story 4

- [ ] T018 [US4] Implement `clearHistory()` in `frontend/src/hooks/useChatHistory.ts` — show `window.confirm()` dialog, on confirmation call `clearStoredHistory()` from the storage utility, reset in-memory history array to `[]`, reset navigation index to -1, reset draft to empty string (FR-010)
- [ ] T019 [US4] Add Clear History UI element in `frontend/src/components/chat/ChatInterface.tsx` — add a "Clear History" button or link near the chat input area, wire it to the `clearHistory()` function from the `useChatHistory` hook, ensure it is discoverable but not intrusive

**Checkpoint**: All user stories (1-4) should now be independently functional. Complete history navigation, persistence, multi-line compatibility, and clear functionality.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation.

- [ ] T020 [P] Ensure TypeScript types are strict and exported in `frontend/src/hooks/useChatHistory.ts` — export `UseChatHistoryReturn` interface type for consumers
- [ ] T021 Code cleanup — review all new code for consistency with existing codebase conventions in `frontend/src/hooks/` and `frontend/src/utils/`
- [ ] T022 Run quickstart.md validation — manually walk through all scenarios in `specs/018-chat-history-navigation/quickstart.md` to verify end-to-end functionality
- [ ] T023 [P] Verify no regressions in existing chat functionality — ensure autocomplete, message sending, Shift+Enter multi-line, and other existing ChatInterface behaviors still work correctly

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational phase — delivers MVP
- **User Story 2 (Phase 4)**: Depends on Foundational phase — can start in parallel with US1 (but verifies persistence behaviors built in Foundation)
- **User Story 3 (Phase 5)**: Depends on Foundational phase — can start in parallel with US1/US2
- **User Story 4 (Phase 6)**: Depends on Foundational phase — can start in parallel with US1/US2/US3
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories. This is the MVP.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) — Verifies persistence built in T001-T006. Independent of US1.
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) — Adds multi-line guards to `handleHistoryNavigation`. Independent of US1/US2.
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) — Adds clear functionality. Independent of US1/US2/US3.

### Within Each User Story

- Storage utility before hook logic
- Hook logic before component integration
- Core implementation before edge cases
- Story complete before moving to next priority

### Parallel Opportunities

- T001 and T002 are sequential (T002 depends on T001 exports)
- T003, T004, T005 can run in parallel (different functions in same file, but logically independent)
- Once Foundational phase completes, US1, US2, US3, US4 can start in parallel (different concerns, mostly different code sections)
- T016 and T017 can run in parallel (Up Arrow and Down Arrow detection are independent checks)
- T020 and T023 can run in parallel (different files/concerns)

---

## Parallel Example: User Story 1

```bash
# These User Story 1 tasks must be sequential (each builds on previous):
Task T007: "Implement Up Arrow history navigation in frontend/src/hooks/useChatHistory.ts"
Task T008: "Implement Down Arrow history navigation in frontend/src/hooks/useChatHistory.ts"
Task T009: "Implement cursor positioning at end of restored text in frontend/src/hooks/useChatHistory.ts"
Task T010: "Handle empty history edge case in frontend/src/hooks/useChatHistory.ts"
Task T011: "Integrate useChatHistory hook into frontend/src/components/chat/ChatInterface.tsx"
```

## Parallel Example: User Story 3

```bash
# These User Story 3 tasks can run in parallel (independent multi-line checks):
Task T016: "Implement multi-line first-line detection for Up Arrow"
Task T017: "Implement multi-line last-line detection for Down Arrow"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T002)
2. Complete Phase 2: Foundational (T003-T006)
3. Complete Phase 3: User Story 1 (T007-T011)
4. **STOP and VALIDATE**: Test history navigation with Up/Down arrows, draft preservation, cursor positioning
5. Deploy/demo if ready — core feature is fully usable

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (**MVP!**)
3. Add User Story 2 → Verify persistence across refresh → Deploy/Demo
4. Add User Story 3 → Verify multi-line compatibility → Deploy/Demo
5. Add User Story 4 → Verify clear history with confirmation → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (core navigation + integration)
   - Developer B: User Story 3 (multi-line detection)
3. After US1 integration is done:
   - Developer A: User Story 4 (clear history + UI)
   - Developer B: User Story 2 (persistence verification)
4. All developers: Polish phase

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All source changes are in `frontend/` only — no backend changes required
- No new npm dependencies needed — uses standard browser APIs and existing React/TypeScript stack
- Tests are NOT included (not explicitly requested in spec) — can be added as a follow-up
