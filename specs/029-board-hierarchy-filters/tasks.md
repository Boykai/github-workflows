# Tasks: Project Board — Parent Issue Hierarchy, Sub-Issue Display, Agent Pipeline Fixes & Functional Filters

**Input**: Design documents from `/specs/029-board-hierarchy-filters/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/ (api.md, components.md), quickstart.md

**Tests**: Not explicitly requested in the feature specification. Existing tests must continue to pass (Constitution Check IV). No new test tasks are included.

**Organization**: Tasks grouped by user story (P1–P3) for independent implementation and testing. Each story can be delivered as an independently testable increment. User Stories 1, 2, and 3 are P1 and form the MVP. User Stories 4–7 are P2 incremental enhancements. User Story 8 is P3.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3…US8)
- Exact file paths included in descriptions

## Path Conventions

- **Web app**: `frontend/src/` (React/TypeScript), `backend/src/` (Python/FastAPI)
- Backend models: `backend/src/models/`
- Backend services: `backend/src/services/github_projects/`
- Frontend components: `frontend/src/components/board/`
- Frontend hooks: `frontend/src/hooks/`
- Frontend types: `frontend/src/types/`
- Frontend pages: `frontend/src/pages/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add new backend models, frontend types, and shared data fields needed by multiple user stories.

- [x] T001 Add `Label` Pydantic model (`id: str`, `name: str`, `color: str`) and new fields (`labels: list[Label] = []`, `created_at: str | None = None`, `updated_at: str | None = None`, `milestone: str | None = None`) to `BoardItem` in backend/src/models/board.py
- [x] T002 [P] Add `BoardLabel` interface (`id: string`, `name: string`, `color: string`) and new fields (`labels: BoardLabel[]`, `created_at?: string`, `updated_at?: string`, `milestone?: string`) to the `BoardItem` interface in frontend/src/types/index.ts

**Checkpoint**: All shared types and models are in place. Ready for foundational backend changes.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Extend the GraphQL query to fetch labels, timestamps, and milestone; parse them in the service layer; and filter sub-issues from ALL columns to produce a parent-only board dataset.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete — all UI changes depend on the backend providing labels, timestamps, milestone, and parent-only data.

- [x] T003 Extend `BOARD_GET_PROJECT_ITEMS_QUERY` `... on Issue` fragment with `createdAt`, `updatedAt`, `milestone { title }`, and `labels(first: 20) { nodes { id name color } }` in backend/src/services/github_projects/graphql.py
- [x] T004 Parse `labels`, `createdAt`, `updatedAt`, and `milestone` from the GraphQL response in the item processing loop — construct `Label` objects from `labels.nodes`, extract `createdAt`/`updatedAt` as strings, extract `milestone.title` as string — and assign to `BoardItem` in backend/src/services/github_projects/service.py
- [x] T005 Update sub-issue filtering to exclude sub-issue `content_id`s from ALL columns instead of only Done/Closed/Completed columns (`_DONE_STATUS_NAMES`) — the current code only filters sub-issues from done columns (lines ~970-990), but FR-001 requires sub-issues to be excluded from every column so only parent issues appear as top-level cards — remove the `if col.status.name.lower() in _DONE_STATUS_NAMES` guard so the filter applies unconditionally in backend/src/services/github_projects/service.py
- [x] T006 Recalculate `item_count` and `estimate_total` per column after the expanded sub-issue filtering so column header counts reflect the parent-only item set in backend/src/services/github_projects/service.py

**Checkpoint**: Backend returns parent-only board items with labels, timestamps, and milestone fields populated. Sub-issues no longer appear as standalone cards in any column.

---

## Phase 3: User Story 1 — Parent-Only Board with Collapsible Sub-Issues (Priority: P1) 🎯 MVP

**Goal**: Show only parent issues as top-level board cards; nest sub-issues in a collapsible panel within each parent card displaying agent name and model name.

