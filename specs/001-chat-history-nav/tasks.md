# Tasks: Chat History Navigation

**Input**: Design documents from `/specs/001-chat-history-nav/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Not requested in feature specification. Hook is designed for independent testability if tests are requested later.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `frontend/src/` for source code, `frontend/tests/` for tests (optional)

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create project structure and hook file with configuration constants and type definitions

- [ ] T001 Create `useChatHistory` hook file with exported constants (`MAX_HISTORY_SIZE`, `STORAGE_KEY`), option and return type interfaces per contract in `frontend/src/hooks/useChatHistory.ts`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core hook state management skeleton and initial ChatInterface integration that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002 Implement core hook skeleton with `useState` for history array, `useRef` for navigation index and draft buffer, and `resetNavigation` function in `frontend/src/hooks/useChatHistory.ts`
- [ ] T003 Implement empty `handleKeyDown` function signature (returns `null` for all events initially) and expose `isNavigating` boolean state in `frontend/src/hooks/useChatHistory.ts`
- [ ] T004 Import `useChatHistory` hook and call it in the component — destructure `handleKeyDown` (renamed to `handleHistoryKeyDown` to avoid collision with existing handler) and `isNavigating` in `frontend/src/components/chat/ChatInterface.tsx`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Navigate Backward Through Sent Messages (Priority: P1) 🎯 MVP

**Goal**: Users can press Up Arrow in the chat input to step backward through previously sent messages, populating the input with each historical message in reverse chronological order.

**Independent Test**: Send messages "Hello", "How are you?", "Goodbye". Press Up Arrow once → input shows "Goodbye". Press Up Arrow again → input shows "How are you?". Press Up Arrow again → input shows "Hello". Press Up Arrow again → input stays on "Hello" (no wrap). With empty history, Up Arrow does nothing.

### Implementation for User Story 1

- [ ] T005 [US1] Implement `addToHistory(message)` function with capacity cap (`MAX_HISTORY_SIZE`) and oldest-entry eviction in `frontend/src/hooks/useChatHistory.ts`
- [ ] T006 [US1] Implement ArrowUp handling in `handleKeyDown` — decrement navigation index, return history entry at new index, call `preventDefault()`, check cursor position is at start of input or input is empty (FR-002, FR-011, FR-013) in `frontend/src/hooks/useChatHistory.ts`
- [ ] T007 [US1] Wire hook's `handleKeyDown` (destructured as `handleHistoryKeyDown`) into existing `handleKeyDown` function — insert call after autocomplete logic and before Enter key handling, update input state when non-null value returned in `frontend/src/components/chat/ChatInterface.tsx`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Navigate Forward and Restore Draft (Priority: P1)

**Goal**: Users can press Down Arrow to step forward through history toward the most recent entry, and pressing Down past the newest entry restores any in-progress draft text.

**Independent Test**: Type "Hey there" in input. Press Up Arrow (shows most recent history message). Press Down Arrow → input restores "Hey there". With empty draft before navigating, Down Arrow past newest restores empty string. Down Arrow at draft position does nothing.

### Implementation for User Story 2

- [ ] T008 [US2] Implement draft buffer capture — save current input value to `draftRef` when navigation index transitions from draft position (`history.length`) to history on first ArrowUp press in `frontend/src/hooks/useChatHistory.ts`
- [ ] T009 [US2] Implement ArrowDown handling in `handleKeyDown` — increment navigation index, return history entry or restore draft buffer when index reaches `history.length`, call `preventDefault()`, check cursor is at end of input (FR-003, FR-011, FR-014) in `frontend/src/hooks/useChatHistory.ts`
- [ ] T010 [US2] Update `isNavigating` state to return `true` when navigation index is less than `history.length` (browsing history) and `false` when at draft position in `frontend/src/hooks/useChatHistory.ts`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently — full Up/Down Arrow navigation with draft preservation

---

## Phase 5: User Story 3 - Persist History Across Sessions (Priority: P2)

**Goal**: Chat message history is persisted to localStorage so it survives page refreshes and browser session restores, with graceful degradation when storage is unavailable.

**Independent Test**: Send messages "Alpha" and "Beta". Refresh the page. Press Up Arrow → input shows "Beta". Close browser tab and reopen → history is still available. In private browsing mode → history works in-session but does not persist (no errors shown).

### Implementation for User Story 3

- [ ] T011 [US3] Implement localStorage loading on hook mount — read from `STORAGE_KEY`, parse JSON, validate as string array, fallback to empty array on parse error or invalid data, wrap in try-catch for unavailable storage in `frontend/src/hooks/useChatHistory.ts`
- [ ] T012 [US3] Implement localStorage sync via `useEffect` — write history array to `STORAGE_KEY` on every history state change, wrap in try-catch to silently handle write failures (quota exceeded, private browsing) in `frontend/src/hooks/useChatHistory.ts`
- [ ] T013 [US3] Support configurable `storageKey` option from `UseChatHistoryOptions` — use `options.storageKey ?? STORAGE_KEY` for localStorage operations to enable per-room or per-user namespacing in `frontend/src/hooks/useChatHistory.ts`

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work — history navigation persists across page refreshes

---

## Phase 6: User Story 4 - Send Recalled or Edited Historical Message (Priority: P2)

**Goal**: Users can recall a historical message via Up Arrow, optionally edit it, and send it as a new message. Edits to recalled messages do NOT overwrite the original stored history entry — only successfully sent messages are recorded.

**Independent Test**: Recall "Hello" via Up Arrow. Send without editing → "Hello" is sent, pointer resets. Recall "Hello", edit to "Hello World", send → "Hello World" added as new entry, original "Hello" unchanged in history. Recall and edit but don't send, navigate away → original history entry unchanged.

### Implementation for User Story 4

- [ ] T014 [US4] Destructure `addToHistory` from `useChatHistory` hook and call `addToHistory(content)` in `doSubmit` function before `onSendMessage()` call — ensures every successfully sent message (including recalled/edited ones) is appended to history in `frontend/src/components/chat/ChatInterface.tsx`
- [ ] T015 [US4] Ensure `addToHistory` resets navigation pointer to new draft position (`history.length` after append) and clears draft buffer — guarantees history immutability and clean state after send in `frontend/src/hooks/useChatHistory.ts`

**Checkpoint**: At this point, User Stories 1–4 should all work — full send/recall/edit cycle with history immutability

---

## Phase 7: User Story 5 - Deduplicate Consecutive Identical Messages (Priority: P3)

**Goal**: Consecutive duplicate messages are stored only once in history, keeping history clean and navigation efficient while preserving non-consecutive duplicates.

**Independent Test**: Send "Hello" three times consecutively → Up Arrow shows only one "Hello". Send "Hello", "World", "Hello" → all three entries appear (non-consecutive duplicates preserved).

### Implementation for User Story 5

- [ ] T016 [US5] Add consecutive duplicate check in `addToHistory` — compare new message with `history[history.length - 1]` using strict string equality, skip append if identical (FR-009) in `frontend/src/hooks/useChatHistory.ts`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Edge case hardening, multiline input support, and final validation

- [ ] T017 Ensure ArrowUp cursor position check handles multiline inputs — only activate history navigation when `selectionStart === 0` (cursor at very beginning) per FR-013 in `frontend/src/hooks/useChatHistory.ts`
- [ ] T018 Ensure ArrowDown cursor position check handles multiline inputs — only activate history navigation when `selectionStart === currentInput.length` (cursor at very end) per FR-014 in `frontend/src/hooks/useChatHistory.ts`
- [ ] T019 Validate `maxSize` option from `UseChatHistoryOptions` — use `options.maxSize ?? MAX_HISTORY_SIZE` and ensure it is applied in `addToHistory` eviction logic in `frontend/src/hooks/useChatHistory.ts`
- [ ] T020 Run quickstart.md manual validation — start dev server, send messages, test Up/Down Arrow navigation, test draft preservation, test page refresh persistence, test consecutive dedup per `specs/001-chat-history-nav/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational phase completion
- **User Story 2 (Phase 4)**: Depends on User Story 1 (ArrowDown builds on ArrowUp navigation index logic)
- **User Story 3 (Phase 5)**: Depends on Foundational phase (localStorage is independent of navigation logic)
- **User Story 4 (Phase 6)**: Depends on User Story 1 (requires addToHistory and navigation to exist)
- **User Story 5 (Phase 7)**: Depends on User Story 1 (requires addToHistory to exist)
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P1)**: Depends on User Story 1 — draft buffer capture occurs during ArrowUp handling implemented in US1
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) — localStorage is orthogonal to navigation; can proceed in parallel with US1/US2 if desired
- **User Story 4 (P2)**: Depends on User Story 1 — requires `addToHistory` function and navigation pointer reset
- **User Story 5 (P3)**: Depends on User Story 1 — requires `addToHistory` function to add dedup check

