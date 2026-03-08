# Tasks: Chores Page — Counter Fixes, Featured Rituals Panel, Inline Editing, AI Enhance Toggle, Agent Pipeline Config & Auto-Merge PR Flow

**Input**: Design documents from `/specs/029-chores-page-enhancements/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/ (api.md, components.md), quickstart.md

**Tests**: Not explicitly requested in the feature specification. Existing tests must continue to pass (Constitution Check IV). No new test tasks are included.

**Organization**: Tasks grouped by user story (P1–P2) for independent implementation and testing. Each story can be delivered as an independently testable increment. User Stories 1–3 are P1 and form the MVP; User Stories 4–6 are P2 enhancements.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4, US5, US6)
- Exact file paths included in descriptions

## Path Conventions

- **Web app**: `frontend/src/` (React/TypeScript), `backend/src/` (Python/FastAPI)
- Frontend components: `frontend/src/components/chores/`
- Frontend hooks: `frontend/src/hooks/`
- Frontend types: `frontend/src/types/`
- Frontend services: `frontend/src/services/`
- Frontend pages: `frontend/src/pages/`
- Backend API: `backend/src/api/`
- Backend models: `backend/src/models/`
- Backend services: `backend/src/services/chores/`
- Backend migrations: `backend/src/migrations/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Database migration, backend model extensions, frontend type definitions, and API client methods shared across all user stories.

- [x] T001 Create database migration in backend/src/migrations/016_chores_enhancements.sql — add `execution_count INTEGER NOT NULL DEFAULT 0`, `ai_enhance_enabled INTEGER NOT NULL DEFAULT 1`, `agent_pipeline_id TEXT NOT NULL DEFAULT ''` columns to `chores` table; add `idx_chores_execution_count` and `idx_chores_last_triggered_at` indexes per data-model.md schema
- [x] T002 [P] Extend Chore Pydantic model with `execution_count: int = 0`, `ai_enhance_enabled: bool = True`, `agent_pipeline_id: str = ""` fields; extend ChoreUpdate with optional `ai_enhance_enabled` and `agent_pipeline_id` fields; add ChoreInlineUpdate, ChoreInlineUpdateResponse, ChoreCreateWithConfirmation, ChoreCreateResponse model classes; add `ai_enhance: bool = True` field to ChoreChatMessage in backend/src/models/chores.py
- [x] T003 [P] Extend Chore TypeScript interface with `execution_count: number`, `ai_enhance_enabled: boolean`, `agent_pipeline_id: string` fields; add ChoreInlineUpdate, ChoreInlineUpdateResponse, ChoreCreateWithConfirmation, ChoreCreateResponse, FeaturedRituals, FeaturedRitualCard, ChoreEditState, ChoreCounterData, ChoreChatMessage interfaces in frontend/src/types/index.ts per data-model.md definitions
- [x] T004 [P] Add `inlineUpdate(projectId, choreId, data)` and `createWithAutoMerge(projectId, data)` methods to choresApi; extend existing `chat()` method to accept and pass `ai_enhance` boolean parameter in frontend/src/services/api.ts per contracts/api.md
- [x] T005 [P] Add `useInlineUpdateChore(projectId)` and `useCreateChoreWithAutoMerge(projectId)` TanStack Query mutation hooks; extend `useChoreChat` to pass `ai_enhance` parameter in frontend/src/hooks/useChores.ts per contracts/components.md hook extensions

**Checkpoint**: All shared types, models, API methods, and hooks are in place. Database migration ready to run on next startup. Ready for user story implementation.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Cross-cutting infrastructure needed by multiple user stories before story-specific work begins.

**⚠️ CRITICAL**: parentIssueCount computation is needed by US1 (counter) and US2 (featured rituals). useUnsavedChanges hook is needed by US3 (inline editing) and the ChoresPage navigation guard.

- [x] T006 Compute `parentIssueCount` from `useProjectBoard()` data in frontend/src/pages/ChoresPage.tsx — count GitHub Parent Issues (content_type === 'issue' items excluding sub-issues) using useMemo, pass as prop to ChoresPanel and FeaturedRitualsPanel
- [x] T007 [P] Create useUnsavedChanges hook in frontend/src/hooks/useUnsavedChanges.ts — register `beforeunload` event listener when `isDirty=true`, activate `useBlocker` from react-router-dom for SPA navigation blocking, return `{ blocker, isBlocked }` for custom modal rendering per contracts/components.md

