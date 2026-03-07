# Research: Project Page — Agent Pipeline UX Overhaul

**Feature Branch**: `028-project-page-ux`
**Date**: 2026-03-07

## R1: Drag/Drop Teleport Bug Root Cause

**Decision**: Fix @dnd-kit offset calculation by ensuring `useSortable` transform is applied correctly without conflicting CSS transforms, and verify DragOverlay uses the correct drag origin offset.
**Rationale**: The agent tile "teleports to the right on-click" is a classic @dnd-kit symptom caused by one of three issues: (1) the `CSS.Transform.toString(transform)` in `useSortable` conflicts with existing CSS transforms or positioning on the tile or its container, (2) the DragOverlay does not receive the correct initial position relative to the pointer, or (3) the grid container's `padding`/`margin` causes a coordinate-space mismatch between the drag sensor and the visual element. In `AgentColumnCell.tsx`, the sortable item applies `CSS.Transform.toString(transform)` directly — if the element's offsetParent has padding or the grid gap affects bounding-rect calculations, the initial transform will jump. The fix is: (a) use `CSS.Translate.toString(transform)` instead of `CSS.Transform.toString(transform)` to avoid scale/rotation interference; (b) ensure the DragOverlay's `dropAnimation` is correctly configured; (c) set `modifiers={[restrictToWindowEdges]}` or use the built-in pointer offset to anchor the overlay to the cursor grab point.
**Alternatives considered**:
- Replace @dnd-kit with react-beautiful-dnd — react-beautiful-dnd is in maintenance mode and doesn't support React 19. @dnd-kit is the correct choice.
- Replace @dnd-kit with @hello-pangea/dnd — Adds an unnecessary dependency swap when the root cause is configuration, not library capability.

## R2: DragOverlay Pointer Offset Configuration

**Decision**: Use `useDraggable`/`useSortable` with the DragOverlay pattern, capturing the pointer's offset relative to the element's top-left at drag start, then applying that offset to the overlay position.
**Rationale**: @dnd-kit's `DragOverlay` renders a portal-positioned clone. By default it centers on the pointer unless configured otherwise. The `handleDragStart` handler in `AgentConfigRow.tsx` already captures `event.active.rect.current.initial` — the fix needs to compute the pointer offset as `pointerPosition - elementTopLeft` and pass it to DragOverlay's style or use the `modifiers` prop. The `@dnd-kit/modifiers` package (already installed) provides `restrictToWindowEdges` but the key modifier needed is a custom offset adjuster or using the `activatorEvent` from `DragStartEvent` to compute `{x: clientX - rect.left, y: clientY - rect.top}`.
**Alternatives considered**:
- Fixed center-of-element offset — Less natural; users expect the element to stay anchored at their click point.
- No DragOverlay (transform-in-place only) — Loses the visual polish of a floating clone and causes layout shifts.

## R3: Agent Pipeline Restyling Reference

**Decision**: Mirror the `PipelineBoard.tsx` component's styling: use `border border-border/60`, `rounded-[1.2rem]`, `celestial-panel`, `gap-3`, and `bg-background/50` for headers. Replace the current heavier styling in `AgentConfigRow.tsx`.
**Rationale**: The spec requires the Agent Pipeline on the project page to match the "Pipeline Stages" component on the pipeline page. Inspecting `PipelineBoard.tsx`, the key classes are: container uses `celestial-panel flex flex-col gap-4`, stage cards use `rounded-[1.2rem] border border-border/60`, grid uses `gap-3`, and the overall visual weight is lighter (no heavy borders, no dark backgrounds). The current `AgentConfigRow.tsx` uses heavier borders and spacing that need to be reduced.
**Alternatives considered**:
- Extract a shared "PipelineCard" component — Premature abstraction per constitution Principle V. The styling alignment can be achieved by matching Tailwind classes without a shared component.

## R4: Agent Name Formatting Strategy

**Decision**: Implement `formatAgentName(slug: string, displayName?: string | null): string` as a pure utility function in `frontend/src/utils/formatAgentName.ts`.
**Rationale**: The function handles: (1) if `displayName` is provided and non-empty, return it as-is (display_name takes precedence); (2) split slug on `.`; (3) filter empty segments (handles `..` edge case); (4) title-case each segment (first letter uppercase, rest lowercase); (5) special handling: "speckit" → "Spec Kit" (split known compound words); (6) join with " - ". Currently, 4+ components use `agent.display_name || agent.slug` — all should call this utility instead. Edge cases: "speckit.tasks" → "Spec Kit - Tasks", "linter" → "Linter", "agent.v2.runner" → "Agent - V2 - Runner", "speckit..tasks" → "Spec Kit - Tasks" (empty segment filtered).
**Alternatives considered**:
- Inline formatting in each component — Violates DRY (4+ call sites).
- Backend-side formatting — Adds unnecessary coupling; the slug is the canonical identifier, display formatting is a presentation concern.

## R5: Markdown Rendering Library Choice

