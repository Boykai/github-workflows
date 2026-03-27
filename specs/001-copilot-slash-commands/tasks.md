# Tasks: Add 9 GitHub Copilot Slash Commands to Solune Chat

**Input**: Design documents from `/specs/001-copilot-slash-commands/`
**Prerequisites**: spec.md (user stories with priorities P1–P3), issue description (technical plan)

**Tests**: Included — the specification (FR-012, FR-013) explicitly requires frontend and backend tests.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Frontend**: `solune/frontend/src/`
- **Backend**: `solune/backend/src/`
- **Frontend tests**: `solune/frontend/src/lib/commands/__tests__/`
- **Backend tests**: `solune/backend/tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Extend shared type definitions and create new files needed across multiple user stories

- [ ] T001 Add optional `category` field (`'solune' | 'copilot'`) to `CommandDefinition` type in `solune/frontend/src/lib/commands/types.ts`
- [ ] T002 [P] Create Copilot passthrough handler file `solune/frontend/src/lib/commands/handlers/copilot.ts` exporting `copilotPassthroughHandler()` that returns `{ success: true, message: '', clearInput: true, passthrough: true }`
- [ ] T003 [P] Create backend Copilot commands service file `solune/backend/src/services/copilot_commands.py` with `COPILOT_COMMANDS` set and `COPILOT_COMMAND_PROMPTS` dict stub (empty prompts initially)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Register all 9 commands in the frontend registry and wire backend detection — MUST be complete before user stories can be validated end-to-end

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Tag all existing commands with `category: 'solune'` in `solune/frontend/src/lib/commands/registry.ts` (add `category: 'solune'` to every `registerCommand()` call for /help, /agent, /plan, /clear, /theme, /language, /notifications, /view, /experimental, /model, /mcp, /compact, /context, /diff, /usage, /share, /feedback)
- [ ] T005 Register 9 new Copilot commands (/explain, /fix, /doc, /tests, /setupTests, /new, /newNotebook, /search, /startDebugging) in `solune/frontend/src/lib/commands/registry.ts` with `handler: copilotPassthroughHandler`, `passthrough: true`, and `category: 'copilot'`
- [ ] T006 Implement `is_copilot_command(content: str) -> tuple[str, str] | None` function in `solune/backend/src/services/copilot_commands.py` — must match exact command names (longest match first for /new vs /newNotebook), extract arguments, return `None` for non-matches
- [ ] T007 Implement `execute_copilot_command(command: str, args: str, github_token: str) -> str` function in `solune/backend/src/services/copilot_commands.py` — builds `[{role: 'system', content: prompt}, {role: 'user', content: args}]` messages and calls `CopilotCompletionProvider.complete()`
- [ ] T008 Add `_handle_copilot_command()` method in `solune/backend/src/api/chat.py` at priority 0.1 (after `_handle_agent_command` at priority 0, before transcript handler at priority 0.5) — mirrors `_handle_agent_command` pattern: detect via `is_copilot_command()`, call `execute_copilot_command()`, create `ChatMessage(sender=ASSISTANT)`, call `add_message()`, return message or `None`

**Checkpoint**: Foundation ready — all 9 commands registered in frontend, backend can detect and route them

---

## Phase 3: User Story 1 — Invoke a Copilot Command from Chat Input (Priority: P1) 🎯 MVP

**Goal**: A user can type any of the 9 Copilot slash commands in the chat input, submit, and receive an AI-powered response from the Copilot completion provider

**Independent Test**: Type `/explain What is a closure?` in the chat input, submit, and verify a Copilot-generated explanation appears as an assistant message

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Create backend test file `solune/backend/tests/unit/test_copilot_commands.py` — test `is_copilot_command()` correctly parses all 9 commands with arguments, returns `(command, args)` tuples
- [ ] T010 [P] [US1] Add tests in `solune/backend/tests/unit/test_copilot_commands.py` — test `is_copilot_command()` returns `None` for non-Copilot input (plain text, `/help`, `/agent`, `/explains`, `/newtest`)
- [ ] T011 [P] [US1] Add tests in `solune/backend/tests/unit/test_copilot_commands.py` — test `is_copilot_command()` handles edge cases: empty arguments (`/explain`), longest match (`/newNotebook` vs `/new`), case sensitivity, whitespace
- [ ] T012 [P] [US1] Add tests in `solune/backend/tests/unit/test_copilot_commands.py` — test `execute_copilot_command()` calls `CopilotCompletionProvider.complete()` with correct system prompt and user message using `unittest.mock.AsyncMock`
- [ ] T013 [P] [US1] Create frontend test file `solune/frontend/src/lib/commands/__tests__/copilot-commands.test.ts` — test all 9 Copilot commands exist in registry via `getCommand()`, verify each has `passthrough: true` and `category: 'copilot'`
- [ ] T014 [P] [US1] Add tests in `solune/frontend/src/lib/commands/__tests__/copilot-commands.test.ts` — test `parseCommand()` correctly parses `/explain What is a closure?` as `{ command: 'explain', args: 'What is a closure?' }` for all 9 commands
- [ ] T015 [P] [US1] Add tests in `solune/frontend/src/lib/commands/__tests__/copilot-commands.test.ts` — test `copilotPassthroughHandler()` returns `{ success: true, message: '', clearInput: true, passthrough: true }`

### Implementation for User Story 1

- [ ] T016 [US1] Populate all 9 intent-specific system prompts in `COPILOT_COMMAND_PROMPTS` dict in `solune/backend/src/services/copilot_commands.py`: /explain (explain code/concepts with examples), /fix (identify issues, provide corrected code with explanation), /doc (generate idiomatic documentation comments), /tests (generate comprehensive unit tests with edge cases), /setupTests (recommend test framework, provide setup steps/config), /new (generate project scaffold with directory structure), /newNotebook (generate Jupyter notebook outline with cells), /search (generate effective code search queries/patterns), /startDebugging (generate debug launch.json config)
- [ ] T017 [US1] Add error handling in `_handle_copilot_command()` in `solune/backend/src/api/chat.py` — wrap `execute_copilot_command()` call with try/except, log error, return user-friendly error message without leaking internal details (follow `_handle_agent_command` pattern)
- [ ] T018 [US1] Run backend Copilot command tests: `cd solune/backend && python -m pytest tests/unit/test_copilot_commands.py -v` — verify all tests pass

**Checkpoint**: User Story 1 complete — users can invoke any of the 9 Copilot commands and receive intent-specific responses. Input is cleared after submission.

---

## Phase 4: User Story 2 — Discover Copilot Commands via Autocomplete Dropdown (Priority: P2)

**Goal**: When a user types `/` in the chat input, the autocomplete dropdown displays commands grouped under "Solune" and "GitHub Copilot" section headers

**Independent Test**: Type `/` in the chat input and verify the dropdown shows two category sections: "Solune" (with /help, /agent, /plan, /clear, etc.) and "GitHub Copilot" (with all 9 new commands)

### Implementation for User Story 2

- [ ] T019 [US2] Update `CommandAutocomplete.tsx` in `solune/frontend/src/components/chat/CommandAutocomplete.tsx` — group commands by `category` field, render "Solune" section header before `solune`-category commands and "GitHub Copilot" section header before `copilot`-category commands
- [ ] T020 [US2] Ensure category headers in `CommandAutocomplete.tsx` are non-selectable (not part of keyboard navigation index), styled distinctly from command items (e.g., smaller text, muted color, uppercase or bold label)
- [ ] T021 [US2] Verify autocomplete filtering still works — when user types `/ex`, only matching commands appear but category headers still display for non-empty groups
- [ ] T022 [US2] Run frontend lint and type-check: `cd solune/frontend && npm run lint && npm run type-check` — verify no errors introduced

**Checkpoint**: User Story 2 complete — autocomplete dropdown shows categorized commands with clear visual grouping

---

## Phase 5: User Story 3 — Each Copilot Command Produces Intent-Specific Responses (Priority: P3)

**Goal**: Each of the 9 Copilot commands produces a qualitatively different response tailored to its specific intent, driven by distinct system prompts

**Independent Test**: Submit the same code snippet to `/explain`, `/fix`, and `/doc` and verify each produces a different response aligned with its stated purpose

### Tests for User Story 3

- [ ] T023 [P] [US3] Add tests in `solune/backend/tests/unit/test_copilot_commands.py` — verify each of the 9 commands in `COPILOT_COMMAND_PROMPTS` has a non-empty, distinct system prompt string
- [ ] T024 [P] [US3] Add tests in `solune/backend/tests/unit/test_copilot_commands.py` — verify `execute_copilot_command()` passes the correct command-specific system prompt (not a generic one) for each of the 9 commands

### Implementation for User Story 3

- [ ] T025 [US3] Review and refine all 9 system prompts in `COPILOT_COMMAND_PROMPTS` in `solune/backend/src/services/copilot_commands.py` — ensure each prompt clearly instructs the model on its specific role: /explain → teaching tone with examples, /fix → corrected code with diff-style explanation, /doc → language-specific comment format, /tests → edge cases + assertions, /setupTests → framework recommendation + config files, /new → directory tree + boilerplate, /newNotebook → cell-by-cell outline, /search → regex patterns + grep commands, /startDebugging → launch.json with platform detection
- [ ] T026 [US3] Run backend Copilot command tests: `cd solune/backend && python -m pytest tests/unit/test_copilot_commands.py -v` — verify prompt distinctness tests pass

**Checkpoint**: User Story 3 complete — each command produces differentiated, intent-aligned responses

---

## Phase 6: User Story 4 — Existing Commands Remain Unaffected (Priority: P1)

**Goal**: All existing commands (/help, /agent, /plan, /clear, and others) continue to work exactly as before with zero regressions

**Independent Test**: Exercise each existing command and verify output/behavior is identical to pre-change baseline

### Tests for User Story 4

- [ ] T027 [P] [US4] Add tests in `solune/frontend/src/lib/commands/__tests__/copilot-commands.test.ts` — verify existing commands (/help, /agent, /plan, /clear) still exist in registry with `category: 'solune'` and their handlers are unchanged
- [ ] T028 [P] [US4] Add tests in `solune/frontend/src/lib/commands/__tests__/copilot-commands.test.ts` — verify `parseCommand()` for existing commands still works correctly (not intercepted by Copilot logic)
- [ ] T029 [P] [US4] Add tests in `solune/backend/tests/unit/test_copilot_commands.py` — verify `is_copilot_command()` returns `None` for `/help`, `/agent`, `/plan`, `/clear` and plain text messages

### Implementation for User Story 4

- [ ] T030 [US4] Run full frontend test suite: `cd solune/frontend && npm run test` — verify no regressions in existing command tests (registry.test.ts, settings.test.ts, help.test.ts, session.test.ts, monitoring.test.ts, advanced.test.ts)
- [ ] T031 [US4] Run full backend test suite: `cd solune/backend && python -m pytest` — verify no regressions in existing chat tests (test_api_chat.py and others)
- [ ] T032 [US4] Run frontend lint: `cd solune/frontend && npx eslint src/lib/commands/` — verify no lint errors in command directory

**Checkpoint**: User Story 4 complete — all existing commands verified unaffected

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, cleanup, and quality assurance across all stories

- [ ] T033 [P] Verify explicitly excluded commands (/clear, /compact, /fork, /yolo, init, /agents, /create-*) are NOT registered as Copilot commands — `/clear` and `/compact` remain as existing Solune commands (tagged `category: 'solune'`), and none of the excluded names appear in `COPILOT_COMMANDS` set or `COPILOT_COMMAND_PROMPTS` dict
- [ ] T034 Run full frontend CI pipeline: `cd solune/frontend && npm run lint && npm run type-check && npm run test:coverage && npm run build` — verify all pass
- [ ] T035 Run full backend test suite: `cd solune/backend && python -m pytest` — verify zero regressions across all test categories
- [ ] T036 Code review: verify `_handle_copilot_command()` in chat.py follows error handling pattern (`handle_service_error()` or try/except with safe error messages), no internal details leak to user
- [ ] T037 Code review: verify `copilot_commands.py` does NOT import or modify `completion_providers.py` internals — only uses public `CopilotCompletionProvider.complete()` API
- [ ] T038 Code review: verify exact command matching in `is_copilot_command()` — `/explains` must NOT match `/explain`, `/newtest` must NOT match `/new`, `/newNotebook` must match before `/new`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup (Phase 1) completion — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) — core command execution
- **User Story 2 (Phase 4)**: Depends on Foundational (Phase 2) — can run in parallel with US1
- **User Story 3 (Phase 5)**: Depends on User Story 1 (Phase 3) — refines prompts from US1
- **User Story 4 (Phase 6)**: Depends on Foundational (Phase 2) — can run in parallel with US1/US2
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Depends on Phase 2 — core MVP, no other story dependencies
- **User Story 2 (P2)**: Depends on Phase 2 — independent of US1 (commands just need to be registered)
- **User Story 3 (P3)**: Depends on US1 — refines the prompts that US1 creates
- **User Story 4 (P1)**: Depends on Phase 2 — regression testing, independent of other stories

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Backend service before API handler
- Registry changes before UI changes
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- **Phase 1**: T002 and T003 can run in parallel (different files: frontend handler vs backend service)
- **Phase 2**: T004 and T006/T007 can run in parallel (frontend registry vs backend service)
- **Phase 3 tests**: T009–T015 can ALL run in parallel (different test files, no dependencies)
- **Phase 4 + Phase 3**: US2 (autocomplete UI) can run in parallel with US1 (command execution)
- **Phase 5 tests**: T023 and T024 can run in parallel
- **Phase 6 tests**: T027–T029 can run in parallel (frontend vs backend tests)
- **Phase 7**: T033 can run in parallel with T034/T035

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (they target different test files/sections):
Task: T009 "Backend test: is_copilot_command() parses all 9 commands" in solune/backend/tests/unit/test_copilot_commands.py
Task: T010 "Backend test: is_copilot_command() rejects non-Copilot input" in solune/backend/tests/unit/test_copilot_commands.py
Task: T011 "Backend test: is_copilot_command() edge cases" in solune/backend/tests/unit/test_copilot_commands.py
Task: T012 "Backend test: execute_copilot_command() calls provider" in solune/backend/tests/unit/test_copilot_commands.py
Task: T013 "Frontend test: all 9 commands in registry" in solune/frontend/src/lib/commands/__tests__/copilot-commands.test.ts
Task: T014 "Frontend test: parseCommand() for Copilot commands" in solune/frontend/src/lib/commands/__tests__/copilot-commands.test.ts
Task: T015 "Frontend test: copilotPassthroughHandler() shape" in solune/frontend/src/lib/commands/__tests__/copilot-commands.test.ts
```

