# Tasks: Pipeline Page — MCP Tool Selection, Model Override, Flow Graph Cards, Preset Configs & Agent Stamp Isolation

**Input**: Design documents from `/specs/028-pipeline-mcp-config/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Not explicitly requested in the feature specification. Existing tests should continue to pass.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4, US5, US6)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Database migration, backend model extensions, frontend type extensions, and static preset data

- [x] T001 Create database migration adding `is_preset` (INTEGER DEFAULT 0) and `preset_id` (TEXT DEFAULT '') columns to `pipeline_configs`, unique partial index on `(preset_id, project_id)` where `preset_id != ''`, and `assigned_pipeline_id` (TEXT DEFAULT '') column to `project_settings` in `backend/src/migrations/015_pipeline_mcp_presets.sql`
- [x] T002 [P] Extend backend Pydantic models: add `tool_ids: list[str]` and `tool_count: int` to `PipelineAgentNode`, add `is_preset: bool` and `preset_id: str` to `PipelineConfig`, extend `PipelineConfigSummary` with `total_tool_count`, `is_preset`, `preset_id`, and `stages: list[PipelineStage]`, add new `ProjectPipelineAssignment` and `ProjectPipelineAssignmentUpdate` models in `backend/src/models/pipeline.py`
- [x] T003 [P] Extend frontend TypeScript interfaces: add `toolIds: string[]` and `toolCount: number` to `PipelineAgentNode`, add `isPreset: boolean` and `presetId: string` to `PipelineConfig`, extend `PipelineConfigSummary` with `totalToolCount`, `isPreset`, `presetId`, `stages`, and add new types `PipelineModelOverride`, `PipelineValidationErrors`, `ProjectPipelineAssignment`, `PresetPipelineDefinition`, `FlowGraphNode`, `PresetSeedResult` in `frontend/src/types/index.ts`
- [x] T004 [P] Create static preset pipeline definitions for "Spec Kit" (5 stages: Specify → Plan → Tasks → Implement → Analyze with corresponding agent slugs) and "GitHub Copilot" (single stage with GitHub Copilot agent) in `frontend/src/data/preset-pipelines.ts`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core backend service extensions, API endpoints, frontend API client, and hook extensions that MUST be complete before ANY user story UI can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Extend PipelineService `create_pipeline` and `update_pipeline` to auto-compute `tool_count = len(tool_ids)` for each `PipelineAgentNode` on save, ensuring denormalized count is always consistent in `backend/src/services/pipelines/service.py`
- [x] T006 Add preset protection to PipelineService `update_pipeline` — check `is_preset` flag before update and raise HTTP 403 with message "Cannot modify preset pipelines. Use 'Save as Copy' to create an editable version." in `backend/src/services/pipelines/service.py`
- [x] T007 Modify PipelineService `list_pipelines` to return enriched `PipelineConfigSummary` objects with full `stages` array, `total_tool_count` (sum of all agents' tool_counts), `is_preset`, and `preset_id` fields in `backend/src/services/pipelines/service.py`
- [x] T008 Implement `seed_presets(project_id)` method in PipelineService — idempotently insert "Spec Kit" and "GitHub Copilot" preset pipelines using `INSERT OR IGNORE` keyed on `(preset_id, project_id)` with predefined stage/agent configurations in `backend/src/services/pipelines/service.py`
- [x] T009 Implement `get_assignment(project_id)` and `set_assignment(project_id, pipeline_id)` methods in PipelineService — read/write `assigned_pipeline_id` in `project_settings`, validate pipeline exists when setting non-empty assignment in `backend/src/services/pipelines/service.py`
- [x] T010 Add `POST /{project_id}/seed-presets` endpoint calling `seed_presets` service method, returning `{ seeded, skipped, total }` response in `backend/src/api/pipelines.py`
- [x] T011 Add `GET /{project_id}/assignment` and `PUT /{project_id}/assignment` endpoints calling assignment service methods, with 404 response for non-existent pipeline_id in `backend/src/api/pipelines.py`
- [x] T012 Add 403 Forbidden response to `PUT /{project_id}/{pipeline_id}` for preset pipelines by wiring preset protection from service layer in `backend/src/api/pipelines.py`
- [x] T013 [P] Add `seedPresets(projectId)`, `getAssignment(projectId)`, and `setAssignment(projectId, pipelineId)` methods to `pipelinesApi` namespace, and add `assignment` query key to `pipelineKeys` in `frontend/src/services/api.ts`
- [x] T014 [P] Extend `usePipelineConfig` hook with: `modelOverride` state and `setModelOverride` handler (batch-updates all agents' modelId/modelName), `validationErrors` state and `validatePipeline`/`clearValidationError` methods, `updateAgentTools(stageId, agentNodeId, toolIds)` method, `isPreset` flag and `saveAsCopy(newName)` method, `assignedPipelineId` state and `assignPipeline(pipelineId)` method in `frontend/src/hooks/usePipelineConfig.ts`

**Checkpoint**: Foundation ready — all backend endpoints operational, frontend API client and hooks wired. User story implementation can now begin.

---

## Phase 3: User Story 1 — Build a Multi-Agent Pipeline with Per-Agent MCP Tool Selection (Priority: P1) 🎯 MVP

**Goal**: Users can add agents from saved Agents to a pipeline and select MCP tools per agent via a lightweight pop-out module, with tool count badges on agent cards.

**Independent Test**: Create a new pipeline, add two or more agents from the saved Agents list, open the MCP tool selector for each agent, toggle tool selections, and verify selected tools appear as a count badge (e.g., "3 tools") on the agent cards.

### Implementation for User Story 1

- [x] T015 [P] [US1] Modify `ToolSelectorModal` to accept optional `title` (string) and `context` ('agent' | 'pipeline') props — when `context === 'pipeline'`, display custom title; no changes to core tile grid selection logic in `frontend/src/components/tools/ToolSelectorModal.tsx`
- [x] T016 [P] [US1] Add tool count badge and tool selector trigger to `AgentNode` — display `agentNode.toolCount` as a badge (e.g., "3 tools"), show "+ Tools" link when `toolCount === 0`, add `onToolsChange: (toolIds: string[]) => void` callback prop in `frontend/src/components/pipeline/AgentNode.tsx`
- [x] T017 [US1] Wire `ToolSelectorModal` per agent in `StageCard` — manage modal open/close state and selected agent context, pass `availableTools` and agent's current `toolIds` as `selectedToolIds`, on confirm call `onUpdateAgent(agentNodeId, { toolIds, toolCount: toolIds.length })`, add `availableTools: McpToolConfig[]` prop in `frontend/src/components/pipeline/StageCard.tsx`
- [x] T018 [US1] Pass `availableTools` prop through `PipelineBoard` to `StageCard` components — fetch tools via `useTools()` hook and thread through, add `availableTools: McpToolConfig[]` to `PipelineBoardProps` in `frontend/src/components/pipeline/PipelineBoard.tsx`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. Users can add agents to a pipeline and select MCP tools per agent with visible tool count badges.

---

## Phase 4: User Story 2 — Pipeline-Level Model Override with Agent Stamp Isolation (Priority: P1)

**Goal**: Users can set a single model for all agents via a pipeline-level dropdown (or "Auto" to use each agent's stamp settings), with all overrides scoped to the pipeline only.

**Independent Test**: Create a pipeline with multiple agents having different saved models, select "GPT-4o" from the pipeline-level dropdown → all agents show "GPT-4o", select "Auto" → agents revert to stamp models. After saving, verify source agents on the Agents page retain original settings.

### Implementation for User Story 2

- [x] T019 [P] [US2] Create `PipelineModelDropdown` component — dropdown with "Auto" as first option followed by available models from props, "Mixed" state detection when agents have heterogeneous models, calls `onModelChange(PipelineModelOverride)` on selection, uses existing `Select`/`Popover` UI components in `frontend/src/components/pipeline/PipelineModelDropdown.tsx`
- [x] T020 [US2] Integrate `PipelineModelDropdown` into `PipelineBoard` — render below pipeline name field, wire `onModelOverrideChange` to batch-update all agents' `modelId`/`modelName` across all stages (specific model sets all agents, "Auto" clears overrides), add `modelOverride` and `onModelOverrideChange` props to `PipelineBoardProps` in `frontend/src/components/pipeline/PipelineBoard.tsx`
- [x] T021 [US2] Wire model override state from `usePipelineConfig` into `AgentsPipelinePage` — pass `modelOverride` and `setModelOverride` through to `PipelineBoard`, pass available models list in `frontend/src/pages/AgentsPipelinePage.tsx`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. Users can select MCP tools per agent and set pipeline-level model overrides with full agent stamp isolation.

---

## Phase 5: User Story 3 — Always-Available Save with Inline Validation (Priority: P1)

**Goal**: The Save button is always clickable; clicking it with missing required fields highlights offending inputs with red borders and helper text.

**Independent Test**: Click Save on an empty pipeline form → pipeline name input highlighted red with "Pipeline name is required" helper text. Fill in name → click Save → pipeline saves successfully and validation highlights clear.

### Implementation for User Story 3

- [x] T022 [US3] Modify `PipelineToolbar` to keep Save button always enabled when `boardState !== 'empty'` — remove `disabled` condition on Save, add `validationErrors` prop for error count badge display, add `isPreset` and `onSaveAsCopy` props (wired in US5) in `frontend/src/components/pipeline/PipelineToolbar.tsx`
- [x] T023 [US3] Add inline validation error display to `PipelineBoard` — render red border (`border-red-500`) and helper text below pipeline name field when `validationErrors.name` is set, clear error on field edit via `clearValidationError('name')`, add `validationErrors` and `onClearValidationError` props to `PipelineBoardProps` in `frontend/src/components/pipeline/PipelineBoard.tsx`
- [x] T024 [US3] Wire validation flow in `AgentsPipelinePage` — on Save click call `validatePipeline()` from `usePipelineConfig`, block save mutation if invalid, scroll to first error field, pass `validationErrors` through to `PipelineBoard` and `PipelineToolbar` in `frontend/src/pages/AgentsPipelinePage.tsx`

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently. The core pipeline creation experience with tool selection, model override, and inline validation is complete.

---

## Phase 6: User Story 4 — Enhanced Saved Workflows Cards with Agent Details and Flow Graph (Priority: P2)

**Goal**: Saved Workflows cards display stages, agents, models, tool counts, and a compact inline flow graph showing agent execution order across stages.

**Independent Test**: Save multiple pipelines with varying stages and agents, navigate to Saved Workflows section, verify each card shows pipeline name, stages, agents per stage, model per agent, tool count per agent, and a compact horizontal flow graph.

### Implementation for User Story 4

- [x] T025 [P] [US4] Create `PipelineFlowGraph` component — horizontal SVG node-edge diagram rendering each stage as a rounded rectangle with agent count, connected by edge lines left-to-right, responsive sizing (default 200×48px), handles 0 stages (empty), 1 stage (single node), 5+ stages (scaled nodes), memoized with `React.memo`, uses Tailwind color classes in `frontend/src/components/pipeline/PipelineFlowGraph.tsx`
- [x] T026 [US4] Enhance `SavedWorkflowsList` cards to display: pipeline name and description, `PipelineFlowGraph` component per card, list of stages with agents per stage showing model name and tool count (e.g., "GPT-4o · 3 tools"), `totalToolCount` aggregate, use enriched `PipelineConfigSummary` data from list endpoint in `frontend/src/components/pipeline/SavedWorkflowsList.tsx`

**Checkpoint**: At this point, User Story 4 should be fully functional. Saved Workflows cards show rich pipeline detail and visual flow graphs.

---

## Phase 7: User Story 5 — Preset Pipeline Configurations (Priority: P2)

**Goal**: "Spec Kit" and "GitHub Copilot" preset pipeline configurations appear in Saved Workflows, visually differentiated with badges, and editable only via "Save as Copy".

**Independent Test**: Navigate to Saved Workflows → two preset pipelines visible with distinguishing badges. Click a preset → loaded in builder with read-only indicator. Edit → "Save as Copy" prompt. Enter new name → saved as new user pipeline.

### Implementation for User Story 5

- [x] T027 [P] [US5] Create `PresetBadge` component — small badge with `lucide-react` `Lock` icon and preset display name ("Spec Kit" blue/purple accent, "GitHub Copilot" green accent), uses existing `Badge` component from `components/ui/badge.tsx` in `frontend/src/components/pipeline/PresetBadge.tsx`
- [x] T028 [US5] Add `PresetBadge` rendering to `SavedWorkflowsList` cards for pipelines where `isPreset === true`, add subtle background color differentiation for preset vs. user-created cards in `frontend/src/components/pipeline/SavedWorkflowsList.tsx`
- [x] T029 [US5] Add "Save as Copy" button variant to `PipelineToolbar` when `isPreset === true` — replace Save button text with "Save as Copy", trigger `onSaveAsCopy` which opens a name input dialog, saved as new user pipeline with `isPreset: false` in `frontend/src/components/pipeline/PipelineToolbar.tsx`
- [x] T030 [US5] Seed presets on mount — call `pipelinesApi.seedPresets(projectId)` idempotently when `AgentsPipelinePage` loads (guarded by projectId availability), invalidate pipeline list query on success in `frontend/src/pages/AgentsPipelinePage.tsx`

**Checkpoint**: At this point, User Stories 4 AND 5 should both work. Saved Workflows shows enriched cards with flow graphs, and preset pipelines are seeded and visually distinguished.

---

## Phase 8: User Story 6 — Agent Pipeline Configuration Assignment for New Issues (Priority: P3)

**Goal**: Users can assign a saved pipeline configuration to a project, and newly created GitHub Issues automatically inherit that pipeline configuration.

**Independent Test**: Select a saved pipeline from the assignment dropdown, create a new GitHub Issue in the project, verify the issue's metadata includes the assigned pipeline configuration ID.

### Implementation for User Story 6

- [x] T031 [US6] Modify issue creation in `github_projects/service.py` to read `project_settings.assigned_pipeline_id` and inject `pipeline_config_id` as metadata on newly created issues when assignment is non-empty in `backend/src/services/github_projects/service.py`
- [x] T032 [US6] Add pipeline assignment action per card in `SavedWorkflowsList` — "Assign to Project" button or checkmark indicator on assigned pipeline, add `assignedPipelineId` and `onAssign` props, highlight the currently assigned pipeline card in `frontend/src/components/pipeline/SavedWorkflowsList.tsx`
- [x] T033 [US6] Add pipeline assignment dropdown to `AgentsPipelinePage` — fetch current assignment via `usePipelineConfig`, render dropdown with saved pipelines + "None" option, call `assignPipeline(pipelineId)` on selection, pass `assignedPipelineId` and `onAssign` to `SavedWorkflowsList` in `frontend/src/pages/AgentsPipelinePage.tsx`

**Checkpoint**: All user stories should now be independently functional. Full pipeline creation, configuration, preset, and assignment lifecycle complete.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Verification and quality assurance across all user stories

- [x] T034 [P] Verify agent stamp isolation — create pipeline with model/tool overrides, save, navigate to Agents page, confirm all source agents retain their original model and tool settings unchanged
- [x] T035 [P] Verify flow graph rendering on Saved Workflow and Recent Activity cards — confirm horizontal node-edge diagram matches stage order and agent counts for all saved pipelines
- [x] T036 Run existing frontend test suite (`npm run test`) and backend test suite (`pytest`) to confirm no regressions from modifications to models, types, api.ts, hooks, and pipeline components
- [x] T037 Verify quickstart.md scenarios — walk through all 9 verification steps from `specs/028-pipeline-mcp-config/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3–8)**: All depend on Foundational phase completion
  - US1 (Phase 3), US2 (Phase 4), and US3 (Phase 5) are all P1 and can proceed in parallel
  - US4 (Phase 6) and US5 (Phase 7) are P2; US5 builds on US4's `SavedWorkflowsList` changes, so execute US4 → US5 sequentially
  - US6 (Phase 8) is P3 and builds on US4/US5's `SavedWorkflowsList` changes, so execute after US5
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 3 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) — Independently testable; enriches cards from list endpoint
- **User Story 5 (P2)**: Must execute after US4 — Modifies `SavedWorkflowsList.tsx` with preset badges on top of US4's enriched card changes
- **User Story 6 (P3)**: Must execute after US5 — Modifies `SavedWorkflowsList.tsx` with assignment action on top of US4/US5 changes; backend issue hook (T031) is independent

