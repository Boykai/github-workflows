# Tasks: Agents Page — Sun/Moon Avatars, Featured Agents, Inline Editing with PR Flow, Bulk Model Update, Repo Name Display & Tools Editor

**Input**: Design documents from `/specs/029-agents-page-ux/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Not explicitly requested in the feature specification. Existing tests should continue to pass.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization — no new project setup required. This phase covers shared utilities and types used by multiple user stories.

- [x] T001 Create the `AgentAvatar` component with 12 inline SVG sun/moon icon variants and djb2 hash function in `frontend/src/components/agents/AgentAvatar.tsx`
- [x] T002 [P] Add `BulkModelUpdateRequest` and `BulkModelUpdateResult` Pydantic models in `backend/src/models/agents.py`
- [x] T003 [P] Add `bulkUpdateModels` API client method to the `agentsApi` namespace in `frontend/src/services/api.ts`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before user story phases can begin — backend endpoint and shared hook for bulk model update.

**⚠️ CRITICAL**: No user story work should begin until this phase is complete.

- [x] T004 Add `bulk_update_models()` method to the agents service in `backend/src/services/agents/service.py` — iterate over all active agents, update each agent's `default_model_id` and `default_model_name` via existing model preference storage, return `BulkModelUpdateResult` summary
- [x] T005 Add `PATCH /{project_id}/bulk-model` endpoint in `backend/src/api/agents.py` — parse `BulkModelUpdateRequest` body, call `bulk_update_models()` service method, return `BulkModelUpdateResult` response
- [x] T006 [P] Add `useBulkUpdateModels(projectId)` TanStack Query mutation hook in `frontend/src/hooks/useAgents.ts` — call `agentsApi.bulkUpdateModels()`, invalidate `['agents', 'list', projectId]` and `['agents', 'pending', projectId]` queries on success

**Checkpoint**: Backend bulk-model endpoint is functional and frontend API client + hook are wired. User story implementation can now begin in parallel.

---

## Phase 3: User Story 1 — Inline Agent Definition Editing with PR-Based Save (Priority: P1) 🎯 MVP

**Goal**: Enable users to edit agent definitions via the existing modal editor with dirty-state tracking, unsaved-changes navigation guard, and PR URL display on save.

**Independent Test**: Open an agent's detail view → click "Edit" → modify a field → see unsaved-changes banner → click "Save" → verify PR is created and link is displayed. Try closing modal with unsaved changes → confirm blocking dialog appears. Refresh page with unsaved changes → confirm browser warning.

### Implementation for User Story 1

- [x] T007 [US1] Add dirty-state tracking to `AddAgentModal` in `frontend/src/components/agents/AddAgentModal.tsx` — snapshot original agent values on modal open in edit mode, compare current form state against snapshot using field-by-field comparison (name, description, system_prompt, tools, default_model_id), expose `isDirty` boolean
- [x] T008 [US1] Add persistent unsaved-changes banner to `AddAgentModal` in `frontend/src/components/agents/AddAgentModal.tsx` — when `isDirty` is true, render a yellow warning banner ("You have unsaved changes") at the top of the modal content area
- [x] T009 [US1] Add close guard to `AddAgentModal` in `frontend/src/components/agents/AddAgentModal.tsx` — intercept `onOpenChange(false)` and Escape key when `isDirty`, show a confirmation dialog with "Save," "Discard," and "Cancel" options; Save triggers the update mutation, Discard closes the modal, Cancel keeps the modal open
- [x] T010 [US1] Add `beforeunload` guard to `AddAgentModal` in `frontend/src/components/agents/AddAgentModal.tsx` — add/remove `window.addEventListener('beforeunload', handler)` based on `isDirty` state via `useEffect`
- [x] T011 [US1] Add PR link notification to `AddAgentModal` in `frontend/src/components/agents/AddAgentModal.tsx` — on successful save, display the `pr_url` from `AgentCreateResult` in a success toast/notification with a clickable link ("Changes saved! PR created: #N — View PR →"); preserve unsaved changes on save failure for retry (FR-020)

**Checkpoint**: At this point, User Story 1 should be fully functional — users can edit agents inline with dirty-state protection and see PR links on save.

---

## Phase 4: User Story 2 — Tools Editor within Agent Configuration (Priority: P1)

**Goal**: Provide an interactive tools list editor within the agent configuration modal, allowing add, remove, and reorder operations tracked as unsaved changes.

**Independent Test**: Open agent editor → view tools section as an ordered list → add a tool from the selector → tool appears at end of list → reorder using ↑/↓ buttons → remove a tool with × button → all changes reflected in unsaved-changes state → remove all tools → inline validation error appears → save blocked until at least one tool is assigned.

### Implementation for User Story 2

- [x] T012 [P] [US2] Create `ToolsEditor` component in `frontend/src/components/agents/ToolsEditor.tsx` — render ordered `<ul>` of tool items with: tool name chip, up arrow button (disabled for first item), down arrow button (disabled for last item), remove button (×); "Add Tools" button at bottom opens existing `ToolSelectorModal`; empty state message; validation error display below list; icons from lucide-react (`ChevronUp`, `ChevronDown`, `X`, `Plus`)
- [x] T013 [US2] Integrate `ToolsEditor` into `AddAgentModal` edit mode in `frontend/src/components/agents/AddAgentModal.tsx` — replace static tool chip display with `<ToolsEditor tools={tools} onToolsChange={setTools} error={toolsError} />`; wire `onToolsChange` callback to update local tools state and mark form as dirty
- [x] T014 [US2] Add tools validation to `AddAgentModal` save flow in `frontend/src/components/agents/AddAgentModal.tsx` — before save, check `tools.length >= 1`; if empty, set `toolsError` to "At least one tool must be assigned" and block save; clear error when tools list becomes non-empty (FR-019)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work — inline editing with tools reorder/add/remove and full dirty-state management.

---

## Phase 5: User Story 3 — Sun/Moon Themed Agent Avatars (Priority: P2)

**Goal**: Each agent displays a unique, deterministic sun/moon themed avatar on its card for visual distinction.

**Independent Test**: Load Agents page with multiple agents → each card shows a distinct sun/moon SVG icon → refresh page → same icons persist → same agent always gets the same avatar.

### Implementation for User Story 3

- [x] T015 [US3] Integrate `AgentAvatar` into `AgentCard` in `frontend/src/components/agents/AgentCard.tsx` — import `AgentAvatar`, render `<AgentAvatar slug={agent.slug} size="md" />` in the card header before the agent name, wrapped in a circular container (`rounded-full bg-muted/50 p-1`)

**Checkpoint**: At this point, all agent cards display deterministic sun/moon avatars.

---

## Phase 6: User Story 4 — Featured Agents Section (Priority: P2)

**Goal**: Display a "Featured Agents" section at the top of the Agents page showing up to 3 agents, prioritized by usage count and supplemented by recently created agents.

**Independent Test**: With agents having usage data → top 3 by usage shown in Featured section. With new agents (< 3 days old) and fewer than 3 high-usage agents → recent agents supplement. With no qualifiers → Featured section hidden or shows empty state.

### Implementation for User Story 4

- [x] T016 [US4] Update `spotlightAgents` computation in `AgentsPanel` in `frontend/src/components/agents/AgentsPanel.tsx` — replace existing logic (lines ~67–73) with two-pass algorithm: Pass 1 selects agents with usage count > 0 sorted descending (up to 3); Pass 2 supplements with agents whose `created_at` is within past 3 days (72 hours), excluding duplicates, sorted by creation date descending; cap total at 3; hide Featured section when 0 agents qualify (FR-003, FR-004, FR-005)

**Checkpoint**: Featured Agents section correctly ranks by usage and supplements with recent agents.

---

## Phase 7: User Story 5 — Bulk Update All Agent Models (Priority: P2)

**Goal**: Provide a single action to update the runtime model for all agents at once with explicit user confirmation.

**Independent Test**: Click "Update All Models" → dialog shows model selector → select model → confirmation lists all agents with current/target model → click Confirm → all agents updated → success toast shown. Click Cancel → no changes.

### Implementation for User Story 5

- [x] T017 [P] [US5] Create `BulkModelUpdateDialog` component in `frontend/src/components/agents/BulkModelUpdateDialog.tsx` — two-step dialog: Step 1 shows model selector (reuse existing model list pattern), "Next" enabled when model selected; Step 2 shows confirmation listing all agents with current model and target model, agent count badge, "Cancel" and "Confirm" buttons; loading spinner during API call; error display with retry; calls `useBulkUpdateModels` mutation on confirm; closes and calls `onSuccess` on success
- [x] T018 [US5] Add "Update All Models" button and `BulkModelUpdateDialog` integration to `AgentsPanel` in `frontend/src/components/agents/AgentsPanel.tsx` — add button with `RefreshCw` icon in the catalog controls toolbar; render `<BulkModelUpdateDialog>` controlled by local `bulkUpdateOpen` state; pass agents list and projectId as props

**Checkpoint**: Bulk model update flow is complete — select model, confirm, all agents updated atomically via single API call.

---

## Phase 8: User Story 6 — Repository Name Display with Dynamic Fitting (Priority: P3)

**Goal**: Display only the repository name (not owner/repo) on agent cards, dynamically fitted within a styled bubble/chip with ellipsis truncation for long names.

**Independent Test**: View agent cards → repo name shows "my-repo" (not "owner/my-repo") in a styled chip → long names truncate with ellipsis → hover shows full repo name via title attribute.

### Implementation for User Story 6

- [x] T019 [P] [US6] Extract repository name from project context in `AgentsPage` in `frontend/src/pages/AgentsPage.tsx` — parse `fullRepo.split('/').pop()` to get repo name only; pass `repoName` prop down to `AgentsPanel` → `AgentCard`
- [x] T020 [US6] Add repository name bubble to `AgentCard` in `frontend/src/components/agents/AgentCard.tsx` — render a styled chip/bubble (`inline-flex max-w-[12rem] items-center truncate rounded-full bg-muted px-3 py-0.5 text-xs`) showing only the repo name; set `title={fullRepoName}` for hover tooltip on truncated names

**Checkpoint**: Repository names display correctly — owner stripped, text fitted, ellipsis on overflow.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation.

- [x] T021 Verify all existing frontend tests pass after modifications by running `npm test` in `frontend/`
- [x] T022 Verify all existing backend tests pass after modifications by running `pytest` in `backend/`
- [x] T023 Run quickstart.md verification scenarios (all 22 verification steps) to validate end-to-end feature behavior
- [x] T024 Code cleanup — ensure consistent import ordering, remove unused imports, and verify TypeScript types are correctly applied across all modified files

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on T002 (backend models) for T004/T005; depends on T003 (API client) for T006
- **User Story 1 (Phase 3)**: Depends on Foundational phase completion — modifies `AddAgentModal.tsx`
- **User Story 2 (Phase 4)**: Depends on Phase 3 completion — also modifies `AddAgentModal.tsx` (same file)
- **User Story 3 (Phase 5)**: Depends on T001 (AgentAvatar component) — modifies `AgentCard.tsx`
- **User Story 4 (Phase 6)**: Depends on Foundational phase — modifies `AgentsPanel.tsx`
- **User Story 5 (Phase 7)**: Depends on T006 (useBulkUpdateModels hook) — modifies `AgentsPanel.tsx`
- **User Story 6 (Phase 8)**: No inter-story dependencies — modifies `AgentsPage.tsx` and `AgentCard.tsx`
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — no dependencies on other stories
- **User Story 2 (P1)**: Should start after US1 (Phase 3) since both modify `AddAgentModal.tsx` — avoids merge conflicts
- **User Story 3 (P2)**: Can start after T001 (Setup) — independent of other stories; only touches `AgentCard.tsx`
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) — independent of other stories; only touches `AgentsPanel.tsx`
- **User Story 5 (P2)**: Can start after T006 (Foundational) — needs `useBulkUpdateModels` hook; touches `AgentsPanel.tsx` (coordinate with US4)
- **User Story 6 (P3)**: Can start any time after Setup — independent; touches `AgentsPage.tsx` and `AgentCard.tsx` (coordinate with US3)

### Within Each User Story

- Models/types before services
- Services before API endpoints
- API client before hooks
- Hooks before components
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- **Phase 1**: T001, T002, and T003 can all run in parallel (different files, no dependencies)
- **Phase 2**: T004 depends on T002; T005 depends on T004; T006 can run in parallel with T004/T005 (frontend vs backend)
- **Phase 3–4**: US1 and US2 share `AddAgentModal.tsx` — should be sequential
- **Phase 5–8**: US3, US4, US5, US6 can proceed in parallel (different primary files):
  - US3 → `AgentCard.tsx` (avatar)
  - US4 → `AgentsPanel.tsx` (featured logic)
  - US5 → `BulkModelUpdateDialog.tsx` + `AgentsPanel.tsx` (bulk update)
  - US6 → `AgentsPage.tsx` + `AgentCard.tsx` (repo name)
- **Within US5**: T017 (dialog) and T018 (integration) are sequential; T017 can run in parallel with US4's T016

---

## Parallel Example: Phase 1 (Setup)

```bash
# Launch all setup tasks together (different files, no dependencies):
Task T001: "Create AgentAvatar component in frontend/src/components/agents/AgentAvatar.tsx"
Task T002: "Add BulkModelUpdate Pydantic models in backend/src/models/agents.py"
Task T003: "Add bulkUpdateModels API method in frontend/src/services/api.ts"
```

## Parallel Example: User Stories 3–6 (After Foundational)

```bash
# These user stories touch different primary files and can proceed in parallel:
US3 (T015): "Integrate AgentAvatar into AgentCard.tsx"
US4 (T016): "Update spotlightAgents in AgentsPanel.tsx"
US5 (T017): "Create BulkModelUpdateDialog.tsx"
US6 (T019): "Extract repo name in AgentsPage.tsx"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup (T001–T003)
2. Complete Phase 2: Foundational (T004–T006)
3. Complete Phase 3: User Story 1 — Inline Editing with PR Save (T007–T011)
4. Complete Phase 4: User Story 2 — Tools Editor (T012–T014)
5. **STOP and VALIDATE**: Test inline editing end-to-end with tools editor
6. Deploy/demo if ready — this delivers the core value proposition

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add US1 + US2 (P1) → Test independently → Deploy/Demo (**MVP!**)
3. Add US3 (P2) → Avatars appear on cards → Deploy/Demo
4. Add US4 (P2) → Featured Agents enhanced → Deploy/Demo
5. Add US5 (P2) → Bulk model update available → Deploy/Demo
6. Add US6 (P3) → Repo name display polished → Deploy/Demo
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 + 2 (inline editing + tools editor — same file, sequential)
   - Developer B: User Story 3 + 6 (avatars + repo name — both touch AgentCard.tsx)
   - Developer C: User Story 4 + 5 (featured agents + bulk update — both touch AgentsPanel.tsx)
