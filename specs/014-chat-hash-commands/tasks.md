# Tasks: Enhance Chat # Commands — App-Wide Settings Control & #help Command with Test Coverage

**Input**: Design documents from `/specs/014-chat-hash-commands/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are explicitly requested (FR-019, User Story 6). Test tasks are included in each user story phase.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- This feature is entirely frontend — no backend changes required.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the directory structure and type definitions for the command system

- [x] T001 Create directory structure for command system: `frontend/src/lib/commands/` and `frontend/src/lib/commands/handlers/`
- [x] T002 Create command system TypeScript type definitions (`CommandDefinition`, `ParameterSchema`, `CommandContext`, `CommandResult`, `ParsedCommand`) in `frontend/src/lib/commands/types.ts`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core command infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 Implement command registry with `Map<string, CommandDefinition>` storage and exported helper functions (`getCommand`, `getAllCommands`, `filterCommands`) in `frontend/src/lib/commands/registry.ts`
- [x] T004 Implement `parseCommand(input: string): ParsedCommand` function in `frontend/src/lib/commands/registry.ts` with rules: `#`-prefix detection, command name extraction (lowercase), argument parsing, whitespace normalization, case insensitivity, bare `#` handling, and `help` keyword alias
- [x] T005 [P] Create `SystemMessage` component for rendering command responses (distinct visual style using existing Tailwind theme classes: no avatar, muted background via theme-aware utility classes consistent with current chat message styling) in `frontend/src/components/chat/SystemMessage.tsx`
- [x] T006 [P] Add command-related test factories (`createCommandDefinition`, `createCommandContext`, `createCommandResult`, `createParsedCommand`) in `frontend/src/test/factories/index.ts`

**Checkpoint**: Foundation ready — command registry, parsing, system message display, and test factories are in place. User story implementation can now begin.

---

## Phase 3: User Story 1 — Discover Available Commands via #help (Priority: P1) 🎯 MVP

**Goal**: Users can type `#help` or `help` in chat and receive a formatted list of all available commands with names, syntax, and descriptions as a system message.

**Independent Test**: Type `#help` or `help` in the chat input and verify the response contains a complete, formatted command reference listing all registered commands.

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T007 [P] [US1] Write unit tests for help command handler (output contains all registered commands, format includes name/syntax/description, auto-updates when new commands are added) in `frontend/src/lib/commands/handlers/help.test.ts`
- [x] T008 [P] [US1] Write unit tests for command registry (registration, lookup by name, case-insensitive lookup, unknown command returns undefined, `getAllCommands` returns sorted list) in `frontend/src/lib/commands/registry.test.ts`

### Implementation for User Story 1

- [x] T009 [US1] Implement `#help` command handler that iterates `getAllCommands()` and formats each command's name, syntax, and description into a readable system message in `frontend/src/lib/commands/handlers/help.ts`
- [x] T010 [US1] Register the `help` command in the command registry with name, description, syntax, handler, and no parameterSchema in `frontend/src/lib/commands/registry.ts`
- [x] T011 [US1] Create `useCommands` hook with `parseCommand()`, `executeCommand()`, and `isCommand()` functions, integrating with `useTheme()` and `useSettings()` to build `CommandContext` in `frontend/src/hooks/useCommands.ts`
- [x] T012 [US1] Write hook tests for `useCommands` covering: `parseCommand` returns correct `ParsedCommand`, `isCommand` identifies commands vs regular messages, `executeCommand` for `#help` returns formatted help output in `frontend/src/hooks/useCommands.test.tsx`

**Checkpoint**: `#help` and `help` commands are fully functional. Users can discover all available commands. This is the MVP — delivers standalone value.

---

## Phase 4: User Story 2 — Update App-Wide Settings via # Commands (Priority: P1)

**Goal**: Users can type settings commands (e.g., `#theme dark`, `#language en`, `#notifications off`, `#view chat`) and have changes applied immediately across the entire app with confirmation or error messages.

**Independent Test**: Submit `#theme dark` and verify the app-wide theme changes immediately. Submit `#theme rainbow` and verify an error message with valid options appears.

### Tests for User Story 2 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T013 [P] [US2] Write unit tests for settings command handlers covering: valid value applies setting and returns confirmation with old/new values, invalid value returns error listing valid options, missing argument returns usage message, each setting command (theme, language, notifications, view) in `frontend/src/lib/commands/handlers/settings.test.ts`

### Implementation for User Story 2