**Checkpoint**: Foundation ready — parentIssueCount available for counter and panel components. Navigation guard hook ready for inline editing.

---

## Phase 3: User Story 1 — Per-Chore "Every x Issues" Counter Fix (Priority: P1) 🎯 MVP

**Goal**: Fix each Chore tile's counter to show the number of GitHub Parent Issues created since that specific Chore's last execution, scoped per-Chore rather than globally.

**Independent Test**: Create a Chore with "Every 5 issues" trigger → create 3 Parent Issues → verify tile shows "2 remaining" (not a global count). Trigger the Chore → verify counter resets.

### Implementation for User Story 1

- [x] T008 [US1] Fix per-Chore counter computation in backend/src/services/chores/counter.py to query GitHub Parent Issues created since `chore.last_triggered_at` timestamp, returning the scoped count for that specific Chore (not a global total) per FR-001
- [x] T009 [US1] Modify `trigger_chore()` in backend/src/services/chores/service.py to atomically increment `execution_count` (`SET execution_count = execution_count + 1`) and update `last_triggered_count` to the current parent issue count on each successful trigger per FR-002
- [x] T010 [US1] Pass `parentIssueCount` prop from ChoresPanel to each ChoreCard in frontend/src/components/chores/ChoresPanel.tsx for per-Chore counter computation
- [x] T011 [US1] Fix counter display in frontend/src/components/chores/ChoreCard.tsx — for count-based Chores, compute `remaining = schedule_value - (parentIssueCount - last_triggered_count)` clamped to 0 minimum, display as "X remaining" badge on the tile per FR-002 and quickstart.md pattern

**Checkpoint**: Each Chore tile shows an accurate per-Chore countdown. Counter resets on trigger. Two Chores with different thresholds show independent counters.

---

## Phase 4: User Story 2 — Featured Rituals Panel (Priority: P1)

**Goal**: Display a "Featured Rituals" panel above the Chore grid with three highlight cards: Next Run (soonest to trigger), Most Recently Run (latest execution), and Most Run (highest all-time count).

**Independent Test**: Create several Chores with varying execution histories → verify the panel correctly identifies and displays the three highlighted Chores. Delete all Chores → verify empty state message.

### Implementation for User Story 2

- [x] T012 [P] [US2] Create FeaturedRitualsPanel component in frontend/src/components/chores/FeaturedRitualsPanel.tsx — accept `chores: Chore[]` and `parentIssueCount: number` props; compute three rankings (Next Run by lowest remaining count, Most Recently Run by latest `last_triggered_at`, Most Run by highest `execution_count`); render three horizontally arranged cards (`grid grid-cols-3 gap-4`) with Clock/PlayCircle/Trophy icons from lucide-react; handle empty state with onboarding message per contracts/components.md
- [x] T013 [US2] Render FeaturedRitualsPanel above ChoresPanel in frontend/src/pages/ChoresPage.tsx, passing `chores` array and `parentIssueCount`; wire `onChoreClick` to scroll-to or highlight the clicked Chore in the grid per FR-003 and FR-004

**Checkpoint**: Featured Rituals panel shows three cards with correct rankings. Empty state renders when no Chores exist. Cards link to their respective Chores.

---

## Phase 5: User Story 3 — Inline Chore Definition Editing with PR on Save (Priority: P1)

**Goal**: Make Chore definitions directly editable on the Chores page. Show dirty-state indicators, block navigation on unsaved changes, and create a Pull Request on save.

**Independent Test**: Edit a Chore's name inline → verify dirty indicator appears → click Save → verify PR is created with updated file. Navigate away with unsaved changes → verify confirmation dialog appears.

### Implementation for User Story 3

