# Tasks: Project Page — Agent Pipeline UX Overhaul, Drag/Drop Fixes, Issue Rendering & Layout Improvements

**Input**: Design documents from `/specs/028-project-page-ux/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Unit tests included for `formatAgentName` utility (pure function with defined edge cases) and sub-issue filtering logic (critical data correctness), as specified in the plan's test optionality section.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- **Frontend tests**: `frontend/src/tests/` or `frontend/tests/`
- **Backend tests**: `backend/tests/unit/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Install new dependencies, scaffold new utility files, and prepare shared infrastructure

- [x] T001 Install `react-markdown` and `remark-gfm` npm dependencies in `frontend/package.json`
- [x] T002 [P] Create `frontend/src/utils/formatAgentName.ts` with the pure utility function implementing slug-to-display-name formatting per contract C1 (dot-split, empty-segment filter, title-case, "speckit" → "Spec Kit" compound handling, join with " - ", displayName precedence)
- [x] T003 [P] Create `frontend/src/tests/utils/formatAgentName.test.ts` with unit tests covering all contract C1 examples: "linter" → "Linter", "speckit.tasks" → "Spec Kit - Tasks", "speckit.implement" → "Spec Kit - Implement", "agent.v2.runner" → "Agent - V2 - Runner", "speckit..tasks" → "Spec Kit - Tasks", "" → "", displayName precedence, "LINTER" → "Linter", empty displayName fallback

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Type extensions and data mapping changes that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Extend `AvailableAgent` interface in `frontend/src/types/index.ts` to add `default_model_name?: string | null` and `tools_count?: number | null` fields per data-model.md
- [x] T005 Update the frontend agent data mapping in `frontend/src/hooks/useAgentConfig.ts` (or the hook/service that fetches agents) to populate `default_model_name` from `agent.default_model_name` and `tools_count` from `agent.tools?.length` when mapping backend `Agent` responses to `AvailableAgent` per contract A2

**Checkpoint**: Foundation ready — user story implementation can now begin in parallel

---

## Phase 3: User Story 1 — Fix Drag/Drop Interaction Bugs (Priority: P1) 🎯 MVP

**Goal**: Eliminate the agent tile teleportation bug and fix all drag/drop interaction issues on the project page so tiles follow the cursor precisely from grab-start through drop

**Independent Test**: Open any project with an agent pipeline, grab an agent tile, and confirm the tile stays under the cursor from grab-start through drop with no positional jump on mousedown. Repeat 10 times with zero teleport occurrences.

### Implementation for User Story 1

- [x] T006 [US1] Audit `frontend/src/components/board/AgentConfigRow.tsx` DnD sensor configuration — verify PointerSensor (distance: 5), TouchSensor (delay: 250, tolerance: 5), and KeyboardSensor are correctly configured per research R1 and R10
- [x] T007 [US1] Fix DragOverlay pointer offset in `frontend/src/components/board/AgentConfigRow.tsx` — compute pointer offset as `{x: clientX - rect.left, y: clientY - rect.top}` from `activatorEvent` in `handleDragStart` and apply to DragOverlay positioning per research R2
- [x] T008 [US1] Replace `CSS.Transform.toString(transform)` with `CSS.Translate.toString(transform)` in `frontend/src/components/board/AgentColumnCell.tsx` sortable items to avoid scale/rotation interference causing teleport per research R1
- [x] T009 [US1] Audit and remove any conflicting custom `transform` or `translate` CSS on agent tiles in `frontend/src/components/board/AgentTile.tsx` and `frontend/src/components/board/AgentColumnCell.tsx` that may cause coordinate-space mismatch
- [x] T010 [US1] Configure DragOverlay `dropAnimation` correctly in `frontend/src/components/board/AgentConfigRow.tsx` to ensure smooth drop without visual glitches
- [x] T011 [US1] Add visual drop target indicator to `frontend/src/components/board/AgentColumnCell.tsx` — apply `border-primary/40 bg-primary/5` on valid drag-over state, `transition-colors duration-150` for smooth transitions per contract C7
- [x] T012 [US1] Verify issue card drag/drop in kanban columns works smoothly — audit `frontend/src/components/board/ProjectBoard.tsx` and `frontend/src/components/board/BoardColumn.tsx` for similar offset/transform issues and fix if present