**Independent Test**: Load a project board with parent issues that have sub-issues. Confirm only parent issues appear as top-level cards. Expand a parent card to see sub-issue tiles with agent and model metadata. Collapse it again. Confirm collapsed by default.

### Implementation for User Story 1

- [x] T007 [US1] Add `availableAgents?: AvailableAgent[]` prop to `IssueCard` interface and thread the prop from `ProjectsPage` → `ProjectBoard` → `BoardColumn` → `IssueCard` in frontend/src/pages/ProjectsPage.tsx, frontend/src/components/board/ProjectBoard.tsx, frontend/src/components/board/BoardColumn.tsx, and frontend/src/components/board/IssueCard.tsx
- [x] T008 [US1] Add collapsible sub-issue toggle to `IssueCard` with `useState<boolean>(false)` — render a clickable row with chevron icon (`▶` collapsed / `▼` expanded) and count badge (`"{n} sub-issue{n !== 1 ? 's' : ''}"`) — hide entire toggle row when `item.sub_issues.length === 0` in frontend/src/components/board/IssueCard.tsx
- [x] T009 [US1] Render expanded sub-issue tiles inside the collapsible section — each tile shows state icon (`○` open / `✓` closed), title, agent name (formatted from `assigned_agent` slug, "Unassigned" if absent), and model name (resolved via `availableAgents.find(a => a.slug === subIssue.assigned_agent)?.default_model_name`, `"—"` if absent) in frontend/src/components/board/IssueCard.tsx
- [x] T010 [US1] Add `max-h-60 overflow-y-auto` to the expanded sub-issue panel container so large sub-issue lists (50+) scroll internally without growing the parent card excessively in frontend/src/components/board/IssueCard.tsx

**Checkpoint**: Parent-only board view is functional. Sub-issues are nested within parent cards in a collapsible panel with agent and model metadata. Collapsed by default.

---

## Phase 4: User Story 2 — Parent Issue Labels on Board Cards (Priority: P1)

**Goal**: Display all GitHub labels as colored chips on each parent issue card for at-a-glance visual triage.

**Independent Test**: Load a project board where parent issues have GitHub labels. Confirm each card shows colored label chips matching GitHub label colors and names. Confirm cards with no labels show no label section.

### Implementation for User Story 2

- [x] T011 [P] [US2] Render `item.labels` as colored label chips below the card description and above assignees — use `background: #{label.color}` with contrast-computed text color (white on dark backgrounds, black on light — use WCAG relative luminance formula: `L = 0.2126*R + 0.7152*G + 0.0722*B`, threshold `L > 0.179` → black text, else white text) in frontend/src/components/board/IssueCard.tsx
- [x] T012 [US2] Add `max-w-[120px] truncate` with `title={label.name}` hover tooltip for long label names, and `flex flex-wrap gap-1` on the label container for multi-line wrapping — hide the label section entirely when `item.labels.length === 0` in frontend/src/components/board/IssueCard.tsx

**Checkpoint**: Label chips display correctly on parent cards with proper colors, truncation, and wrapping. Cards with no labels show no empty placeholder.

---

## Phase 5: User Story 3 — Scrollable Project Board Columns (Priority: P1)

**Goal**: Make each board column independently vertically scrollable so tall columns do not overflow the viewport.

**Independent Test**: Load a project board with one column containing 15+ parent issue cards. Scroll within that column — confirm only that column scrolls and other columns remain stationary. No page-level scrolling.

### Implementation for User Story 3

- [x] T013 [US3] Ensure `BoardColumn` card list container has constrained height — set column container to `flex flex-col h-full` with header as `flex-shrink-0` and card list as `flex-1 overflow-y-auto` in frontend/src/components/board/BoardColumn.tsx
- [x] T014 [P] [US3] Ensure `ProjectBoard` outer grid/flex container constrains column heights — apply `h-full` (or `max-h-[calc(100vh-<header-offset>)]`) and `overflow-y-hidden` on the board wrapper so individual columns activate their `overflow-y-auto` in frontend/src/components/board/ProjectBoard.tsx

