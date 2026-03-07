# Tasks: Pipeline Page — CRUD for Agent Pipeline Configurations with Model Selection and Saved Workflow Management

**Input**: Design documents from `/specs/026-pipeline-crud/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Not explicitly requested in the feature specification. Existing tests should continue to pass.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- Backend: Python 3.13, FastAPI, aiosqlite, Pydantic v2
- Frontend: TypeScript ~5.9, React 19.2, TanStack Query v5, @dnd-kit, Tailwind CSS v4, lucide-react

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization — new directories, migration, and shared types/models that all user stories depend on.

- [x] T001 Create database migration file at backend/src/migrations/013_pipeline_configs.sql with pipeline_configs table (id, project_id, name, description, stages JSON, created_at, updated_at), UNIQUE(name, project_id) constraint, and indexes on project_id and updated_at DESC
- [x] T002 Create backend Pydantic models at backend/src/models/pipeline.py defining PipelineConfig, PipelineStage, PipelineAgentNode, AIModel, PipelineConfigCreate, PipelineConfigUpdate, PipelineConfigSummary, and PipelineConfigListResponse per data-model.md
- [x] T003 [P] Create pipeline service package at backend/src/services/pipelines/__init__.py with re-exports for PipelineService
- [x] T004 [P] Add pipeline and model TypeScript interfaces (PipelineConfig, PipelineStage, PipelineAgentNode, PipelineConfigSummary, PipelineConfigCreate, PipelineConfigUpdate, AIModel, ModelGroup, PipelineBoardState) to frontend/src/types/index.ts
- [x] T005 [P] Create empty frontend/src/components/pipeline/ directory structure (add an index barrel file at frontend/src/components/pipeline/index.ts re-exporting all pipeline components)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Backend service, API endpoints, and frontend API client that MUST be complete before ANY user story UI can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T006 Implement PipelineService in backend/src/services/pipelines/service.py with CRUD methods: list_pipelines(project_id), get_pipeline(project_id, pipeline_id), create_pipeline(project_id, data), update_pipeline(project_id, pipeline_id, data), delete_pipeline(project_id, pipeline_id) — following the pattern from backend/src/services/chores/service.py with aiosqlite queries against pipeline_configs table
- [x] T007 Implement list_models() method in backend/src/services/pipelines/service.py returning a static list of AIModel objects (GPT-4o, GPT-4o Mini, Claude Sonnet 4, Claude 3.5 Haiku, Gemini 2.5 Pro, Gemini 2.5 Flash) per contracts/api.md
- [x] T008 Create FastAPI router at backend/src/api/pipelines.py with endpoints: GET /api/v1/pipelines (list), POST /api/v1/pipelines (create), GET /api/v1/pipelines/{pipeline_id} (get), PUT /api/v1/pipelines/{pipeline_id} (update), DELETE /api/v1/pipelines/{pipeline_id} (delete), GET /api/v1/models (list models) — wired to PipelineService, following pattern from existing API routers
- [x] T009 Register the pipelines router in backend/src/main.py by importing and including the new router with appropriate prefix
- [x] T010 Add pipeline and models API client methods to frontend/src/services/api.ts: pipelines.list(), pipelines.get(id), pipelines.create(data), pipelines.update(id, data), pipelines.delete(id), models.list() — following existing API client patterns
- [x] T011 [P] Create useModels hook at frontend/src/hooks/useModels.ts that fetches models via TanStack Query with queryKey ['models'] and staleTime 300000ms, deriving modelsByProvider grouping from the flat models array

**Checkpoint**: Backend CRUD + API + frontend API client ready — user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 — Create a New Agent Pipeline Configuration (Priority: P1) 🎯 MVP

**Goal**: Users can open the pipeline page, click "New Pipeline," name it, add stages with agents, select models per agent, save, and see it in the Saved Workflows list.

**Independent Test**: Open pipeline page → click "New Pipeline" → name it → add a stage → add an agent → select a model → click "Save" → confirm pipeline appears in Saved Workflows list at the bottom.

### Implementation for User Story 1

- [x] T012 [US1] Create usePipelineConfig hook at frontend/src/hooks/usePipelineConfig.ts implementing board state management (empty/creating/editing), local working copy, isDirty tracking via deep comparison, newPipeline(), savePipeline() with TanStack Query mutation (debounced), setPipelineName(), setPipelineDescription(), addStage(), removeStage(), addAgentToStage(), removeAgentFromStage(), updateAgentInStage() — per contracts/components.md hook contract
- [x] T013 [P] [US1] Create ModelSelector component at frontend/src/components/pipeline/ModelSelector.tsx as a popover/dropdown showing models grouped by provider with name, context window size, cost tier badge; includes search filter and recently used models pinned at top — uses useModels hook per contracts/components.md
- [x] T014 [P] [US1] Create AgentNode component at frontend/src/components/pipeline/AgentNode.tsx displaying agent display name, current model selection (or "Select model" prompt), model area that opens ModelSelector on click, and remove (X) button — per contracts/components.md
- [x] T015 [P] [US1] Create PipelineToolbar component at frontend/src/components/pipeline/PipelineToolbar.tsx with New Pipeline, Save, Delete, Discard buttons following the toolbar state matrix from data-model.md (enabled/disabled based on boardState and isDirty) — per contracts/components.md
- [x] T016 [US1] Create StageCard component at frontend/src/components/pipeline/StageCard.tsx rendering stage name, contained AgentNode components, and an "Add Agent" button/popover to assign agents from availableAgents list — per contracts/components.md
- [x] T017 [US1] Create PipelineBoard component at frontend/src/components/pipeline/PipelineBoard.tsx rendering pipeline name as editable inline field, stages as StageCard components, and an "Add Stage" button; shows empty state with "Add your first stage" CTA when stages array is empty — per contracts/components.md
- [x] T018 [US1] Create SavedWorkflowsList component at frontend/src/components/pipeline/SavedWorkflowsList.tsx displaying pipeline summaries as cards with name, relative last modified date, stage count, agent count; cards are clickable; shows loading skeleton during fetch — per contracts/components.md
- [x] T019 [US1] Modify frontend/src/pages/AgentsPipelinePage.tsx to compose PipelineToolbar, PipelineBoard, and SavedWorkflowsList; wire usePipelineConfig hook for state management; fetch saved pipelines list via TanStack Query with queryKey ['pipelines', 'list']
- [x] T020 [US1] Update frontend/src/components/pipeline/index.ts barrel file to re-export all new components (PipelineBoard, PipelineToolbar, StageCard, AgentNode, ModelSelector, SavedWorkflowsList)

**Checkpoint**: At this point, users can create, name, configure, and save a new pipeline. The saved pipeline appears in the list. This is the MVP.

---

## Phase 4: User Story 2 — Load and Edit a Saved Pipeline (Priority: P1)

**Goal**: Users can click a saved workflow card, see it fully restored on the board in edit mode with a visual indicator, make changes, and save updates.

**Independent Test**: Save a pipeline (from US1) → click its card in Saved Workflows → verify all stages/agents/models restored → see "Edit Mode" banner → change a model → click "Save" → confirm change persists on page reload.

### Implementation for User Story 2

- [x] T021 [US2] Add loadPipeline(pipelineId) method to usePipelineConfig hook in frontend/src/hooks/usePipelineConfig.ts that fetches pipeline detail via API, populates local board state, sets editingPipelineId, and transitions boardState to 'editing'
- [x] T022 [US2] Add edit mode visual indicator to PipelineBoard in frontend/src/components/pipeline/PipelineBoard.tsx — display a banner or highlighted header showing "Editing: [pipeline name]" when isEditMode is true (FR-014)
- [x] T023 [US2] Update savePipeline() in usePipelineConfig hook (frontend/src/hooks/usePipelineConfig.ts) to call pipelines.update() when editingPipelineId is set (update existing) vs. pipelines.create() when null (create new); invalidate ['pipelines', 'list'] query on success
- [x] T024 [US2] Wire SavedWorkflowsList onSelect handler in frontend/src/pages/AgentsPipelinePage.tsx to call loadPipeline(pipelineId), highlighting the active pipeline card via activePipelineId prop
- [x] T025 [US2] Ensure SavedWorkflowsList in frontend/src/components/pipeline/SavedWorkflowsList.tsx visually highlights the currently active/selected pipeline card and updates the displayed last modified date and counts after save operations

**Checkpoint**: At this point, users can create, save, load, edit, and re-save pipelines. Full Create + Read + Update flow works.

---

## Phase 5: User Story 3 — Delete a Saved Pipeline (Priority: P2)

**Goal**: Users can select a saved workflow, click "Delete," confirm via dialog, and see the pipeline removed from the list with the board reset.

**Independent Test**: Create and save a pipeline → select it → click "Delete" → confirm in dialog → verify pipeline removed from Saved Workflows list → board resets to empty state.

### Implementation for User Story 3

- [x] T026 [US3] Add deletePipeline() method to usePipelineConfig hook in frontend/src/hooks/usePipelineConfig.ts that calls pipelines.delete(editingPipelineId), invalidates ['pipelines', 'list'] query, and resets board to 'empty' state on success
- [x] T027 [US3] Add delete confirmation dialog to frontend/src/pages/AgentsPipelinePage.tsx — when toolbar's onDelete fires, show a confirmation prompt (using existing UI dialog/card components) warning the action is permanent; on confirm call deletePipeline(), on cancel do nothing (FR-005)
- [x] T028 [US3] Verify PipelineToolbar Delete button states in frontend/src/components/pipeline/PipelineToolbar.tsx: disabled when boardState is 'empty' or 'creating'; enabled when boardState is 'editing' — per toolbar state matrix in data-model.md

**Checkpoint**: Full CRUD lifecycle (Create, Read, Update, Delete) is now complete.

---

## Phase 6: User Story 4 — Model Selection per Agent (Priority: P2)

**Goal**: Users get a rich model picking experience with models grouped by provider, metadata displayed, and recently used models pinned.

**Independent Test**: Open model picker on any agent card → verify models grouped by provider → verify metadata (context window, cost tier) visible → select a model → confirm agent card updates → reopen picker → verify recently used model appears at top.

### Implementation for User Story 4

- [x] T029 [US4] Enhance ModelSelector in frontend/src/components/pipeline/ModelSelector.tsx to track recently used models in session state (last 3 selected models) and display them in a pinned "Recent" group at the top of the list (FR-009)
- [x] T030 [US4] Add cost tier badge styling to ModelSelector in frontend/src/components/pipeline/ModelSelector.tsx — display economy/standard/premium as colored badges alongside each model entry (FR-008)
- [x] T031 [US4] Ensure AgentNode in frontend/src/components/pipeline/AgentNode.tsx displays "Select model" prompt when no model is selected, and shows model name plus provider badge when a model is selected (FR-010)
- [x] T032 [US4] Add search/filter input at the top of the ModelSelector popover in frontend/src/components/pipeline/ModelSelector.tsx for quick lookup when model list is long

**Checkpoint**: Model selection UX is polished with grouping, metadata, recent models, and search.

---

## Phase 7: User Story 5 — Unsaved Changes Protection and Stage Reordering (Priority: P3)

**Goal**: Users are protected from accidental data loss via confirmation dialogs and browser guards. Stages can be drag-and-drop reordered and inline-renamed.

**Independent Test**: Make a change → click different saved workflow → verify confirmation dialog appears → test Save/Discard/Cancel options. Drag a stage to a new position → save → verify order persists. Click stage title → rename → verify name updates.

### Implementation for User Story 5

- [x] T033 [US5] Create UnsavedChangesDialog component at frontend/src/components/pipeline/UnsavedChangesDialog.tsx with Save, Discard, and Cancel buttons; accepts isOpen, onSave, onDiscard, onCancel, and actionDescription props — per contracts/components.md (FR-018)
- [x] T034 [US5] Integrate unsaved changes check in frontend/src/pages/AgentsPipelinePage.tsx: when user clicks a different saved workflow and isDirty is true, show UnsavedChangesDialog before proceeding; wire Save (save then load), Discard (reset then load), and Cancel (no-op) handlers
- [x] T035 [US5] Add browser navigation guard in frontend/src/pages/AgentsPipelinePage.tsx using window.onbeforeunload when isDirty is true, and React Router useBlocker hook for in-app route changes (FR-019)
- [x] T036 [US5] Add discardChanges() method to usePipelineConfig hook in frontend/src/hooks/usePipelineConfig.ts that reverts the working copy to the last saved state (or clears the board if creating a new unsaved pipeline) (FR-006)
- [x] T037 [US5] Add drag-and-drop stage reordering to PipelineBoard in frontend/src/components/pipeline/PipelineBoard.tsx using @dnd-kit SortableContext and DndContext with arrayMove from @dnd-kit/sortable; call onStagesChange after reorder (FR-015)
- [x] T038 [US5] Add reorderStages(newOrder) method to usePipelineConfig hook in frontend/src/hooks/usePipelineConfig.ts that updates stage order values and marks board as dirty
- [x] T039 [US5] Add inline rename support to StageCard in frontend/src/components/pipeline/StageCard.tsx: click stage name → inline text input → Enter or blur to confirm rename; call onUpdate with new name (FR-016)
- [x] T040 [US5] Update frontend/src/components/pipeline/index.ts barrel file to re-export UnsavedChangesDialog

**Checkpoint**: Unsaved changes protection is active for both in-app and browser navigation. Stages support drag-and-drop reordering and inline renaming.

---

## Phase 8: User Story 6 — Empty States and Contextual Actions (Priority: P3)

**Goal**: First-time users see welcoming empty states with CTAs. Toolbar actions are contextually enabled/disabled based on board state.

**Independent Test**: Load pipeline page with no saved workflows → verify board empty state with "Create your first pipeline" CTA → verify Saved Workflows empty state → verify toolbar button states match the state matrix for each board state.

### Implementation for User Story 6

- [x] T041 [US6] Add board empty state to PipelineBoard in frontend/src/components/pipeline/PipelineBoard.tsx: when no pipeline is loaded (stages is null/empty and boardState is 'empty'), display a welcoming message with "Create your first pipeline" CTA button that triggers onNewPipeline (FR-021)
- [x] T042 [US6] Add Saved Workflows empty state to SavedWorkflowsList in frontend/src/components/pipeline/SavedWorkflowsList.tsx: when pipelines array is empty and isLoading is false, display "No saved pipelines yet. Create your first pipeline above!" message with CTA (FR-022)
- [x] T043 [US6] Verify and refine PipelineToolbar contextual states in frontend/src/components/pipeline/PipelineToolbar.tsx: ensure all five board states from the toolbar state matrix in data-model.md are correctly handled — empty (only New enabled), creating no changes (all disabled), creating with changes (Save/Discard enabled), editing no changes (New/Delete enabled), editing with changes (all enabled) (FR-017)

**Checkpoint**: All empty states render correctly. Toolbar actions are contextually appropriate in every board state.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories — error handling, optimistic updates, performance, and cleanup.

- [x] T044 Add error handling and user-facing error notifications for all pipeline API operations (create, update, delete, load) in frontend/src/hooks/usePipelineConfig.ts — show error toast/message on failure with retry option (edge case: save failure)
- [x] T045 Add optimistic UI updates for delete operations in usePipelineConfig hook (frontend/src/hooks/usePipelineConfig.ts) — immediately remove pipeline from list, rollback on failure
- [x] T046 Add save debouncing logic to savePipeline() in frontend/src/hooks/usePipelineConfig.ts to prevent multiple rapid save requests (FR-020)
- [x] T047 [P] Add validation in frontend/src/hooks/usePipelineConfig.ts and frontend/src/components/pipeline/PipelineBoard.tsx: prevent saving with no stages (display validation message), warn when a stage has no agents (edge cases from spec)
- [x] T048 [P] Add pipeline name validation in frontend/src/hooks/usePipelineConfig.ts: prompt user to provide a name before saving if name is empty (acceptance scenario US1-6)
- [x] T049 [P] Verify all pipeline components use existing UI primitives (Button from components/ui/button.tsx, Card from components/ui/card.tsx) consistent with the rest of the application
- [x] T050 Run quickstart.md verification steps: create pipeline, reload to verify persistence, load saved pipeline, modify and save, delete, test model selection, test unsaved changes dialog, test stage reordering

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational phase completion — this is the MVP
- **User Story 2 (Phase 4)**: Depends on US1 (needs created pipelines to load/edit)
- **User Story 3 (Phase 5)**: Depends on US2 (needs loaded pipeline to delete)
- **User Story 4 (Phase 6)**: Can start after Foundational (Phase 2) — enhances existing ModelSelector from US1
- **User Story 5 (Phase 7)**: Can start after US2 (needs load + edit for unsaved changes guard)
- **User Story 6 (Phase 8)**: Can start after US1 (needs basic board + toolbar to add empty states)
- **Polish (Phase 9)**: Depends on all user stories being substantially complete

### User Story Dependencies

- **User Story 1 (P1)**: Depends on Foundational (Phase 2) only — MVP entry point
- **User Story 2 (P1)**: Depends on US1 (needs saved pipelines to exist for load/edit)
- **User Story 3 (P2)**: Depends on US2 (needs pipeline loaded in edit mode to delete)
- **User Story 4 (P2)**: Depends on Foundational (Phase 2) — enhances ModelSelector independently
- **User Story 5 (P3)**: Depends on US2 (needs edit mode for unsaved changes protection)
- **User Story 6 (P3)**: Depends on US1 (needs board + toolbar to add empty states)

### Within Each User Story

- Models/types before services
- Services before components
- Components before page integration
- Core implementation before polish
- Story complete before moving to next priority

### Parallel Opportunities

- Phase 1: T003, T004, T005 can all run in parallel
- Phase 2: T011 can run in parallel with T006–T010
- Phase 3: T013, T014, T015 can all run in parallel (different files)
- Phase 4: All tasks are sequential (each builds on the previous)
- Phase 6: T029, T030, T031, T032 can run in parallel (different concerns within same file but logically independent)
- Phase 8: T041, T042, T043 can run in parallel (different components)
- Phase 9: T047, T048, T049 can run in parallel (different files/concerns)

---

## Parallel Example: User Story 1

```bash
# After Phase 2 is complete, launch parallel component creation:
Task T013: "Create ModelSelector component at frontend/src/components/pipeline/ModelSelector.tsx"
Task T014: "Create AgentNode component at frontend/src/components/pipeline/AgentNode.tsx"
Task T015: "Create PipelineToolbar component at frontend/src/components/pipeline/PipelineToolbar.tsx"