**Checkpoint**: At this point, User Story 1 should be fully functional — drag/drop works without teleportation

---

## Phase 4: User Story 2 — Subtle Agent Pipeline Restyling & Unified Layout Alignment (Priority: P1)

**Goal**: Restyle the Agent Pipeline section to match the Pipeline Stages component's subtle design and align pipeline columns with kanban columns in a shared grid layout

**Independent Test**: Open the project page and visually compare the Agent Pipeline section against the Pipeline Stages on the pipeline page — styling should be indistinguishable. Verify column-by-column horizontal alignment between the pipeline row and the kanban board at viewport widths above 1024px.

### Implementation for User Story 2

- [x] T013 [US2] Restyle `frontend/src/components/board/AgentConfigRow.tsx` container to use `celestial-panel rounded-[1.2rem] border border-border/60` and grid `gap-3` to match PipelineBoard.tsx visual weight per research R3 and contract C3
- [x] T014 [P] [US2] Restyle `frontend/src/components/board/AgentColumnCell.tsx` cells to use `border border-border/60 rounded-[1.2rem] p-2` with lighter background and reduced visual weight per contract C3
- [x] T015 [US2] Convert `frontend/src/components/board/ProjectBoard.tsx` from flex layout with `w-[320px]` fixed-width columns to CSS grid using `gridTemplateColumns: repeat(N, minmax(14rem, 1fr))` per contract C5 and research R8
- [x] T016 [US2] Remove the `+ Add column` button and its associated logic from `frontend/src/components/board/ProjectBoard.tsx` per contract C5 and FR-009
- [x] T017 [P] [US2] Update `frontend/src/components/board/BoardColumn.tsx` to remove fixed `w-[320px]` width and use dynamic grid-child sizing per contract C5
- [x] T018 [US2] Wrap the Agent Pipeline section and kanban board in a shared unified layout container in `frontend/src/pages/ProjectsPage.tsx` so both sections reference the same grid column count and template per research R8 and contract C3/C5

**Checkpoint**: At this point, User Stories 1 AND 2 should both work — pipeline is restyled and aligned with kanban

---

## Phase 5: User Story 3 — Agent Tile Metadata & Auto-Formatted Names (Priority: P2)

**Goal**: Display auto-formatted agent names, configured model name, and tool count on each agent tile in the pipeline

**Independent Test**: Load any project page with agents that have dot-namespaced identifiers, and verify the formatted names (e.g., "Spec Kit - Tasks"), model labels (e.g., "GPT-4o"), and tool counts (e.g., "3 tools") render correctly on each tile. Verify agents with no configured model/tools show name only.

### Implementation for User Story 3

- [x] T019 [US3] Integrate `formatAgentName` utility into `frontend/src/components/board/AgentTile.tsx` — replace raw slug/display_name rendering with `formatAgentName(agent.slug, agent.display_name)` per contract C2
- [x] T020 [US3] Add model name and tool count metadata display to `frontend/src/components/board/AgentTile.tsx` — look up matching `AvailableAgent` by slug from `availableAgents` prop, display model as secondary text (e.g., "GPT-4o"), tool count as "N tools", join with " · " separator per contract C2
- [x] T021 [US3] Handle metadata edge cases in `frontend/src/components/board/AgentTile.tsx` — omit secondary metadata line when neither model name nor tools count is available, omit individual fields when null/0 per contract C2
- [x] T022 [P] [US3] Update `frontend/src/components/board/AgentDragOverlay.tsx` to use `formatAgentName` for the dragged tile's display name per contract C1
- [x] T023 [US3] Pass `availableAgents` prop down to `AgentTile` in `frontend/src/components/board/AgentColumnCell.tsx` to enable metadata lookup per data-model.md component prop changes

**Checkpoint**: At this point, User Story 3 should be fully functional — agent tiles display formatted names and metadata