**Checkpoint**: Columns scroll independently. Scrolling one column does not affect others or trigger page-level scroll. No scrollbars on columns with few items.

---

## Phase 6: User Story 4 — Agent Pipeline Model & Tool Count Fixes (Priority: P2)

**Goal**: Fix data-binding bugs causing some agent tiles in the Agent Pipeline to show missing model names or tool counts.

**Independent Test**: Load a project with an Agent Pipeline where agents have configured models and tools. Verify every agent tile shows the correct model name and tool count with no omissions.

### Implementation for User Story 4

- [x] T015 [US4] Fix `AgentTile` metadata lookup to use case-insensitive slug comparison — change `availableAgents?.find((a) => a.slug === agent.slug)` to `availableAgents?.find((a) => a.slug.toLowerCase() === agent.slug.toLowerCase())` in frontend/src/components/board/AgentTile.tsx
- [x] T016 [US4] Audit `metaParts` array construction — ensure `metadata?.default_model_name` and `metadata?.tools_count` are correctly appended when present, that `tools_count` of `0` renders as `"0 tools"` or is gracefully omitted, and that the warning badge (`⚠`) only appears when metadata is truly unavailable in frontend/src/components/board/AgentTile.tsx

**Checkpoint**: All agent tiles in the Agent Pipeline display correct model names and tool counts. No missing metadata for agents that are in the available agents list.

---

## Phase 7: User Story 5 — Custom Pipeline Label Updates to Saved Configuration Name (Priority: P2)

**Goal**: Dynamically replace the "Custom" label in the Agent Pipeline with the name of the active saved pipeline configuration when selected, reverting to "Custom" when no named configuration is active.

**Independent Test**: Load a project with saved pipeline configurations. Select a saved configuration and confirm the header label updates from "Custom" to the configuration name. Deselect or modify the configuration and confirm revert to "Custom". Refresh the page and confirm persistence.

### Implementation for User Story 5

- [x] T017 [US5] Add `activePipelineName` derived state via `useMemo` — look up `selectedPipelineId` (from localStorage) in the `savedPipelines` list fetched via `pipelinesApi.list()`, return `pipeline.name` when matched and configuration is not dirty, return `null` otherwise in frontend/src/components/board/AgentPresetSelector.tsx
- [x] T018 [US5] Update header label rendering to display `activePipelineName` when non-null, falling back to `matchedPreset.label` (e.g., "Custom") when null — ensuring the label reverts to "Custom" on dirty state or deselection in frontend/src/components/board/AgentPresetSelector.tsx

**Checkpoint**: Pipeline header label dynamically reflects the saved configuration name. Reverts to "Custom" on deselection or manual changes. Persists across page refresh.

---

## Phase 8: User Story 6 — Functional Filter Controls on the Project Board (Priority: P2)

**Goal**: Implement filter controls that narrow displayed parent issue cards by label, assignee, and milestone — with visual active state and localStorage persistence.

**Independent Test**: Load a project board with diverse parent issues. Click "Filter" → select a label filter → confirm only matching cards appear. Apply multiple filters → confirm AND logic. Clear filters → confirm full board restored. Refresh page → confirm persistence.

### Implementation for User Story 6

