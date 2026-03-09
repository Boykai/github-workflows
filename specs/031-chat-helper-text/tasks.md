# Tasks: Update User Chat Helper Text for Comprehensive UX Guidance

**Input**: Design documents from `/specs/031-chat-helper-text/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/components.md, quickstart.md

**Tests**: Not explicitly requested in the feature specification. Existing MentionInput tests should continue to pass. No new test tasks are generated.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- All changes in this feature are frontend-only — no backend modifications.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the centralized placeholder copy constants that all subsequent phases depend on.

- [x] T001 Create `ChatPlaceholderConfig` interface, `CHAT_PLACEHOLDERS` registry, and `CYCLING_EXAMPLES` array in `frontend/src/constants/chat-placeholders.ts`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Update MentionInput to accept responsive placeholder props and render responsive dual-span layout. MUST be complete before any user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T002 Add `placeholderMobile?: string` and `ariaLabel?: string` optional props to `MentionInputProps` interface in `frontend/src/components/chat/MentionInput.tsx`
- [x] T003 Update MentionInput placeholder overlay to render responsive dual-span layout with Tailwind `max-sm:hidden` / `hidden max-sm:inline` classes when `placeholderMobile` is provided in `frontend/src/components/chat/MentionInput.tsx`
- [x] T004 Update MentionInput contentEditable `aria-label` attribute to use the new `ariaLabel` prop with `"Chat input"` fallback in `frontend/src/components/chat/MentionInput.tsx`

**Checkpoint**: MentionInput now accepts `placeholderMobile` and `ariaLabel` props and renders responsive placeholder — user story implementation can begin.

---

## Phase 3: User Story 1 — Descriptive Chat Placeholder on Desktop (Priority: P1) 🎯 MVP

**Goal**: The main chat input displays a descriptive, actionable placeholder that communicates at least four supported interaction types (questions, tasks, slash commands, pipeline mentions) on desktop viewports (≥640px, per the Tailwind `sm` breakpoint used for responsive switching).

**Independent Test**: Open the chat interface on a desktop viewport (≥1024px wide), observe the placeholder text in the empty chat input, and verify it reads "Ask a question, describe a task, use / for commands, or @ to select a pipeline…" and fits within the input boundary without overflow.

### Implementation for User Story 1

- [x] T005 [US1] Import `CHAT_PLACEHOLDERS` from `@/constants/chat-placeholders` and replace hardcoded placeholder string with `CHAT_PLACEHOLDERS.main.desktop` on the MentionInput component in `frontend/src/components/chat/ChatInterface.tsx`

**Checkpoint**: Desktop placeholder shows "Ask a question, describe a task, use / for commands, or @ to select a pipeline…" — User Story 1 is complete.

---

## Phase 4: User Story 2 — Responsive Helper Text on Mobile (Priority: P1)

**Goal**: A shortened placeholder variant displays on small-screen viewports (<640px, per the Tailwind `max-sm:` breakpoint from research.md R2) that still communicates the chat's purpose without layout breakage.

**Independent Test**: Open the chat interface on a mobile viewport (<640px wide), observe the placeholder text, and verify it reads "Ask anything or use / and @ for more…" and fits within the input without overflow or truncation.

### Implementation for User Story 2

- [x] T006 [US2] Pass `placeholderMobile={CHAT_PLACEHOLDERS.main.mobile}` prop to MentionInput in `frontend/src/components/chat/ChatInterface.tsx`

**Checkpoint**: Mobile viewport (<640px) shows "Ask anything or use / and @ for more…" — User Story 2 is complete.

---

## Phase 5: User Story 3 — Accessible Helper Text for All Users (Priority: P1)

**Goal**: All accessibility attributes (aria-label) on the main chat input are updated to reflect the new helper text, and placeholder color contrast meets WCAG AA 4.5:1 minimum.

**Independent Test**: Use a screen reader to navigate to the chat input and verify the announced label conveys the same guidance as the visible placeholder. Measure the color contrast ratio of `text-muted-foreground` against the input background and confirm it meets or exceeds 4.5:1.

### Implementation for User Story 3

- [x] T007 [US3] Pass `ariaLabel={CHAT_PLACEHOLDERS.main.ariaLabel}` prop to MentionInput in `frontend/src/components/chat/ChatInterface.tsx`
- [x] T008 [US3] Verify `text-muted-foreground` contrast ratio meets WCAG AA 4.5:1 in both light and dark modes against `--background` (no code change needed — verification per research.md R3) in `frontend/src/index.css`

**Checkpoint**: Screen reader announces "Chat input — ask questions, describe tasks, use slash commands, or mention pipelines"; contrast ratio confirmed ≥4.5:1 — User Story 3 is complete.

---

## Phase 6: User Story 4 — Consistent Helper Text Across All Chat Instances (Priority: P2)

**Goal**: All chat input instances across the application (agent chat, chore chat) display updated, descriptive helper text from the centralized constants, eliminating generic "Type your response…" placeholders.

**Independent Test**: Navigate to the agent creation chat and chore template chat; verify each displays its updated placeholder and aria-label from `CHAT_PLACEHOLDERS`.

### Implementation for User Story 4

- [x] T009 [P] [US4] Import `CHAT_PLACEHOLDERS` and replace `placeholder="Type your response…"` with `placeholder={CHAT_PLACEHOLDERS.agentFlow.desktop}` and add `aria-label={CHAT_PLACEHOLDERS.agentFlow.ariaLabel}` on the input element in `frontend/src/components/agents/AgentChatFlow.tsx`
- [x] T010 [P] [US4] Import `CHAT_PLACEHOLDERS` and replace `placeholder="Type your response…"` with `placeholder={CHAT_PLACEHOLDERS.choreFlow.desktop}` and add `aria-label={CHAT_PLACEHOLDERS.choreFlow.ariaLabel}` on the input element in `frontend/src/components/chores/ChoreChatFlow.tsx`

**Checkpoint**: Agent chat shows "Describe what you'd like your agent to do…"; Chore chat shows "Add details or refine your request…" — all chat instances are consistent. User Story 4 is complete.

---

## Phase 7: User Story 5 — Cycling Contextual Placeholder Examples (Priority: P3)

**Goal**: The main chat placeholder cycles through example prompts (≥3 distinct examples) with smooth fade transitions, stopping when the input is focused, and respecting `prefers-reduced-motion`.

**Independent Test**: Observe the main chat input for 15–30 seconds and verify the placeholder text cycles through at least 3 distinct example prompts with smooth transitions, without layout shifts. Focus the input and verify cycling stops immediately. Enable `prefers-reduced-motion: reduce` and verify the placeholder falls back to the static text.

### Implementation for User Story 5

- [x] T011 [US5] Create `useCyclingPlaceholder` hook that cycles through an array of placeholder strings at a configurable interval with `prefers-reduced-motion` fallback and cleanup on unmount in `frontend/src/hooks/useCyclingPlaceholder.ts`
- [x] T012 [US5] Integrate `useCyclingPlaceholder` hook with `CYCLING_EXAMPLES` into the MentionInput placeholder overlay for the main chat context, adding CSS opacity transition for smooth fade between prompts in `frontend/src/components/chat/ChatInterface.tsx`

**Checkpoint**: Main chat cycles through 5 example prompts every 5 seconds; stops on focus; respects reduced motion — User Story 5 is complete.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Verification, regression testing, and final validation across all stories.

- [x] T013 [P] Run frontend build (`cd frontend && npm run build`) to verify no TypeScript errors
- [x] T014 [P] Run existing frontend tests (`cd frontend && npx vitest run`) to verify no regressions in MentionInput or other chat components
- [x] T015 Run quickstart.md manual verification checklist: desktop placeholder, mobile responsive, agent chat, chore chat, screen reader, type-and-clear, message submission

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (T001 must exist before T002–T004 can import types)
- **User Story 1 (Phase 3)**: Depends on Phase 2 — T005 needs MentionInput to accept new props
- **User Story 2 (Phase 4)**: Depends on Phase 2 — T006 passes the `placeholderMobile` prop added in T003
- **User Story 3 (Phase 5)**: Depends on Phase 2 — T007 passes the `ariaLabel` prop added in T004
- **User Story 4 (Phase 6)**: Depends on Phase 1 only — T009/T010 import from constants, do not depend on MentionInput changes (AgentChatFlow and ChoreChatFlow use native `<input>` elements)
- **User Story 5 (Phase 7)**: Depends on Phases 1–3 — T011/T012 build on the cycling examples from T001 and the MentionInput rendering from T003
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — no dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) — no dependencies on other stories
- **User Story 3 (P1)**: Can start after Foundational (Phase 2) — no dependencies on other stories
- **User Story 4 (P2)**: Can start after Setup (Phase 1) — independent of US1–US3 (different components, native `<input>` elements)
- **User Story 5 (P3)**: Can start after US1 is complete — extends the main chat placeholder with cycling behavior

### Within Each User Story

- Constants (Phase 1) before component modifications
- MentionInput prop changes (Phase 2) before consumer components pass those props
- Core implementation before integration/verification
- Story complete before moving to next priority

### Parallel Opportunities

- **Phase 2**: T003 and T004 modify different sections of MentionInput.tsx but are in the same file — execute sequentially
- **Phase 3–5**: US1, US2, US3 all modify ChatInterface.tsx — execute sequentially (T005 → T006 → T007) or batch into a single edit
- **Phase 6**: T009 (AgentChatFlow.tsx) and T010 (ChoreChatFlow.tsx) are in different files — can run in parallel [P]
- **Phase 6 vs Phase 3**: US4 (Phase 6) can start in parallel with US1 (Phase 3) since it only depends on Phase 1, not Phase 2
- **Phase 8**: T013 (build) and T014 (tests) can run in parallel [P]

---

## Parallel Example: User Story 4

```bash
# These two tasks modify different files and can run in parallel:
Task T009: "Update AgentChatFlow.tsx placeholder and aria-label from CHAT_PLACEHOLDERS.agentFlow"
Task T010: "Update ChoreChatFlow.tsx placeholder and aria-label from CHAT_PLACEHOLDERS.choreFlow"
```

## Parallel Example: Phase 8 Verification

```bash
# Build and test can run in parallel:
Task T013: "Run frontend build (npm run build) to verify no TypeScript errors"
Task T014: "Run existing frontend tests (npx vitest run) to verify no regressions"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (create constants file)
2. Complete Phase 2: Foundational (update MentionInput props and rendering)
3. Complete Phase 3: User Story 1 (wire up ChatInterface to constants)
4. **STOP and VALIDATE**: Open chat on desktop, verify descriptive placeholder
5. Deploy/demo if ready — users immediately see better guidance

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test on desktop → MVP! (descriptive placeholder)
3. Add User Story 2 → Test on mobile → Responsive placeholder
4. Add User Story 3 → Test with screen reader → Accessible placeholder
5. Add User Story 4 → Test agent + chore chats → Consistent across app
6. Add User Story 5 → Test cycling animation → Delight enhancement (P3)
7. Each story adds value without breaking previous stories

### Practical Batching (Recommended)

Given the XS size of this feature and deeply interconnected P1 stories:

1. **Batch 1** (T001–T008): Setup + Foundational + US1 + US2 + US3 — all P1 stories in a single pass
2. **Batch 2** (T009–T010): US4 — agent and chore chat consistency
3. **Batch 3** (T011–T012): US5 — cycling placeholder (P3, optional)
4. **Batch 4** (T013–T015): Polish — build, test, manual verification

---

## Notes

- [P] tasks = different files, no dependencies — safe to run in parallel
- [Story] label maps task to specific user story for traceability
- US1, US2, US3 are all P1 and modify the same files — recommend batching into a single implementation pass
- US4 is P2 and modifies separate files (AgentChatFlow, ChoreChatFlow) — can run in parallel with US1–US3
- US5 is P3 and optional — can be deferred without blocking core deliverables
- Tests are not included because they were not explicitly requested in the specification
- WCAG contrast verification (T008) is a manual check, not a code change — existing `text-muted-foreground` already meets 4.5:1
- Total estimated effort: ~1 hour (aligned with issue metadata)
- Commit after each task or logical batch
- Stop at any checkpoint to validate story independently