### Within Each User Story

- Backend services before API endpoints
- API endpoints before frontend API client
- Frontend types before hooks
- Hooks before components
- Components before page integration
- Story complete before moving to next priority

### Parallel Opportunities

- **Phase 1**: T002, T003, T004 can all run in parallel (different files, no dependencies)
- **Phase 2**: T013, T014 (frontend) can run in parallel with each other and with T005–T012 (backend) once their backend dependencies are met
- **Phase 3**: T015 and T016 can run in parallel (different component files; interfaces defined in contracts)
- **Phase 4**: T019 is parallel (standalone new component)
- **Phase 6**: T025 is parallel (standalone new component)
- **Phase 7**: T027 is parallel (standalone new component)
- **Phase 9**: T034 and T035 can run in parallel (independent verification tasks)

---

## Parallel Example: Phase 1 Setup

```bash
# Launch all parallelizable setup tasks together (different files):
Task T002: "Extend backend Pydantic models in backend/src/models/pipeline.py"
Task T003: "Extend frontend TypeScript types in frontend/src/types/index.ts"
Task T004: "Create preset pipeline definitions in frontend/src/data/preset-pipelines.ts"
```

## Parallel Example: User Story 1

```bash
# Launch standalone component changes in parallel (different files, interfaces from contracts):
Task T015: "Modify ToolSelectorModal with optional title/context props in frontend/src/components/tools/ToolSelectorModal.tsx"
Task T016: "Add tool count badge and trigger to AgentNode in frontend/src/components/pipeline/AgentNode.tsx"
# Then sequential:
Task T017: "Wire ToolSelectorModal per agent in StageCard in frontend/src/components/pipeline/StageCard.tsx"
Task T018: "Pass availableTools through PipelineBoard in frontend/src/components/pipeline/PipelineBoard.tsx"
```