- [x] T019 [US6] Create `useBoardControls` hook in frontend/src/hooks/useBoardControls.ts — define `BoardFilterState`, `BoardSortState`, `BoardGroupState`, and `BoardControlsState` interfaces per data-model.md; manage state with `useState`; persist to `localStorage` keyed by `board-controls-{projectId}`; restore state on mount; derive `availableLabels`, `availableAssignees`, and `availableMilestones` from raw board data using `useMemo`; export `controls`, `setFilters`, `setSort`, `setGroup`, `clearAll`, `hasActiveControls`, and available option arrays
- [x] T020 [US6] Implement filter transform in `useBoardControls` using `useMemo` — for each column, filter items where: `labels` array intersection (if `filters.labels.length > 0`), `assignees` array intersection (if `filters.assignees.length > 0`), `milestone` inclusion (if `filters.milestones.length > 0`) — apply AND logic across criteria; empty filter arrays mean no restriction for that field in frontend/src/hooks/useBoardControls.ts
- [x] T021 [P] [US6] Create `BoardToolbar` component in frontend/src/components/board/BoardToolbar.tsx — render Filter button with dropdown panel containing checkbox lists for labels, assignees, and milestones (populated from `availableLabels`, `availableAssignees`, `availableMilestones` props); include "Clear All" button; only one panel open at a time (local `activePanel` state); accept `controls`, `onControlsChange`, and available option arrays as props per contracts/components.md C5
- [x] T022 [US6] Integrate `useBoardControls` and `BoardToolbar` into `ProjectsPage` — call `useBoardControls(projectId, boardData)`, render `BoardToolbar` above `ProjectBoard`, pass `transformedData` (output of hook) to `ProjectBoard` instead of raw `boardData` in frontend/src/pages/ProjectsPage.tsx

**Checkpoint**: Filter controls are functional. Selecting label/assignee/milestone filters narrows the board view. Clearing filters restores full view. State persists in localStorage.

---

## Phase 9: User Story 7 — Functional Sort Controls on the Project Board (Priority: P2)

**Goal**: Implement sort controls that reorder parent issue cards within each column by created date, updated date, priority, or title.

**Independent Test**: Load a project board. Click "Sort" → select "Title A-Z" → confirm cards in each column are alphabetically ordered. Sort by "Priority — Highest First" → confirm P1 before P2 before P3. Clear sort → confirm default order restored.

### Implementation for User Story 7

- [x] T023 [US7] Implement sort transform in `useBoardControls` using `useMemo` — after filter, sort items within each column by: `created_at` (ISO string comparison), `updated_at` (ISO string comparison), `priority` (numeric mapping: P0=0, P1=1, P2=2, P3=3, null=99), or `title` (localeCompare); apply `asc`/`desc` direction; null sort field = no reorder in frontend/src/hooks/useBoardControls.ts
- [x] T024 [US7] Add Sort panel to `BoardToolbar` — render radio options for sort field (Created, Updated, Priority, Title) with ascending/descending toggle per option; include "Clear Sort" button; show Sort panel when sort button clicked (mutually exclusive with filter/group panels) in frontend/src/components/board/BoardToolbar.tsx

**Checkpoint**: Sort controls are functional. Cards reorder within columns based on selected field and direction. Clearing sort restores default order.

---

## Phase 10: User Story 8 — Functional Group By Controls on the Project Board (Priority: P3)

**Goal**: Implement group-by controls that reorganize parent issue cards into named groups within each column by label, assignee, or milestone.

**Independent Test**: Load a project board with parent issues assigned to different milestones. Group by "Milestone" → confirm cards within each column are organized under "Sprint 1", "Sprint 2", etc. headers. Remove grouping → confirm default layout restored.

### Implementation for User Story 8

- [x] T025 [US8] Implement group-by transform in `useBoardControls` — after filter and sort, group items within each column by first label name (`"No Label"` fallback), first assignee login (`"Unassigned"` fallback), or milestone (`"No Milestone"` fallback); export grouped structure alongside flat transformed data; omit empty groups from output in frontend/src/hooks/useBoardControls.ts
- [x] T026 [US8] Add Group By panel to `BoardToolbar` — render radio options for group field (Label, Assignee, Milestone) plus "Remove Grouping" button; show Group By panel when group button clicked (mutually exclusive with filter/sort panels) in frontend/src/components/board/BoardToolbar.tsx
- [x] T027 [US8] Update `BoardColumn` and `ProjectBoard` to render group headers within each column when grouping is active — headers styled as `text-xs font-semibold uppercase text-gray-400 tracking-wide border-b border-gray-700 pb-1 mb-2 mt-3` (first group: `mt-0`); hide headers for empty groups; items sorted within each group per active sort in frontend/src/components/board/ProjectBoard.tsx and frontend/src/components/board/BoardColumn.tsx

