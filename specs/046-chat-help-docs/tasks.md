# Tasks: Update Chat Help & Help Page for Comprehensive Chat Commands & Features

**Input**: Design documents from `/specs/046-chat-help-docs/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md

**Tests**: Tests are explicitly required per spec FR-018 through FR-022 and User Story 5 (P5). Test tasks are organized in Phase 6 (US5) as a dedicated test story.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing. User Stories 1–4 each modify distinct code regions (US1: help.ts, US2–US4: different sections of HelpPage.tsx). US3 also modifies registry.ts for language labels. US5 covers all test files. All five user stories can proceed after Setup completes.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Frontend app**: `solune/frontend/src/`
- **Frontend tests**: colocated `solune/frontend/src/**/*.test.ts(x)`
- **Command handlers**: `solune/frontend/src/lib/commands/handlers/`
- **Command registry**: `solune/frontend/src/lib/commands/registry.ts`
- **Pages**: `solune/frontend/src/pages/`
- **Feature artifacts**: `specs/046-chat-help-docs/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Validate baseline state before making any source changes.

- [ ] T001 Run baseline validation commands (`npx vitest run`, `npm run type-check`, `npm run lint`) in `solune/frontend/` to record any pre-existing failures before making source changes

---

## Phase 2: User Story 1 — Expanded /help Chat Command Output (Priority: P1) 🎯 MVP

**Goal**: Users who type `/help` (or `help` without the slash) see not only the six-command list but also a "Chat Features" section with four feature descriptions and a "Tips" section with four tips — all in plain text.

**Independent Test**: Invoke the `/help` command handler and verify the returned message string contains the "Chat Features:" header with @Pipeline Mentions, File Attachments, Voice Input, and AI Enhance lines, followed by the "Tips:" header with autocomplete hint, help alias, history navigation, and Help page pointer.

### Implementation for User Story 1

- [ ] T002 [US1] Append a "Chat Features:" header and four feature lines below the command list in `solune/frontend/src/lib/commands/handlers/help.ts` — lines: `@Pipeline Mentions — Type @ to invoke a pipeline by name`, `File Attachments — Use the attachment button to add files (images, PDF, code, up to 10 MB)`, `Voice Input — Use the microphone button for speech-to-text (Chrome/Edge recommended)`, `AI Enhance — Toggle AI Enhance in the toolbar for smarter responses`
- [ ] T003 [US1] Append a "Tips:" header and four tip lines below the Chat Features block in `solune/frontend/src/lib/commands/handlers/help.ts` — lines: `• Type / to browse and autocomplete commands`, `• You can also type help without the slash`, `• Use Arrow Up/Down to browse previous messages`, `• Visit the Help page for the full guide`

**Checkpoint**: At this point, typing `/help` in chat returns the standard command list plus the new Chat Features and Tips sections in plain text. User Story 1 is fully functional and testable independently.

---

## Phase 3: User Story 2 — New Chat Features Section on Help Page (Priority: P2)

**Goal**: The Help page displays a new "Chat Features" section between FAQ and Feature Guides containing seven informational cards: @Pipeline Mentions, File Attachments, Voice Input, AI Enhance, Task Proposals, Message History, and Keyboard Shortcuts.

**Independent Test**: Render the Help page and verify seven feature cards appear in the Chat Features section, each with the correct title, icon, and description content matching the codebase audit.

### Implementation for User Story 2

- [ ] T004 [US2] Define a `CHAT_FEATURES` constant array of 7 feature objects with `title`, `description`, and `icon` properties and import icons (`AtSign`, `Paperclip`, `Mic`, `Sparkles`, `ListTodo`, `History`, `Keyboard`) from `lucide-react` in `solune/frontend/src/pages/HelpPage.tsx` — feature titles: @Pipeline Mentions, File Attachments, Voice Input, AI Enhance, Task Proposals, Message History, Keyboard Shortcuts; descriptions per spec FR-008
- [ ] T005 [US2] Add a "Chat Features" `<section>` with heading and responsive card grid (`grid-cols-1 sm:grid-cols-2 lg:grid-cols-3`) between the FAQ section and Feature Guides section in `solune/frontend/src/pages/HelpPage.tsx` — render each card as a `<div>` with moonwell styling matching `FeatureGuideCard` visual pattern (icon circle, title, description) per research RT-002

**Checkpoint**: The Help page now shows seven Chat Features cards between FAQ and Feature Guides. User Story 2 is fully functional and testable independently.

---

## Phase 4: User Story 3 — Enriched Slash Commands Table (Priority: P3)

**Goal**: The Slash Commands table on the Help page has an "Options" column showing valid parameter values for each command, driven dynamically from `parameterSchema`. A footer note reminds users about autocomplete and the `help` alias.

**Independent Test**: Render the Help page Slash Commands section and verify the table has four columns (Name, Syntax, Description, Options) with correct option values per command (e.g., "light, dark, system" for `/theme`, "en (English), es (Spanish)..." for `/language`), plus a footer note.

### Implementation for User Story 3