- [x] T014 [P] [US3] Create ChoreInlineEditor component in frontend/src/components/chores/ChoreInlineEditor.tsx — render editable `<input>` for name, `<textarea>` with auto-resize for template_content, reuse ChoreScheduleConfig for schedule fields; call `onChange(updates)` on every field change; respect `disabled` prop during save operations per contracts/components.md
- [x] T015 [P] [US3] Add `update_template_in_repo()` method to backend/src/services/chores/template_builder.py — create branch `chore/update-{slug}-{timestamp}`, commit updated template file via existing `commit_files_workflow`, open PR with title `chore: update {chore_name}` and auto-generated description per plan.md Phase 1 step 4
- [x] T016 [US3] Add `inline_update_chore(chore_id, body: ChoreInlineUpdate)` method to backend/src/services/chores/service.py — check `expected_sha` for conflict detection (return 409 if mismatch), update Chore record in database, call `update_template_in_repo()` if template_content or name changed per contracts/api.md inline-update behavior
- [x] T017 [US3] Add `PUT /{project_id}/{chore_id}/inline-update` endpoint to backend/src/api/chores.py — accept ChoreInlineUpdate body, call `inline_update_chore`, return ChoreInlineUpdateResponse with PR details, return 409 with current_sha and current_content on conflict per contracts/api.md
- [x] T018 [US3] Add inline edit state management to frontend/src/components/chores/ChoresPanel.tsx — maintain `editState: Record<string, ChoreEditState>` tracking per-Chore original values and current edits; compute `isDirty` per Chore and global `isAnyDirty`; render persistent "You have unsaved changes" banner and "Save All" button when dirty per FR-005 and contracts/components.md
- [x] T019 [US3] Modify frontend/src/components/chores/ChoreCard.tsx to render ChoreInlineEditor for editable fields, show dirty indicator (asterisk or highlight border) when `isDirty=true`, display Save and Discard action buttons when dirty per FR-005
- [x] T020 [US3] Wire useUnsavedChanges hook into frontend/src/pages/ChoresPage.tsx — pass `isAnyDirty` from ChoresPanel state; when `blocker.state === 'blocked'`, render custom confirmation modal with "You have unsaved changes — are you sure you want to leave?" and Stay/Discard and Leave buttons per FR-006

**Checkpoint**: Chore fields render as editable inputs. Editing shows dirty indicator. Navigation away prompts confirmation. Save creates a PR with updated file. Conflict detection works on stale edits.

---

## Phase 6: User Story 4 — AI Enhance Toggle for Issue Template Creation (Priority: P2)

**Goal**: Add an "AI Enhance" toggle to the Chore creation/editing flow. When ON, existing AI flow is preserved. When OFF, user's exact input is used as the template body while AI generates only metadata.

**Independent Test**: Create a Chore with AI Enhance OFF → provide specific body text → verify the Issue Template body matches input exactly with AI-generated metadata. Toggle ON → verify existing flow unchanged.

### Implementation for User Story 4

- [x] T021 [US4] Add metadata-only generation path in backend/src/services/chores/chat.py — when `ai_enhance=False`, use structured system prompt requesting only metadata fields (name, about, title, labels, assignees); inject user's raw chat input as pre-filled locked body field; assemble final template as AI front matter + user verbatim body per FR-009 and plan.md Phase 1 step 6
- [x] T022 [US4] Pass `ai_enhance` field from ChoreChatMessage through `POST /{project_id}/chat` endpoint in backend/src/api/chores.py to the chat service's `generate_chat_response()` per contracts/api.md modified chat endpoint
- [x] T023 [US4] Modify frontend/src/components/chores/ChoreChatFlow.tsx to accept `aiEnhance: boolean` prop (default true), pass `ai_enhance` parameter in choresApi.chat() calls, show subtle indicator "Your input will be used as the template body" when aiEnhance is false per contracts/components.md
- [x] T024 [P] [US4] Add AI Enhance toggle button (Sparkles icon from lucide-react, ChatToolbar pill style with ON/OFF badge) to frontend/src/components/chores/AddChoreModal.tsx — default ON, pass value to ChoreChatFlow as aiEnhance prop per FR-008 and quickstart.md pattern
- [x] T025 [P] [US4] Add AI Enhance toggle to inline edit section of frontend/src/components/chores/ChoreCard.tsx — wire to `editState.ai_enhance_enabled`, persist via onEditChange handler per FR-008