- [x] T014 [US2] Implement `#theme` handler that validates against `light|dark|system`, reads current theme from `context.currentTheme`, calls `context.setTheme()`, and returns confirmation message in `frontend/src/lib/commands/handlers/settings.ts`
- [x] T015 [P] [US2] Implement `#language` handler that validates against `en|es|fr|de|ja|zh`, reads current value from `context.currentSettings`, calls `context.updateSettings()`, and returns confirmation message in `frontend/src/lib/commands/handlers/settings.ts`
- [x] T016 [P] [US2] Implement `#notifications` handler that validates against `on|off`, reads current value from `context.currentSettings`, calls `context.updateSettings()`, and returns confirmation message in `frontend/src/lib/commands/handlers/settings.ts`
- [x] T017 [P] [US2] Implement `#view` handler that validates against `chat|board|settings`, reads current value from `context.currentSettings`, calls `context.updateSettings()`, and returns confirmation message in `frontend/src/lib/commands/handlers/settings.ts`
- [x] T018 [US2] Register all settings commands (theme, language, notifications, view) in the command registry with names, descriptions, syntax, handlers, and parameterSchemas in `frontend/src/lib/commands/registry.ts`
- [x] T019 [US2] Write hook tests for settings command execution covering: `executeCommand` for `#theme dark` calls `setTheme`, confirmation system message content, error message for invalid value in `frontend/src/hooks/useCommands.test.tsx`

**Checkpoint**: All settings commands are functional. Users can update theme, language, notifications, and default view via chat. Changes propagate app-wide via existing ThemeProvider and settingsApi.

---

## Phase 5: User Story 3 — Autocomplete Command Suggestions While Typing (Priority: P2)

**Goal**: When users type `#` in the chat input, an autocomplete overlay appears listing matching commands in real time, with keyboard navigation (ArrowUp/Down, Enter, Escape) and mouse click selection.

**Independent Test**: Type `#` in the chat input and verify a suggestion overlay appears. Type `#th` and verify only `#theme` is shown. Press ArrowDown, Enter to select. Press Escape to dismiss.

### Tests for User Story 3 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T020 [P] [US3] Write component tests for `CommandAutocomplete` covering: renders all commands when prefix is `#`, filters by typed prefix, keyboard navigation (ArrowDown/Up highlights items, Enter selects, Escape dismisses), mouse click selects, shows command name and description in `frontend/src/components/chat/CommandAutocomplete.test.tsx`

### Implementation for User Story 3

- [x] T021 [US3] Add `getFilteredCommands(prefix: string)` to `useCommands` hook that calls `filterCommands` from registry and returns matching `CommandDefinition[]` in `frontend/src/hooks/useCommands.ts`
- [x] T022 [US3] Implement `CommandAutocomplete` component with: overlay positioned above chat input, list of suggestions with `#` prefix and description, keyboard navigation state (highlighted index), ArrowUp/Down/Enter/Escape/Tab key handlers, click handlers, `role="listbox"` and `aria-activedescendant` accessibility attributes in `frontend/src/components/chat/CommandAutocomplete.tsx`
- [x] T023 [US3] Write hook tests for `getFilteredCommands` covering: returns all commands for empty prefix, filters by prefix, case-insensitive filtering, returns empty array for no matches in `frontend/src/hooks/useCommands.test.tsx`

**Checkpoint**: Autocomplete overlay is functional. Users can discover and select commands interactively while typing.

---

## Phase 6: User Story 4 — Commands Intercepted Before Reaching Chat Agent (Priority: P2)

**Goal**: `#`-prefixed messages and the `help` keyword are handled entirely client-side, never sent to the AI/LLM backend. System messages appear inline in chat. Non-command messages continue to the AI agent as normal.

**Independent Test**: Submit `#help` and verify no network request is made to the chat API. Submit a regular message and verify it is sent to the AI backend.

### Tests for User Story 4 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T024 [P] [US4] Write integration tests for command interception in ChatInterface covering: `#help` submission shows system message without calling chatApi, `#theme dark` changes theme without calling chatApi, regular message calls chatApi.sendMessage, unrecognized `#foobar` shows error without calling chatApi, `help` keyword is intercepted in `frontend/src/components/chat/ChatInterface.test.tsx`

### Implementation for User Story 4

- [x] T025 [US4] Modify `useChat` hook to check `isCommand(input)` before calling `chatApi.sendMessage()`, and if command: call `executeCommand()`, create `SystemChatMessage` (with `sender_type: "system"`, client-side UUID, timestamp), and insert into local message list in `frontend/src/hooks/useChat.ts`
- [x] T026 [US4] Integrate `CommandAutocomplete` overlay into `ChatInterface.tsx`: render above chat input, trigger on `#` as first character, pass filtered commands, handle selection (insert command name into input), handle dismissal in `frontend/src/components/chat/ChatInterface.tsx`
- [x] T027 [US4] Integrate `SystemMessage` component into chat message rendering in `ChatInterface.tsx` to display command responses with distinct styling for `sender_type: "system"` messages in `frontend/src/components/chat/ChatInterface.tsx`
- [x] T028 [US4] Implement input preservation on error: when `executeCommand` returns `clearInput: false`, do not clear the chat input field, allowing users to correct their command in `frontend/src/components/chat/ChatInterface.tsx`