## Parallel Example: User Story 2 + User Story 1

```bash
# US2 (autocomplete UI) can run in parallel with US1 (command execution):
# Developer A works on US1 backend (T016–T018)
# Developer B works on US2 frontend (T019–T022)
# Both depend only on Phase 2 being complete
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup — extend types, create handler and service files
2. Complete Phase 2: Foundational — register commands, wire backend detection and routing
3. Complete Phase 3: User Story 1 — system prompts, error handling, full test suite
4. **STOP and VALIDATE**: Type `/explain What is a closure?` and verify response
5. Deploy/demo if ready — all 9 commands functional

### Incremental Delivery

1. Complete Setup + Foundational → Commands registered, backend routing ready
2. Add User Story 1 → Test independently → Commands work end-to-end (MVP!)
3. Add User Story 2 → Test independently → Autocomplete shows categorized commands
4. Add User Story 3 → Test independently → Each command produces distinct responses
5. Add User Story 4 → Test independently → Backward compatibility verified
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (backend prompts + error handling)
   - Developer B: User Story 2 (autocomplete UI grouping)
   - Developer C: User Story 4 (regression testing)
3. Developer A then refines prompts for User Story 3
4. Polish phase validates everything together

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 38 |
| **Phase 1 (Setup)** | 3 tasks |
| **Phase 2 (Foundational)** | 5 tasks |
| **Phase 3 (US1 — Invoke Commands)** | 10 tasks (7 test + 3 impl) |
| **Phase 4 (US2 — Autocomplete)** | 4 tasks |
| **Phase 5 (US3 — Intent Prompts)** | 4 tasks (2 test + 2 impl) |
| **Phase 6 (US4 — Backward Compat)** | 6 tasks (3 test + 3 impl) |
| **Phase 7 (Polish)** | 6 tasks |
| **Parallel opportunities** | 22 tasks marked [P] |
| **New files created** | 4 (copilot.ts, copilot-commands.test.ts, copilot_commands.py, test_copilot_commands.py) |
| **Modified files** | 4 (types.ts, registry.ts, CommandAutocomplete.tsx, chat.py) |
| **Suggested MVP scope** | Phases 1–3 (User Story 1: 18 tasks) |

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Tests are included per FR-012 (frontend) and FR-013 (backend) requirements
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All 9 commands: /explain, /fix, /doc, /tests, /setupTests, /new, /newNotebook, /search, /startDebugging