**Checkpoint**: Group-by controls are functional. Cards organize into named groups within columns. Removing grouping restores default layout. Groups + filters + sort compose correctly.

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Visual polish, edge case handling, and validation across all user stories.

- [x] T028 [P] Add active state indicators (colored dot badge and accent background) on Filter, Sort, and Group By toolbar buttons when any non-default configuration is active — use `hasActiveControls` and per-control checks from `useBoardControls` per FR-013 in frontend/src/components/board/BoardToolbar.tsx
- [x] T029 [P] Add empty state message ("No issues match the current filters") when filtering results in zero parent issues across all columns — render centered message in `ProjectBoard` when `transformedData` columns all have zero items and filters are active in frontend/src/components/board/ProjectBoard.tsx
- [x] T030 Run quickstart.md manual verification checklist (sections 1–11) to validate all features against acceptance scenarios

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup (Phase 1) completion — BLOCKS all user stories
- **User Stories (Phases 3–10)**: All depend on Foundational (Phase 2) completion
  - US1 (Phase 3): No dependencies on other stories — MVP start
  - US2 (Phase 4): Can run in parallel with US1 (different card sections)
  - US3 (Phase 5): Can run in parallel with US1 and US2 (different components)
  - US4 (Phase 6): Can run in parallel with US1–3 (different component: AgentTile)
  - US5 (Phase 7): Can run in parallel with US1–4 (different component: AgentPresetSelector)
  - US6 (Phase 8): Depends on US1 completion (filter operates on parent-only board)
  - US7 (Phase 9): Depends on US6 (extends useBoardControls hook and BoardToolbar)
  - US8 (Phase 10): Depends on US7 (extends useBoardControls hook and BoardToolbar)
- **Polish (Phase 11)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Start after Phase 2 — No dependencies on other stories
- **US2 (P1)**: Start after Phase 2 — Can run in parallel with US1
- **US3 (P1)**: Start after Phase 2 — Can run in parallel with US1 and US2
- **US4 (P2)**: Start after Phase 2 — Can run in parallel with US1–3
- **US5 (P2)**: Start after Phase 2 — Can run in parallel with US1–4
- **US6 (P2)**: Start after Phase 2 (and US1 recommended) — Creates useBoardControls + BoardToolbar
- **US7 (P2)**: Depends on US6 — Extends the same hook and toolbar with sort
- **US8 (P3)**: Depends on US7 — Extends the same hook and toolbar with group-by

### Within Each User Story

- Models/types before services/logic
- Core implementation before integration
- Story complete and testable before moving to next priority

### Parallel Opportunities

- **Phase 1**: T001 and T002 can run in parallel (backend vs. frontend)
- **Phase 2**: T003 → T004 → T005 → T006 are sequential (same backend files, dependent)
- **Phases 3–7**: US1, US2, US3, US4, and US5 can all be worked in parallel by different developers
- **Phases 8–10**: US6 → US7 → US8 are sequential (shared hook and toolbar)
- **Phase 11**: T028 and T029 can run in parallel (different components)

---

## Parallel Example: MVP Sprint (User Stories 1–3)

```bash
# After completing Setup (Phase 1) and Foundational (Phase 2):

# Developer A: User Story 1 — Collapsible Sub-Issues
Task: T007 "Thread availableAgents prop through component hierarchy"
Task: T008 "Add collapsible sub-issue toggle to IssueCard"
Task: T009 "Render sub-issue tiles with agent/model metadata"
Task: T010 "Add overflow scrolling for large sub-issue lists"

# Developer B: User Story 2 — Label Chips (parallel with US1)
Task: T011 "Render label chips on parent cards"
Task: T012 "Add truncation and tooltip for long label names"

# Developer C: User Story 3 — Scrollable Columns (parallel with US1, US2)
Task: T013 "Constrain BoardColumn height with flex layout"
Task: T014 "Constrain ProjectBoard container height"
```