**Checkpoint**: Full command flow works end-to-end. Commands are intercepted client-side, system messages display inline, non-commands pass through to AI, errors preserve input.

---

## Phase 7: User Story 5 — Command Registry as Single Source of Truth (Priority: P2)

**Goal**: Developers can add a new command by registering it in a single location, and it automatically appears in `#help` output, autocomplete suggestions, and is executable — no other code changes needed.

**Independent Test**: Add a test command to the registry and verify it appears in `#help` output and autocomplete suggestions without any other code changes.

### Tests for User Story 5 ⚠️

- [x] T029 [P] [US5] Write single-source-of-truth verification tests: register a new test command, verify it appears in `getAllCommands()`, verify `#help` handler output includes it, verify `filterCommands` returns it, verify it is executable via `executeCommand` in `frontend/src/lib/commands/registry.test.ts`

### Implementation for User Story 5

- [x] T030 [US5] Verify and document that the command registry `Map` in `registry.ts` is the single source of truth by ensuring `getAllCommands()` drives `#help` output, `filterCommands()` drives autocomplete, and `getCommand()` drives execution — add inline code comments confirming the pattern in `frontend/src/lib/commands/registry.ts`

**Checkpoint**: Registry single-source-of-truth pattern is verified. Adding a new command requires only one registry entry.

---

## Phase 8: User Story 6 — Comprehensive Test Coverage (Priority: P3)

**Goal**: Meaningful unit and integration tests cover command parsing, #help output, settings updates, error handling, and autocomplete generation, ensuring future changes do not introduce regressions.

**Independent Test**: Run the full test suite (`cd frontend && npm test`) and confirm all command-related tests pass covering happy-path and edge-case scenarios.

### Tests for User Story 6 ⚠️

- [x] T031 [P] [US6] Write edge-case parsing tests: bare `#` returns helpful message, `#` mid-sentence is NOT a command, extra whitespace is normalized (`#theme   dark` works), mixed case is handled (`#Theme Dark`), empty string is not a command, whitespace-only string is not a command in `frontend/src/lib/commands/registry.test.ts`
- [x] T032 [P] [US6] Write edge-case settings handler tests: concurrent rapid settings updates apply correctly, setting to same value returns appropriate message, all valid values for each setting command are accepted in `frontend/src/lib/commands/handlers/settings.test.ts`
- [x] T033 [P] [US6] Write autocomplete edge-case tests: overlay closes when `#` is deleted, overlay closes on message submit, no matches shows appropriate state, Tab key selects like Enter, wrapping navigation (ArrowDown past last item wraps to first) in `frontend/src/components/chat/CommandAutocomplete.test.tsx`
- [x] T034 [P] [US6] Write full integration tests: complete flow from typing `#theme dark` → autocomplete appears → submit → theme changes → confirmation message appears → input cleared; error flow from `#theme rainbow` → error message → input preserved in `frontend/src/components/chat/ChatInterface.test.tsx`
- [x] T035 [US6] Run full frontend test suite to verify all command system tests pass and no existing tests regress: `cd frontend && npm test`

**Checkpoint**: Comprehensive test coverage achieved. All happy-path and edge-case scenarios are covered across registry, handlers, hook, autocomplete, and integration levels.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final cleanup, documentation, and validation across all user stories

