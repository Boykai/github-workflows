# Research: Project Board — Parent Issue Hierarchy, Sub-Issue Display, Agent Pipeline Fixes & Functional Filters

**Feature**: 029-board-hierarchy-filters  
**Date**: 2026-03-07

## R1: Parent-Only Board View — Sub-Issue Filtering Strategy

- **Decision**: Filter sub-issues from top-level board rendering on the backend by tracking all `content_id` values that appear in any parent's `sub_issues` list, then excluding those IDs from the column items across ALL columns (not just Done columns as currently implemented).
- **Rationale**: The backend already collects `all_sub_issue_ids` and filters Done columns (lines 970-990 of `service.py`). Extending this filter to all columns ensures sub-issues never appear as standalone cards. This is a minimal change — expanding the existing filter scope from `_DONE_STATUS_NAMES` columns to all columns. Frontend receives a clean parent-only dataset with no additional logic needed.
- **Alternatives considered**:
  - *Frontend-only filtering*: Would require the frontend to duplicate the sub-issue-ID-collection logic and filter items client-side. Rejected because it wastes bandwidth sending items that will be hidden, and duplicates logic across layers.
  - *Add `is_parent` flag to BoardItem*: Would require a new field and frontend filter. Rejected because the existing sub-issue-ID exclusion pattern already works and is simpler — no new fields needed.

## R2: Labels Data Pipeline — GraphQL Query Extension

- **Decision**: Extend `BOARD_GET_PROJECT_ITEMS_QUERY` in `graphql.py` to include `labels(first: 20) { nodes { id name color } }` in the `... on Issue` fragment. Add a `Label` Pydantic model and `labels: list[Label]` field to `BoardItem`. Parse labels in the service layer item processing loop.
- **Rationale**: GitHub's GraphQL API supports `labels` on Issue nodes natively. Adding it to the existing query avoids a separate REST call per issue. The `first: 20` limit is sufficient for typical issue labeling (most issues have <10 labels). The `color` field from GitHub returns a hex string (without `#` prefix) that can be used directly for chip styling.
- **Alternatives considered**:
  - *REST API call per issue*: Would add N additional API calls (one per issue) to fetch labels. Rejected due to rate limit impact and latency.
  - *Fetch labels only on frontend demand*: Lazy-load labels when card is hovered. Rejected because labels are needed for filtering and must be available upfront.

## R3: Collapsible Sub-Issue Panel — Component Design

- **Decision**: Add a local `useState<boolean>(false)` toggle to `IssueCard.tsx` that controls visibility of the sub-issue section. The toggle button shows a chevron icon (▶ collapsed, ▼ expanded) with a count badge (e.g., "3 sub-issues"). Sub-issue tiles display agent name and model name. The toggle is hidden when `sub_issues.length === 0`.
- **Rationale**: The current `IssueCard.tsx` already renders sub-issues inline (lines 115-129). Converting this to a collapsible section requires wrapping the existing sub-issue rendering in a conditional block controlled by local state. This is the simplest approach — no global state, no context, no new components for the toggle itself.
- **Alternatives considered**:
  - *Global expand/collapse state in a store*: Would allow "expand all" / "collapse all" functionality. Rejected as YAGNI — the spec does not require bulk expand/collapse, and adding it introduces unnecessary complexity.
  - *Separate SubIssuePanel component*: Extracting to a new component. This may be done as a refactor but the core logic stays in IssueCard to minimize file changes.

## R4: Sub-Issue Agent & Model Display — Data Availability

- **Decision**: The `SubIssue` type currently has `assigned_agent?: string` (slug). To display the model name, resolve the agent slug against the `AvailableAgent[]` list (already fetched via `useAvailableAgents` hook) to get `default_model_name`. Pass `availableAgents` down to the sub-issue tile rendering context.
- **Rationale**: The `AvailableAgent` interface already contains `default_model_name` and the agents list is already fetched at the page level. No additional API calls or type changes are needed — just prop threading from `ProjectsPage` → `ProjectBoard` → `BoardColumn` → `IssueCard` → sub-issue tiles.
- **Alternatives considered**:
  - *Add `model_name` to SubIssue backend model*: Would require the backend to resolve agent → model for each sub-issue. Rejected because the frontend already has the agent metadata and this would couple the board API to the agent configuration service unnecessarily.
  - *Fetch agent metadata in IssueCard*: Each card could call `useAvailableAgents`. Rejected because it would trigger N queries (one per card) when the data is already available at the page level.

## R5: Agent Pipeline Model & Tool Count Bug — Root Cause

- **Decision**: Audit the data flow from `workflowApi.listAgents()` → `useAvailableAgents()` → `AgentTile` prop threading. The likely root cause is that `AgentTile` looks up metadata via `availableAgents?.find((a) => a.slug === agent.slug)` (line 33 of `AgentTile.tsx`), but the `agent.slug` from `AgentAssignment` may not match the slug in `AvailableAgent` due to case differences or the agent not being in the available list. Fix by normalizing slug comparison (case-insensitive) and ensuring the available agents list is complete.
- **Rationale**: The `AgentTile` component already has the correct rendering logic (lines 38-41 build `metaParts` from `metadata?.default_model_name` and `metadata?.tools_count`). If `metadata` is `undefined` (slug mismatch), both model and tools disappear. The ⚠ warning badge on line 91 already detects this case (`!metadata`), confirming the lookup failure is the root cause.
- **Alternatives considered**:
  - *Embed model_name directly in AgentAssignment*: Would require changing the assignment storage format. Rejected because assignments are lightweight (slug + config) and metadata resolution from the available agents list is the correct separation of concerns.
  - *Cache agent metadata per slug in a Map*: Could improve lookup performance. Considered as an optional optimization but not necessary for correctness.

