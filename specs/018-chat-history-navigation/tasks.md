# Tasks: Chat Message History Navigation with Up Arrow Key

**Input**: Design documents from `/specs/018-chat-history-navigation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Not explicitly requested in feature specification. Test tasks are omitted per Test Optionality principle. The `useChatHistory` hook is test-friendly and tests can be added later if desired.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- This feature is frontend-only — all changes in `frontend/src/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the new hook file and establish project structure for the feature

- [x] T001 Create `useChatHistory` hook file with minimal scaffolding (empty function, placeholder return object) in `frontend/src/hooks/useChatHistory.ts`
- [x] T002 [P] Verify existing imports and dependencies are available (React 18.3, Lucide React `History` icon, Tailwind CSS utilities) — no new packages needed

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core hook infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 Implement `UseChatHistoryOptions` and `UseChatHistoryReturn` interfaces in `frontend/src/hooks/useChatHistory.ts` per the contract in `specs/018-chat-history-navigation/contracts/useChatHistory-api.md`
- [x] T004 Implement localStorage load logic in `useChatHistory` hook: read from key `chat-message-history`, parse JSON, return `string[]`, fallback to `[]` on error — in `frontend/src/hooks/useChatHistory.ts`
- [x] T005 Implement localStorage save logic in `useChatHistory` hook: serialize history array to JSON, write to key `chat-message-history`, silently catch errors — in `frontend/src/hooks/useChatHistory.ts`
- [x] T006 Implement core hook state: `history` (useState, initialized from localStorage), `historyIndex` (useState, initialized to -1), `draftBuffer` (useRef<string>) — in `frontend/src/hooks/useChatHistory.ts`
- [x] T007 Implement `addToHistory(message: string)` method: append message to history array, enforce max 100 cap by removing oldest, persist to localStorage, reset historyIndex to -1 — in `frontend/src/hooks/useChatHistory.ts`
- [x] T008 Implement `resetNavigation()` method: set historyIndex to -1, clear draftBuffer ref — in `frontend/src/hooks/useChatHistory.ts`
- [x] T009 Export `useChatHistory` hook function with the `UseChatHistoryReturn` interface from `frontend/src/hooks/useChatHistory.ts`

**Checkpoint**: Foundation ready — hook is importable and has core state management + localStorage persistence. User story implementation can now begin.

---

## Phase 3: User Story 1 — Recall Previous Messages with Up Arrow (Priority: P1) 🎯 MVP

**Goal**: Users can press the up arrow key in the chat input to cycle backwards through previously sent messages (most recent first)

**Independent Test**: Send 3+ messages, then press the up arrow key repeatedly and verify the input field is populated with each previous message in reverse chronological order. Pressing up at the oldest message keeps the oldest message displayed.

### Implementation for User Story 1

- [x] T010 [US1] Implement `navigateUp(currentInput: string)` method in `useChatHistory` hook: on first call (historyIndex === -1) capture currentInput to draftBuffer ref and set historyIndex to 0; on subsequent calls increase historyIndex by 1 (capped at history.length - 1) to step toward older messages; return `history[history.length - 1 - historyIndex]` or null if no history — in `frontend/src/hooks/useChatHistory.ts`
- [x] T011 [US1] Import `useChatHistory` hook in `ChatInterface` component and destructure all returned methods/properties (`navigateUp`, `navigateDown`, `addToHistory`, `resetNavigation`, `isNavigating`, `history`, `selectFromHistory`); note: the hook exports stubs for all methods from T009 so all destructured names are safe even before later stories implement them — in `frontend/src/components/chat/ChatInterface.tsx`
- [x] T012 [US1] Add ArrowUp history navigation to `handleKeyDown` in `ChatInterface.tsx`: after the autocomplete guard block and before Enter-to-submit, check `e.key === 'ArrowUp'` when autocomplete is NOT active, verify cursor is on first line via `(input.indexOf('\n') === -1 || selectionStart <= input.indexOf('\n'))`, call `navigateUp(input)`, if result is non-null call `e.preventDefault()` and `setInput(result)` — in `frontend/src/components/chat/ChatInterface.tsx`
- [x] T013 [US1] Integrate `addToHistory(trimmed)` and `resetNavigation()` calls into `doSubmit` function, placed before `onSendMessage()` and `setInput('')` — in `frontend/src/components/chat/ChatInterface.tsx`

**Checkpoint**: At this point, User Story 1 should be fully functional — users can send messages and recall them with the up arrow key.

---

## Phase 4: User Story 2 — Navigate Forward with Down Arrow and Restore Draft (Priority: P1)

**Goal**: Users can press the down arrow key to step forward toward more recent messages, and pressing down past the most recent message restores any in-progress draft

**Independent Test**: Type a draft message, press up arrow to enter history navigation, then press down arrow until the draft is restored in the input field. Also verify that pressing down when not navigating does nothing.

### Implementation for User Story 2