# Then sequentially (dependencies):
Task T016: "Create StageCard (depends on AgentNode T014)"
Task T017: "Create PipelineBoard (depends on StageCard T016)"
Task T018: "Create SavedWorkflowsList (can parallel with T016/T017)"
Task T019: "Integrate into AgentsPipelinePage (depends on all components)"
```

## Parallel Example: User Story 4 (Model Selection Enhancement)

```bash
# All tasks can run in parallel (logically independent enhancements):
Task T029: "Add recently used models tracking to ModelSelector"
Task T030: "Add cost tier badge styling to ModelSelector"
Task T031: "Ensure AgentNode shows model/prompt states correctly"
Task T032: "Add search/filter to ModelSelector"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T005)
2. Complete Phase 2: Foundational (T006–T011)
3. Complete Phase 3: User Story 1 (T012–T020)
4. **STOP and VALIDATE**: Test creating, naming, configuring, and saving a pipeline
5. Deploy/demo if ready — users can create and save pipelines

### Incremental Delivery

1. Complete Setup + Foundational → Backend and API ready
2. Add User Story 1 → Create + Save pipelines → Deploy/Demo (**MVP!**)
3. Add User Story 2 → Load + Edit saved pipelines → Deploy/Demo
4. Add User Story 3 → Delete pipelines → Full CRUD complete → Deploy/Demo
5. Add User Story 4 → Rich model selection UX → Deploy/Demo
6. Add User Story 5 → Unsaved changes protection + drag-and-drop → Deploy/Demo
7. Add User Story 6 → Empty states + contextual toolbar polish → Deploy/Demo
8. Polish phase → Error handling, validation, optimistic updates → Final release

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (MVP — must be first)
   - Developer B: User Story 4 (model selection — independent of US1 UI)
3. After US1 is complete:
   - Developer A: User Story 2 (load/edit)
   - Developer B: User Story 6 (empty states)
4. After US2 is complete:
   - Developer A: User Story 3 (delete)
   - Developer B: User Story 5 (unsaved changes + drag-and-drop)
5. All developers: Polish phase

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 50 |
| **Phase 1 (Setup)** | 5 tasks |
| **Phase 2 (Foundational)** | 6 tasks |
| **US1 — Create Pipeline (P1)** | 9 tasks |
| **US2 — Load & Edit (P1)** | 5 tasks |
| **US3 — Delete Pipeline (P2)** | 3 tasks |
| **US4 — Model Selection (P2)** | 4 tasks |
| **US5 — Unsaved Changes + Reorder (P3)** | 8 tasks |
| **US6 — Empty States (P3)** | 3 tasks |
| **Polish** | 7 tasks |
| **Parallel opportunities** | 16 tasks marked [P] across phases |
| **Suggested MVP scope** | Phases 1–3 (US1): 20 tasks |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- No new UI libraries — use existing Button, Card, @dnd-kit components
- Backend follows existing service patterns (chores/service.py, agents API)
- Frontend follows existing hook patterns (useAgentConfig.ts)
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
