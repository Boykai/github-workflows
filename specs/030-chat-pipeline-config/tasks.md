# Tasks: Use Selected Agent Pipeline Config from Project Page When Creating GitHub Issues via Chat

**Input**: Design documents from `/specs/030-chat-pipeline-config/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/ (api.md, components.md), quickstart.md

**Tests**: Not explicitly requested in the feature specification. Existing tests must continue to pass (Constitution Check IV). No new test tasks are included.

**Organization**: Tasks grouped by user story (P1–P3) for independent implementation and testing. Each story can be delivered as an independently testable increment. User Story 1 is P1 and forms the MVP.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Exact file paths included in descriptions

## Path Conventions

- **Web app**: `frontend/src/` (React/TypeScript), `backend/src/` (Python/FastAPI)
- Frontend components: `frontend/src/components/chat/`
- Frontend hooks: `frontend/src/hooks/`
- Frontend types: `frontend/src/types/`
- Frontend services: `frontend/src/services/`
- Backend API: `backend/src/api/`
- Backend services: `backend/src/services/workflow_orchestrator/`
- Backend models: `backend/src/models/`

---

## Phase 1: Setup

**Purpose**: Define new backend and frontend types/dataclasses shared across multiple user stories.

- [x] T001 Add `PipelineResolutionResult` dataclass to backend/src/services/workflow_orchestrator/config.py with fields: `agent_mappings` (dict mapping status names to lists of AgentAssignment), `source` (str: "pipeline" | "user" | "default"), `pipeline_name` (str | None), `pipeline_id` (str | None) per data-model.md
- [x] T002 [P] Extend backend `AITaskProposal` response model with optional `pipeline_name: str | None = None` and `pipeline_source: str | None = None` fields in the relevant backend model file (backend/src/models/ or backend/src/api/chat.py where AITaskProposal is defined) per data-model.md
- [x] T003 [P] Extend frontend `AITaskProposal` TypeScript interface with optional `pipeline_name?: string` and `pipeline_source?: string` fields in frontend/src/types/index.ts per data-model.md

**Checkpoint**: All shared types and dataclasses are in place. Ready for foundational function implementation.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core pipeline resolution functions and shared React hook that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T004 Implement `load_pipeline_as_agent_mappings(project_id, pipeline_id)` async function in backend/src/services/workflow_orchestrator/config.py — fetch PipelineConfig from pipeline_configs table via PipelineService.get_pipeline(), iterate over stages in order, build dict mapping each stage name to an ordered list of AgentAssignment objects converted from PipelineAgentNode fields (slug, display_name, model_id, model_name), return tuple of (agent_mappings dict, pipeline_name str) or None if pipeline not found per research.md R2
- [x] T005 Implement `resolve_project_pipeline_mappings(project_id, github_user_id)` async function in backend/src/services/workflow_orchestrator/config.py — three-tier fallback chain: (1) read assigned_pipeline_id from project_settings where github_user_id=`"__workflow__"`, call load_pipeline_as_agent_mappings(), (2) call existing load_user_agent_mappings(github_user_id, project_id), (3) use DEFAULT_AGENT_MAPPINGS — return PipelineResolutionResult with resolved mappings and metadata per research.md R3 and contracts/api.md resolution logic
- [x] T006 [P] Create `useSelectedPipeline(projectId)` shared React hook in frontend/src/hooks/useSelectedPipeline.ts — wrap two React Query calls: (1) pipelinesApi.getAssignment(projectId) with query key ['pipelines', 'assignment', projectId], (2) pipelinesApi.list(projectId) with query key ['pipelines', projectId] — return SelectedPipelineState object with pipelineId, pipelineName (resolved by matching ID in list), isLoading, hasAssignment per contracts/components.md hook specification, staleTime of 60000 (1 minute), enabled only when projectId is non-null

**Checkpoint**: Pipeline resolution backend functions and frontend hook are ready. User story implementation can now begin.

---

## Phase 3: User Story 1 — Automatic Pipeline Inheritance on Issue Creation (Priority: P1) 🎯 MVP

**Goal**: New GitHub Issues created via chat automatically use the Agent Pipeline configuration selected on the Project page, with fallback to user mappings and then system defaults.

**Independent Test**: Select a pipeline on the Project page → open chat → create a new issue → verify the issue's agent mappings match the selected pipeline's stages and agents. Change the pipeline on the Project page → create another issue → verify the new pipeline is used. Remove pipeline assignment → create issue → verify user mappings or defaults are used.

### Implementation for User Story 1

- [x] T007 [US1] Integrate `resolve_project_pipeline_mappings()` in the `confirm_proposal` endpoint in backend/src/api/chat.py — replace the existing direct `load_user_agent_mappings()` call with `resolve_project_pipeline_mappings(project_id, github_user_id)`, apply the returned `agent_mappings` to the WorkflowConfiguration used by create_all_sub_issues(), per research.md R1 (backend-side resolution, no pipeline_id in request) and contracts/api.md resolution logic
- [x] T008 [US1] Populate `pipeline_name` and `pipeline_source` fields from PipelineResolutionResult in the confirm_proposal response in backend/src/api/chat.py — set pipeline_name from result.pipeline_name and pipeline_source from result.source on the AITaskProposal response object per contracts/api.md new response fields

**Checkpoint**: At this point, User Story 1 is fully functional. Issues created via chat inherit the project's assigned pipeline. The confirm response includes pipeline metadata. This is the MVP — stop and validate independently.

---

## Phase 4: User Story 2 — Warning When No Pipeline Is Selected (Priority: P2)

**Goal**: Chat displays an inline warning when no Agent Pipeline is assigned to the current project, preventing silent misconfiguration.

**Independent Test**: Ensure no pipeline is selected on the Project page → open chat → verify an amber warning banner appears above the chat input: "⚠ No Agent Pipeline selected — issues will use the default pipeline. Select one on the Project page." → select a pipeline on the Project page → refocus the chat tab → verify the warning disappears.

### Implementation for User Story 2

- [x] T009 [P] [US2] Create PipelineWarningBanner component in frontend/src/components/chat/PipelineWarningBanner.tsx — accept `projectId: string` prop, consume useSelectedPipeline(projectId) hook, render amber/yellow inline warning banner when hasAssignment === false and isLoading === false with text "⚠ No Agent Pipeline selected — issues will use the default pipeline. Select one on the Project page.", render nothing when loading or assigned, style with `bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-3 text-xs`, add `role="alert"` and `aria-hidden="true"` on warning icon per contracts/components.md
- [x] T010 [US2] Render PipelineWarningBanner in ChatInterface — import PipelineWarningBanner into frontend/src/components/chat/ChatInterface.tsx, render it above the chat input area when projectId is available, no changes to existing chat logic or message handling per contracts/components.md ChatInterface modification spec

**Checkpoint**: At this point, User Stories 1 AND 2 are both functional. Pipeline inheritance works and users are warned when no pipeline is selected.

---

## Phase 5: User Story 3 — Pipeline Confirmation in Chat (Priority: P3)

**Goal**: After creating an issue via chat, the confirmation message shows which Agent Pipeline was applied so users can verify correctness without navigating away.

**Independent Test**: Select "Full Review Pipeline" on the Project page → create an issue via chat → verify the TaskPreview confirmation shows a badge "Agent Pipeline: Full Review Pipeline". Create with no pipeline → verify badge shows "Agent Pipeline: Default". Create with user mappings fallback → verify badge shows "Agent Pipeline: Custom Mappings".

### Implementation for User Story 3

- [x] T011 [US3] Display applied pipeline name badge in TaskPreview confirmation view in frontend/src/components/chat/TaskPreview.tsx — after successful confirmation (proposal.status === "confirmed"), render inline badge showing pipeline info: if proposal.pipeline_name exists show "Agent Pipeline: {pipeline_name}", if proposal.pipeline_source === "default" show "Agent Pipeline: Default", if proposal.pipeline_source === "user" show "Agent Pipeline: Custom Mappings" — style badge with `inline-flex items-center gap-1 rounded-full bg-muted px-2 py-0.5 text-[10px] text-muted-foreground`, use Workflow or GitBranch icon from lucide-react per contracts/components.md TaskPreview modification spec

**Checkpoint**: All three primary user stories are functional. Users see pipeline inheritance, warnings, and confirmations.

---

## Phase 6: User Story 4 — Handling Deleted or Unavailable Pipelines (Priority: P3)

**Goal**: When a previously selected pipeline is deleted mid-session, the system gracefully falls back and notifies the user.

**Independent Test**: Select a pipeline on the Project page → delete that pipeline → attempt to create an issue via chat → verify the system falls back to user/default mappings, the confirm response reflects the fallback source, the stale assigned_pipeline_id is cleared from project_settings, and on next refetch the PipelineWarningBanner appears in the chat.

### Implementation for User Story 4

- [x] T012 [US4] Add stale pipeline auto-cleanup logic in resolve_project_pipeline_mappings() in backend/src/services/workflow_orchestrator/config.py — when assigned_pipeline_id is found but load_pipeline_as_agent_mappings() returns None (pipeline deleted), log a warning for observability, clear the stale assigned_pipeline_id from project_settings table, and fall through to Tier 2 (user mappings) or Tier 3 (defaults) per research.md R5
- [x] T013 [P] [US4] Handle deleted pipeline edge case in useSelectedPipeline hook in frontend/src/hooks/useSelectedPipeline.ts — when pipelineId is non-empty but not found in the pipeline list (assigned pipeline was deleted), return hasAssignment as true but pipelineName as "Unknown Pipeline" so the UI can distinguish between no-assignment and stale-assignment states per contracts/components.md hook specification

**Checkpoint**: All four user stories are complete. The system handles creation, warnings, confirmations, and edge cases for deleted pipelines.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Optional improvements and end-to-end validation across all user stories.

- [ ] T014 [P] Optional DRY refactor: update ProjectsPage.tsx to use the shared useSelectedPipeline hook — replace inline useQuery for pipeline assignment in frontend/src/pages/ProjectsPage.tsx with useSelectedPipeline(projectId), ensuring the same query keys and cache are shared with the chat per contracts/components.md optional ProjectsPage refactor note
- [ ] T015 Run quickstart.md validation scenarios end-to-end per specs/030-chat-pipeline-config/quickstart.md — verify all four phases: Phase 1 (backend pipeline resolution with and without assigned pipeline in backend/src/services/workflow_orchestrator/config.py), Phase 2 (frontend warning banner visibility in frontend/src/components/chat/PipelineWarningBanner.tsx), Phase 3 (pipeline name in confirmation in frontend/src/components/chat/TaskPreview.tsx), Phase 4 (deleted pipeline fallback and auto-cleanup in backend/src/api/chat.py)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3–6)**: All depend on Foundational phase completion
  - User stories can proceed in priority order (P1 → P2 → P3)
  - US1 (Phase 3) is fully independent — delivers the MVP
  - US2 (Phase 4) is independent of US1 but both share the useSelectedPipeline hook
  - US3 (Phase 5) depends on US1 (needs pipeline_name in response to display)
  - US4 (Phase 6) extends foundational functions (T005) and the hook (T006)
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories. Backend-only changes. MVP.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) — Independent of US1. Frontend-only changes using the shared hook.
- **User Story 3 (P3)**: Depends on US1 (Phase 3) — needs pipeline_name and pipeline_source fields in the confirm response to display in TaskPreview.
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) — Extends backend resolution (T005) and frontend hook (T006) to handle the deleted pipeline edge case.

### Within Each User Story

- Models/types before services/functions
- Services before API endpoints
- Backend changes before frontend changes that consume them
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- **Phase 1**: T002 and T003 can run in parallel (different files: backend model vs frontend type)
- **Phase 2**: T006 (frontend hook) can run in parallel with T004/T005 (backend functions)
- **Phase 3**: T007 and T008 are sequential (same file, T008 depends on T007)
- **Phase 4**: T009 (component) can be built in parallel with Phase 3 (different file)
- **Phase 6**: T012 (backend) and T013 (frontend) can run in parallel (different files)
- **Phase 7**: T014 is independent and can run anytime after Phase 2

---

## Parallel Example: After Foundational Phase Completes

```text
# Backend and Frontend can proceed in parallel:

