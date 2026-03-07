# Tasks: Fix #help Command Auto-Repeat Bug & Add Optimistic Message Rendering in Chat UI

**Input**: Design documents from `/specs/026-chat-help-optimistic-render/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/components.md ✓, quickstart.md ✓

**Tests**: Regression tests are explicitly requested (FR-016, FR-017). Test tasks are included in Phase 7 (US5).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing. All changes are frontend-only — no backend modifications.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `frontend/src/` for all source, `frontend/src/hooks/` for hooks, `frontend/src/components/chat/` for chat UI, `frontend/src/types/` for shared types

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No new project initialization needed — this feature modifies only existing files in an established codebase. Setup phase ensures the shared type foundation is in place.

- [ ] T001 Add `MessageStatus` type export (`'pending' | 'sent' | 'failed'`) and optional `status?: MessageStatus` field to `ChatMessage` interface in `frontend/src/types/index.ts`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core hook-level infrastructure that MUST be complete before any user story UI work can begin. Adds the `retryMessage` function stub and restructures `sendMessage` for optimistic flow.

**⚠️ CRITICAL**: No user story UI work can begin until this phase is complete.

- [ ] T002 Add `retryMessage` function stub (no-op returning `Promise<void>`) to the `useChat` hook return object in `frontend/src/hooks/useChat.ts`
- [ ] T003 Refactor `sendMessage` in `frontend/src/hooks/useChat.ts` to separate command path from regular message path with explicit early return after command dispatch, ensuring no shared mutable state between the two paths

**Checkpoint**: Foundation ready — type changes and hook structure support all user stories.

---

## Phase 3: User Story 1 — Send a Command Without Auto-Repeat (Priority: P1) 🎯 MVP

**Goal**: Fix the critical bug where `#help` (and other hash/slash commands) auto-repeats on subsequent messages due to stale command state surviving dispatch.

**Independent Test**: Send `#help` in the chat, then send a follow-up plain-text message and verify only the plain-text message is dispatched without any command re-injection.

### Implementation for User Story 1

- [ ] T004 [US1] Audit command dispatch path in `sendMessage()` in `frontend/src/hooks/useChat.ts` — ensure `isCommand(content)` is evaluated fresh on each call using only the `content` parameter, with no reference to stored state or previous options
- [ ] T005 [US1] Add defensive clearing of any reply-to context or pending-command references after command execution completes in `sendMessage()` in `frontend/src/hooks/useChat.ts` — reset `localMessages` command entries to prevent re-injection
- [ ] T006 [US1] Verify `doSubmit()` in `frontend/src/components/chat/ChatInterface.tsx` calls `setInput('')` and `resetNavigation()` unconditionally after dispatch, and that the `isCommand` flag from `options` is not stored in any component state or ref

**Checkpoint**: After Phase 3, sending `#help` followed by a normal message dispatches only the normal message. The auto-repeat bug is fixed.

---

## Phase 4: User Story 2 — See Sent Messages Instantly (Priority: P1)

**Goal**: Implement optimistic message rendering — user messages appear in the conversation thread immediately upon submission, before any server response.

**Independent Test**: Send a message and verify it appears in the conversation thread within 100ms of pressing send, before any server response arrives.

### Implementation for User Story 2

- [ ] T007 [US2] Generate a unique temporary ID (e.g., `crypto.randomUUID()` or `Date.now()` prefix) for each optimistic message in `sendMessage()` in `frontend/src/hooks/useChat.ts`
- [ ] T008 [US2] Append an optimistic `ChatMessage` with `status: 'pending'` and the temp ID to `localMessages` state immediately before calling `sendMutation.mutateAsync()` in `frontend/src/hooks/useChat.ts`
- [ ] T009 [US2] Implement server success reconciliation in `sendMessage()` in `frontend/src/hooks/useChat.ts` — on `sendMutation` success, remove the optimistic message from `localMessages` by filtering out the temp ID, then call `queryClient.invalidateQueries()` to refetch server-confirmed messages
- [ ] T010 [US2] Ensure the merged messages array in `useChat.ts` returns `[...serverMessages, ...localMessages]` so optimistic messages appear at the end of the conversation thread in `frontend/src/hooks/useChat.ts`
- [ ] T011 [US2] Verify auto-scroll to bottom triggers after optimistic message is appended by checking `scrollToBottom()` behavior in `frontend/src/components/chat/ChatInterface.tsx`

**Checkpoint**: After Phase 4, user messages appear instantly in the thread upon send. Server-confirmed messages seamlessly replace optimistic ones without duplication.

---

## Phase 5: User Story 3 — See a Thinking Indicator While the Agent Processes (Priority: P1)

**Goal**: Show a visual thinking indicator (animated bouncing dots) below the user's optimistic message while the agent processes, replacing it with the agent's response when complete.

**Independent Test**: Send a message, observe the thinking indicator appears after the sent message, and verify it is replaced by the agent's response when processing completes — with no layout shift.

### Implementation for User Story 3

