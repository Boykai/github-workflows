# Tasks: Add Tools Page with MCP Configuration Upload and Agent Tool Selection via Grid Modal

**Input**: Design documents from `/specs/027-mcp-tools-page/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Not explicitly requested in the feature specification. Existing tests should continue to pass.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization — database migration, backend models, frontend types, and navigation wiring

- [ ] T001 Create database migration to extend `mcp_configurations` table and add `agent_tool_associations` junction table in `backend/src/migrations/014_extend_mcp_tools.sql`
- [ ] T002 [P] Create Pydantic models for MCP tools (McpToolConfig, McpToolConfigCreate, McpToolConfigUpdate, McpToolConfigResponse, McpToolConfigListResponse, McpToolConfigSyncResult, AgentToolAssociation) in `backend/src/models/tools.py`
- [ ] T003 [P] Add MCP tool TypeScript interfaces (McpToolConfig, McpToolConfigCreate, McpToolConfigListResponse, McpToolSyncResult, ToolChip, ToolSelectorState) to `frontend/src/types/index.ts`
- [ ] T004 [P] Add Tools navigation route entry with Wrench icon to `NAV_ROUTES` in `frontend/src/constants.ts`
- [ ] T005 [P] Add `/tools` route pointing to `ToolsPage` in `frontend/src/App.tsx` (or router config file)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core backend service, API router, frontend API client, and hooks that MUST be complete before ANY user story UI can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 Create `backend/src/services/tools/__init__.py` with re-exports following the existing service package pattern (e.g., `services/agents/__init__.py`)
- [ ] T007 Implement ToolsService CRUD operations (list_tools, get_tool, create_tool, delete_tool) with aiosqlite in `backend/src/services/tools/service.py` following the existing service pattern from `services/mcp_store.py` and `services/agents/service.py`
- [ ] T008 Implement MCP configuration JSON schema validation function (`validate_mcp_config`) in `backend/src/services/tools/service.py` — validates `mcpServers` object structure, server type, required fields per type (url for http, command for stdio), and 256 KB size limit (R2)
- [ ] T009 Implement GitHub sync operation (`sync_tool_to_github`) in `backend/src/services/tools/service.py` — reads/merges `.copilot/mcp.json` via Contents API, writes updated file with SHA conflict detection (R4)
- [ ] T010 Implement agent-tool association helpers (`get_agents_using_tool`, `update_agent_tools`, `get_agent_tools`) in `backend/src/services/tools/service.py` — dual storage: junction table + `agent_configs.tools` JSON column (R7)
- [ ] T011 Create FastAPI router with tool CRUD + sync endpoints (GET list, POST create, GET detail, POST sync, DELETE) in `backend/src/api/tools.py` following the pattern from `api/agents.py` with session dependency injection
- [ ] T012 Create agent-tool association endpoints (GET agent tools, PUT agent tools) in `backend/src/api/tools.py` mounted under `/agents/{project_id}/{agent_id}/tools`
- [ ] T013 Register tools router in `backend/src/api/__init__.py` with `router.include_router(tools_router, prefix="/tools", tags=["tools"])`
- [ ] T014 [P] Add `toolsApi` namespace (list, get, create, sync, delete) to `frontend/src/services/api.ts` following existing API client patterns
- [ ] T015 [P] Extend `agentsApi` with `getTools` and `updateTools` methods in `frontend/src/services/api.ts`
- [ ] T016 [P] Create `useToolsList` hook with TanStack Query for tool list, upload/sync/delete mutations, per-item loading states, and auth error detection in `frontend/src/hooks/useTools.ts`
- [ ] T017 [P] Create `useAgentTools` hook with TanStack Query for agent-tool assignment query and update mutation in `frontend/src/hooks/useAgentTools.ts`

**Checkpoint**: Foundation ready — all backend endpoints operational, frontend API client and hooks wired. User story implementation can now begin in parallel.

---

## Phase 3: User Story 1 — Browse and Manage MCP Tools (Priority: P1) 🎯 MVP

**Goal**: Users can navigate to the Tools page, see MCP tool cards with sync status, or an empty state prompting first upload. The page mirrors the Agents page layout.

**Independent Test**: Navigate to Tools page via sidebar link; verify layout matches Agents page pattern (header, action bar, card grid, empty state). With tools present, verify each card shows name, description, and sync status badge.

### Implementation for User Story 1

- [ ] T018 [P] [US1] Create `ToolCard` component displaying tool name, description, sync status badge (synced=green, pending=yellow+spinner, error=red), sync error message, and action button placeholders (re-sync, delete) in `frontend/src/components/tools/ToolCard.tsx`
- [ ] T019 [P] [US1] Create `ToolsPanel` component with header ("MCP Tools" title + "Upload MCP Config" button placeholder), search input, `ToolCard` grid (`grid gap-4 md:grid-cols-2 2xl:grid-cols-3`), loading skeleton, error state, and empty state (wrench icon + "No MCP tools configured yet" + upload CTA) in `frontend/src/components/tools/ToolsPanel.tsx`
- [ ] T020 [US1] Create `ToolsPage` route component with `CelestialCatalogHero` header (Tools-specific copy), "Select a project" guard, and `ToolsPanel` main content in `frontend/src/pages/ToolsPage.tsx`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. Users can navigate to the Tools page, see the correct layout mirroring AgentsPage, view tool cards, and see the empty state.

---

## Phase 4: User Story 2 — Upload and Sync MCP Configuration to GitHub (Priority: P1)

**Goal**: Users can upload a valid MCP configuration via modal (paste JSON or upload file), see it validated, and watch it sync to the connected GitHub repository with status tracking.

**Independent Test**: Click "Upload MCP Config" on Tools page; paste valid MCP JSON → submit → new tool card appears with "Pending" then "Synced" status. Try invalid JSON → see specific validation error. Try invalid MCP schema → see field-level error.

### Implementation for User Story 2

- [ ] T021 [US2] Create `UploadMcpModal` component with dialog overlay, name input (required, 1–100 chars), description textarea (optional, 0–500 chars), config content area with paste mode (textarea) and file mode (file input for .json), mode toggle button, client-side JSON + MCP schema validation with inline errors, 256 KB file size check, duplicate name warning, github repo target input, Cancel/Upload buttons, uploading state, and server error display in `frontend/src/components/tools/UploadMcpModal.tsx`
- [ ] T022 [US2] Wire `UploadMcpModal` into `ToolsPanel` — connect "Upload MCP Config" button to open modal, pass `uploadTool` mutation and `isUploading`/`uploadError` state from `useToolsList` hook in `frontend/src/components/tools/ToolsPanel.tsx`
- [ ] T023 [US2] Add duplicate name detection to `create_tool` in `backend/src/services/tools/service.py` — check existing tool names for the project and return 409 Conflict if duplicate found (FR-017)
- [ ] T024 [US2] Trigger GitHub sync automatically after successful tool creation in `backend/src/services/tools/service.py` — call `sync_tool_to_github` after insert, update `sync_status` to "synced" or "error" with message (FR-006, FR-014)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. Users can upload MCP configs, see them appear on the Tools page with sync status tracking, and get clear validation feedback for invalid configs.

---

## Phase 5: User Story 3 — Select MCP Tools When Creating or Editing an Agent (Priority: P1)

**Goal**: Users can select MCP tools for an agent via a responsive tile-grid modal during agent creation/edit, see selected tools as removable chips, and have selections persist on save.

**Independent Test**: Open Agent creation form; click "Add Tools" → tile grid modal opens showing all available MCPs. Select 2 tools → confirm → chips appear on form with × to remove. Save agent → reload → selected tools visible on agent detail. Re-open modal → previous selections pre-checked.

### Implementation for User Story 3

- [ ] T025 [P] [US3] Create `ToolChips` component rendering selected tools as removable chips with × button, an "Add Tools" button/chip at the end, and empty state (only "Add Tools" button) in `frontend/src/components/tools/ToolChips.tsx`
- [ ] T026 [P] [US3] Create `ToolSelectorModal` component with full overlay dialog, header ("Select MCP Tools" + close button), search/filter input, responsive tile grid (CSS Grid: 1 col <640px, 2 cols 640–1023px, 3 cols ≥1024px), each tile showing wrench icon placeholder + name + description (truncated 2 lines) + selected state (checkmark + highlighted border), multi-select via local `Set<string>`, `initialSelectedIds` prop for pre-selection, footer with "N tools selected" count + Cancel + Confirm buttons, and empty state with link to Tools page in `frontend/src/components/tools/ToolSelectorModal.tsx`
- [ ] T027 [US3] Modify `AddAgentModal` in `frontend/src/components/agents/AddAgentModal.tsx` to add "Add Tools" section below system prompt — render `ToolChips` showing selected tools, open `ToolSelectorModal` on "Add Tools" click, manage local tool selection state, include `tool_ids` in agent create/update payload, pre-populate selections when editing existing agent
- [ ] T028 [US3] Update agent create/update backend handler to accept and persist `tool_ids` field — on agent save, write tool IDs to both `agent_configs.tools` JSON column and `agent_tool_associations` junction table in `backend/src/services/tools/service.py` (or agents service as appropriate)

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all be independently functional. Users can upload MCP tools, assign them to agents, and see selections persist.

---

## Phase 6: User Story 4 — Re-sync and Delete MCP Configurations (Priority: P2)

**Goal**: Users can manually re-sync MCP configurations to fix sync issues and delete configurations they no longer need, with warnings for in-use tools.

**Independent Test**: Click re-sync on a tool card → status updates from current to "Pending" then "Synced". Click delete on a tool card → confirmation prompt appears. If tool is assigned to agents, warning lists affected agents. Confirm → tool removed from page and GitHub repo.

### Implementation for User Story 4

- [ ] T029 [US4] Wire re-sync action in `ToolCard` — connect refresh icon button to `syncTool` mutation from `useToolsList`, show loading spinner on the specific card during sync, update status on completion in `frontend/src/components/tools/ToolCard.tsx`
- [ ] T030 [US4] Implement delete flow in `ToolCard` — connect delete icon button to show confirmation dialog, call backend DELETE endpoint with `confirm=false` first to check affected agents, display warning with agent names if any, on user confirm call DELETE with `confirm=true`, remove card from UI on success in `frontend/src/components/tools/ToolCard.tsx`
- [ ] T031 [US4] Implement GitHub repo cleanup on tool deletion in `backend/src/services/tools/service.py` — on confirmed delete, remove the MCP server entry from `.copilot/mcp.json` via Contents API, clean up `agent_tool_associations` rows for the deleted tool (FR-015, FR-016)

**Checkpoint**: All user stories should now be independently functional. Full CRUD + sync + agent assignment lifecycle complete.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032 [P] Verify Tools page layout parity with Agents page — compare header, action bar, card grid, empty state spacing and structure (SC-012)
- [ ] T033 [P] Verify responsive tile grid in `ToolSelectorModal` across 768px to 1920px viewport widths (SC-011)
- [ ] T034 Run existing frontend test suite (`npm run test`) and backend test suite (`pytest`) to confirm no regressions from modifications to types, api.ts, constants.ts, AddAgentModal
- [ ] T035 Verify quickstart.md scenarios — walk through all 14 verification steps from `specs/027-mcp-tools-page/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3–6)**: All depend on Foundational phase completion
  - US1 (Phase 3) and US2 (Phase 4) can proceed in parallel
  - US3 (Phase 5) can start after Foundational but benefits from US1/US2 having test data
  - US4 (Phase 6) can start after Foundational but depends on US1/US2 for visible cards
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) — Independently testable; integrates with US1 via ToolsPanel
- **User Story 3 (P1)**: Can start after Foundational (Phase 2) — Independently testable; uses tools from US2 if available
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) — Independently testable; operates on cards from US1/US2

