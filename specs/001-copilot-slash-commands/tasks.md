# Tasks: Add GitHub Copilot Slash Commands to Solune Chat

**Input**: Design documents from `/specs/001-copilot-slash-commands/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Not explicitly requested in the feature specification. Existing test patterns (registry.test.ts, settings.test.ts, help.test.ts) provide convention for new commands when tests are added later.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `solune/frontend/src/` (TypeScript/React), `solune/backend/src/` (Python/FastAPI)
- Handler files: `solune/frontend/src/lib/commands/handlers/`
- Registry: `solune/frontend/src/lib/commands/registry.ts`
- Types: `solune/frontend/src/lib/commands/types.ts`
- Hooks: `solune/frontend/src/hooks/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Extend type definitions and create new handler file stubs for the 3 new command domains

- [ ] T001 Extend CommandContext interface with `clearChat: () => Promise<void>` and `messages: ChatMessage[]` fields in solune/frontend/src/lib/commands/types.ts
- [ ] T002 [P] Create session command handler file solune/frontend/src/lib/commands/handlers/session.ts with module structure and type imports
- [ ] T003 [P] Create monitoring command handler file solune/frontend/src/lib/commands/handlers/monitoring.ts with module structure and type imports
- [ ] T004 [P] Create advanced command handler file solune/frontend/src/lib/commands/handlers/advanced.ts with module structure and type imports

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Wire the extended CommandContext so handlers can access clearChat and messages at runtime

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Wire clearChat and messages into CommandContext builder in solune/frontend/src/hooks/useCommands.ts so handlers receive them at execution time
- [ ] T006 Pass clearChat (from clearChatMutation) and messages (from chat state) from useChat hook to useCommands in solune/frontend/src/hooks/useChat.ts

**Checkpoint**: Foundation ready — CommandContext provides clearChat and messages to all command handlers

---

## Phase 3: User Story 1 — Manage Chat Session (Priority: P1) 🎯 MVP

**Goal**: Users can clear conversations, compact context, and view session statistics using /clear, /compact, and /context

**Independent Test**: Open a chat, send several messages, then use /clear (all messages removed from UI and backend), /compact (AI summarizes conversation), and /context (shows message count, proposals, pipelines)

### Implementation for User Story 1

- [ ] T007 [US1] Implement clearHandler in solune/frontend/src/lib/commands/handlers/session.ts — calls context.clearChat(), handles empty conversation edge case (display "No messages to clear" if already empty)
- [ ] T008 [US1] Implement compactHandler (passthrough) in solune/frontend/src/lib/commands/handlers/session.ts — returns { passthrough: true } to forward /compact to backend AI for conversation summarization
- [ ] T009 [US1] Implement contextHandler (passthrough) in solune/frontend/src/lib/commands/handlers/session.ts — returns { passthrough: true } to forward /context to backend for session stats
- [ ] T010 [US1] Register /clear, /compact, /context commands in solune/frontend/src/lib/commands/registry.ts with correct name, description, syntax, handler, and passthrough flag

**Checkpoint**: User Story 1 fully functional — /clear deletes all messages (UI + backend), /compact forwards to AI for summarization, /context forwards to backend for session stats

---

## Phase 4: User Story 2 — Customize AI Experience (Priority: P2)

**Goal**: Users can view/switch AI models with /model and toggle experimental features with /experimental

**Independent Test**: Type /model to see current model and alternatives, /model [name] to switch, /experimental to see status, /experimental on|off to toggle

### Implementation for User Story 2

- [ ] T011 [P] [US2] Implement modelHandler (passthrough) in solune/frontend/src/lib/commands/handlers/advanced.ts — returns { passthrough: true } to forward /model [MODEL] to backend for model show/switch
- [ ] T012 [P] [US2] Implement experimentalHandler in solune/frontend/src/lib/commands/handlers/settings.ts — toggles experimental features via context.updateSettings({ experimental: { enabled } }), shows status when no args, handles already-enabled/disabled edge case
- [ ] T013 [US2] Register /model and /experimental commands in solune/frontend/src/lib/commands/registry.ts with correct name, description, syntax, handler, and passthrough flag

**Checkpoint**: User Story 2 fully functional — /model forwards to backend for model management, /experimental toggles features locally and persists setting

---

## Phase 5: User Story 3 — Monitor and Share Sessions (Priority: P3)

**Goal**: Users can review changes with /diff, check metrics with /usage, export chat with /share, and submit feedback with /feedback

**Independent Test**: Type /diff (see task/issue changes), /usage (see session metrics), /share (download Markdown file), /feedback (see feedback link)