- [x] T014 [US2] Implement `navigateDown()` method in `useChatHistory` hook: decrement historyIndex; when reaching -1, return draftBuffer value (restoring draft); return the corresponding history message or null if not navigating — in `frontend/src/hooks/useChatHistory.ts`
- [x] T015 [US2] Add ArrowDown history navigation to `handleKeyDown` in `ChatInterface.tsx`: check `e.key === 'ArrowDown'` when autocomplete is NOT active and `isNavigating` is true, verify cursor is on last line via `(input.indexOf('\n') === -1 || selectionStart > input.lastIndexOf('\n'))`, call `navigateDown()`, if result is non-null call `e.preventDefault()` and `setInput(result)` — in `frontend/src/components/chat/ChatInterface.tsx`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work — full up/down navigation with draft preservation.

---

## Phase 5: User Story 3 — Persist Chat History Across Sessions (Priority: P2)

**Goal**: Message history survives page refreshes and new sessions via localStorage persistence

**Independent Test**: Send several messages, refresh the page, then press the up arrow key and verify previously sent messages from the prior session are still available. Also verify that exceeding 100 messages causes the oldest to be discarded.

### Implementation for User Story 3

- [x] T016 [US3] Verify and harden history cap enforcement in `addToHistory`: ensure that when `history.length >= 100`, the oldest entry (index 0) is removed before appending the new message — in `frontend/src/hooks/useChatHistory.ts`
- [x] T017 [US3] Implement graceful localStorage degradation: wrap all `localStorage.getItem` and `localStorage.setItem` calls in try-catch blocks so that in-session history navigation works even when storage is unavailable (e.g., private browsing mode) — in `frontend/src/hooks/useChatHistory.ts`

**Checkpoint**: History persists across sessions and degrades gracefully when localStorage is unavailable.

---

## Phase 6: User Story 4 — Cursor Positioning on Recalled Messages (Priority: P2)

**Goal**: When a historical message is recalled via arrow key navigation, the text cursor is positioned at the end of the message text

**Independent Test**: Press the up arrow to recall a message and verify the cursor (caret) is positioned at the very end of the text. Navigate through multiple entries and confirm cursor is repositioned each time.

### Implementation for User Story 4

- [x] T018 [US4] Add a `useEffect` in `ChatInterface.tsx` that watches for input changes triggered by history navigation (use `isNavigating` as a dependency): when `isNavigating` is true and `inputRef.current` exists, set `inputRef.current.selectionStart` and `inputRef.current.selectionEnd` to the end of the input value — in `frontend/src/components/chat/ChatInterface.tsx`

**Checkpoint**: Cursor is correctly positioned at end of text when navigating history.

---

## Phase 7: User Story 5 — Visual Feedback During History Navigation (Priority: P2)

**Goal**: A subtle visual indicator on the chat input field distinguishes history-navigation mode from normal typing

**Independent Test**: Press the up arrow to enter history navigation mode and verify a visual indicator (left border accent + background tint) appears on the textarea. Press down past the most recent message to exit history mode and verify the indicator disappears. Send a recalled message and verify the indicator is removed.

### Implementation for User Story 5

- [x] T019 [US5] Add conditional Tailwind CSS classes to the textarea element: when `isNavigating` is true, apply `border-l-4 border-l-primary bg-primary/5` to the existing className — in `frontend/src/components/chat/ChatInterface.tsx`

**Checkpoint**: Visual feedback clearly indicates when the user is browsing history vs. composing a new message.

---

## Phase 8: User Story 6 — Mobile/Touch-Friendly History Access (Priority: P3)

**Goal**: An accessible history button allows mobile/touch users to browse and select past messages without a physical keyboard

**Independent Test**: Tap the history button near the chat input and verify a scrollable popover/dropdown appears listing past messages. Tap a message to populate the input field. Verify the button is hidden or disabled when no history exists. Verify an empty-state message when there is no history.

### Implementation for User Story 6

- [x] T020 [US6] Implement `selectFromHistory(index: number, currentInput: string)` method in `useChatHistory` hook: save currentInput to draftBuffer if not already navigating, set historyIndex to map to the given array index, return `history[index]` or null if index is invalid — in `frontend/src/hooks/useChatHistory.ts`
- [x] T021 [US6] Add a history button (Lucide React `History` icon) adjacent to the textarea in the form area, visible only when `history.length > 0`, with `aria-label="Message history"` and `type="button"` — in `frontend/src/components/chat/ChatInterface.tsx`
- [x] T022 [US6] Add local state `showHistoryPopover` (boolean) to `ChatInterface.tsx` and toggle it on history button click — in `frontend/src/components/chat/ChatInterface.tsx`
- [x] T023 [US6] Implement history popover UI: a scrollable dropdown positioned near the history button, listing `history` array entries (most recent first), each entry clickable to call `selectFromHistory(index, input)` and set the input field — in `frontend/src/components/chat/ChatInterface.tsx`
- [x] T024 [US6] Add empty-state message in the history popover when `history.length === 0`, e.g., "No message history yet" — in `frontend/src/components/chat/ChatInterface.tsx`
- [x] T025 [US6] Dismiss the history popover when a message is selected, when the user clicks outside, or when a message is sent — in `frontend/src/components/chat/ChatInterface.tsx`

