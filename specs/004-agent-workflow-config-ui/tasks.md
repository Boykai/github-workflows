# Tasks: Custom Agent Workflow Configuration UI

**Input**: Design documents from `/specs/004-agent-workflow-config-ui/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/openapi.yaml

**Tests**: Not explicitly requested in feature specification. Test tasks are omitted per Test Optionality principle.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Install new dependencies and verify project structure

- [X] T001 Install @dnd-kit frontend dependencies by running `npm install @dnd-kit/core@6.3.1 @dnd-kit/sortable@10.0.0 @dnd-kit/modifiers@9.0.0 @dnd-kit/utilities@3.2.2` in frontend/
- [X] T002 Verify backend dependencies — confirm `pyyaml` is available or add to backend/pyproject.toml for YAML frontmatter parsing

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Migrate the `agent_mappings` data model from `dict[str, list[str]]` to `dict[str, list[AgentAssignment]]` with backward compatibility. All user stories depend on this migration.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Add `AgentAssignment` model and `_coerce_agent` BeforeValidator to backend/src/models/chat.py — define AgentAssignment(id: UUID, slug: str, display_name: str|None, config: dict|None), AgentAssignmentInput annotated type, and AgentSource StrEnum
- [X] T004 Update `WorkflowConfiguration.agent_mappings` field type from `dict[str, list[str]]` to `dict[str, list[AgentAssignmentInput]]` with default_factory that promotes DEFAULT_AGENT_MAPPINGS strings in backend/src/models/chat.py
- [X] T005 Add `AvailableAgent` and `AvailableAgentsResponse` Pydantic models to backend/src/models/chat.py
- [X] T006 Add `get_agent_slugs(config, status) -> list[str]` helper function to backend/src/services/workflow_orchestrator.py
- [X] T007 Update all downstream `agent_mappings` consumers to use `.slug` or `get_agent_slugs()` — update backend/src/services/workflow_orchestrator.py, backend/src/services/agent_tracking.py, backend/src/api/workflow.py, and backend/src/api/chat.py
- [X] T008 [P] Add `AgentAssignment`, `AvailableAgent`, `AgentSource`, and `AgentPreset` TypeScript interfaces to frontend/src/types/index.ts and update `WorkflowConfiguration.agent_mappings` type from `Record<string, string[]>` to `Record<string, AgentAssignment[]>`
- [X] T009 [P] Update frontend/src/hooks/useWorkflow.ts to handle the new `AgentAssignment[]` response shape from GET /workflow/config

**Checkpoint**: Data model migration complete — backend accepts both string[] and AgentAssignment[] inputs, always returns AgentAssignment[]. Frontend types updated. All existing functionality preserved.

---

## Phase 3: User Story 1 — View Agent Row + User Story 5 — Save/Discard (Priority: P1) 🎯 MVP

**Goal**: Display a collapsible agent configuration row above the board columns, aligned with project status columns, showing assigned agents as card tiles. Include a floating save bar with Save/Discard buttons and visual diff indicators on modified columns.

**Independent Test**: Load the Project Board page → agent row appears expanded above columns → each column shows assigned agents from workflow config → collapse/expand toggle works → modify agent state locally → save bar appears with modified column highlights → Save persists to backend → Discard reverts.

### Implementation

- [X] T010 [US1] [US5] Create `useAgentConfig` custom hook in frontend/src/hooks/useAgentConfig.ts — manages local agent_mappings state cloned from server config, provides isDirty flag, per-column dirty detection, addAgent/removeAgent/reorderAgents/applyPreset/save/discard functions, uses useWorkflow().getConfig and updateConfig for server sync
- [X] T011 [P] [US1] Create `AgentTile` component in frontend/src/components/board/AgentTile.tsx — card-style tile displaying agent avatar/icon placeholder, display_name or slug, and "X" remove button. Accept onRemove callback prop. No drag-and-drop yet (added in US3)
- [X] T012 [US1] Create `AgentColumnCell` component in frontend/src/components/board/AgentColumnCell.tsx — renders vertical stack of AgentTile components for one status column, plus a "+ Add Agent" button placeholder (wired in US2). Accept agents array, status name, isModified flag (for highlighted border), onRemoveAgent callback
- [X] T013 [P] [US5] Create `AgentSaveBar` component in frontend/src/components/board/AgentSaveBar.tsx — floating bar with "Save" and "Discard" buttons, only visible when isDirty is true. Shows saving/error states. Accept onSave, onDiscard, isSaving, error props
- [X] T014 [US1] Create `AgentConfigRow` component in frontend/src/components/board/AgentConfigRow.tsx — collapsible container with toggle button in header row, renders one AgentColumnCell per status column (from boardData.columns), passes useAgentConfig state. Renders AgentSaveBar. Default expanded
- [X] T015 [US1] Integrate AgentConfigRow into frontend/src/pages/ProjectBoardPage.tsx — render AgentConfigRow between board header and ProjectBoard component, pass boardData.columns and workflow config. Ensure agent row columns align with board columns below

**Checkpoint**: MVP complete — agent configuration row visible on board, shows current agent mappings per column, save/discard workflow functional. Users can see their agent pipeline at a glance and persist changes.

---

## Phase 4: User Story 2 — Add Agents + User Story 8 — Agent Discovery (Priority: P1/P2)

**Goal**: Enable users to add agents to status columns via a dropdown popover. Backend discovers available agents from the repository's `.github/agents/*.agent.md` files plus built-in agents.

**Independent Test**: Open add-agent popover in any column → see list of available agents fetched from repository → select one → agent appears at bottom of column → column marked as modified → save bar appears.

### Implementation

- [X] T016 [US8] Implement `list_available_agents(owner, repo, token)` method in backend/src/services/github_projects.py — use existing `_client.get` to call GitHub Contents API for `.github/agents/` directory, filter for `*.agent.md` files, fetch each file's raw content, parse YAML frontmatter for name/description, combine with hardcoded built-in agents: Copilot (`copilot`) and Copilot Review (`copilot-review`). Return list of AvailableAgent objects. Handle 404 (no agents dir) gracefully
- [X] T017 [US8] Add `GET /api/v1/workflow/agents` endpoint to backend/src/api/workflow.py — accept optional `owner` and `repo` query params (default to current config), call list_available_agents(), return AvailableAgentsResponse. Return 404 if no project configured
- [X] T018 [US8] Add `useAvailableAgents` query hook to frontend/src/hooks/useAgentConfig.ts (or separate file) — call GET /api/v1/workflow/agents via @tanstack/react-query, return agents list with loading/error states, support refetch
- [X] T019 [US2] Create `AddAgentPopover` component in frontend/src/components/board/AddAgentPopover.tsx — anchored dropdown triggered by "+ Add Agent" button, displays list of AvailableAgent items with slug, display_name, description. On select, calls useAgentConfig.addAgent(status, agent). Shows loading spinner while fetching, error state with retry
- [X] T020 [US2] Wire AddAgentPopover into AgentColumnCell in frontend/src/components/board/AgentColumnCell.tsx — replace placeholder "+ Add Agent" button with AddAgentPopover component, pass status name and available agents
- [X] T021 [US2] Add soft limit warning in AgentColumnCell — when agent count exceeds 10 in a column, display a warning message below the agent stack in frontend/src/components/board/AgentColumnCell.tsx

**Checkpoint**: Users can discover and add agents from their repository. The add → save flow is complete.

---

## Phase 5: User Story 3 — Reorder via Drag-and-Drop + User Story 4 — Remove Agents (Priority: P2)

**Goal**: Enable drag-and-drop reordering of agent tiles within a column (vertical axis only, keyboard accessible) and "X" button removal of agents.

**Independent Test**: Add 3+ agents to a column → drag one to a new position → animation plays, order updates → column marked modified → click "X" on an agent → it is removed → save bar appears.

### Implementation

- [X] T022 [US3] Wrap AgentColumnCell with DndContext and SortableContext in frontend/src/components/board/AgentColumnCell.tsx — import DndContext, SortableContext, closestCenter, KeyboardSensor, PointerSensor, useSensors from @dnd-kit/core, verticalListSortingStrategy and sortableKeyboardCoordinates from @dnd-kit/sortable, restrictToVerticalAxis from @dnd-kit/modifiers. Set up sensors with keyboard coordinate getter. Handle onDragEnd with arrayMove and call useAgentConfig.reorderAgents(status, newOrder)
- [X] T023 [US3] Make AgentTile draggable using useSortable hook in frontend/src/components/board/AgentTile.tsx — import useSortable from @dnd-kit/sortable and CSS from @dnd-kit/utilities. Apply transform/transition styles, spread attributes and listeners onto tile element. Configure transition duration to 150ms. Add drag handle visual indicator
- [X] T024 [US4] Wire remove functionality — ensure AgentTile "X" button calls useAgentConfig.removeAgent(status, agentInstanceId) and confirm columns with zero agents show only the "+ Add Agent" button in frontend/src/components/board/AgentColumnCell.tsx

**Checkpoint**: Full CRUD cycle complete — add, reorder (drag-and-drop + keyboard), remove, save/discard all functional.

---

## Phase 6: User Story 6 — Preset Agent Configurations (Priority: P2)

**Goal**: Provide three quick-select preset buttons (Custom, GitHub Copilot, Spec Kit) with confirmation dialog before replacing current configuration.

**Independent Test**: Click "Spec Kit" preset → confirmation dialog appears → confirm → all columns update to Spec Kit mappings → save bar appears (unsaved) → click Save → config persisted.

### Implementation

- [X] T025 [US6] Define preset constants in frontend/src/components/board/AgentPresetSelector.tsx — create PRESETS array with three AgentPreset objects: Custom (all empty), GitHub Copilot (In Progress → copilot, In Review → copilot-review), Spec Kit (Backlog → speckit.specify, Ready → speckit.plan + speckit.tasks, In Progress → speckit.implement, In Review → copilot-review). Presets use case-insensitive status matching against actual project columns
- [X] T026 [US6] Create `AgentPresetSelector` component in frontend/src/components/board/AgentPresetSelector.tsx — renders three preset buttons in the agent row header area. On click, shows a confirmation dialog ("This will replace your current agent configuration. Continue?"). On confirm, calls useAgentConfig.applyPreset(presetMappings). On cancel, closes dialog
- [X] T027 [US6] Integrate AgentPresetSelector into AgentConfigRow in frontend/src/components/board/AgentConfigRow.tsx — render preset buttons in the row header alongside the collapse toggle

**Checkpoint**: Users can one-click apply predefined agent configurations with safe confirmation.

---

## Phase 7: User Story 9 — Pass-Through Statuses (Priority: P2)

**Goal**: When a status column has no agents assigned, the workflow pipeline treats it as a pass-through — issues move through automatically to the next status.

**Independent Test**: Configure a workflow with an empty status column → trigger an issue through the pipeline → verify it passes through the empty status to the next one with agents.

### Implementation

- [X] T028 [US9] Update pass-through logic in backend/src/services/workflow_orchestrator.py — in the pipeline execution flow, when `get_agent_slugs(config, status)` returns an empty list for the current status, automatically advance the issue to the next status in the pipeline. Handle consecutive empty statuses by looping until a status with agents is found or the final status is reached

**Checkpoint**: Flexible workflows supported — empty statuses don't stall the pipeline.

---

## Phase 8: User Story 7 — Expandable Agent Tiles (Priority: P3)

**Goal**: Each agent card tile has an expand/collapse toggle revealing agent description and metadata.

**Independent Test**: Click expand toggle on an agent tile → description and metadata appear → click again → tile collapses back to compact view.

### Implementation

- [X] T029 [US7] Add expand/collapse state and detail section to AgentTile in frontend/src/components/board/AgentTile.tsx — add isExpanded local state, toggle button (chevron icon), and collapsible detail area showing agent description, source, and slug. Use graceful fallback ("No description available") when metadata is missing

**Checkpoint**: Informational enhancement complete — users can view agent details in-context.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Edge cases, error handling, and UX refinements across all user stories

- [X] T030 Add loading skeleton for agent row while board data is loading in frontend/src/components/board/AgentConfigRow.tsx — show placeholder cells matching expected column count
- [X] T031 Add unsaved changes warning when switching projects in frontend/src/pages/ProjectBoardPage.tsx — if useAgentConfig.isDirty is true, show confirmation prompt before project switch
- [X] T032 Add "Agent not found" warning indicator on AgentTile in frontend/src/components/board/AgentTile.tsx — when an assigned agent's slug is not found in the available agents list, show a warning badge on the tile
- [X] T033 [P] Add CSS styles for agent row, tiles, save bar, and popover — ensure consistent styling with existing board components, modified column highlight (border glow), floating save bar positioning, and drag animation, in appropriate CSS/styled files under frontend/src/
- [X] T034 [P] Run quickstart.md verification checklist — manually verify all 14 items from specs/004-agent-workflow-config-ui/quickstart.md pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **US1+US5 (Phase 3)**: Depends on Phase 2 — MVP delivery target
- **US2+US8 (Phase 4)**: Depends on Phase 2 + Phase 3 (AgentColumnCell must exist)
- **US3+US4 (Phase 5)**: Depends on Phase 3 (AgentTile and AgentColumnCell must exist)
- **US6 (Phase 6)**: Depends on Phase 3 (AgentConfigRow and useAgentConfig must exist)
- **US9 (Phase 7)**: Depends on Phase 2 only (backend-only, independent of frontend stories)
- **US7 (Phase 8)**: Depends on Phase 3 (AgentTile must exist)
- **Polish (Phase 9)**: Depends on all prior phases being complete

### User Story Dependencies

- **US1+US5 (P1)**: Can start after Foundational (Phase 2) — no dependencies on other stories
- **US2+US8 (P1/P2)**: Depends on US1 (needs AgentColumnCell) and Foundational (needs backend models)
- **US3+US4 (P2)**: Depends on US1 (needs AgentTile component)
- **US6 (P2)**: Depends on US1+US5 (needs AgentConfigRow + useAgentConfig.applyPreset)
- **US7 (P3)**: Depends on US1 (needs AgentTile component)
- **US9 (P2)**: Independent of all frontend stories — depends only on Foundational

### Within Each Phase

- Backend models/services before frontend components
- Custom hook (useAgentConfig) before components that consume it
- Container components (AgentConfigRow) after child components (AgentTile, AgentColumnCell)
- Integration into existing pages last

### Parallel Opportunities

Within Phase 2:
- T008 (frontend types) and T009 (useWorkflow update) can run in parallel with each other and with T003-T007

Within Phase 3:
- T011 (AgentTile) and T013 (AgentSaveBar) can run in parallel after T010 (useAgentConfig hook)
- T012 (AgentColumnCell) can start once T011 is done

Within Phase 4:
- T016 (backend discovery) and T018 (frontend query hook) are independent until integration
- T019 (AddAgentPopover) can start alongside T016/T017 if mock data is used

Post-Phase 2:
- Phase 7 (US9, backend-only pass-through) can run in parallel with any frontend phase

---

## Parallel Example: Phase 2 (Foundational)

```
# Backend tasks (sequential — each depends on prior):
T003 → T004 → T005 → T006 → T007

# Frontend tasks (parallel with each other, parallel with backend):
T008: Add TypeScript interfaces to frontend/src/types/index.ts
T009: Update useWorkflow hook in frontend/src/hooks/useWorkflow.ts
```

## Parallel Example: Phase 3 (US1+US5)

```
# After T010 (useAgentConfig hook), these can run in parallel:
T011: Create AgentTile component
T013: Create AgentSaveBar component

# Then sequentially:
T012: Create AgentColumnCell (needs T011)
T014: Create AgentConfigRow (needs T012, T013)
T015: Integrate into ProjectBoardPage (needs T014)
```

---

## Implementation Strategy

### MVP First (Phase 1 + 2 + 3)

1. Complete Phase 1: Setup (install @dnd-kit deps)
2. Complete Phase 2: Foundational (data model migration)
3. Complete Phase 3: US1+US5 (view agent row + save/discard)
4. **STOP and VALIDATE**: Board page shows agent row, save/discard works
5. Deploy/demo — users can see and save agent configurations

### Incremental Delivery

1. Setup + Foundational → Migration complete, backward-compatible
2. Add US1+US5 → Agent row visible, save/discard works → **MVP!**
3. Add US2+US8 → Users can add agents from repository → Key interaction
4. Add US3+US4 → Drag-and-drop reorder + remove → Full CRUD
5. Add US6 → Presets for quick setup → Onboarding accelerator
6. Add US9 → Pass-through statuses → Pipeline flexibility
7. Add US7 → Expandable tiles → Informational polish
8. Polish → Edge cases, loading states, warnings → Production-ready

### Key Optimization

Phase 7 (US9 — pass-through, backend-only) can run in parallel with any frontend phase after Phase 2, reducing total wall-clock time.

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Backend changes (Phase 2, Phase 4 backend, Phase 7) are minimal — mostly model updates and one new endpoint
- Frontend is the bulk of the work (~70% of tasks) — 6 new components + 1 new hook
- Commit after each task or logical group
- Stop at any checkpoint to validate the increment independently
