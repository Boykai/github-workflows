# Tasks: Agents Section on Project Board

**Input**: Design documents from `/specs/017-agents-section/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/agents-api.yaml

**Tests**: Not explicitly requested in spec. Test tasks omitted.

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story (e.g., [US1], [US2])
- Exact file paths included in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization — new files, directories, route registration

- [x] T001 Create backend agents service directory structure: `backend/src/services/agents/__init__.py`
- [x] T002 [P] Create backend Pydantic models file `backend/src/models/agents.py` with `AgentStatus`, `AgentSource`, `Agent`, `AgentCreate`, `AgentUpdate`, `AgentChatMessage`, `AgentChatResponse`, `AgentDeleteResult`, `AgentCreateResult` per data-model.md
- [x] T003 [P] Create backend API router scaffold `backend/src/api/agents.py` with empty route handlers for GET, POST, PATCH, DELETE, and chat endpoints per contracts/agents-api.yaml
- [x] T004 Register agents router in `backend/src/api/__init__.py` under `/agents` prefix with tag `agents`
- [x] T005 [P] Create frontend agents component directory with placeholder files: `frontend/src/components/agents/AgentsPanel.tsx`, `frontend/src/components/agents/AgentCard.tsx`, `frontend/src/components/agents/AddAgentModal.tsx`, `frontend/src/components/agents/AgentChatFlow.tsx`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: DRY extraction and shared infrastructure that all user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 Make `_generate_config_files` public (rename to `generate_config_files`) in `backend/src/services/agent_creator.py` and update all internal callers in the same file
- [x] T007 Make `_generate_issue_body` public (rename to `generate_issue_body`) in `backend/src/services/agent_creator.py` and update all internal callers in the same file
- [x] T008 Create shared `backend/src/services/github_commit_workflow.py` with `CommitWorkflowResult` dataclass and `async def commit_files_workflow()` function extracting the branch → commit → PR → issue → project-board pipeline from `agent_creator.py` (Steps 4-8)
- [x] T009 Add `list_agent_files_from_repo` method to `backend/src/services/github_projects.py` (or as a standalone function in agents service) that queries GitHub GraphQL API for `.github/agents/*.agent.md` file listing and content parsing (YAML frontmatter extraction)
- [x] T010 Refactor `_execute_creation_pipeline` in `backend/src/services/agent_creator.py` to call `commit_files_workflow()` from the shared module instead of inline implementation (Steps 4-8)
- [x] T011 [P] Add `agentsApi` object to `frontend/src/services/api.ts` with `list`, `create`, `update`, `delete`, and `chat` methods per contracts/agents-api.yaml, following the `choresApi` pattern
- [x] T012 [P] Create `frontend/src/hooks/useAgents.ts` with TanStack Query hooks: `useAgentsList`, `useCreateAgent`, `useUpdateAgent`, `useDeleteAgent`, `useAgentChat` following the `useChores.ts` pattern with query key factory `agentKeys`

**Checkpoint**: Foundation ready — shared functions extracted, API client and hooks scaffolded, user story implementation can begin

---

## Phase 3: User Story 1 — View Agents List on Project Board (Priority: P1) 🎯 MVP

**Goal**: Display an "Agents" section below Chores in the right-side panel showing all agents with name, description, and status badge

**Independent Test**: Navigate to project board, verify Agents section renders below Chores with agent cards or empty state

### Implementation for User Story 1

- [x] T013 [US1] Implement `AgentsService.list_agents()` in `backend/src/services/agents/service.py` — query SQLite `agent_configs` table, fetch `.github/agents/*.agent.md` from repo via `list_agent_files_from_repo` (T009), merge by slug (repo content takes precedence, SQLite metadata preserved), determine status (active/pending_pr/pending_deletion), return list of `Agent` models
- [x] T014 [US1] Implement GET `/{project_id}` handler in `backend/src/api/agents.py` — call `AgentsService.list_agents()`, return `list[Agent]` response
- [x] T015 [US1] Implement `AgentCard` component in `frontend/src/components/agents/AgentCard.tsx` — display agent name, description, status badge (green "Active" / yellow "Pending PR" / red "Pending Deletion"), and action buttons (delete, edit placeholder)
- [x] T016 [US1] Implement `AgentsPanel` component in `frontend/src/components/agents/AgentsPanel.tsx` — header ("🤖 Agents"), "+ Add Agent" button, loading/error/empty states, render list of `AgentCard` components using `useAgentsList` hook, following `ChoresPanel.tsx` pattern
- [x] T017 [US1] Add `AgentsPanel` to `frontend/src/pages/ProjectBoardPage.tsx` — render below `ChoresPanel` in the right-side panel, passing `projectId`, `owner`, and `repo` props

**Checkpoint**: Agents section visible on project board with agent list or empty state. MVP can be validated independently.

---

## Phase 4: User Story 2 — Create a New Custom GitHub Agent (Priority: P1)

**Goal**: Users can create agents via a form, generating .agent.md + .prompt.md files committed via branch + PR

**Independent Test**: Click "Add Agent", enter name + content, submit, verify branch created with files and PR opened

### Implementation for User Story 2

- [x] T018 [US2] Implement `AgentsService.create_agent()` in `backend/src/services/agents/service.py` — validate input (name length, prompt ≤30k chars, filename chars), check for duplicate slug (both SQLite and repo), build `AgentPreview` using `AgentPreview.name_to_slug()`, generate files via `generate_config_files()`, execute `commit_files_workflow()`, save to SQLite `agent_configs`, return `AgentCreateResult`
- [x] T019 [US2] Implement POST `/{project_id}` handler in `backend/src/api/agents.py` — accept `AgentCreate` body, resolve owner/repo from project_id, call `AgentsService.create_agent()`, return 201 with `AgentCreateResult`
- [x] T020 [US2] Implement `AddAgentModal` component in `frontend/src/components/agents/AddAgentModal.tsx` — modal with name input, description input, system prompt textarea, optional tools input, character count for prompt (max 30k), sparse input detection via `isSparseInput()` (reuse from `AddChoreModal.tsx`), submit calls `useCreateAgent` mutation, success state with PR link
- [x] T021 [US2] Wire "Add Agent" button in `AgentsPanel.tsx` to open `AddAgentModal`, pass `projectId` prop, invalidate agent list on successful creation

**Checkpoint**: Full agent creation flow works end-to-end. Users can create agents that appear in the list with "Pending PR" status.

---

## Phase 5: User Story 3 — AI-Assisted Agent Content Refinement (Priority: P2)

**Goal**: Sparse input triggers a multi-turn chat refinement flow to produce a complete agent configuration

**Independent Test**: Enter sparse description (e.g., "reviews security"), verify chat flow opens, answer questions, confirm preview, agent created

### Implementation for User Story 3

- [x] T022 [US3] Implement `AgentsService.chat()` in `backend/src/services/agents/service.py` — maintain chat sessions (keyed by session_id), call AI service to generate clarifying questions or agent preview, return `AgentChatResponse` with reply, session_id, is_complete flag, and optional preview
- [x] T023 [US3] Implement POST `/{project_id}/chat` handler in `backend/src/api/agents.py` — accept `AgentChatMessage` body, call `AgentsService.chat()`, return `AgentChatResponse`
- [x] T024 [US3] Implement `AgentChatFlow` component in `frontend/src/components/agents/AgentChatFlow.tsx` — multi-turn chat interface showing AI messages and user input, preview display when `is_complete=true`, confirm button that triggers agent creation via `useCreateAgent`, following `ChoreChatFlow.tsx` pattern
- [x] T025 [US3] Integrate sparse detection in `AddAgentModal.tsx` — when `isSparseInput()` detects sparse system_prompt content, transition to `AgentChatFlow` component instead of direct submission, pass initial sparse content as first message

**Checkpoint**: Sparse input flow produces complete agent configurations via AI assistance. Direct creation still works for detailed input.

---

## Phase 6: User Story 4 — Delete an Existing Agent (Priority: P2)

**Goal**: Users can delete agents via PR-based removal of files from the repository

**Independent Test**: Click delete on an agent card, confirm, verify deletion PR opened and agent removed from list

### Implementation for User Story 4

- [x] T026 [US4] Implement `AgentsService.delete_agent()` in `backend/src/services/agents/service.py` — resolve agent by id/slug, generate deletion branch name (`agent/delete-{slug}`), create file deletions for `.agent.md` and `.prompt.md`, execute `commit_files_workflow()` with deletion commit, create tracking issue, remove SQLite record, return `AgentDeleteResult`
- [x] T027 [US4] Implement DELETE `/{project_id}/{agent_id}` handler in `backend/src/api/agents.py` — resolve agent, call `AgentsService.delete_agent()`, return `AgentDeleteResult`
- [x] T028 [US4] Add delete action to `AgentCard.tsx` — delete button with confirmation dialog, call `useDeleteAgent` mutation on confirm, show success with PR link, invalidate agent list

**Checkpoint**: Full deletion lifecycle works. Agents can be removed via PR. List updates to reflect removal.

---

## Phase 7: User Story 5 — Best Practices Documentation (Priority: P3)

**Goal**: Comprehensive documentation for writing Custom GitHub Agent markdown files

**Independent Test**: Verify `docs/custom-agents-best-practices.md` exists with agent file structure, YAML properties, prompt guidelines, tool config, and ≥3 examples

### Implementation for User Story 5

- [x] T029 [P] [US5] Create `docs/custom-agents-best-practices.md` with sections: overview, agent file structure (.agent.md format), YAML frontmatter properties (name, description, tools, target, model, mcp-servers, disable-model-invocation), prompt writing guidelines, tool configuration (aliases, MCP servers), and at least 3 example agent configurations (testing specialist, implementation planner, security reviewer)
- [x] T030 [US5] Add documentation link to empty state in `AgentsPanel.tsx` — when no agents exist, include a reference or link text to the best practices guide

**Checkpoint**: Documentation complete and discoverable from the UI empty state.

---

## Phase 8: User Story 6 — Edit an Existing Agent (Priority: P3)

**Goal**: Users can edit agent configurations and open a PR with updated files

**Independent Test**: Click edit on an agent card, modify content, submit, verify PR opened with updated files

### Implementation for User Story 6

- [x] T031 [US6] Implement `AgentsService.update_agent()` in `backend/src/services/agents/service.py` — resolve agent by id/slug, apply updates to config, rebuild `AgentPreview`, generate updated files via `generate_config_files()`, create update branch (`agent/update-{slug}`), execute `commit_files_workflow()`, update SQLite record, return `AgentCreateResult`
- [x] T032 [US6] Implement PATCH `/{project_id}/{agent_id}` handler in `backend/src/api/agents.py` — accept `AgentUpdate` body, call `AgentsService.update_agent()`, return `AgentCreateResult`
- [x] T033 [US6] Add edit action to `AgentCard.tsx` — edit button that opens `AddAgentModal` in edit mode (pre-populated with current agent data), call `useUpdateAgent` mutation on submit, show success with PR link

**Checkpoint**: Full edit lifecycle works. Agent configurations can be updated via PR.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T034 [P] Add error handling and logging for all agent operations in `backend/src/services/agents/service.py` — structured logging with agent slug/project context, consistent error responses
- [x] T035 [P] Validate agent file format compliance in `AgentsService.create_agent()` — ensure generated `.agent.md` files have valid YAML frontmatter and content ≤30k chars, enforce filename character restrictions per FR-011
- [x] T036 Run `quickstart.md` validation — verify all documented workflows work end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 completion
- **US2 (Phase 4)**: Depends on Phase 2 + US1 (needs list to verify creation)
- **US3 (Phase 5)**: Depends on Phase 4 (extends creation flow)
- **US4 (Phase 6)**: Depends on Phase 2 + US1 (needs agent cards with delete button)
- **US5 (Phase 7)**: Can start after Phase 2 — independent of other stories
- **US6 (Phase 8)**: Depends on Phase 2 + US1 (needs agent cards with edit button)
- **Polish (Phase 9)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: Standalone after Foundational — no story dependencies
- **US2 (P1)**: Builds on US1 (adds creation to the panel)
- **US3 (P2)**: Extends US2 (adds chat flow to creation modal)
- **US4 (P2)**: Builds on US1 (adds delete to agent cards) — independent of US2/US3
- **US5 (P3)**: Fully independent — documentation only
- **US6 (P3)**: Builds on US1 (adds edit to agent cards) — independent of US2/US3/US4

### Within Each User Story

- Backend service before API handler
- API handler before frontend components
- Core implementation before integration

### Parallel Opportunities

- T002, T003, T005 can all run in parallel (different files)
- T006 and T007 can run in parallel (different functions in same file, but no conflict)
- T011 and T012 can run in parallel (different frontend files)
- T015 and T016 can run in parallel within US1 (different components)
- US4, US5, US6 can all run in parallel after US1 completes (independent stories)
- T029 can run in parallel with any implementation task (documentation)

---

## Parallel Example: User Story 1

```text
# After Foundational phase completes, launch in parallel:
T015: AgentCard component in frontend/src/components/agents/AgentCard.tsx
T016: AgentsPanel component in frontend/src/components/agents/AgentsPanel.tsx

# Then sequentially:
T013: AgentsService.list_agents() in backend/src/services/agents/service.py
T014: GET handler in backend/src/api/agents.py
T17: Wire AgentsPanel into ProjectBoardPage.tsx
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1 — View agent list
4. Complete Phase 4: User Story 2 — Create agents
5. **STOP and VALIDATE**: Agents can be viewed and created from the project board
6. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. US1 → Agent list visible → Validate independently
3. US2 → Agent creation works → Validate end-to-end (MVP!)
4. US3 → AI refinement for sparse input → Enhanced usability
5. US4 → Deletion via PR → Lifecycle management
6. US5 → Documentation → Developer support
7. US6 → Edit via PR → Full CRUD
8. Polish → Error handling, validation, cleanup

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- US5 (Documentation) can be done at any time — fully independent
- The `commit_files_workflow` shared module (T008) is the most critical foundational task — it enables create, delete, and edit flows
- No database migrations needed — `agent_configs` table already exists
- Frontend components mirror the Chores pattern exactly for consistency
