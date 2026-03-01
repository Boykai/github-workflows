# Tasks: Custom Agent Creation via Chat (#agent)

**Input**: Design documents from `/specs/001-custom-agent-creation/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Not explicitly requested in the feature specification. Test tasks are omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. User stories map to spec.md priorities (P1–P5).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create new files that all user stories depend on — Pydantic models and database migration.

- [X] T001 Create Pydantic models (CreationStep enum, AgentCreationState, AgentPreview, PipelineStepResult) per data-model.md in backend/src/models/agent_creator.py
- [X] T002 [P] Create database migration for agent_configs table per data-model.md schema in backend/src/migrations/007_agent_configs.sql

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Extend existing services with shared methods that multiple user stories require. These are the GitHub GraphQL operations and AI generation methods.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T003 Add GraphQL constants (GET_REPOSITORY_INFO_QUERY, CREATE_BRANCH_MUTATION, CREATE_COMMIT_ON_BRANCH_MUTATION, CREATE_PULL_REQUEST_MUTATION) per research.md R-002 in backend/src/services/github_projects/graphql.py
- [X] T004 Implement get_repository_info() and create_branch() methods using new GraphQL constants per contracts in backend/src/services/github_projects/service.py
- [X] T005 Implement commit_files() with Base64 encoding and create_pull_request() methods per contracts in backend/src/services/github_projects/service.py
- [X] T006 [P] Add generate_agent_config() and edit_agent_config() methods using _call_completion() per contracts in backend/src/services/ai_agent.py

**Checkpoint**: Foundation ready — all shared service extensions in place, user story implementation can now begin.

---

## Phase 3: User Story 1 — Create Agent via In-App Chat (Priority: P1) 🎯 MVP

**Goal**: Admin user types `#agent <description> #<status>` in the chat widget and completes the full guided flow: parse → resolve status → AI preview → confirm → pipeline creates all artifacts.

**Independent Test**: Type `#agent Reviews PRs for security vulnerabilities #in-review` in the chat widget, review the preview, confirm with "looks good", verify saved config + GitHub Issue + branch with config files + PR + board update.

### Implementation for User Story 1

- [X] T007 [US1] Create AgentCreatorService scaffold with BoundedDict state store, parse_command(), and basic fuzzy_match_status() (normalized exact match) in backend/src/services/agent_creator.py
- [X] T008 [US1] Implement generate_preview() delegating to AIAgentService.generate_agent_config() and basic confirmation keyword detection in backend/src/services/agent_creator.py
- [X] T009 [US1] Implement execute_pipeline() with all 7 steps (save config, create column, create issue, create branch, commit files, open PR, move issue to In Review) and best-effort error handling in backend/src/services/agent_creator.py
- [X] T010 [US1] Implement handle_message() state machine routing (PARSE → RESOLVE_STATUS → PREVIEW → EXECUTING → DONE) with markdown-formatted responses in backend/src/services/agent_creator.py
- [X] T011 [US1] Add #agent command routing as Priority 0 in send_message() with admin check before AI calls in backend/src/api/chat.py
- [X] T012 [P] [US1] Verify selected project context (session.selected_project_id) is available for #agent flow and add missing-project error handling in frontend/src/hooks/useChat.ts

**Checkpoint**: User Story 1 fully functional — admin can create an agent end-to-end via in-app chat.

---

## Phase 4: User Story 2 — Create Agent via Signal (Priority: P2)

**Goal**: Admin user sends `#agent` command via Signal. If multiple projects are accessible, system presents a numbered list for selection. Same guided flow then proceeds.

**Independent Test**: Send `#agent Triages new issues #backlog` via Signal, select a project from the numbered list, complete the flow, verify all artifacts created.

### Implementation for User Story 2

- [X] T013 [US2] Add #agent command detection in process_signal_chat() after confirm/reject keyword check, before _run_ai_pipeline() in backend/src/services/signal_chat.py
- [X] T014 [US2] Implement RESOLVE_PROJECT step with numbered project list for multi-project users and auto-select for single-project users in backend/src/services/agent_creator.py

**Checkpoint**: User Story 2 functional — agent creation works via Signal with project selection.

---

## Phase 5: User Story 3 — Status Column Resolution and Creation (Priority: P3)

**Goal**: Status name matching handles all documented variations (hyphenated, underscored, mixed case, concatenated), detects ambiguous matches, and prompts user when no status is provided.

**Independent Test**: Provide `#in-review`, `#InReview`, `#IN_REVIEW` against a project with "In Review" column — all resolve correctly. Provide `#review` against a project with both "In Review" and "Code Review" — system presents both for selection.

### Implementation for User Story 3

- [X] T015 [US3] Enhance fuzzy_match_status() to detect and present ambiguous matches (multiple normalized collisions) for user selection per FR-009 in backend/src/services/agent_creator.py
- [X] T016 [US3] Implement no-status-provided flow (RESOLVE_STATUS prompts with existing column list and new-column option) per FR-008 in backend/src/services/agent_creator.py

**Checkpoint**: Status resolution handles all edge cases — variations, ambiguity, and missing status.

---

## Phase 6: User Story 4 — AI Preview & Edit Loop (Priority: P4)

**Goal**: AI generates a complete preview (name, description, system prompt, status, tools) and the user can request multiple rounds of natural language edits before confirming.