### Implementation for User Story 3

- [ ] T014 [US3] Implement diffHandler (passthrough) in solune/frontend/src/lib/commands/handlers/monitoring.ts — returns { passthrough: true } to forward /diff to backend for session change summary
- [ ] T015 [US3] Implement usageHandler (passthrough) in solune/frontend/src/lib/commands/handlers/monitoring.ts — returns { passthrough: true } to forward /usage to backend for session metrics
- [ ] T016 [US3] Implement shareHandler (local) in solune/frontend/src/lib/commands/handlers/monitoring.ts — reads context.messages, generates Markdown with metadata header (export timestamp, message count, sender/timestamp per message), triggers browser download using Blob + URL.createObjectURL, handles empty conversation edge case
- [ ] T017 [US3] Implement feedbackHandler (local) in solune/frontend/src/lib/commands/handlers/monitoring.ts — returns static message with clickable feedback link (https://github.com/Boykai/github-workflows/discussions)
- [ ] T018 [US3] Register /diff, /usage, /share, /feedback commands in solune/frontend/src/lib/commands/registry.ts with correct name, description, syntax, handler, and passthrough flag

**Checkpoint**: User Story 3 fully functional — /diff and /usage forward to backend, /share exports Markdown, /feedback shows link

---

## Phase 6: User Story 4 — Advanced Configuration (Priority: P4)

**Goal**: Power users can manage MCP configurations with /mcp and create/view execution plans with /plan

**Independent Test**: Type /mcp show (list configs), /mcp add (add config), /mcp delete (remove config), /plan (view plan), /plan [description] (create plan)

### Implementation for User Story 4

- [ ] T019 [US4] Implement mcpHandler (passthrough) in solune/frontend/src/lib/commands/handlers/advanced.ts — returns { passthrough: true } to forward /mcp [show|add|delete] to backend for MCP configuration management
- [ ] T020 [US4] Implement planHandler (passthrough) in solune/frontend/src/lib/commands/handlers/advanced.ts — returns { passthrough: true } to forward /plan [description] to backend for plan creation/display
- [ ] T021 [US4] Register /mcp and /plan commands in solune/frontend/src/lib/commands/registry.ts with correct name, description, syntax, handler, and passthrough flag

**Checkpoint**: User Story 4 fully functional — /mcp and /plan forward to backend for advanced configuration and planning

---

## Phase 7: User Story 5 — Command Discoverability (Priority: P5)

**Goal**: All 20 commands (6 existing + 14 new) are discoverable via /help and HelpPage with zero manual updates

**Independent Test**: Type /help and verify all registered commands (6 existing + 11 new = 17 minimum) are listed with correct syntax and descriptions; visit HelpPage and verify same list

### Implementation for User Story 5

- [ ] T022 [US5] Verify /help command output lists all registered commands (6 existing + 11 new) with correct syntax via getAllCommands() in solune/frontend/src/lib/commands/registry.ts
- [ ] T023 [US5] Verify HelpPage displays all registered commands with descriptions and syntax in solune/frontend/src/pages/HelpPage.tsx (auto-updates from registry — no code changes expected)

**Checkpoint**: All 20 commands discoverable — /help and HelpPage automatically reflect the full registry

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Edge case hardening, documentation, and validation across all user stories

- [ ] T024 [P] Validate edge case handling for /clear on empty conversation and /compact on short conversation in solune/frontend/src/lib/commands/handlers/session.ts
- [ ] T025 [P] Validate edge case handling for /share on empty conversation and passthrough error display in solune/frontend/src/lib/commands/handlers/monitoring.ts
- [ ] T026 Run quickstart.md validation per specs/001-copilot-slash-commands/quickstart.md (frontend build, lint, type-check, backend tests)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on T001 (CommandContext type extensions) — BLOCKS all user stories
- **User Stories (Phase 3–7)**: All depend on Foundational phase completion
  - User stories can then proceed in priority order (P1 → P2 → P3 → P4 → P5)
  - Or in parallel if team capacity allows (US1–US4 have no cross-story dependencies)
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) — shares advanced.ts with US2 T011, so T019/T020 should run after T011
- **User Story 5 (P5)**: Depends on ALL other stories being complete (verifies full registry)

### Within Each User Story

- Handler implementations before registry registration
- Local command handlers include edge case validation inline
- Passthrough command handlers are simple stubs returning { passthrough: true }
- Registry registration is the final step per story (single file: registry.ts)

### Parallel Opportunities

