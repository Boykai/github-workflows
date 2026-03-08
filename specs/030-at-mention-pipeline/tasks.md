# Tasks: @ Mention in Chat to Select Agent Pipeline Configuration

**Input**: Design documents from `/specs/030-at-mention-pipeline/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Not explicitly requested in the feature specification. Existing tests should continue to pass.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add shared TypeScript types and backend model changes that multiple user stories depend on.

- [ ] T001 Add `MentionToken`, `MentionInputState`, and `MentionFilterResult` interfaces and extend `ChatMessageRequest` with optional `pipeline_id` field in `frontend/src/types/index.ts`
- [ ] T002 [P] Add optional `pipeline_id: str | None = Field(default=None, ...)` field to `ChatMessageRequest` Pydantic model in `backend/src/models/chat.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Backend endpoint changes and new frontend components/hook that MUST be complete before user story integration can begin.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T003 Update `send_message` handler in `backend/src/api/chat.py` to read `pipeline_id` from `ChatMessageRequest`, validate the referenced pipeline exists when provided (return 400 if not found), and pass `pipeline_id` to the issue creation flow to override the project's default pipeline assignment
- [ ] T004 [P] Create `MentionToken` component in `frontend/src/components/chat/MentionToken.tsx` — render a `<span>` with `contentEditable="false"`, `data-pipeline-id`, and `data-pipeline-name` attributes; implement both valid (blue chip: `bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200`) and invalid (amber/red chip) visual states controlled by `isValid` prop; displays `@[pipeline name]` text (T017 later adds dynamic re-validation styling details)
- [ ] T005 [P] Create `MentionAutocomplete` component in `frontend/src/components/chat/MentionAutocomplete.tsx` — floating dropdown with ARIA `role="listbox"` following `CommandAutocomplete.tsx` pattern; display pipeline name and optional description per item; keyboard navigation (ArrowUp/ArrowDown to highlight, Enter/Tab to select, Escape to dismiss); mouse hover/click support; scrollable list capped at 10 visible items; empty state ("No pipelines found"), loading skeleton, and error state ("Unable to load pipelines")
- [ ] T006 [P] Create `PipelineIndicator` component in `frontend/src/components/chat/PipelineIndicator.tsx` — hidden when no @mention is present; shows "Using pipeline: [name]" badge when a valid pipeline is mentioned; shows info tooltip "Multiple pipelines mentioned — using last" when `hasMultipleMentions` is true; shows warning badge "Pipeline not found" when only invalid mentions exist
- [ ] T007 [P] Create `MentionInput` component in `frontend/src/components/chat/MentionInput.tsx` — `contentEditable` div replacing the textarea; detect `@` trigger condition (preceded by space, newline, or at position 0); insert mention tokens as `<span contentEditable="false">` elements; handle backspace into a token by removing the entire token as a single unit; fire `onSubmit` on Enter (without Shift); fire `onNavigateHistory` on ArrowUp/ArrowDown when cursor is at start/end; auto-resize behavior matching current textarea; expose `focus()` and `clear()` via ref
- [ ] T008 Create `useMentionAutocomplete` hook in `frontend/src/hooks/useMentionAutocomplete.ts` — fetch `pipelinesApi.list(projectId)` via TanStack Query (lazy on first `@` trigger, `staleTime: 30_000`); client-side case-insensitive filtering with 150ms debounce; keyboard navigation state management; token insertion/removal lifecycle; active pipeline tracking (last valid mention's ID); `validateTokens()` to re-check all tokens before submit; `getSubmissionPipelineId()` to return the pipeline ID for submission; `reset()` to clear state after successful send

**Checkpoint**: All new components and hook are created. Backend accepts `pipeline_id`. Integration into ChatInterface can now begin.

---

## Phase 3: User Story 1 — @ Mention Autocomplete for Pipeline Selection (Priority: P1) 🎯 MVP

**Goal**: Enable users to type `@` in the chat input to trigger an autocomplete dropdown listing saved Agent Pipeline configurations, filter by typing, and select a pipeline to insert a visually distinct @mention token.

**Independent Test**: Type `@` in the chat input → autocomplete dropdown appears with pipeline names → type additional characters to filter → select via keyboard (Arrow+Enter) or mouse click → pipeline inserted as styled chip token. Press Escape → dropdown closes, `@` remains as plain text. Backspace into token → entire token removed. No saved pipelines → "No pipelines found" empty state.

### Implementation for User Story 1

- [ ] T009 [US1] Integrate `MentionInput` into `ChatInterface` in `frontend/src/components/chat/ChatInterface.tsx` — replace the existing `<textarea>` with `<MentionInput>` component; wire `onTextChange`, `onMentionTrigger`, `onMentionDismiss`, `onTokenRemove`, `onSubmit`, `onNavigateHistory`, and `onKeyDown` props; preserve all existing textarea functionality (placeholder, disabled state, auto-focus)
- [ ] T010 [US1] Integrate `MentionAutocomplete` overlay into `ChatInterface` in `frontend/src/components/chat/ChatInterface.tsx` — render `<MentionAutocomplete>` as a sibling overlay alongside existing `CommandAutocomplete`; wire to `useMentionAutocomplete` hook state (`filteredPipelines`, `highlightedIndex`, `isLoadingPipelines`, `isAutocompleteOpen`); ensure only one autocomplete (slash-command or @mention) is open at a time
- [ ] T011 [US1] Wire `useMentionAutocomplete` hook into `ChatInterface` in `frontend/src/components/chat/ChatInterface.tsx` — initialize hook with `projectId` and `inputRef`; connect hook handlers to `MentionInput` and `MentionAutocomplete` props; call `reset()` after successful message send

**Checkpoint**: At this point, User Story 1 should be fully functional — users can type `@`, see the dropdown, filter, select a pipeline, and see it as a styled token in the input. Token deletion works atomically.

---

## Phase 4: User Story 2 — Pipeline-Aware GitHub Issue Creation (Priority: P1)

**Goal**: When a chat message containing a valid @mentioned pipeline is submitted, the system uses that pipeline's configuration for GitHub Issue creation instead of the project's default.

**Independent Test**: Compose a chat message with an @mentioned pipeline → submit → verify the backend receives `pipeline_id` and uses the referenced pipeline for issue creation. Submit without @mention → default pipeline behavior preserved. Submit with a deleted pipeline → clear error message displayed, submission blocked.

### Implementation for User Story 2

- [ ] T012 [US2] Update `doSubmit` function in `ChatInterface` in `frontend/src/components/chat/ChatInterface.tsx` — before sending, call `getSubmissionPipelineId()` from the `useMentionAutocomplete` hook; include the returned `pipeline_id` in the `onSendMessage` callback options; strip mention token HTML from the content string before sending plain text to backend
- [ ] T013 [US2] Update `onSendMessage` callback signature and its consumers in `frontend/src/components/chat/ChatInterface.tsx` — extend the options parameter to accept `pipelineId?: string`; update the API call that sends `ChatMessageRequest` to include `pipeline_id` from the options when present
- [ ] T014 [US2] Add submission-time validation in `ChatInterface` in `frontend/src/components/chat/ChatInterface.tsx` — before submit, call `validateTokens()` from the hook; if all tokens are invalid, block submission and display a clear error message ("Pipeline not found — please select a valid pipeline"); if some are valid and some invalid, proceed with last valid and show a transient warning

**Checkpoint**: At this point, User Stories 1 AND 2 should both work — users can mention a pipeline and the correct pipeline ID is sent to the backend for issue creation.

---

## Phase 5: User Story 3 — Active Pipeline Visual Indicator (Priority: P2)

**Goal**: Display a contextual indicator near the submit button showing which pipeline configuration is active when a valid @mention is present.

**Independent Test**: Insert an @mention token → "Using pipeline: [name]" badge appears near the submit button. Remove the @mention → indicator disappears. Replace with a different @mention → indicator updates to the new name.

### Implementation for User Story 3

- [ ] T015 [US3] Integrate `PipelineIndicator` into `ChatInterface` in `frontend/src/components/chat/ChatInterface.tsx` — render `<PipelineIndicator>` between the input area and the submit button row; wire `activePipelineName`, `hasMultipleMentions`, and `hasInvalidMentions` props from the `useMentionAutocomplete` hook state

**Checkpoint**: At this point, the active pipeline indicator correctly reflects the selected pipeline in real time.

---

## Phase 6: User Story 4 — Invalid Pipeline Warning State (Priority: P2)

**Goal**: Render unresolved or invalid @mentions with a warning visual state and prevent submission with only invalid mentions.

**Independent Test**: Type `@nonexistent-pipeline` manually (without selecting from dropdown) → warning visual state appears on the text. Attempt to submit with only invalid mention → submission blocked with error message. A previously valid mention whose pipeline was deleted → token updates to show warning state.

### Implementation for User Story 4

- [ ] T016 [US4] Add real-time token validation in `useMentionAutocomplete` hook in `frontend/src/hooks/useMentionAutocomplete.ts` — whenever the cached pipeline list updates, re-validate all existing tokens' `pipelineId` values against the list; update `isValid` on each `MentionToken`; set `hasInvalidTokens` flag on the state
- [ ] T017 [US4] Add invalid token visual styling to `MentionToken` component in `frontend/src/components/chat/MentionToken.tsx` — when `isValid` is false, apply amber/red chip styling (`bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200`) and render a warning icon (lucide-react `AlertTriangle`) inline before the `@` prefix
- [ ] T018 [US4] Add unresolved @mention detection in `MentionInput` component in `frontend/src/components/chat/MentionInput.tsx` — when the user types `@text` and dismisses the autocomplete without selecting (Escape or click outside), detect if the typed text after `@` does not match any pipeline; if unresolved, optionally render the raw `@text` with a subtle warning underline via CSS class

**Checkpoint**: At this point, invalid and unresolved mentions are visually distinguished and submission is properly guarded.

---

## Phase 7: User Story 5 — Multiple @Mention Handling (Priority: P3)

**Goal**: Gracefully handle multiple @mentions in a single chat input by using the last valid mention and notifying the user.

**Independent Test**: Insert two different @mention tokens → "Using pipeline: [last name]" indicator shows with tooltip "Multiple pipelines mentioned — using last". One valid and one invalid → last valid used, invalid shows warning state. Two invalid → submission blocked.

### Implementation for User Story 5

- [ ] T019 [US5] Add multiple-mention tracking in `useMentionAutocomplete` hook in `frontend/src/hooks/useMentionAutocomplete.ts` — compute `hasMultipleMentions` (true when tokens array contains more than one valid mention); ensure `activePipelineId` always resolves to the last valid token's ID; expose `hasMultipleMentions` in the return value
- [ ] T020 [US5] Add multiple-mention notification in `ChatInterface` in `frontend/src/components/chat/ChatInterface.tsx` — when submitting with multiple valid mentions, display a transient notification/toast: "Multiple pipelines mentioned — using [last pipeline name]"

**Checkpoint**: At this point, all five user stories should be independently functional. Multiple @mentions are handled gracefully with clear feedback.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, cleanup, and coexistence verification across all user stories.

- [ ] T021 Verify slash-command (`/`) autocomplete coexistence with @mention autocomplete in `frontend/src/components/chat/ChatInterface.tsx` — ensure only one autocomplete is open at a time; opening one dismisses the other; slash commands still work correctly at start of input
- [ ] T022 Verify all existing frontend tests pass after modifications by running `npm test` in `frontend/`
- [ ] T023 Verify all existing backend tests pass after modifications by running `pytest` in `backend/`
- [ ] T024 Run quickstart.md verification scenarios (all 13 verification steps) to validate end-to-end feature behavior
- [ ] T025 Code cleanup — ensure consistent import ordering, remove unused imports, verify TypeScript types are correctly applied across all new and modified files

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on T001 (frontend types) and T002 (backend model) for type references; BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational phase completion — modifies `ChatInterface.tsx`
- **User Story 2 (Phase 4)**: Depends on Phase 3 completion — also modifies `ChatInterface.tsx` (same file, builds on US1 integration)
- **User Story 3 (Phase 5)**: Depends on Foundational phase — modifies `ChatInterface.tsx` (coordinate with US1/US2)
- **User Story 4 (Phase 6)**: Depends on Foundational phase — modifies `useMentionAutocomplete.ts`, `MentionToken.tsx`, `MentionInput.tsx`
- **User Story 5 (Phase 7)**: Depends on Foundational phase — modifies `useMentionAutocomplete.ts` and `ChatInterface.tsx`
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — no dependencies on other stories
- **User Story 2 (P1)**: Should start after US1 (Phase 3) since both modify `ChatInterface.tsx` and US2 depends on the @mention infrastructure being wired
- **User Story 3 (P2)**: Should follow US1/US2 for `ChatInterface.tsx` integration — can be done as a small addition
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) — modifies different primary files (`useMentionAutocomplete.ts`, `MentionToken.tsx`, `MentionInput.tsx`) but should follow US1 for integration testing
- **User Story 5 (P3)**: Should follow US1/US2 — builds on the multiple-mention scenario and modifies `ChatInterface.tsx`