### Within Each User Story

- Models/state management before event handlers
- Event handlers before UI integration
- Core implementation before edge case handling
- Story complete before moving to next priority

### Parallel Opportunities

- T002 and T003 can run in parallel within Phase 2 (different concerns in same file, no dependencies)
- US3 (localStorage persistence) can start in parallel with US1/US2 since it operates on different code paths
- T017 and T018 can run in parallel within Phase 8 (independent cursor position checks)

---

## Parallel Example: User Story 1

```bash
# T005 and T006 are sequential (addToHistory must exist before handleKeyDown uses it)
# T007 depends on T006 (ChatInterface integration depends on hook implementation)

# However, US3 tasks can proceed in parallel with US1:
Task: "T005 [US1] Implement addToHistory in frontend/src/hooks/useChatHistory.ts"
Task: "T011 [US3] Implement localStorage loading in frontend/src/hooks/useChatHistory.ts"  # Parallel with US1
```

---

## Parallel Example: Polish Phase

```bash
# These cursor position checks are independent:
Task: "T017 ArrowUp multiline cursor check in frontend/src/hooks/useChatHistory.ts"
Task: "T018 ArrowDown multiline cursor check in frontend/src/hooks/useChatHistory.ts"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 2: Foundational (T002–T004)
3. Complete Phase 3: User Story 1 (T005–T007)
4. **STOP and VALIDATE**: Send messages, press Up Arrow, verify messages appear in reverse chronological order
5. Deploy/demo if ready — core value proposition is delivered

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test Up Arrow navigation → Deploy/Demo (MVP!)
3. Add User Story 2 → Test Down Arrow + draft restoration → Deploy/Demo
4. Add User Story 3 → Test page refresh persistence → Deploy/Demo
5. Add User Story 4 → Test send recalled/edited messages → Deploy/Demo
6. Add User Story 5 → Test consecutive dedup → Deploy/Demo
7. Each story adds value without breaking previous stories

### File Change Summary

| File | Action | Stories |
|------|--------|---------|
| `frontend/src/hooks/useChatHistory.ts` | NEW | All (US1–US5) |
| `frontend/src/components/chat/ChatInterface.tsx` | MODIFY | US1 (T007), US4 (T014) |

### Total Tasks: 20

| Phase | Task Count | Tasks |
|-------|------------|-------|
| Phase 1: Setup | 1 | T001 |
| Phase 2: Foundational | 3 | T002–T004 |
| Phase 3: US1 (P1) | 3 | T005–T007 |
| Phase 4: US2 (P1) | 3 | T008–T010 |
| Phase 5: US3 (P2) | 3 | T011–T013 |
| Phase 6: US4 (P2) | 2 | T014–T015 |
| Phase 7: US5 (P3) | 1 | T016 |
| Phase 8: Polish | 4 | T017–T020 |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Tests not included (not requested in specification); hook design supports independent unit testing if added later
- Only 2 files are affected: 1 new (`useChatHistory.ts`), 1 modified (`ChatInterface.tsx`)
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