### Within Each User Story

- Models before services
- Services before endpoints/API
- API before hooks
- Hooks before components
- Components before page integration
- Story complete before moving to next priority

### Parallel Opportunities

- **Phase 1**: T002, T003, T004, T005 can all run in parallel (different files, no dependencies)
- **Phase 2**: T014, T015, T016, T017 (frontend) can run in parallel with each other; T006–T013 (backend) are sequential
- **Phase 3**: T018 and T019 can run in parallel (different component files)
- **Phase 5**: T025 and T026 can run in parallel (different component files)
- **Phase 7**: T032 and T033 can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch ToolCard and ToolsPanel in parallel (different files):
Task T018: "Create ToolCard component in frontend/src/components/tools/ToolCard.tsx"
Task T019: "Create ToolsPanel component in frontend/src/components/tools/ToolsPanel.tsx"
# Note: T019 imports T018's ToolCard, but can be developed simultaneously since
# the interface is defined in contracts/components.md
```

## Parallel Example: User Story 3

```bash
# Launch ToolChips and ToolSelectorModal in parallel (different files):
Task T025: "Create ToolChips component in frontend/src/components/tools/ToolChips.tsx"
Task T026: "Create ToolSelectorModal component in frontend/src/components/tools/ToolSelectorModal.tsx"
```

## Parallel Example: Phase 1 Setup

```bash
# Launch all setup tasks in parallel (different files, no interdependencies):
Task T002: "Create Pydantic models in backend/src/models/tools.py"
Task T003: "Add TypeScript interfaces in frontend/src/types/index.ts"
Task T004: "Add nav route in frontend/src/constants.ts"
Task T005: "Add /tools route in frontend/src/App.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (migration, models, types, nav)
2. Complete Phase 2: Foundational (service, API, hooks, API client)
3. Complete Phase 3: User Story 1 (ToolCard, ToolsPanel, ToolsPage)
4. **STOP and VALIDATE**: Test User Story 1 independently — navigate to Tools page, verify layout parity
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP! — Tools page visible with cards)
3. Add User Story 2 → Test independently → Deploy/Demo (Upload + sync working)
4. Add User Story 3 → Test independently → Deploy/Demo (Agent tool selection working)
5. Add User Story 4 → Test independently → Deploy/Demo (Re-sync + delete working)
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Tools page UI)
   - Developer B: User Story 2 (Upload modal + sync)
   - Developer C: User Story 3 (Agent tool selection)
3. Stories complete and integrate independently
4. Developer A or B picks up User Story 4 after their story is done

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- Total tasks: 35 (5 setup + 12 foundational + 3 US1 + 4 US2 + 4 US3 + 3 US4 + 4 polish)