### Within Each User Story

- Types before components
- Components before hooks (leaf → composite)
- Hook before integration into ChatInterface
- Core implementation before polish
- Story complete before moving to next priority

### Parallel Opportunities

- **Phase 1**: T001 and T002 can run in parallel (frontend types vs backend model — different repos)
- **Phase 2**: T003 is backend-only and independent; T004, T005, T006, T007 can all run in parallel (different new frontend files); T008 (hook) can be developed in parallel with components since they share a defined interface from contracts/components.md
- **Phase 3**: T009, T010, T011 are sequential (all modify `ChatInterface.tsx`)
- **Phase 6**: T016, T017, T018 touch different files and can run in parallel
- **Phase 7**: T019 and T020 touch different files and can run in parallel

---

## Parallel Example: Phase 2 (Foundational)

```bash
# Launch all new component tasks together (different files, no dependencies):
Task T004: "Create MentionToken component in frontend/src/components/chat/MentionToken.tsx"
Task T005: "Create MentionAutocomplete component in frontend/src/components/chat/MentionAutocomplete.tsx"
Task T006: "Create PipelineIndicator component in frontend/src/components/chat/PipelineIndicator.tsx"
Task T007: "Create MentionInput component in frontend/src/components/chat/MentionInput.tsx"
```

## Parallel Example: Phase 6 (User Story 4)