---

## Parallel Example: Enhancement Sprint (User Stories 4–5)

```bash
# After MVP is validated:

# Developer A: User Story 4 — Agent Pipeline Fix (parallel with US5)
Task: T015 "Fix case-insensitive slug lookup in AgentTile"
Task: T016 "Audit metaParts rendering edge cases"

# Developer B: User Story 5 — Custom Pipeline Label (parallel with US4)
Task: T017 "Add activePipelineName derived state"
Task: T018 "Update header label rendering"
```

---

## Implementation Strategy

### MVP First (User Stories 1–3)

1. Complete Phase 1: Setup (T001–T002)
2. Complete Phase 2: Foundational (T003–T006)
3. Complete Phase 3: User Story 1 — Collapsible Sub-Issues (T007–T010)
4. Complete Phase 4: User Story 2 — Label Chips (T011–T012)
5. Complete Phase 5: User Story 3 — Scrollable Columns (T013–T014)
6. **STOP and VALIDATE**: Test each story independently per quickstart.md sections 1–4
7. Deploy/demo if ready — board shows parent-only cards with collapsible sub-issues, labels, and scrollable columns

### Incremental Delivery

1. Setup + Foundational → Backend data pipeline complete
2. Add US1 → Parent-only board with collapsible sub-issues (MVP core!)
3. Add US2 → Label chips on cards (visual enhancement)
4. Add US3 → Scrollable columns (usability fix)
5. Add US4 + US5 → Agent Pipeline fixes (bug fixes, independent of board)
6. Add US6 → Filter controls (first board control)
7. Add US7 → Sort controls (extends filter infrastructure)
8. Add US8 → Group By controls (extends sort infrastructure)
9. Polish → Active indicators, empty states, final validation

### Parallel Team Strategy

With 3 developers:

1. Team completes Setup + Foundational together (Phase 1–2)
2. Once Foundational is done:
   - Developer A: US1 (collapsible sub-issues) → then US6 (filters) → US7 (sort) → US8 (group-by)
   - Developer B: US2 (labels) → US3 (scrollable columns) → then Polish
   - Developer C: US4 (agent tile fix) → US5 (custom label) → then Polish
3. All stories integrate independently; final validation via quickstart.md

---

## Summary

| Metric | Value |
|--------|-------|
| **Total Tasks** | 30 |
| **Setup Phase** | 2 tasks (T001–T002) |
| **Foundational Phase** | 4 tasks (T003–T006) |
| **US1 — Collapsible Sub-Issues (P1)** | 4 tasks (T007–T010) |
| **US2 — Label Chips (P1)** | 2 tasks (T011–T012) |
| **US3 — Scrollable Columns (P1)** | 2 tasks (T013–T014) |
| **US4 — Agent Pipeline Fix (P2)** | 2 tasks (T015–T016) |
| **US5 — Custom Pipeline Label (P2)** | 2 tasks (T017–T018) |
| **US6 — Filter Controls (P2)** | 4 tasks (T019–T022) |
| **US7 — Sort Controls (P2)** | 2 tasks (T023–T024) |
| **US8 — Group By Controls (P3)** | 3 tasks (T025–T027) |
| **Polish** | 3 tasks (T028–T030) |
| **Parallel Opportunities** | US1–US5 can all run in parallel; T001/T002 parallel; T028/T029 parallel |
| **Suggested MVP Scope** | US1 + US2 + US3 (8 tasks after foundational phase) |
| **Format Validation** | ✅ All 30 tasks follow `- [ ] [TaskID] [P?] [Story?] Description with file path` format |

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable (except US7→US6 and US8→US7 dependency chain)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Backend changes (T001–T006) are prerequisite for all frontend stories
- No new API endpoints are created — only existing response shapes are extended
- No new dependencies are added — all changes use existing libraries (React, Tailwind, TanStack Query)