**Checkpoint**: AI Enhance toggle visible and functional. OFF → user's exact text in body + AI metadata. ON → existing flow. Toggle state saved per Chore.

---

## Phase 7: User Story 5 — Per-Chore Agent Pipeline Configuration (Priority: P2)

**Goal**: Allow each Chore to select a specific saved Agent Pipeline or "Auto" (inherits the project's active pipeline at runtime).

**Independent Test**: Create a Chore with a specific pipeline → verify it uses that pipeline at execution. Switch to "Auto" → change project pipeline → trigger → verify it uses the updated project pipeline.

### Implementation for User Story 5

- [x] T026 [P] [US5] Create PipelineSelector component in frontend/src/components/chores/PipelineSelector.tsx — fetch pipeline list via `usePipelinesList(projectId)` hook; render dropdown with "Auto (Project Default)" as first option (value="") and saved pipelines by name; show "⚠ Pipeline no longer available" warning if selected ID not found; handle loading and error states per contracts/components.md
- [x] T027 [US5] Add agent pipeline resolution logic in `trigger_chore()` in backend/src/services/chores/service.py — if `agent_pipeline_id` non-empty, fetch from `pipeline_configs` (fall back to Auto with logged warning if not found per FR-017); if empty ("Auto"), read `project_settings.assigned_pipeline_id` at runtime per FR-012 and plan.md complexity tracking
- [x] T028 [US5] Integrate PipelineSelector into frontend/src/components/chores/ChoreCard.tsx configuration section (wired to editState.agent_pipeline_id) and frontend/src/components/chores/AddChoreModal.tsx form (default "Auto") per FR-011

**Checkpoint**: Pipeline selector shows Auto + saved pipelines. Chores with specific pipelines use them at trigger time. "Auto" resolves to project's current active pipeline. Deleted pipeline falls back gracefully.

---

## Phase 8: User Story 6 — Double-Confirmation & Auto-Merge PR Flow for New Chores (Priority: P2)

**Goal**: When saving a new Chore, show a two-step confirmation modal, then sequentially create a GitHub Issue, open a PR, and auto-merge the PR into main.

**Independent Test**: Create a new Chore → verify both confirmation steps appear → confirm → verify Issue created, PR opened, PR merged, success toast. Cancel at either step → verify no Issue/PR created.

### Implementation for User Story 6

- [x] T029 [P] [US6] Create ConfirmChoreModal component in frontend/src/components/chores/ConfirmChoreModal.tsx — two-step flow: Step 1 shows AlertTriangle icon with repository warning and "I Understand, Continue" button; Step 2 shows CheckCircle icon with "Yes, Create Chore" button; support isLoading state with spinner; reset to Step 1 when modal reopens per contracts/components.md
- [x] T030 [US6] Add `merge_pull_request(access_token, owner, repo, pr_number, merge_method='squash')` method to backend/src/services/chores/template_builder.py — use GitHub REST API `PUT /repos/{owner}/{repo}/pulls/{pr_number}/merge`, return `(success: bool, error_message: str | None)` tuple per quickstart.md auto-merge pattern
- [x] T031 [US6] Add `create_chore_with_auto_merge()` method to backend/src/services/chores/service.py — sequentially: create branch + commit template, create PR, create tracking issue, attempt merge via `merge_pull_request()`, persist Chore record locally regardless of merge result per FR-014 and data-model.md state machine
- [x] T032 [US6] Modify `POST /{project_id}` endpoint in backend/src/api/chores.py to accept ChoreCreateWithConfirmation body (with `auto_merge` flag) and return ChoreCreateResponse including `pr_merged` and `merge_error` fields per contracts/api.md modified create endpoint
- [x] T033 [US6] Modify frontend/src/components/chores/AddChoreModal.tsx to use ConfirmChoreModal two-step flow when creating a new Chore — on final confirmation call `createWithAutoMerge` mutation; show success toast on merge success or warning toast with PR link on merge failure per FR-015 and FR-016

**Checkpoint**: New Chore creation shows two-step confirmation. Both confirmations lead to Issue + PR + auto-merge. Merge failures surface as actionable errors with PR link. Chore persists locally regardless.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Edge case handling, error notifications, and final validation across all user stories.

- [x] T034 [P] Handle edge cases in frontend/src/components/chores/ChoreCard.tsx and backend/src/services/chores/counter.py — never-executed Chore uses `created_at` for counter base (no `last_triggered_at`), threshold=1 immediate trigger display, bulk Parent Issue creation accuracy, mid-flow AI Enhance toggle preserves existing input per spec.md edge cases section
- [x] T035 [P] Add toast notifications in frontend/src/components/chores/ChoresPanel.tsx and frontend/src/components/chores/AddChoreModal.tsx for all async operations — PR creation success with PR link, auto-merge success/failure status, conflict detection warning with reload option, deleted pipeline fallback notification per FR-015, FR-016, FR-017
- [ ] T036 Run quickstart.md verification scenarios for all 6 user stories — validate counter accuracy (scenarios 1–2), Featured Rituals rankings (scenarios 3–6), inline edit + PR flow (scenarios 7–10), AI Enhance toggle (scenarios 11–12), pipeline selector (scenarios 13–15), double-confirmation + auto-merge (scenarios 16–20) per quickstart.md verification section

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS user stories that need parentIssueCount (US1, US2) and useUnsavedChanges (US3)
- **User Story 1 (Phase 3)**: Depends on Setup + Foundational (needs parentIssueCount)
- **User Story 2 (Phase 4)**: Depends on Setup + Foundational (needs parentIssueCount and chores list)
- **User Story 3 (Phase 5)**: Depends on Setup + Foundational (needs useUnsavedChanges and API client methods)
- **User Story 4 (Phase 6)**: Depends on Setup (needs ChoreChatMessage.ai_enhance and API client)
- **User Story 5 (Phase 7)**: Depends on Setup (needs agent_pipeline_id field and API client)
- **User Story 6 (Phase 8)**: Depends on Setup (needs ChoreCreateWithConfirmation model and API client)
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational (Phase 2) — no dependencies on other stories
- **US2 (P1)**: Can start after Foundational (Phase 2) — uses same parentIssueCount as US1 but no code dependency
- **US3 (P1)**: Can start after Foundational (Phase 2) — independent of US1/US2
- **US4 (P2)**: Can start after Setup (Phase 1) — independent of all P1 stories
- **US5 (P2)**: Can start after Setup (Phase 1) — independent of all P1 stories
- **US6 (P2)**: Can start after Setup (Phase 1) — independent of all other stories; AddChoreModal modifications in US4/US5/US6 should be coordinated if done in parallel

### Within Each User Story

- Backend service changes before API endpoint changes
- API endpoints before frontend component integration
- Models/types before services before UI components
- Core implementation before integration with page-level wiring

### Parallel Opportunities

- All Setup tasks marked [P] (T002–T005) can run in parallel after T001 (migration)
- Foundational T006 and T007 can run in parallel
- US1 T010 and T011 modify different files and can run in parallel after T008–T009
- US2 T012 is standalone (new file) and can start as soon as types are ready
- US3 T014 and T015 are parallel (different files: frontend component vs. backend service)
- US4 T024 and T025 are parallel (different files: AddChoreModal vs. ChoreCard)
- US5 T026 is standalone (new file)
- US6 T029 is standalone (new file)
- US4, US5, and US6 can all start in parallel after Setup since they are independent P2 stories
- Polish T034 and T035 can run in parallel

---

## Parallel Example: User Story 1

```bash
# After Setup + Foundational complete:

# Backend tasks (sequential — service depends on counter fix):
Task T008: "Fix per-Chore counter in backend/src/services/chores/counter.py"
Task T009: "Increment execution_count in backend/src/services/chores/service.py"

# Frontend tasks (can run in parallel after backend):
Task T010: "Pass parentIssueCount through ChoresPanel in frontend/src/components/chores/ChoresPanel.tsx"
Task T011: "Fix counter display in frontend/src/components/chores/ChoreCard.tsx"
```

## Parallel Example: User Story 3

```bash
# After Setup + Foundational complete:

# These can run in parallel (different files):
Task T014: "Create ChoreInlineEditor in frontend/src/components/chores/ChoreInlineEditor.tsx"
Task T015: "Add update_template_in_repo in backend/src/services/chores/template_builder.py"

# Sequential after T015:
Task T016: "Add inline_update_chore method in backend/src/services/chores/service.py"
Task T017: "Add PUT inline-update endpoint in backend/src/api/chores.py"

# Sequential after T014 + T017:
Task T018: "Add edit state management in frontend/src/components/chores/ChoresPanel.tsx"
Task T019: "Render ChoreInlineEditor in frontend/src/components/chores/ChoreCard.tsx"
Task T020: "Wire useUnsavedChanges into frontend/src/pages/ChoresPage.tsx"
```

## Parallel Example: P2 Stories (US4 + US5 + US6)

```bash
# After Setup complete, all three P2 stories can run in parallel:

# Developer A: User Story 4 (AI Enhance Toggle)
Task T021–T025

# Developer B: User Story 5 (Pipeline Config)
Task T026–T028

# Developer C: User Story 6 (Double-Confirmation & Auto-Merge)
Task T029–T033

# Note: US4, US5, and US6 all modify AddChoreModal.tsx and ChoreCard.tsx.
# If done in parallel, coordinate final integration of these shared files.
```

---

## Implementation Strategy

### MVP First (User Stories 1–3 Only)

1. Complete Phase 1: Setup (migration, models, types, API client, hooks)
2. Complete Phase 2: Foundational (parentIssueCount, useUnsavedChanges)
3. Complete Phase 3: User Story 1 — Counter Fix
4. **STOP and VALIDATE**: Verify per-Chore counters are accurate
5. Complete Phase 4: User Story 2 — Featured Rituals Panel
6. **STOP and VALIDATE**: Verify panel shows correct rankings
7. Complete Phase 5: User Story 3 — Inline Editing
8. **STOP and VALIDATE**: Verify inline edit + PR creation + navigation guard
9. Deploy/demo MVP — all P1 stories complete

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add US1 (Counter Fix) → Test independently → Deploy (accurate counters)
3. Add US2 (Featured Rituals) → Test independently → Deploy (discoverability)
4. Add US3 (Inline Editing) → Test independently → Deploy (editability + PR flow) — **MVP complete**
5. Add US4 (AI Enhance) → Test independently → Deploy (content control)
6. Add US5 (Pipeline Config) → Test independently → Deploy (pipeline flexibility)
7. Add US6 (Auto-Merge) → Test independently → Deploy (full automation)
8. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Counter Fix) → then User Story 4 (AI Enhance)
   - Developer B: User Story 2 (Featured Rituals) → then User Story 5 (Pipeline)
   - Developer C: User Story 3 (Inline Editing) → then User Story 6 (Auto-Merge)