**Checkpoint**: Mobile and touch-device users can access message history through the button alternative.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T026 Ensure history navigation does not fire when chat input is not focused (ArrowUp/Down interception only applies inside the textarea's onKeyDown) — verify in `frontend/src/components/chat/ChatInterface.tsx`
- [x] T027 Ensure that editing a recalled message and navigating away with up/down discards the edit (original history is unchanged) — verify behavior in `frontend/src/hooks/useChatHistory.ts`
- [x] T028 Ensure duplicate messages are stored as separate history entries (identical content creates a new entry) — verify in `frontend/src/hooks/useChatHistory.ts`
- [x] T029 [P] Run quickstart.md manual validation scenarios from `specs/018-chat-history-navigation/quickstart.md`
- [x] T030 [P] Code cleanup: remove any unused imports, ensure consistent code style with existing codebase patterns

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup (T001) — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational phase completion (T003–T009)
- **US2 (Phase 4)**: Depends on US1 (Phase 3) — navigateDown complements navigateUp; doSubmit integration in T013
- **US3 (Phase 5)**: Depends on Foundational phase (T004–T005 provide base); can run in parallel with US1/US2 for cap/hardening
- **US4 (Phase 6)**: Depends on US1 (Phase 3) — cursor positioning relies on history navigation being functional
- **US5 (Phase 7)**: Depends on US1 (Phase 3) — visual feedback relies on `isNavigating` being wired
- **US6 (Phase 8)**: Depends on Foundational phase; can run in parallel with other stories but practically benefits from US1/US2 being complete
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — no dependencies on other stories
- **User Story 2 (P1)**: Depends on US1 integration (T011, T013 provide hook wiring + doSubmit changes)
- **User Story 3 (P2)**: Can start after Foundational — hardens existing localStorage logic independently
- **User Story 4 (P2)**: Depends on US1 — needs `isNavigating` and `inputRef` wired
- **User Story 5 (P2)**: Depends on US1 — needs `isNavigating` wired to component
- **User Story 6 (P3)**: Can start after Foundational — adds independent UI; benefits from hook being complete

### Within Each User Story

- Hook logic before component integration
- Core implementation before polish
- Story complete before moving to next priority

### Parallel Opportunities

- T001 and T002 can run in parallel (Setup phase)
- T003, T004, T005, T006 are sequential within the hook but T002 is independent
- US3 (T016–T017) can run in parallel with US4 (T018) and US5 (T019) after US1 is complete
- US6 tasks T020–T025 are mostly sequential within the story but the entire story can be developed in parallel with US3–US5
- All Polish tasks marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# After Foundational phase is complete:

# Hook implementation (sequential within hook):
Task T010: Implement navigateUp in frontend/src/hooks/useChatHistory.ts

# Component integration (sequential, depends on T010):
Task T011: Import and wire useChatHistory in frontend/src/components/chat/ChatInterface.tsx
Task T012: Add ArrowUp handling in handleKeyDown in frontend/src/components/chat/ChatInterface.tsx
Task T013: Integrate addToHistory/resetNavigation in doSubmit in frontend/src/components/chat/ChatInterface.tsx
```

## Parallel Example: P2 User Stories (after US1 + US2 complete)

```bash
# These three stories can run in parallel (different concerns, same files but different sections):
# Developer A: US3 — localStorage hardening
Task T016: Harden history cap in frontend/src/hooks/useChatHistory.ts
Task T017: Graceful localStorage degradation in frontend/src/hooks/useChatHistory.ts

# Developer B: US4 + US5 — UX polish in ChatInterface
Task T018: Cursor positioning useEffect in frontend/src/components/chat/ChatInterface.tsx
Task T019: Visual feedback classes in frontend/src/components/chat/ChatInterface.tsx
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup (T001–T002)
2. Complete Phase 2: Foundational (T003–T009)
3. Complete Phase 3: User Story 1 — Up Arrow Recall (T010–T013)
4. Complete Phase 4: User Story 2 — Down Arrow + Draft Restore (T014–T015)
5. **STOP and VALIDATE**: Test full up/down navigation with draft preservation
6. Deploy/demo if ready — this is the core feature value

### Incremental Delivery

1. Complete Setup + Foundational → Hook is ready
2. Add US1 + US2 → Test up/down navigation → Deploy (MVP!)
3. Add US3 → Test persistence across page refresh → Deploy
4. Add US4 + US5 → Test cursor positioning + visual feedback → Deploy
5. Add US6 → Test mobile history button → Deploy
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 → User Story 2 (sequential, tightly coupled)
   - Developer B: User Story 3 (localStorage hardening, independent)
3. After US1+US2 complete:
   - Developer A: User Story 4 + 5 (UX polish)
   - Developer B: User Story 6 (mobile access)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Tests not included (not requested in spec) — hook design supports easy unit testing with vitest if added later
- No new npm packages required — uses existing React 18.3, Tailwind CSS 3.4, Lucide React
- All changes are frontend-only — no backend modifications needed
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