- [ ] T006 [P] [US3] Add `labels` map `{ en: 'English', es: 'Spanish', fr: 'French', de: 'German', ja: 'Japanese', zh: 'Chinese' }` to the `/language` command `parameterSchema` in `solune/frontend/src/lib/commands/registry.ts` per research RT-003
- [ ] T007 [US3] Implement a `getCommandOptions` helper function in `solune/frontend/src/pages/HelpPage.tsx` that derives Options column content from `cmd.parameterSchema`: enum with labels → "value (Label)" format, enum without labels → comma-joined values, passthrough → parameter syntax + "(admin only)" badge, no schema → "—"
- [ ] T008 [US3] Add "Options" column header to the Slash Commands table and render an Options `<td>` cell for each command row using the `getCommandOptions` helper in `solune/frontend/src/pages/HelpPage.tsx`
- [ ] T009 [US3] Add a footer note below the Slash Commands table reading "Type / in chat to autocomplete commands. You can also type help without the slash." in `solune/frontend/src/pages/HelpPage.tsx`

**Checkpoint**: The Slash Commands table now has a 4th Options column with dynamically derived values and a footer note. User Story 3 is fully functional and testable independently.

---

## Phase 5: User Story 4 — Corrected FAQ Entries (Priority: P4)

**Goal**: The FAQ section no longer references the non-existent `/clear` command or unsupported drag-and-drop file feature. Both entries are corrected to reflect actual application behavior.

**Independent Test**: Render the Help page FAQ section and verify `chat-voice-1` does not contain "/clear" and `chat-voice-2` does not contain "drag-and-drop".

### Implementation for User Story 4

- [ ] T010 [US4] Fix FAQ entry `chat-voice-1` answer: replace `/clear` with `/agent` and update text to `'Type / in the chat to see all available commands. Common ones include /help, /theme, and /agent. See the Slash Commands section below for the full list.'` in `solune/frontend/src/pages/HelpPage.tsx` per research RT-004
- [ ] T011 [US4] Fix FAQ entry `chat-voice-2` answer: replace "drag-and-drop" claim with attachment button instruction — change to `'Yes — click the attachment button in the chat toolbar to select files. Supported formats include images, PDFs, markdown, and code files up to 10 MB each.'` in `solune/frontend/src/pages/HelpPage.tsx` per research RT-004

**Checkpoint**: Both FAQ entries now accurately describe existing application behavior. User Story 4 is fully functional and testable independently.

---

## Phase 6: User Story 5 — Automated Tests for All Changes (Priority: P5)

**Goal**: All changes from User Stories 1–4 are covered by automated tests: expanded `/help` output, Chat Features section, enriched commands table, and corrected FAQ entries.

**Independent Test**: Run the help handler unit tests and Help page component tests — all assertions pass, confirming Chat Features content, Tips content, 7 feature cards, Options column values, corrected FAQ text, and footer note.

### Tests for User Story 5

- [ ] T012 [P] [US5] Add unit test verifying `/help` output includes "Chat Features" section with @Pipeline Mentions, File Attachments, Voice Input, and AI Enhance lines in `solune/frontend/src/lib/commands/handlers/help.test.ts`
- [ ] T013 [P] [US5] Add unit test verifying `/help` output includes "Tips" section with autocomplete hint, help alias, history navigation, and Help page pointer lines in `solune/frontend/src/lib/commands/handlers/help.test.ts`
- [ ] T014 [P] [US5] Create `solune/frontend/src/pages/HelpPage.test.tsx` with test verifying the Chat Features section renders all 7 cards with correct titles (@Pipeline Mentions, File Attachments, Voice Input, AI Enhance, Task Proposals, Message History, Keyboard Shortcuts)
- [ ] T015 [US5] Add test verifying the Slash Commands table has an "Options" column with correct values for each command (theme → "light, dark, system", language → labeled values, etc.) in `solune/frontend/src/pages/HelpPage.test.tsx`
- [ ] T016 [US5] Add test verifying FAQ `chat-voice-1` answer does not contain "/clear" and FAQ `chat-voice-2` answer does not contain "drag-and-drop" in `solune/frontend/src/pages/HelpPage.test.tsx`
- [ ] T017 [US5] Add test verifying the footer note "Type / in chat to autocomplete commands" appears below the Slash Commands table in `solune/frontend/src/pages/HelpPage.test.tsx`

**Checkpoint**: All automated tests pass — expanded help output, Chat Features section, enriched table, corrected FAQ, and footer note are all verified. User Story 5 is complete.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final verification that all changes pass type checking, linting, test suite, and production build.