---

## Phase 6: User Story 4 — Saved Agent Pipeline Configuration Selection (Priority: P2)

**Goal**: Allow users to select from saved pipeline configurations in the Agent Pipeline section, persist the selection, and apply it to newly created GitHub Issues

**Independent Test**: Load a project with at least two saved pipeline configurations, select a different configuration from the dropdown, create a new issue, and verify the new issue inherits the selected pipeline's agent assignments. Navigate away and return to verify selection persists.

### Implementation for User Story 4

- [x] T024 [US4] Extend `frontend/src/components/board/AgentPresetSelector.tsx` to fetch saved pipeline configurations from `GET /api/pipelines/{project_id}` and display them alongside built-in presets in the dropdown per contract C6 and API contract A3
- [x] T025 [US4] Implement `pipelineConfigToMappings()` conversion function in `frontend/src/components/board/AgentPresetSelector.tsx` (or a shared utility) to map `PipelineConfig.stages[].agents[]` to `Record<string, AgentAssignment[]>` per column per contract C6 and API contract A3
- [x] T026 [US4] Add `localStorage` persistence for selected pipeline config ID in `frontend/src/hooks/useAgentConfig.ts` using key `pipeline-config:{project_id}` — read on mount to restore selection, write on change per API contract A4
- [x] T027 [US4] Wire the selected pipeline configuration into the issue creation flow in `frontend/src/hooks/useAgentConfig.ts` so newly created GitHub Issues within the project inherit the active pipeline configuration per FR-006 and contract A4

**Checkpoint**: At this point, User Story 4 should be fully functional — saved configs selectable and applied to new issues

---

## Phase 7: User Story 5 — Markdown-Rendered Issue Descriptions (Priority: P2)

**Goal**: Render GitHub Issue descriptions as properly formatted Markdown in the issue detail view, supporting headings, code blocks, lists, bold, italic, and hyperlinks

**Independent Test**: Select a GitHub Issue with a Markdown body containing headings, code blocks, lists, bold, italic, and links, and verify each element renders correctly in the detail view. Verify long descriptions scroll within container. Verify empty body shows no description section.

### Implementation for User Story 5

- [x] T028 [US5] Replace raw text rendering of `item.body` in `frontend/src/components/board/IssueDetailModal.tsx` with `<ReactMarkdown remarkPlugins={[remarkGfm]}>{item.body}</ReactMarkdown>` per contract C4
- [x] T029 [US5] Style the Markdown content container in `frontend/src/components/board/IssueDetailModal.tsx` with `prose prose-sm dark:prose-invert max-w-none` Tailwind typography classes, `bg-muted/30 p-4 rounded-md border border-border`, and `overflow-y-auto max-h-[50vh]` for overflow handling per contract C4
- [x] T030 [US5] Handle empty/null body gracefully in `frontend/src/components/board/IssueDetailModal.tsx` — conditionally render the description section only when `item.body` is truthy per contract C4

**Checkpoint**: At this point, User Story 5 should be fully functional — Markdown renders correctly in issue detail view

---

## Phase 8: User Story 6 — Done Column Shows Only Parent Issues (Priority: P3)

**Goal**: Exclude sub-issues from the Done/Closed kanban column so only top-level parent issues are displayed

**Independent Test**: View the Done column on a project with parent issues that have sub-issues, and confirm only parent issues appear. Verify issue count is accurate after filtering.

### Implementation for User Story 6

- [x] T031 [US6] In `backend/src/services/github_projects/service.py`, during board data assembly, collect all sub-issue item IDs into a `set[str]` by iterating all parent items' `sub_issues` lists per API contract A1
- [x] T032 [US6] In `backend/src/services/github_projects/service.py`, when building columns with "Done", "Closed", or "Completed" status names, filter out items whose `item_id` is in the collected sub-issue ID set per API contract A1
- [x] T033 [US6] Update `item_count` on filtered Done/Closed columns in `backend/src/services/github_projects/service.py` to reflect the post-filter count per API contract A1
- [ ] T034 [P] [US6] Create `backend/tests/unit/test_board_filter.py` with unit tests verifying: parent issues appear in Done column, sub-issues are excluded from Done column, item_count is correct after filtering, column with only sub-issues renders as empty