# Backend track (Developer A):
Task T007: Integrate resolve_project_pipeline_mappings() in confirm_proposal (backend/src/api/chat.py)
Task T008: Return pipeline metadata in confirm response (backend/src/api/chat.py)
Task T012: Add stale pipeline auto-cleanup (backend/src/services/workflow_orchestrator/config.py)

# Frontend track (Developer B):
Task T009: Create PipelineWarningBanner component (frontend/src/components/chat/PipelineWarningBanner.tsx)
Task T010: Render banner in ChatInterface (frontend/src/components/chat/ChatInterface.tsx)
Task T011: Display pipeline badge in TaskPreview (frontend/src/components/chat/TaskPreview.tsx)
Task T013: Handle deleted pipeline in useSelectedPipeline (frontend/src/hooks/useSelectedPipeline.ts)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T003)
2. Complete Phase 2: Foundational (T004–T006)
3. Complete Phase 3: User Story 1 (T007–T008)
4. **STOP and VALIDATE**: Create issues via chat with various pipeline states — verify correct pipeline inheritance and fallback behavior
5. Deploy/demo if ready — this delivers the core value

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (T007–T008) → Test independently → Deploy/Demo (**MVP!**)
3. Add User Story 2 (T009–T010) → Test warning banner → Deploy/Demo
4. Add User Story 3 (T011) → Test confirmation display → Deploy/Demo
5. Add User Story 4 (T012–T013) → Test deleted pipeline handling → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A (Backend): US1 (T007–T008) then US4 backend (T012)
   - Developer B (Frontend): US2 (T009–T010) then US3 (T011) then US4 frontend (T013)