- [ ] T018 [P] Run TypeScript type-check (`npx tsc --noEmit`) in `solune/frontend/` and verify zero type errors
- [ ] T019 [P] Run ESLint (`npm run lint`) in `solune/frontend/` and verify zero lint errors
- [ ] T020 Run full Vitest suite (`npx vitest run`) in `solune/frontend/` and verify all tests pass including new help and HelpPage tests
- [ ] T021 Run production build (`npm run build`) in `solune/frontend/` and verify successful build with no errors

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **User Story 1 (Phase 2)**: Depends on Setup — modifies only `help.ts`, no dependency on other stories
- **User Story 2 (Phase 3)**: Depends on Setup — modifies only `HelpPage.tsx` (new section), no dependency on other stories
- **User Story 3 (Phase 4)**: Depends on Setup — modifies `registry.ts` (labels) and `HelpPage.tsx` (table + footer)
- **User Story 4 (Phase 5)**: Depends on Setup — modifies only `HelpPage.tsx` (FAQ entries), no dependency on other stories
- **User Story 5 (Phase 6)**: Depends on User Stories 1–4 being complete (tests verify all implementation changes)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Setup — No dependencies on other stories
- **User Story 2 (P2)**: Can start after Setup — No dependencies on other stories
- **User Story 3 (P3)**: Can start after Setup — No dependencies on other stories (labels addition in registry.ts is self-contained within US3)
- **User Story 4 (P4)**: Can start after Setup — No dependencies on other stories
- **User Story 5 (P5)**: Must start after User Stories 1–4 complete — tests verify all prior changes

### Within Each User Story

- US1: T002 (Chat Features block) before T003 (Tips block) — sequential additions to the same output string
- US2: T004 (data definition) before T005 (section rendering) — must define data before rendering
- US3: T006 (labels in registry.ts) can parallel with T007 (helper function) — different files; T007 before T008 (column rendering); T008 before T009 (footer note) — sequential table changes
- US4: T010 and T011 are sequential (same file, same section)
- US5: T012/T013 (help.test.ts) can parallel with T014–T017 (HelpPage.test.tsx) — different test files; within each file, tasks are sequential

### Parallel Opportunities

- User Stories 1, 2, 3, and 4 can all proceed in parallel after Setup completes (different files or non-overlapping file sections)
- Within US3: T006 (registry.ts) runs in parallel with T007 (HelpPage.tsx helper) — different files
- Within US5: T012/T013 (help.test.ts) run in parallel with T014–T017 (HelpPage.test.tsx) — different test files
- Polish tasks T018 (tsc) and T019 (ESLint) can run in parallel

---

## Parallel Example: User Stories 1–4

```bash
# After Setup (Phase 1) completes, all four implementation stories can start in parallel:
Task T002: "Append Chat Features block in help.ts"           # US1 — help.ts
Task T004: "Define CHAT_FEATURES array in HelpPage.tsx"      # US2 — HelpPage.tsx (new section)
Task T006: "Add labels to /language in registry.ts"          # US3 — registry.ts
Task T010: "Fix chat-voice-1 FAQ in HelpPage.tsx"            # US4 — HelpPage.tsx (FAQ section)
# US1 targets help.ts; US3 starts in registry.ts; US2 and US4 target different HelpPage.tsx sections
```

## Parallel Example: User Story 5

```bash
# After US1–US4 complete, test tasks across different files run in parallel:
Task T012: "Add help handler Chat Features test in help.test.ts"
Task T014: "Create HelpPage.test.tsx with Chat Features section test"
# help.test.ts and HelpPage.test.tsx are different files — safe to parallelize
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (baseline validation)
2. Complete Phase 2: User Story 1 — Expand `/help` output
3. **STOP and VALIDATE**: Type `/help` in chat → confirm Chat Features and Tips sections appear
4. Deploy/demo if ready — immediate user discovery improvement

### Incremental Delivery

1. Complete Setup → Baseline verified
2. Add User Story 1 (P1 — /help output) → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 (P2 — Chat Features section) → Test independently → Deploy/Demo
4. Add User Story 3 (P3 — enriched table) → Test independently → Deploy/Demo
5. Add User Story 4 (P4 — FAQ fixes) → Test independently → Deploy/Demo
6. Add User Story 5 (P5 — automated tests) → All tests pass → Deploy/Demo
7. Complete Polish → Final verification (tsc, ESLint, Vitest, build)
8. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup together
2. Once Setup is done:
   - Developer A: User Story 1 (help.ts — highest priority)
   - Developer B: User Story 2 (HelpPage.tsx — Chat Features section)
   - Developer C: User Story 3 (registry.ts + HelpPage.tsx — Options column)
   - Developer D: User Story 4 (HelpPage.tsx — FAQ corrections)
3. After Stories 1–4 complete:
   - Any developer: User Story 5 (test files) + Polish

---

## Notes

- [P] tasks = different files, no dependencies — safe to parallelize
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All `/help` output must remain plain text — no Markdown (chat doesn't render it)
- The `CHAT_FEATURES` cards use an inline card component matching `FeatureGuideCard` styling but as a non-navigable `<div>` (per research RT-002)
- The Options column is dynamically driven from `parameterSchema` — new commands with schemas will appear automatically
- Only 2 source files modified (`help.ts`, `HelpPage.tsx`) + 1 registry enhancement (`registry.ts`) + 2 test files (`help.test.ts`, `HelpPage.test.tsx`)
- Avoid: Markdown in `/help` output, modifying `FeatureGuideCard` component, adding new slash commands, hardcoding option values