**Checkpoint**: At this point, User Story 6 should be fully functional — Done column shows only parent issues

---

## Phase 9: User Story 7 — Remove Add Column Button (Priority: P3)

**Goal**: Remove the "+ Add column" button from the project board UI

**Independent Test**: Load the project page and confirm no "+ Add column" button or column-addition control exists on the board.

### Implementation for User Story 7

- [x] T035 [US7] Remove the "+ Add column" button element and any associated click handler or state from `frontend/src/components/board/ProjectBoard.tsx` per FR-009

> Note: If T016 (Phase 4, US2) already removed this button as part of the layout conversion, this task validates the removal and cleans up any remaining references.

**Checkpoint**: At this point, User Story 7 should be complete — no Add Column button on board

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, cleanup, and cross-cutting improvements that affect multiple user stories

- [x] T036 [P] Verify `formatAgentName` unit tests pass by running `cd frontend && npx vitest run src/tests/utils/formatAgentName.test.ts`
- [ ] T037 [P] Verify backend sub-issue filter tests pass by running `cd backend && pytest tests/unit/test_board_filter.py -x -v`
- [x] T038 [P] Run frontend lint and type check: `cd frontend && npx eslint src/ && npx tsc --noEmit`
- [ ] T039 [P] Run backend lint and type check: `cd backend && ruff check src/ && pyright src/`
- [x] T040 Run frontend build to verify no compilation errors: `cd frontend && npm run build`
- [ ] T041 Run `quickstart.md` manual verification checklist — validate all 9 sections (drag/drop, restyling, metadata, config selector, Markdown rendering, Done filter, Add Column removal, unified layout, drop targets)
- [x] T042 Code cleanup — remove any dead code, unused imports, or temporary debugging artifacts introduced during implementation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on T001 (npm install) — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Phase 2 — No dependencies on other stories
- **User Story 2 (Phase 4)**: Depends on Phase 2 — No dependencies on other stories
- **User Story 3 (Phase 5)**: Depends on Phase 2 (AvailableAgent type extension) and T002 (formatAgentName utility)
- **User Story 4 (Phase 6)**: Depends on Phase 2 — No dependencies on other stories
- **User Story 5 (Phase 7)**: Depends on T001 (react-markdown installed) — No dependencies on other stories
- **User Story 6 (Phase 8)**: Depends on Phase 2 — Backend-only, independent of frontend stories
- **User Story 7 (Phase 9)**: Depends on Phase 2 — May overlap with T016 (US2 layout change)
- **Polish (Phase 10)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 2 — Independent of all other stories
- **User Story 2 (P1)**: Can start after Phase 2 — Independent of US1 but may benefit from DnD fixes being in place
- **User Story 3 (P2)**: Can start after Phase 2 + T002 — Depends on formatAgentName utility and AvailableAgent type extension
- **User Story 4 (P2)**: Can start after Phase 2 — Independent of US1/US2/US3
- **User Story 5 (P2)**: Can start after T001 — Independent of all other stories (only needs react-markdown installed)
- **User Story 6 (P3)**: Backend-only — Can start after Phase 2, fully independent of frontend stories
- **User Story 7 (P3)**: Trivial — Can be absorbed into US2 (T016) or done as standalone

### Within Each User Story

- Models/types before service logic
- Service logic before component integration
- Core implementation before integration and edge-case handling
- Story complete before moving to next priority

### Parallel Opportunities