- [ ] T012 [US3] Verify the existing thinking indicator (three animated bounce dots) in `frontend/src/components/chat/ChatInterface.tsx` renders when `isSending === true` and is positioned after the optimistic user message in the message list
- [ ] T013 [US3] Ensure the thinking indicator occupies the same vertical space as a typical agent response bubble so replacement causes no layout shift, adjusting CSS in `frontend/src/components/chat/ChatInterface.tsx` if needed
- [ ] T014 [US3] Confirm the thinking indicator continues to animate for the full duration of agent processing (no timeout cutoff) by verifying it is purely tied to `isSending` state in `frontend/src/components/chat/ChatInterface.tsx`

**Checkpoint**: After Phase 5, the full send flow is: user message appears instantly → thinking indicator shows → agent response replaces indicator — all without layout shift.

---

## Phase 6: User Story 4 — Handle Failed Messages Gracefully (Priority: P2)

**Goal**: When a message fails to send, the optimistic message remains visible with error styling and a retry option instead of being silently dropped.

**Independent Test**: Simulate a network failure during message send, verify the message is marked as failed with distinct styling, and confirm the retry button resends the message.

### Implementation for User Story 4

- [ ] T015 [US4] Implement error handling in `sendMessage()` in `frontend/src/hooks/useChat.ts` — on `sendMutation` failure, find the optimistic message in `localMessages` by temp ID and update its `status` from `'pending'` to `'failed'`
- [ ] T016 [US4] Implement `retryMessage(messageId: string)` function in `frontend/src/hooks/useChat.ts` — find the failed message in `localMessages`, reset its `status` to `'pending'`, and re-execute `sendMutation.mutateAsync()` with the original content
- [ ] T017 [P] [US4] Add `onRetry?: () => void` prop to `MessageBubbleProps` interface and render failed message styling (red/destructive border accent, error icon, "Failed to send" text, retry button) when `message.status === 'failed'` in `frontend/src/components/chat/MessageBubble.tsx`
- [ ] T018 [US4] Add `onRetryMessage: (messageId: string) => void` prop to `ChatInterfaceProps` and pass `onRetry={() => onRetryMessage(message.message_id)}` to `MessageBubble` for each message in `frontend/src/components/chat/ChatInterface.tsx`
- [ ] T019 [US4] Add `onRetryMessage: (messageId: string) => void` prop to `ChatPopupProps` and pass it through to `ChatInterface` in `frontend/src/components/chat/ChatPopup.tsx`
- [ ] T020 [US4] Wire `retryMessage` from `useChat` hook to `onRetryMessage` prop on the `<ChatPopup>` instance in `frontend/src/layout/AppLayout.tsx`

**Checkpoint**: After Phase 6, failed messages show error styling with a retry button. Clicking retry resends the message. Failed messages don't block subsequent sends.

---

## Phase 7: User Story 5 — Regression Protection for Command State Leaking (Priority: P2)

**Goal**: Automated test coverage that validates command state does not leak across message sends, preventing future regressions.

**Independent Test**: Run the automated test suite and verify all command-state-isolation tests pass.

### Implementation for User Story 5

- [ ] T021 [P] [US5] Add regression test: send `#help` command followed by a normal message — assert the normal message payload contains no command references and `isCommand` is not re-triggered in `frontend/src/hooks/useChat.test.tsx`
- [ ] T022 [P] [US5] Add regression test: send multiple different commands in sequence (`#help`, then `#status`) — assert each command is dispatched independently with no cross-contamination in `frontend/src/hooks/useChat.test.tsx`
- [ ] T023 [P] [US5] Add regression test: verify input field state, reply context, and message queue are fully cleared after command dispatch by checking `localMessages` contains only expected entries in `frontend/src/hooks/useChat.test.tsx`
- [ ] T024 [P] [US5] Add test for optimistic message rendering: call `sendMessage()` with a regular message and assert the message appears in the returned `messages` array with `status: 'pending'` before the mutation resolves in `frontend/src/hooks/useChat.test.tsx`
- [ ] T025 [P] [US5] Add test for failed message retry: simulate a `sendMutation` failure, assert the optimistic message has `status: 'failed'`, call `retryMessage()`, and assert status resets to `'pending'` in `frontend/src/hooks/useChat.test.tsx`

**Checkpoint**: All regression tests pass. Command state isolation and optimistic rendering are validated by automated tests.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Validation, type-checking, linting, and end-to-end verification across all user stories.

