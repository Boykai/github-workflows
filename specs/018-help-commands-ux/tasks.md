# Tasks: Enhance #help and General # Commands with Robust, Best-Practice Chat UX

**Input**: Design documents from `/specs/018-help-commands-ux/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Included — spec explicitly states extending existing vitest test suite (plan.md Constitution Check IV).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `frontend/src/` (all changes are frontend-only per plan.md)

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization — extend types, create helper utilities, update test factory

- [X] T001 Add optional `category` field to `CommandDefinition` interface in frontend/src/lib/commands/types.ts
- [X] T002 [P] Create helper utilities module with `levenshteinDistance`, `findClosestCommands`, and `truncateInput` in frontend/src/lib/commands/helpers.ts
- [X] T003 [P] Add optional `category` field to `createCommandDefinition` factory in frontend/src/test/factories/index.ts

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Registry infrastructure and category assignments that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Add `getCommandsByCategory()` function to frontend/src/lib/commands/registry.ts that groups commands by category with "General" first, others alphabetical, commands sorted alphabetically within each category
- [X] T005 Add `category: 'Settings'` to theme, language, notifications, view command registrations and `category: 'Workflow'` to agent command registration in frontend/src/lib/commands/registry.ts

**Checkpoint**: Foundation ready — command registry supports categories and helpers are available

---

## Phase 3: User Story 1 — Discover All Available Commands via #help (Priority: P1) 🎯 MVP

**Goal**: Users type `#help` and receive a well-structured, categorized listing of every available command with names, descriptions, and usage syntax.

**Independent Test**: Type `#help` in chat input and verify the response contains all registered commands organized into General, Settings, Workflow categories with names, descriptions, and syntax examples.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T006 [P] [US1] Add tests for categorized `#help` output in frontend/src/lib/commands/handlers/help.test.ts — verify response contains category headers (General, Settings, Workflow), all registered commands appear under correct category, commands without explicit category default to General, command entries show name, description, and syntax
- [X] T007 [P] [US1] Add test for empty registry edge case in frontend/src/lib/commands/handlers/help.test.ts — verify #help displays "no commands available" message when registry is empty
- [X] T008 [P] [US1] Add test for dynamically registered command appearing in #help output in frontend/src/lib/commands/handlers/help.test.ts — verify newly registered command automatically appears under its category

### Implementation for User Story 1

- [X] T009 [US1] Refactor `helpHandler` in frontend/src/lib/commands/handlers/help.ts to generate categorized listing using `getCommandsByCategory()` when args is empty — display "Available Commands:" header, category sections with indented command entries in `#syntax  —  description` format
- [X] T010 [US1] Ensure categorized #help output renders without horizontal scrolling at 320px viewport — keep lines within ~40 characters where possible, use indentation instead of tables in frontend/src/lib/commands/handlers/help.ts

**Checkpoint**: User Story 1 fully functional — `#help` returns categorized command listing

---

## Phase 4: User Story 2 — Receive Context-Sensitive Error Guidance (Priority: P2)

**Goal**: Users receive clear, actionable usage hints when they mistype a command or omit required arguments, including "Did you mean?" suggestions for misspelled commands.

**Independent Test**: Invoke `#theme` (no arg), `#theme purple` (invalid arg), and `#hep` (misspelled) — verify each returns a specific, helpful error message with correct syntax and valid options.

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T011 [P] [US2] Add tests for `levenshteinDistance` in frontend/src/lib/commands/helpers.test.ts — verify distance calculations for identical strings (0), single insertion (1), single deletion (1), single substitution (1), transposition (2), completely different strings
- [X] T012 [P] [US2] Add tests for `findClosestCommands` in frontend/src/lib/commands/helpers.test.ts — verify returns closest matches within maxDistance threshold, returns empty array when no matches, returns matches sorted by distance (closest first), default maxDistance is 2
- [X] T013 [P] [US2] Add tests for `truncateInput` in frontend/src/lib/commands/helpers.test.ts — verify short input returned unchanged, input longer than maxLength is truncated with ellipsis, default maxLength is 50
- [X] T014 [P] [US2] Add tests for "Did you mean?" suggestion in frontend/src/hooks/useCommands.test.tsx — verify unknown command `#hep` suggests `#help`, unknown command with no close match shows generic "Type #help" message, very long unknown command name is truncated in error message

### Implementation for User Story 2

- [X] T015 [US2] Update unknown-command handling in `executeCommand` within frontend/src/hooks/useCommands.ts — import `findClosestCommands` and `truncateInput` from helpers, check for fuzzy matches on unrecognized commands, include "Did you mean #<match>?" when match found, fall back to "Type #help to see available commands." when no match

**Checkpoint**: User Story 2 fully functional — misspelled commands and missing/invalid arguments return actionable guidance

---

## Phase 5: User Story 3 — Consistent and Accessible Response Formatting (Priority: P3)

**Goal**: All # command responses follow a consistent visual structure (summary line, detail, contextual hint) and convey meaning through text and structure, not color or emoji alone.

**Independent Test**: Execute multiple commands (success, error, info) and verify all responses follow the same three-part structure: what happened, detail/how to fix, and where to get more help.

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T016 [P] [US3] Add tests for consistent error format in frontend/src/lib/commands/handlers/help.test.ts — verify error responses for unknown single-command lookup follow three-part structure (what went wrong, how to fix, where to get help)
- [X] T017 [P] [US3] Add tests for consistent error format in frontend/src/lib/commands/handlers/settings.test.ts — verify missing-argument and invalid-argument errors show syntax hint and valid options

### Implementation for User Story 3

