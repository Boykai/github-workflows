# Tasks: Add #help Command to User Chat for In-Chat Command Reference

**Input**: Design documents from `/specs/032-chat-help-command/`
**Prerequisites**: plan.md (required), parent issue #2785 context as user-story source because `spec.md` is absent, research.md, data-model.md, quickstart.md, contracts/components.md

**Tests**: Required. Update the existing Vitest coverage in `frontend/src/lib/commands/registry.test.ts` and `frontend/src/lib/commands/handlers/help.test.ts` before implementation.

**Organization**: Tasks are grouped by user story to keep the `#help` alias change independently implementable and testable with a surgical frontend-only scope.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Load the feature design inputs and lock the scope to the planned command-system files only.

- [ ] T001 Review feature scope, constraints, and success conditions in `specs/032-chat-help-command/plan.md` and `specs/032-chat-help-command/research.md`
- [ ] T002 [P] Review parser, output, and verification expectations in `specs/032-chat-help-command/data-model.md`, `specs/032-chat-help-command/contracts/components.md`, and `specs/032-chat-help-command/quickstart.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Confirm the existing command surfaces and test seams that the feature will extend without broadening scope.

**⚠️ CRITICAL**: No user story work should begin until these file-level touch points are confirmed.

- [ ] T003 Verify the current command parsing and help output behavior in `frontend/src/lib/commands/registry.ts` and `frontend/src/lib/commands/handlers/help.ts`
- [ ] T004 [P] Verify the existing Vitest coverage structure to extend in place within `frontend/src/lib/commands/registry.test.ts` and `frontend/src/lib/commands/handlers/help.test.ts`

**Checkpoint**: The exact implementation and verification files are confirmed, so the P1 story can proceed without unrelated edits.

---

## Phase 3: User Story 1 - Trigger in-chat help with `#help` (Priority: P1) 🎯 MVP

**Goal**: Let a chat user type `#help` and receive the same local help response as `/help`, while keeping Markdown headings and other non-command `#` content untouched.

**Independent Test**: In chat, submit `#help`, `#HELP`, and `  #help  ` and verify the user sees the local help system response including `/help (or #help)`; submit `# Heading` and verify it is not parsed as a command; run the targeted Vitest suites for the updated command files.

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests first and confirm they fail before implementation.**

- [ ] T005 [P] [US1] Add `#help` alias parsing coverage for exact match, case-insensitivity, whitespace trimming, raw preservation, and non-matching `#` inputs in `frontend/src/lib/commands/registry.test.ts`
- [ ] T006 [P] [US1] Add help-output coverage asserting the `/help` entry advertises `#help` in `frontend/src/lib/commands/handlers/help.test.ts`

### Implementation for User Story 1

- [ ] T007 [US1] Implement the exact-match `#help` alias in `frontend/src/lib/commands/registry.ts` without changing general `#` Markdown handling
- [ ] T008 [US1] Update the help command output to annotate the `/help` entry with `#help` in `frontend/src/lib/commands/handlers/help.ts`
- [ ] T009 [US1] Run `cd frontend && npx vitest run src/lib/commands/registry.test.ts src/lib/commands/handlers/help.test.ts` to validate `frontend/src/lib/commands/registry.test.ts` and `frontend/src/lib/commands/handlers/help.test.ts`

**Checkpoint**: `#help` works as a local help alias, existing `/help` behavior remains intact, and the targeted Vitest suites pass.

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: Final verification of the surgical frontend change against the documented quickstart and no-regression constraints.

- [ ] T010 Validate the manual verification scenarios in `specs/032-chat-help-command/quickstart.md` against `frontend/src/lib/commands/registry.ts` and `frontend/src/lib/commands/handlers/help.ts`
- [ ] T011 Confirm the delivered scope still matches the planned file set in `specs/032-chat-help-command/plan.md` by limiting implementation changes to `frontend/src/lib/commands/registry.ts`, `frontend/src/lib/commands/handlers/help.ts`, `frontend/src/lib/commands/registry.test.ts`, and `frontend/src/lib/commands/handlers/help.test.ts`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion — confirms the exact code and test surfaces before editing.
- **User Story 1 (Phase 3)**: Depends on Foundational completion.
- **Polish (Phase 4)**: Depends on User Story 1 completion.

### User Story Dependencies

- **User Story 1 (P1)**: Starts after Phase 2 and has no dependency on other stories because this feature has a single scoped story.

### Within User Story 1

- Write and fail tests in `frontend/src/lib/commands/registry.test.ts` and `frontend/src/lib/commands/handlers/help.test.ts` before implementation.
- Implement parsing in `frontend/src/lib/commands/registry.ts` before finalizing output validation.
- Update `frontend/src/lib/commands/handlers/help.ts` after the parser change so the user-facing response advertises the new alias.
- Run targeted Vitest validation after both implementation tasks complete.

### Parallel Opportunities

- T001 and T002 can be completed in parallel while reviewing different design artifacts.
- T003 and T004 can be completed in parallel because they inspect different implementation and test files.
- T005 and T006 can be completed in parallel because they update different test files.

---

## Parallel Example: User Story 1

```bash
# Write the two required test updates in parallel before implementation:
Task: "Add #help alias parsing coverage in frontend/src/lib/commands/registry.test.ts"
Task: "Add help-output coverage for #help in frontend/src/lib/commands/handlers/help.test.ts"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. **STOP and VALIDATE**: Run the targeted Vitest command and the quickstart scenarios for `#help`.

### Incremental Delivery

1. Lock scope to the four planned command files.
2. Add failing tests for parsing and help output.
3. Implement the parser alias and help text update.
4. Validate with targeted Vitest, then complete manual quickstart verification.

### Parallel Team Strategy

With two contributors:

1. Contributor A updates `frontend/src/lib/commands/registry.test.ts`, then `frontend/src/lib/commands/registry.ts`.
2. Contributor B updates `frontend/src/lib/commands/handlers/help.test.ts`, then `frontend/src/lib/commands/handlers/help.ts`.
3. Rejoin for T009-T011 verification once both file pairs are complete.

---

## Notes

- `spec.md` is absent for this feature; the single P1 story is derived from parent issue #2785 plus `specs/032-chat-help-command/plan.md` and `specs/032-chat-help-command/research.md`.
- Keep the implementation surgical: do not introduce new files, new dependencies, or backend changes.
- `[P]` tasks are limited to work on separate files with no incomplete dependencies.
- Every implementation task references the planned frontend command files named in `specs/032-chat-help-command/plan.md` and `specs/032-chat-help-command/contracts/components.md`.