## R6: Custom Pipeline Label — Dynamic Naming

- **Decision**: In `AgentPresetSelector.tsx`, track the selected saved pipeline configuration name in component state. When a saved pipeline is selected, update the header label from "Custom" to the pipeline's `name` field. When the configuration is modified (becomes dirty) or deselected, revert to "Custom". The selected pipeline ID is already persisted in localStorage (line 166-171).
- **Rationale**: The `AgentPresetSelector` already stores the active preset ID in localStorage and has a `matchesPreset` function (line 129-131) that detects the "Custom" state. Extending this to also track the saved pipeline name is a small state addition. The pipeline name comes from the `PipelineConfigSummary` object already fetched via `pipelinesApi.list()`.
- **Alternatives considered**:
  - *Derive name from pipeline list on every render*: Look up the active pipeline ID in the fetched list each render. Viable but slightly less efficient than storing the name directly. Acceptable as the pipeline list is small.
  - *Store name in localStorage alongside ID*: Would persist the name across refreshes without re-fetching. Considered as an enhancement but the pipeline list is already cached by TanStack Query.

## R7: Filter Controls — Client-Side Predicate Architecture

- **Decision**: Implement a `useBoardControls` hook that manages filter state (`{ labels: string[], assignees: string[], statuses: string[], milestones: string[] }`), sort state (`{ field: string, direction: 'asc' | 'desc' }`), and group-by state (`{ field: string | null }`). The hook applies transforms to the board data using `useMemo` — filters narrow the item set, sort reorders within columns, group-by reorganizes into named sections. State is persisted to localStorage keyed by project ID.
- **Rationale**: All data needed for filtering, sorting, and grouping is already present in the in-memory `BoardDataResponse`. No additional API calls are needed. A single hook centralizes the logic, preventing scattered state management across the page. `useMemo` ensures transforms are only recomputed when inputs change. localStorage persistence satisfies FR-012.
- **Alternatives considered**:
  - *URL query parameters*: Would make filter state shareable via URL. Rejected because the spec says "local storage or URL query params" and localStorage is simpler to implement without URL serialization complexity.
  - *Server-side filtering*: Would require new API endpoints. Rejected because the data is already client-side and adding server endpoints violates the simplicity principle for this use case.
  - *Zustand store*: Could provide more structured state management. Rejected as YAGNI — a custom hook with `useState` + `useMemo` + localStorage is sufficient and avoids adding a new dependency pattern.

## R8: Sort Implementation — Priority Derivation

- **Decision**: Priority for sorting is derived from the `priority` custom field on `BoardItem` (e.g., `priority.name` = "P0", "P1", "P2", "P3"). The existing `ProjectsPage.tsx` already implements priority sorting (lines 83-99) with a numeric mapping: `{ P0: 0, P1: 1, P2: 2, P3: 3 }`. Extend this pattern to the `useBoardControls` hook and add sort by created date (`number` as proxy since GitHub issue numbers are sequential), updated date (requires adding field), and title (string comparison).
- **Rationale**: The `BoardItem` already has `priority?: BoardCustomFieldValue` which provides the priority name. Issue `number` serves as a reasonable proxy for creation order. Title sorting uses `localeCompare`. This avoids adding new fields to the backend for most sort options.
- **Alternatives considered**:
  - *Add `created_at` and `updated_at` fields to BoardItem*: Would provide exact timestamps. Recommended as an enhancement — the GraphQL query can include `createdAt` and `updatedAt` from the Issue fragment. Include in implementation if straightforward.
  - *Parse priority from labels (e.g., "p1" label)*: The spec mentions this in assumptions. Rejected because the board already uses the Priority custom field from GitHub Projects, which is more reliable than label parsing.

## R9: Group By Implementation — Column Reorganization

- **Decision**: Group By reorganizes cards within each column into named sub-sections. When grouping is active, each column renders group headers (e.g., "Assignee: Boykai", "Milestone: Sprint 1") with their matching cards beneath. Cards with no value for the group field appear in an "Unassigned" or "None" group. The column structure (status-based) is preserved — grouping adds a secondary organization layer within columns.
- **Rationale**: Preserving columns (which represent status) while adding group sub-sections within them maintains the kanban board mental model. Users expect status columns to remain stable; grouping provides an overlay organization. This is consistent with tools like Jira and Linear.
- **Alternatives considered**:
  - *Replace columns with group-based columns*: Would reorganize the entire board by the group field. Rejected because it destroys the status-based column structure that is fundamental to the board's purpose.
  - *Swimlanes (horizontal groups across columns)*: Would add horizontal rows for each group value. Considered but rejected for V1 as it requires significant layout changes and the within-column grouping is simpler and adequate.

## R10: Scrollable Columns — CSS Approach

- **Decision**: `BoardColumn.tsx` already has `overflow-y-auto` on the card list container (line 50). Verify this works correctly by ensuring the column container has a constrained height (e.g., `max-h-[calc(100vh-<header-height>)]` or `flex-1 overflow-y-auto` within a flex column layout). The `ProjectBoard.tsx` grid container should use `overflow-y-hidden` on the outer wrapper to prevent page-level scroll interference.
- **Rationale**: The existing `overflow-y-auto` class in `BoardColumn.tsx` should already provide independent scrolling. The issue may be that the parent container does not constrain height, allowing columns to grow infinitely. Adding a height constraint (e.g., via `h-full` + flex layout) should resolve this without changing the scroll behavior itself.
- **Alternatives considered**:
  - *Virtual scrolling (react-window)*: Would only render visible cards. Rejected as YAGNI for boards with <100 cards per column. Can be added later if performance issues arise.
  - *overflow-y-scroll (always show scrollbar)*: Would always show scrollbar even with few cards. Rejected in favor of `overflow-y-auto` which shows scrollbar only when needed.