- [X] T018 [US3] Update error messages in settings handlers (theme, language, notifications, view) in frontend/src/lib/commands/handlers/settings.ts to follow consistent three-part format: what went wrong, correct syntax with valid options, "Type #help <command> for more details."
- [X] T019 [US3] Ensure success messages across all handlers use consistent structure — brief summary line followed by detail if applicable in frontend/src/lib/commands/handlers/settings.ts

**Checkpoint**: All command responses use consistent formatting — errors are actionable, success is scannable

---

## Phase 6: User Story 4 — Quick Help for a Specific Command (Priority: P4)

**Goal**: Users type `#help <command>` to see detailed usage for just that one command without scanning the full listing.

**Independent Test**: Type `#help theme` and verify the output shows only the #theme command's description, syntax, valid parameter values, and a usage example.

### Tests for User Story 4

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T020 [P] [US4] Add tests for single-command help in frontend/src/lib/commands/handlers/help.test.ts — verify `#help theme` shows detailed info for theme only (description, syntax, options, example), `#help nonexistent` shows "not found" message with hint to use #help, `#help #theme` (with hash prefix) correctly strips leading # and shows theme help, `#help` with no argument still shows full categorized listing

### Implementation for User Story 4

- [X] T021 [US4] Update `helpHandler` in frontend/src/lib/commands/handlers/help.ts to handle non-empty args — strip leading `#` from argument, look up command in registry, display detailed single-command info (description, usage syntax, valid options from parameterSchema, example), show "Command not found" message when lookup fails

**Checkpoint**: User Story 4 fully functional — `#help <command>` returns targeted command details

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T022 [P] Add test for `getCommandsByCategory` in frontend/src/lib/commands/registry.test.ts — verify "General" category appears first, other categories sorted alphabetically, commands sorted alphabetically within each category, commands without category default to "General"
- [X] T023 Run full frontend test suite and fix any regressions — `cd frontend && npx vitest run`
- [X] T024 Run type checking across frontend — `cd frontend && npx tsc --noEmit`
- [X] T025 Run linter across frontend — `cd frontend && npx eslint .`
- [ ] T026 Run quickstart.md validation — manually verify all 10 verification scenarios from specs/018-help-commands-ux/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (T001 must be complete for T004, T005) — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Phase 2 completion (needs `getCommandsByCategory`)
- **User Story 2 (Phase 4)**: Depends on Phase 1 completion (needs helpers.ts) — can run in parallel with Phase 3
- **User Story 3 (Phase 5)**: Can start after Phase 2 — can run in parallel with Phases 3 and 4
- **User Story 4 (Phase 6)**: Depends on Phase 3 (extends the same helpHandler refactored in US1)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Depends on Foundational (Phase 2). No dependencies on other stories.
- **User Story 2 (P2)**: Depends on Phase 1 (helpers.ts). Independent of US1 — touches different files (useCommands.ts, helpers.ts).
- **User Story 3 (P3)**: Depends on Foundational (Phase 2). Independent of US1/US2 — touches settings.ts handlers.
- **User Story 4 (P4)**: Depends on US1 (Phase 3) — extends helpHandler already refactored in US1.

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Helper utilities before consumers
- Registry changes before handler changes
- Core implementation before integration
- Story complete before checkpoint validation

### Parallel Opportunities

- **Phase 1**: T002 and T003 can run in parallel (different files, no dependencies)
- **Phase 3 (US1)**: T006, T007, T008 test tasks can all run in parallel
- **Phase 4 (US2)**: T011, T012, T013, T014 test tasks can all run in parallel
- **Phase 5 (US3)**: T016, T017 test tasks can run in parallel
- **Phase 6 (US4)**: T020 is a single test task
- **Phase 7**: T022 can run in parallel with other Polish tasks
- **Cross-story**: US1 (Phase 3) and US2 (Phase 4) can execute in parallel — they modify different files (help.ts vs. useCommands.ts/helpers.ts)
- **Cross-story**: US3 (Phase 5) can execute in parallel with US1 and US2 — it modifies settings.ts only

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: T006 "Tests for categorized #help output in frontend/src/lib/commands/handlers/help.test.ts"
Task: T007 "Test for empty registry edge case in frontend/src/lib/commands/handlers/help.test.ts"
Task: T008 "Test for dynamically registered command in frontend/src/lib/commands/handlers/help.test.ts"

# Then implement sequentially:
Task: T009 "Refactor helpHandler for categorized listing in frontend/src/lib/commands/handlers/help.ts"
Task: T010 "Ensure 320px viewport readability in frontend/src/lib/commands/handlers/help.ts"
```

## Parallel Example: User Story 2

```bash
# Launch all tests for User Story 2 together:
Task: T011 "Tests for levenshteinDistance in frontend/src/lib/commands/helpers.test.ts"
Task: T012 "Tests for findClosestCommands in frontend/src/lib/commands/helpers.test.ts"
Task: T013 "Tests for truncateInput in frontend/src/lib/commands/helpers.test.ts"
Task: T014 "Tests for 'Did you mean?' in frontend/src/hooks/useCommands.test.tsx"

# Then implement:
Task: T015 "Update unknown-command handling in frontend/src/hooks/useCommands.ts"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T003)
2. Complete Phase 2: Foundational (T004–T005)
3. Complete Phase 3: User Story 1 (T006–T010)
4. **STOP and VALIDATE**: Type `#help` and verify categorized output
5. Deploy/demo if ready — categorized help listing is immediately valuable

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (error guidance)
4. Add User Story 3 → Test independently → Deploy/Demo (consistent formatting)
5. Add User Story 4 → Test independently → Deploy/Demo (per-command help)
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (help.ts — categorized listing)
   - Developer B: User Story 2 (useCommands.ts + helpers.ts — error guidance)
   - Developer C: User Story 3 (settings.ts — consistent formatting)
3. User Story 4 starts after Developer A completes US1 (extends help.ts)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