- [ ] T026 [P] Run TypeScript type-check with `npx tsc --noEmit` in `frontend/` and fix any type errors
- [ ] T027 [P] Run linter with `npx eslint src/` in `frontend/` and fix any lint violations
- [ ] T028 Run full frontend test suite with `npx vitest run` in `frontend/` and verify all tests pass (existing + new)
- [ ] T029 Perform manual quickstart.md validation: execute all three verification scenarios (bug fix, optimistic rendering, failed message handling) per `specs/026-chat-help-optimistic-render/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (`MessageStatus` type must exist before `retryMessage` stub and `sendMessage` refactor)
- **User Story 1 (Phase 3)**: Depends on Phase 2 (refactored `sendMessage` structure)
- **User Story 2 (Phase 4)**: Depends on Phase 2 (type changes + `sendMessage` structure)
- **User Story 3 (Phase 5)**: Depends on Phase 4 (optimistic message must exist for thinking indicator to appear after it)
- **User Story 4 (Phase 6)**: Depends on Phase 4 (optimistic rendering must exist for failure handling)
- **User Story 5 (Phase 7)**: Depends on Phases 3–6 (tests validate all implemented behaviors)
- **Polish (Phase 8)**: Depends on all prior phases

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 — independent bug fix, no dependency on other stories
- **US2 (P1)**: Can start after Phase 2 — can run in parallel with US1 (different code paths in `sendMessage`)
- **US3 (P1)**: Depends on US2 — thinking indicator must appear after optimistic message
- **US4 (P2)**: Depends on US2 — failure handling applies to optimistic messages
- **US5 (P2)**: Depends on US1–US4 — regression tests validate all implemented behaviors

### Within Each User Story

- Hook logic before UI component changes
- State management before rendering
- Core implementation before integration points
- Story complete and testable before moving to next priority

### Parallel Opportunities

- **Phase 2**: T002 and T003 are sequential (T003 depends on T002's stub)
- **Phase 3 + Phase 4**: US1 (T004–T006) and US2 (T007–T011) can run in parallel — US1 modifies command path, US2 modifies regular message path
- **Phase 6**: T017 (MessageBubble changes) can run in parallel with T015–T016 (hook changes) — different files
- **Phase 7**: All test tasks (T021–T025) can run in parallel — all write to different test blocks in the same file
- **Phase 8**: T026 (type-check) and T027 (lint) can run in parallel

---

## Parallel Example: User Story 1 + User Story 2

```text
# After Phase 2 completes, launch US1 and US2 in parallel:

# Developer A: US1 — Command State Bug Fix
Task T004: Audit command dispatch path in useChat.ts
Task T005: Clear reply-to context after command execution in useChat.ts
Task T006: Verify doSubmit() state clearing in ChatInterface.tsx

# Developer B: US2 — Optimistic Message Rendering
Task T007: Generate unique temp ID for optimistic messages in useChat.ts
Task T008: Append optimistic message to localMessages in useChat.ts
Task T009: Server success reconciliation in useChat.ts
Task T010: Verify merged messages array ordering in useChat.ts
Task T011: Verify auto-scroll behavior in ChatInterface.tsx
```

## Parallel Example: User Story 4

```text
# Within US4, hook work and component work can overlap:

# Track 1: Hook logic (sequential)
Task T015: Error handler — mark message as 'failed' in useChat.ts
Task T016: Implement retryMessage() in useChat.ts

# Track 2: UI components (parallel with Track 1)
Task T017: [P] Failed message styling + retry button in MessageBubble.tsx

# Integration (after both tracks):
Task T018: Wire onRetryMessage in ChatInterface.tsx
Task T019: Pass onRetryMessage in ChatPopup.tsx
Task T020: Wire at top-level integration point
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001) — 1 task
2. Complete Phase 2: Foundational (T002–T003) — 2 tasks
3. Complete Phase 3: User Story 1 (T004–T006) — 3 tasks
4. **STOP and VALIDATE**: Test by sending `#help` then a normal message — the bug is fixed
5. Deploy/demo if ready — the chat is usable again

### Incremental Delivery

1. Setup + Foundational (T001–T003) → Foundation ready
2. Add US1 (T004–T006) → Bug fix deployed → **MVP!** Chat is no longer broken
3. Add US2 (T007–T011) → Messages appear instantly → Responsive UX
4. Add US3 (T012–T014) → Thinking indicator → Complete feedback loop
5. Add US4 (T015–T020) → Failed messages handled → Robust error UX
6. Add US5 (T021–T025) → Regression tests → Future-proofed
7. Polish (T026–T029) → Clean, validated, shippable

### Task Summary

| Phase | Story | Task Count | Parallelizable |
|-------|-------|-----------|----------------|
| Phase 1: Setup | — | 1 | 0 |
| Phase 2: Foundational | — | 2 | 0 |
| Phase 3: US1 | P1 | 3 | 0 |
| Phase 4: US2 | P1 | 5 | 0 |
| Phase 5: US3 | P1 | 3 | 0 |
| Phase 6: US4 | P2 | 6 | 1 (T017) |
| Phase 7: US5 | P2 | 5 | 5 (all) |
| Phase 8: Polish | — | 4 | 2 (T026, T027) |
| **Total** | | **29** | **8** |

---

## Notes

- All changes are frontend-only — no backend API changes required
- No new npm dependencies — uses existing React, TanStack Query, Tailwind, lucide-react
- No new files created — all modifications are in-place to existing files (~6 files)
- The `ChatMessage.status` field is optional to maintain backward compatibility with server-returned messages
- Optimistic messages use `localMessages` state (already exists) — no new state management patterns
- The thinking indicator already exists (three animated dots); the change ensures it appears *after* the optimistic message
- [P] tasks = different files, no dependencies on incomplete tasks in the same phase
- Commit after each task or logical group
- Stop at any checkpoint to validate the story independently