3. Stories complete and integrate independently
4. Coordinate AddChoreModal.tsx and ChoreCard.tsx changes across US4/US5/US6

---

## Summary

| Metric | Value |
|--------|-------|
| **Total Tasks** | 36 |
| **Setup Tasks** | 5 (T001–T005) |
| **Foundational Tasks** | 2 (T006–T007) |
| **US1 Tasks (Counter Fix, P1)** | 4 (T008–T011) |
| **US2 Tasks (Featured Rituals, P1)** | 2 (T012–T013) |
| **US3 Tasks (Inline Editing, P1)** | 7 (T014–T020) |
| **US4 Tasks (AI Enhance, P2)** | 5 (T021–T025) |
| **US5 Tasks (Pipeline Config, P2)** | 3 (T026–T028) |
| **US6 Tasks (Auto-Merge, P2)** | 5 (T029–T033) |
| **Polish Tasks** | 3 (T034–T036) |
| **Parallel Opportunities** | 15 tasks marked [P] across 8 phases |
| **Suggested MVP Scope** | User Stories 1–3 (Phases 1–5, 20 tasks) |
| **Total Estimated Effort** | 32h (from issue metadata) |
| **Estimated MVP Effort** | ~18h of the 32h total |

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- AddChoreModal.tsx and ChoreCard.tsx are modified by multiple stories (US3, US4, US5, US6) — coordinate changes if implementing in parallel
- Auto-merge failures must not block local Chore persistence (FR-014)
- Agent Pipeline "Auto" must be runtime lookup, not cached (FR-012)
- All new columns have defaults — migration is backward-compatible with existing data