**Decision**: Add `react-markdown` (with `remark-gfm` plugin) as a new frontend dependency for rendering GitHub Issue descriptions.
**Rationale**: `react-markdown` is the standard React Markdown renderer: lightweight (~12KB gzip), supports remark/rehype plugin ecosystem, renders to React elements (no dangerouslySetInnerHTML), and handles GFM (GitHub Flavored Markdown) via `remark-gfm`. The project has no existing Markdown renderer. Using `react-markdown` + `remark-gfm` covers: headings, lists, code blocks (fenced), inline code, bold, italic, strikethrough, tables, task lists, and autolinks — all of which appear in GitHub Issue bodies.
**Alternatives considered**:
- `marked` + `dangerouslySetInnerHTML` — XSS risk; requires separate sanitization (DOMPurify). More code, more risk.
- `@mdx-js/react` — Overkill; designed for MDX (JSX in Markdown), not plain Markdown rendering.
- `markdown-it` — Good library but requires manual React integration. `react-markdown` provides this out of the box.

## R6: Sub-Issue Filtering for Done Column

**Decision**: Filter sub-issues from the Done column on the backend by checking if a board item has a parent issue reference, and excluding it from "Done"/"Closed" status columns.
**Rationale**: The backend `service.py` (lines 920-970) groups items by `status_option_id` into column buckets. Sub-issues are fetched per parent issue and attached as `BoardItem.sub_issues[]`. However, sub-issues that have their own project item (with their own status) can independently appear in columns including Done. The fix is: when building column items for a "Done" or "Closed" status, filter out items whose `item_id` appears as a sub-issue of any parent item. This requires cross-referencing the sub-issue IDs collected during the board data build. The filtering happens at the board data assembly step, not at the GitHub API query level.
**Alternatives considered**:
- Frontend-only filtering — Would still fetch unnecessary data and increase payload size. Backend filtering is more efficient.
- GitHub API query parameter — The GitHub Projects V2 API does not support filtering by parent/sub-issue status in the query. Post-fetch filtering is required.

## R7: Pipeline Configuration Selector Enhancement

**Decision**: Extend `AgentPresetSelector.tsx` to fetch and display saved pipeline configurations from the `/api/pipelines/{project_id}` endpoint alongside the existing built-in presets (Custom, GitHub Copilot, Spec Kit).
**Rationale**: The backend already has `GET /api/pipelines/{project_id}` returning `PipelineConfigListResponse` with saved pipeline configurations including stages and agent nodes. The current `AgentPresetSelector` only shows hardcoded presets. The enhancement adds a "Saved Configurations" section that fetches from the API and maps `PipelineConfig.stages[].agents[]` to `AgentAssignment[]` per column. The selected config ID is persisted in project-level state (localStorage key `pipeline-config:{project_id}`) so it survives sessions. When a new GitHub Issue is created, the active pipeline config ID is included in the creation payload.
**Alternatives considered**:
- Separate selector component — Unnecessary; the existing preset selector is the right UI element to extend.
- Backend-only config persistence — The frontend needs to know the selected config for immediate UI updates; localStorage provides instant read on page load while the backend persists the authoritative selection.

## R8: Unified Layout Alignment Strategy

**Decision**: Replace the current fixed-width column layout (`w-[320px]`) with a shared CSS grid that spans both the Agent Pipeline section and the kanban board, using `grid-template-columns: repeat(N, minmax(14rem, 1fr))` where N is the column count.
**Rationale**: Currently, `AgentConfigRow` uses `gridTemplateColumns: repeat(${columnCount}, minmax(14rem, 1fr))` but `ProjectBoard` uses `flex` with `w-[320px]` fixed-width columns. This mismatch prevents alignment. The fix wraps both sections in a shared container where the grid column count is derived from the project's status columns. Both the pipeline row and the board columns reference the same grid template, ensuring 1:1 horizontal alignment. The grid uses `minmax(14rem, 1fr)` to remain responsive while maintaining alignment.
**Alternatives considered**:
- CSS `subgrid` — Browser support is sufficient (Chrome 117+, Firefox 71+, Safari 16+) but unnecessary complexity; a shared parent grid with explicit `grid-template-columns` is simpler and more portable.
- Flex with percentage widths — Harder to maintain alignment when column counts change dynamically.

## R9: Agent Metadata Display Sources

**Decision**: Display model name and tool count on agent tiles by looking up the agent's full configuration from the `AvailableAgent` data or the `Agent` backend model (which includes `default_model_name` and `tools: list[str]`).
**Rationale**: The `AgentAssignment` type (used in the board pipeline) only has `id`, `slug`, `display_name`, and `config`. However, the `AvailableAgent` type has more detail, and the full `Agent` backend model has `default_model_name` and `tools` (list of tool slugs). The `AgentConfigRow` component already receives `availableAgents: AvailableAgent[]` as a prop. The approach is: (1) extend the `AvailableAgent` type to include `default_model_name` and `tools_count` (or pass the full agent data); (2) look up the matching agent by slug in `availableAgents` to get model name and tool count; (3) display beneath the formatted agent name in `AgentTile`.
**Alternatives considered**:
- Fetch full agent details per-tile — N+1 query problem. Bulk lookup from already-fetched data is preferred.
- Store model/tools in AgentAssignment — Would require schema migration and break existing data. Better to derive from the full agent list already available.

## R10: Touch Device Drag Support

**Decision**: Keep existing touch sensor configuration (`TouchSensor` with `delay: 250, tolerance: 5`) from @dnd-kit, which is already correctly configured in the codebase.
**Rationale**: The `AgentConfigRow.tsx` already configures `TouchSensor` with `activationConstraint: { delay: 250, tolerance: 5 }`. This prevents accidental drags while supporting intentional touch gestures. No changes needed for touch support — only the pointer sensor offset calculation needs fixing.
**Alternatives considered**:
- Custom touch handler — Unnecessary; @dnd-kit's TouchSensor handles this correctly.