- T002 and T003 can run in parallel (utility file and test file are independent)
- T004 and T005 can run in parallel within Phase 2 (type extension and data mapping)
- After Phase 2 completes: US1, US2, US4, US5, US6 can all start in parallel
- US3 can start once T002 (formatAgentName) is also complete
- Within US1: T006-T010 are sequential (audit → fix → verify), but T011 (drop targets) is parallel
- Within US2: T014, T017 are parallel with each other (different files)
- Within US3: T022 is parallel with T019-T021 (AgentDragOverlay vs AgentTile)
- US6 (backend) is fully independent of all frontend stories
- All Phase 10 lint/test tasks marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Sequential: Audit → Fix → Verify (same files, dependencies)
Task T006: "Audit AgentConfigRow.tsx DnD sensor configuration"
Task T007: "Fix DragOverlay pointer offset in AgentConfigRow.tsx"
Task T008: "Replace CSS.Transform with CSS.Translate in AgentColumnCell.tsx"

# Parallel: Different files, no dependencies
Task T011: "Add visual drop target indicator to AgentColumnCell.tsx"  (parallel with T009-T010)
Task T012: "Verify issue card drag/drop in ProjectBoard.tsx"         (parallel with T009-T010)
```

## Parallel Example: Cross-Story

```bash
# After Phase 2 completion, these stories can run in parallel:
Developer A: User Story 1 (DnD fixes - frontend)
Developer B: User Story 2 (Restyling/layout - frontend, different files)
Developer C: User Story 6 (Done column filter - backend, fully independent)
Developer D: User Story 5 (Markdown rendering - frontend, different file)
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup (install deps, create utility)
2. Complete Phase 2: Foundational (type extensions, data mapping)
3. Complete Phase 3: User Story 1 — Fix Drag/Drop (P1, blocking interaction bug)
4. Complete Phase 4: User Story 2 — Restyle + Layout Alignment (P1, visual consistency)
5. **STOP and VALIDATE**: Test drag/drop works without teleport, pipeline styling matches reference, layout is aligned
6. Deploy/demo if ready — the project page is now usable and visually consistent

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test DnD independently → Interaction bugs fixed (MVP!)
3. Add User Story 2 → Test styling independently → Visual consistency achieved
4. Add User Story 3 → Test metadata independently → Agent tiles show full context
5. Add User Story 5 → Test Markdown independently → Issue descriptions readable
6. Add User Story 4 → Test config selector independently → Pipeline configs selectable
7. Add User Story 6 → Test Done filter independently → Cleaner Done column
8. Add User Story 7 → Validate removal → Board simplified
9. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (DnD fixes)
   - Developer B: User Story 2 (Restyling + layout)
   - Developer C: User Story 6 (Backend Done filter — fully independent)
3. After US1/US2 validated:
   - Developer A: User Story 3 (Metadata — needs formatAgentName from Setup)
   - Developer B: User Story 4 (Config selector)
   - Developer D: User Story 5 (Markdown rendering)
4. User Story 7 can be done by anyone as a small task
5. Stories complete and integrate independently

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 42 |
| **Phase 1 (Setup)** | 3 tasks |
| **Phase 2 (Foundational)** | 2 tasks |
| **Phase 3 (US1 — DnD Fix)** | 7 tasks |
| **Phase 4 (US2 — Restyling/Layout)** | 6 tasks |
| **Phase 5 (US3 — Metadata/Names)** | 5 tasks |
| **Phase 6 (US4 — Config Selector)** | 4 tasks |
| **Phase 7 (US5 — Markdown)** | 3 tasks |
| **Phase 8 (US6 — Done Filter)** | 4 tasks |
| **Phase 9 (US7 — Remove Button)** | 1 task |
| **Phase 10 (Polish)** | 7 tasks |
| **Parallel opportunities** | 16 tasks marked [P] + cross-story parallelism |
| **Suggested MVP scope** | User Stories 1 + 2 (Phases 1-4, 18 tasks) |
| **Format validated** | ✅ ALL tasks follow `- [ ] [TaskID] [P?] [Story?] Description with file path` format |

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- US7 (Remove Add Column) may be absorbed into US2 T016 during implementation — T035 serves as validation
- Backend (US6) and frontend stories are fully independent and can proceed in parallel
- Two new npm dependencies: `react-markdown`, `remark-gfm` — both are standard, lightweight, XSS-safe
- No backend schema changes required — all backend changes are behavior-only (filtering logic)