## Parallel Example: User Stories 1 + 2 + 3 (P1 stories after Foundational)

```bash
# With multiple developers, all P1 stories can start simultaneously:
Developer A: User Story 1 (T015–T018) — MCP tool selection UI
Developer B: User Story 2 (T019–T021) — Model override dropdown
Developer C: User Story 3 (T022–T024) — Save validation
# Each story modifies different primary components; shared files (PipelineBoard, AgentsPipelinePage)
# are extended incrementally and can be merged in priority order.
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (migration, models, types, preset data)
2. Complete Phase 2: Foundational (service, API, hooks, API client)
3. Complete Phase 3: User Story 1 (MCP tool selection per agent)
4. **STOP and VALIDATE**: Test User Story 1 independently — add agents, select tools, verify tool count badges
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP! — Tool selection per agent)
3. Add User Story 2 → Test independently → Deploy/Demo (Pipeline-level model override)
4. Add User Story 3 → Test independently → Deploy/Demo (Always-available Save with validation)
5. Add User Story 4 → Test independently → Deploy/Demo (Rich Saved Workflows cards with flow graphs)
6. Add User Story 5 → Test independently → Deploy/Demo (Preset pipeline configurations)
7. Add User Story 6 → Test independently → Deploy/Demo (Project pipeline assignment for issues)
8. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (MCP tool selection)
   - Developer B: User Story 2 (Model override)
   - Developer C: User Story 3 (Save validation)
3. After P1 stories complete:
   - Developer A: User Story 4 (Enhanced cards + flow graph)
   - Developer B: User Story 5 (Preset configurations)
   - Developer C: User Story 6 (Pipeline assignment for issues)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Agent stamp isolation (FR-006) is enforced architecturally: pipeline save path writes only to `pipeline_configs`, never to `agent_configs` or `agent_tool_associations`
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- Total tasks: 37 (4 setup + 10 foundational + 4 US1 + 3 US2 + 3 US3 + 2 US4 + 4 US5 + 3 US6 + 4 polish)