3. Stories complete and integrate independently

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 15 |
| **Setup tasks** | 3 (T001–T003) |
| **Foundational tasks** | 3 (T004–T006) |
| **US1 tasks** | 2 (T007–T008) |
| **US2 tasks** | 2 (T009–T010) |
| **US3 tasks** | 1 (T011) |
| **US4 tasks** | 2 (T012–T013) |
| **Polish tasks** | 2 (T014–T015) |
| **Parallel opportunities** | 6 tasks marked [P]; backend/frontend tracks fully parallelizable after Phase 2 |
| **MVP scope** | Phases 1–3 (T001–T008): 8 tasks |
| **Backend files modified** | 2 (chat.py, config.py) |
| **Frontend files modified** | 3 (ChatInterface.tsx, TaskPreview.tsx, types/index.ts) |
| **Frontend files created** | 2 (useSelectedPipeline.ts, PipelineWarningBanner.tsx) |

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Tests are NOT included (not requested in specification — Constitution Check IV: Test Optionality)
- No new database tables or migrations required — reuses existing project_settings and pipeline_configs tables
- No new API endpoints required — reuses existing GET/PUT /pipelines/{projectId}/assignment
- Backend resolves pipeline at confirmation time (not frontend) to avoid stale-state bugs (Research R1)
- Three-tier fallback preserves backward compatibility: project pipeline → user mappings → defaults (Research R3)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