- **Phase 1**: T002, T003, T004 can run in parallel (different new files)
- **Phase 4**: T011 and T012 can run in parallel (different files: advanced.ts vs. settings.ts)
- **Phase 7**: T022 and T023 can run in parallel (different verification targets)
- **Phase 8**: T024 and T025 can run in parallel (different handler files)
- **Cross-story**: US1, US2, US3 can run in parallel after Foundational (different handler files). US4 shares advanced.ts with US2 — schedule accordingly.

---

## Parallel Example: User Story 2

```text
# T011 and T012 can run in parallel (different files):
Task T011: "Implement modelHandler (passthrough) in solune/frontend/src/lib/commands/handlers/advanced.ts"
Task T012: "Implement experimentalHandler in solune/frontend/src/lib/commands/handlers/settings.ts"

# Then T013 after both complete (registry.ts):
Task T013: "Register /model, /experimental commands in solune/frontend/src/lib/commands/registry.ts"
```

## Parallel Example: Cross-Story

```text
# After Phase 2 (Foundational) completes, these stories can start in parallel:
Developer A: Phase 3 (US1) — session.ts + registry.ts registrations
Developer B: Phase 4 (US2) — advanced.ts (modelHandler) + settings.ts + registry.ts registrations
Developer C: Phase 5 (US3) — monitoring.ts + registry.ts registrations

# Phase 6 (US4) should follow US2 since both use advanced.ts
# Phase 7 (US5) must wait for all stories to verify full registry
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T004)
2. Complete Phase 2: Foundational (T005–T006) — CRITICAL: blocks all stories
3. Complete Phase 3: User Story 1 (T007–T010)
4. **STOP and VALIDATE**: Test /clear, /compact, /context independently
5. Deploy/demo if ready — 3 new commands available

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready (6 tasks)
2. Add User Story 1 → Test independently → Deploy/Demo (MVP: +3 commands = 9 total)
3. Add User Story 2 → Test independently → Deploy/Demo (+2 commands = 11 total)
4. Add User Story 3 → Test independently → Deploy/Demo (+4 commands = 15 total)
5. Add User Story 4 → Test independently → Deploy/Demo (+2 commands = 17 total)
6. Complete User Story 5 → Verify all commands discoverable via /help and HelpPage
7. Each story adds value without breaking previous stories

> **Note**: 11 new commands are fully specified (17 total). The spec targets ~14 new (20 total); up to 3 additional commands may be added once the truncated original issue is clarified.

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (Phases 1–2)
2. Once Foundational is done:
   - Developer A: User Story 1 (session.ts — /clear, /compact, /context)
   - Developer B: User Story 2 (advanced.ts modelHandler + settings.ts /experimental)
   - Developer C: User Story 3 (monitoring.ts — /diff, /usage, /share, /feedback)
3. After Developer B completes: Developer D starts User Story 4 (advanced.ts — /mcp, /plan)
4. After all complete: User Story 5 verification + Polish

---

## Command-to-Task Mapping

| Command | Type | Handler File | User Story | Tasks |
|---------|------|-------------|------------|-------|
| `/clear` | Local + API | handlers/session.ts | US1 | T007, T010 |
| `/compact` | Passthrough | handlers/session.ts | US1 | T008, T010 |
| `/context` | Passthrough | handlers/session.ts | US1 | T009, T010 |
| `/model` | Passthrough | handlers/advanced.ts | US2 | T011, T013 |
| `/experimental` | Local (settings) | handlers/settings.ts | US2 | T012, T013 |
| `/diff` | Passthrough | handlers/monitoring.ts | US3 | T014, T018 |
| `/usage` | Passthrough | handlers/monitoring.ts | US3 | T015, T018 |
| `/share` | Local | handlers/monitoring.ts | US3 | T016, T018 |
| `/feedback` | Local | handlers/monitoring.ts | US3 | T017, T018 |
| `/mcp` | Passthrough | handlers/advanced.ts | US4 | T019, T021 |
| `/plan` | Passthrough | handlers/advanced.ts | US4 | T020, T021 |

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Passthrough handlers are simple stubs: `{ success: true, message: '', clearInput: true, passthrough: true }`
- Local handlers contain actual logic: /clear calls clearChat, /share generates Markdown, /feedback returns link, /experimental toggles settings
- HelpPage and /help auto-update from registry — no manual documentation needed
- /theme enhancements deferred to follow-up feature (research.md decision #2)
- Case-insensitive input already handled by existing parseCommand() (research.md decision #9)
- Unknown command error already handled by existing executeCommand() (research.md decision #10)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