**Independent Test**: Generate a preview, request "change the name to SecBot", verify preview updates. Request "also update the system prompt to check for SQL injection", verify cumulative changes preserved. Confirm after 3+ edit rounds.

### Implementation for User Story 4

- [X] T017 [US4] Implement apply_edit() delegating to AIAgentService.edit_agent_config() for natural language edit requests in backend/src/services/agent_creator.py
- [X] T018 [US4] Implement multi-round EDIT_LOOP state with cumulative edit tracking and re-display after each edit per FR-013 in backend/src/services/agent_creator.py

**Checkpoint**: Preview and edit loop supports unlimited iterative refinement with cumulative changes.

---

## Phase 7: User Story 5 — Pipeline Execution & Artifact Generation (Priority: P5)

**Goal**: Pipeline creates all artifacts reliably with idempotent handling (existing resources treated as success), duplicate name detection, proper file generation, and formatted per-step status reporting.

**Independent Test**: Confirm an agent, verify all 7 artifacts exist. Re-run against same name — system detects conflict. Simulate a step failure — remaining steps still execute and report shows checkmarks/crosses.

### Implementation for User Story 5

- [X] T019 [US5] Add duplicate agent name detection (query agent_configs by name+project_id) before pipeline execution per FR-026 in backend/src/services/agent_creator.py
- [X] T020 [US5] Implement idempotent step handling (existing column/branch/PR treated as success) per FR-024 in backend/src/services/agent_creator.py
- [X] T021 [US5] Generate agent YAML config, prompt markdown, and README entry content for commit per research.md R-009 in backend/src/services/agent_creator.py
- [X] T022 [US5] Format per-step status report with checkmarks/crosses, error details, and artifact URLs per FR-023 in backend/src/services/agent_creator.py

**Checkpoint**: Pipeline execution is robust, idempotent, and produces clear status reports.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories.

- [X] T023 [P] Add comprehensive logging (structlog pattern) for all #agent conversation states and pipeline steps in backend/src/services/agent_creator.py
- [X] T024 [P] Update project agent_pipeline_mappings to include newly created agent after successful pipeline execution in backend/src/services/agent_creator.py
- [X] T025 Run quickstart.md end-to-end validation of the #agent command flow

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion (models used by service methods) — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Phase 2 completion — delivers MVP
- **User Stories 2–5 (Phases 4–7)**: All depend on Phase 3 (US1) — each refines a different aspect of the core flow
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: Depends on Foundational only — no other story dependencies. This is the MVP.
- **US2 (P2)**: Depends on US1 (needs AgentCreatorService and handle_message state machine)
- **US3 (P3)**: Depends on US1 (enhances fuzzy_match_status created in US1)
- **US4 (P4)**: Depends on US1 (enhances PREVIEW/EDIT_LOOP states from US1)
- **US5 (P5)**: Depends on US1 (enhances execute_pipeline created in US1)
- **US2, US3, US4, US5** are independent of each other and can proceed in any order after US1

### Within Each User Story

- Models before services
- Services before API routing
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- **Phase 1**: T001 ∥ T002 (different files: models vs migration)
- **Phase 2**: T006 ∥ T003→T004→T005 (ai_agent.py vs graphql.py + service.py chain)
- **Phase 3**: T012 ∥ T007→T008→T009→T010→T011 (frontend vs backend)
- **Phases 4–7**: US2, US3, US4, US5 can proceed in parallel after US1 (each modifies different logic areas, though same primary file)

---

## Parallel Example: User Story 1 (MVP)

```bash
# Phase 1 — Launch setup tasks in parallel:
Task: T001 "Create Pydantic models in backend/src/models/agent_creator.py"
Task: T002 "Create migration in backend/src/migrations/007_agent_configs.sql"

# Phase 2 — Launch foundational tasks (parallel where possible):
Task: T003 "GraphQL constants in graphql.py"
Task: T006 "AI service methods in ai_agent.py"  # parallel with T003

# Phase 2 continued — Sequential (depends on T003):
Task: T004 "get_repository_info + create_branch in service.py"
Task: T005 "commit_files + create_pull_request in service.py"

# Phase 3 — US1 implementation (sequential backend, parallel frontend):
Task: T007 "AgentCreatorService scaffold with parse_command"
Task: T008 "generate_preview + confirmation detection"
Task: T009 "execute_pipeline with 7 steps"
Task: T010 "handle_message state machine"
Task: T011 "#agent routing in chat.py"
Task: T012 "Frontend project context verification"  # parallel with T007-T011
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T002)
2. Complete Phase 2: Foundational (T003–T006) — **CRITICAL, blocks all stories**
3. Complete Phase 3: User Story 1 (T007–T012)
4. **STOP and VALIDATE**: Test the full `#agent` flow in the chat widget end-to-end
5. Deploy/demo if ready — this is a fully functional agent creation feature

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 → Test independently → **Deploy (MVP!)**
3. Add US2 → Test Signal flow → Deploy (multi-channel)
4. Add US3 → Test status edge cases → Deploy (robust matching)
5. Add US4 → Test edit loop → Deploy (refined UX)
6. Add US5 → Test pipeline resilience → Deploy (production-ready)
7. Polish → Logging, pipeline mapping updates, final validation
8. Each story adds value without breaking previous stories

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks in the same phase
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable after US1 (MVP) exists
- agent_creator.py is the primary new file — US1 creates it, US2–US5 enhance it
- Commit after each task or logical group
- Stop at any checkpoint to validate the story independently