3. Stories complete and integrate independently

---

## Summary

| Metric | Value |
|--------|-------|
| **Total Tasks** | 24 |
| **Setup Phase** | 3 tasks (T001–T003) |
| **Foundational Phase** | 3 tasks (T004–T006) |
| **US1 — Inline Editing (P1)** | 5 tasks (T007–T011) |
| **US2 — Tools Editor (P1)** | 3 tasks (T012–T014) |
| **US3 — Avatars (P2)** | 1 task (T015) |
| **US4 — Featured Agents (P2)** | 1 task (T016) |
| **US5 — Bulk Model Update (P2)** | 2 tasks (T017–T018) |
| **US6 — Repo Name Display (P3)** | 2 tasks (T019–T020) |
| **Polish Phase** | 4 tasks (T021–T024) |
| **Parallel Opportunities** | 8 tasks marked [P]; US3–US6 can proceed in parallel |
| **MVP Scope** | US1 + US2 (8 tasks) — delivers core inline editing value |

## Notes

- [P] tasks = different files, no dependencies on other incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- US1 and US2 share `AddAgentModal.tsx` — implement sequentially to avoid conflicts
- US3 and US6 share `AgentCard.tsx` — coordinate or implement sequentially
- US4 and US5 share `AgentsPanel.tsx` — coordinate or implement sequentially
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