```bash
# Launch all US4 tasks together (different files):
Task T016: "Add real-time token validation in useMentionAutocomplete.ts"
Task T017: "Add invalid token styling in MentionToken.tsx"
Task T018: "Add unresolved @mention detection in MentionInput.tsx"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup (T001–T002)
2. Complete Phase 2: Foundational (T003–T008)
3. Complete Phase 3: User Story 1 — @Mention Autocomplete (T009–T011)
4. Complete Phase 4: User Story 2 — Pipeline-Aware Issue Creation (T012–T014)
5. **STOP and VALIDATE**: Test @mention selection and pipeline-aware submission end-to-end
6. Deploy/demo if ready — this delivers the core value proposition

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add US1 + US2 (P1) → Test independently → Deploy/Demo (**MVP!**)
3. Add US3 (P2) → Pipeline indicator visible → Deploy/Demo
4. Add US4 (P2) → Invalid mention warnings → Deploy/Demo
5. Add US5 (P3) → Multiple mention handling → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 + 2 (core @mention flow — sequential, same files)
   - Developer B: User Story 4 (invalid pipeline warning — different primary files)
3. After US1+US2 complete:
   - Developer A: User Story 3 + 5 (indicator + multiple mention — additions to ChatInterface)
4. Stories complete and integrate independently

---

## Summary

| Metric | Value |
|--------|-------|
| **Total Tasks** | 25 |
| **Setup Phase** | 2 tasks (T001–T002) |
| **Foundational Phase** | 6 tasks (T003–T008) |
| **US1 — @Mention Autocomplete (P1)** | 3 tasks (T009–T011) |
| **US2 — Pipeline-Aware Issue Creation (P1)** | 3 tasks (T012–T014) |
| **US3 — Active Pipeline Indicator (P2)** | 1 task (T015) |
| **US4 — Invalid Pipeline Warning (P2)** | 3 tasks (T016–T018) |
| **US5 — Multiple @Mention Handling (P3)** | 2 tasks (T019–T020) |
| **Polish Phase** | 5 tasks (T021–T025) |
| **Parallel Opportunities** | 9 tasks marked [P]; Phase 2 components can all proceed in parallel |
| **MVP Scope** | US1 + US2 (6 tasks T009–T014) — delivers core @mention + pipeline-aware issue creation |

## Notes

- [P] tasks = different files, no dependencies on other incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- US1, US2, US3, and US5 all modify `ChatInterface.tsx` — implement sequentially in priority order to avoid conflicts
- US4 primarily modifies `useMentionAutocomplete.ts`, `MentionToken.tsx`, and `MentionInput.tsx` — can proceed in parallel with US3/US5
- The backend changes (T002, T003) are minimal and backward-compatible — existing clients unaffected
- The `contentEditable` approach (R1) avoids adding any new UI library dependencies
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