- [x] T036 [P] Code cleanup and consistent code style review across all command system files in `frontend/src/lib/commands/` and `frontend/src/hooks/useCommands.ts`
- [x] T037 [P] Verify accessibility: confirm `role="listbox"`, `role="option"`, and `aria-activedescendant` attributes are correctly set on autocomplete overlay in `frontend/src/components/chat/CommandAutocomplete.tsx`
- [x] T038 Run lint, type-check, and build to confirm no regressions: `cd frontend && npm run lint && npm run type-check && npm run build`
- [x] T039 Run quickstart.md validation: execute all commands from quickstart.md to verify developer workflow is accurate

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational (Phase 2) — creates the hook and help command
- **US2 (Phase 4)**: Depends on Foundational (Phase 2) and US1 (Phase 3, for useCommands hook)
- **US3 (Phase 5)**: Depends on Foundational (Phase 2) — can run in parallel with US1/US2 if hook exists
- **US4 (Phase 6)**: Depends on US1, US2, and US3 (integrates all components into chat flow)
- **US5 (Phase 7)**: Depends on US1 and US2 (verifies registry pattern with real commands)
- **US6 (Phase 8)**: Depends on all previous user stories (comprehensive edge-case tests)
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Starts after Foundational (Phase 2) — creates useCommands hook and help command — **MVP**
- **User Story 2 (P1)**: Starts after US1 (reuses useCommands hook) — extends command system with settings handlers
- **User Story 3 (P2)**: Starts after Foundational (Phase 2) — can partially parallel with US1/US2 (component-only)
- **User Story 4 (P2)**: Starts after US1, US2, US3 — integrates all pieces into ChatInterface
- **User Story 5 (P2)**: Starts after US1 and US2 — verifies registry drives all surfaces
- **User Story 6 (P3)**: Starts after all other stories — comprehensive test coverage

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Types/models before logic
- Pure functions before hooks
- Hooks before components
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- T005 and T006 (Phase 2) can run in parallel — different files
- T007 and T008 (Phase 3 tests) can run in parallel — different test files
- T015, T016, T017 (Phase 4 settings handlers for language, notifications, view) can run in parallel — independent handler functions with no shared state; T014 (theme handler) should complete first as it establishes the handler pattern
- T020 (Phase 5 tests) can start while Phase 3/4 implementation completes
- T024 (Phase 6 tests) can be drafted while Phase 5 completes
- T031, T032, T033, T034 (Phase 8) can all run in parallel — different test files

---

## Parallel Example: User Story 1

```bash
# Launch tests for User Story 1 together (write first, ensure they fail):
Task T007: "Write unit tests for help handler in frontend/src/lib/commands/handlers/help.test.ts"
Task T008: "Write unit tests for command registry in frontend/src/lib/commands/registry.test.ts"

# Then implement sequentially:
Task T009: "Implement help command handler in frontend/src/lib/commands/handlers/help.ts"
Task T010: "Register help command in frontend/src/lib/commands/registry.ts"
Task T011: "Create useCommands hook in frontend/src/hooks/useCommands.ts"
Task T012: "Write hook tests in frontend/src/hooks/useCommands.test.tsx"
```

## Parallel Example: User Story 6

```bash
# Launch all edge-case test tasks in parallel (different test files):
Task T031: "Edge-case parsing tests in frontend/src/lib/commands/registry.test.ts"
Task T032: "Edge-case settings handler tests in frontend/src/lib/commands/handlers/settings.test.ts"
Task T033: "Autocomplete edge-case tests in frontend/src/components/chat/CommandAutocomplete.test.tsx"
Task T034: "Full integration tests in frontend/src/components/chat/ChatInterface.test.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T002)
2. Complete Phase 2: Foundational (T003–T006)
3. Complete Phase 3: User Story 1 — #help command (T007–T012)
4. **STOP and VALIDATE**: Test `#help` command independently
5. Deploy/demo if ready — users can discover all commands

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (#help) → Test independently → Deploy/Demo (**MVP!**)
3. Add User Story 2 (Settings commands) → Test independently → Deploy/Demo
4. Add User Story 3 (Autocomplete) → Test independently → Deploy/Demo
5. Add User Story 4 (Chat integration) → Test independently → Deploy/Demo
6. Add User Story 5 (Registry verification) → Validate pattern
7. Add User Story 6 (Comprehensive tests) → Full test suite green
8. Polish → Final cleanup and validation

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (help command + hook) → then User Story 4 (integration)
   - Developer B: User Story 2 (settings handlers) → then User Story 5 (registry verification)
   - Developer C: User Story 3 (autocomplete component) → then User Story 6 (test coverage)
3. Stories complete and integrate in Phase 6 (US4)

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 39 |
| **Phase 1 (Setup)** | 2 tasks |
| **Phase 2 (Foundational)** | 4 tasks |
| **Phase 3 (US1 — Help, P1)** | 6 tasks |
| **Phase 4 (US2 — Settings, P1)** | 7 tasks |
| **Phase 5 (US3 — Autocomplete, P2)** | 4 tasks |
| **Phase 6 (US4 — Interception, P2)** | 5 tasks |
| **Phase 7 (US5 — Registry SoT, P2)** | 2 tasks |
| **Phase 8 (US6 — Test Coverage, P3)** | 5 tasks |
| **Phase 9 (Polish)** | 4 tasks |
| **Parallel opportunities** | 18 tasks marked [P] |
| **Suggested MVP scope** | Phase 1 + 2 + 3 (User Story 1: #help command) |

## Notes

- [P] tasks = different files, no dependencies — can run in parallel
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Tests are INCLUDED (explicitly requested in FR-019 and User Story 6)
- All file paths follow the structure defined in plan.md
- No backend changes required — this feature is entirely frontend
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
