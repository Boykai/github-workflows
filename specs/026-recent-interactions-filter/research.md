# Research: Recent Interactions — Filter Deleted Items & Display Only Parent Issues with Project Board Status Colors

**Feature Branch**: `026-recent-interactions-filter`
**Date**: 2026-03-07

## R1: Deleted Item Detection Strategy

**Decision**: Treat board data as the source of truth. Any item not present in `BoardDataResponse.columns[*].items` is considered deleted or removed from the project.
**Rationale**: The current `useRecentParentIssues` hook already derives its list from `BoardDataResponse`. The board data is fetched from the GitHub Projects V2 GraphQL API via `boardApi.getBoardData()` and cached by TanStack Query with automatic polling via `useBoardRefresh`. If an issue is deleted from GitHub or removed from the project board, it will no longer appear in the API response. Since the hook operates on this response, deleted items are implicitly excluded — no additional REST API calls (e.g., `GET /repos/{owner}/{repo}/issues/{number}` to check for 404s) are needed.
**Alternatives considered**:
- Individual issue validation via REST API — Would require N additional API calls per render cycle for N cached items. Excessive API usage, adds latency, and complicates rate limiting. The board data already serves as a batch validation.
- WebSocket push notifications for deletions — The app already has `useRealTimeSync` via WebSocket, but it doesn't currently push deletion events. Adding this would require backend changes (out of scope for a frontend-only feature).
- localStorage cache with TTL expiration — Would only remove items after a timeout, not immediately upon deletion. Does not meet SC-001 (removal within one render cycle).

## R2: Parent Issue Identification

**Decision**: A parent issue is a `BoardItem` where `content_type === 'issue'` AND the item's `number` does NOT appear in any other `BoardItem`'s `sub_issues` array within the same board data.
**Rationale**: The `BoardItem` model includes `content_type: ContentType` (values: `'issue' | 'draft_issue' | 'pull_request'`) and `sub_issues: SubIssue[]`. The `content_type` filter eliminates draft issues and pull requests immediately. For sub-issue detection: the GitHub Sub-Issues API populates each parent's `sub_issues` array with `SubIssue` objects containing `number` fields. If a board item's `number` appears in any other item's `sub_issues[*].number`, it is a sub-issue and must be excluded. This cross-referencing is O(N×M) where N is board items and M is average sub-issues per item — negligible for typical board sizes (< 200 items).
**Alternatives considered**:
- Check for `sub_issues_summary` parent reference via GitHub REST API — Would require additional per-item API calls. The board data already contains sub-issue relationships.
- Use `sub_issues.length > 0` as parent indicator — Incorrect; having children doesn't exclude items. The requirement is to exclude items that ARE sub-issues (have a parent), not items that have no children.
- Backend endpoint to return parent-only list — Out of scope (no backend changes). The frontend has all necessary data in `BoardDataResponse`.

## R3: Status Color Mapping for Recent Interactions

**Decision**: Map each parent issue to its board column's `StatusOption.color` (a `StatusColor` enum value), then use the existing `statusColorToCSS()` and `statusColorToBg()` utilities from `colorUtils.ts` to render the color accent.
**Rationale**: The `BoardDataResponse` structure is `columns: BoardColumn[]` where each `BoardColumn` has `status: BoardStatusOption` (with `color: StatusColor`) and `items: BoardItem[]`. When building the recent interactions list, we know which column each item belongs to, so we capture the column's status color alongside the item data. The existing `colorUtils.ts` already maps all 8 `StatusColor` values (GRAY, BLUE, GREEN, YELLOW, ORANGE, RED, PINK, PURPLE) to CSS hex and rgba values. The spec's suggested mapping (Todo→grey, In Progress→blue, In Review→yellow, Done→green, Blocked→red) naturally aligns with how project boards typically assign these colors. Since colors come from the actual board status options (not hardcoded status names), the feature automatically supports custom status names with custom colors.
**Alternatives considered**:
- Hardcoded status-name-to-color map — Would break for projects with custom status names or non-standard color assignments. Using the actual `StatusOption.color` from the board data is more robust.
- New CSS variables for status colors — Unnecessary; `colorUtils.ts` already provides the complete mapping. Adding parallel definitions would violate DRY.
- Tailwind color classes (e.g., `bg-blue-500`) — Less precise than the existing hex/rgba system. The `STATUS_COLOR_MAP` already provides the exact GitHub project board colors.

## R4: Rendering Strategy for Status Color Accent

**Decision**: Use a left border accent (`border-l-2` with inline `borderLeftColor` style) on each recent interaction entry in the Sidebar.
**Rationale**: The spec suggests "background chip, left border accent, or badge." A left border accent is the least intrusive option for a compact sidebar list — it provides clear color differentiation without adding visual weight or altering the layout flow. The existing sidebar items use `rounded-2xl` with padding, so a 2px left border fits within the existing spacing. The border color is set via inline style using `statusColorToCSS()` output (hex value), which works seamlessly with Tailwind's utility classes for the rest of the styling. For the status label, a small text indicator showing the status name provides additional context on hover via the existing `title` attribute.
**Alternatives considered**:
- Background chip (full colored background) — Too visually heavy for the sidebar's compact layout. Would compete with the active nav link highlight.
- Status badge/pill — Adds a separate element that takes horizontal space in an already narrow sidebar. Would require truncating the issue title further.
- Icon indicator (colored dot) — Subtle but may not meet the "immediately understand workflow state at a glance" requirement (SC-004). A border is more visible than a dot.

## R5: Empty State and Fallback Behavior

**Decision**: Update the existing empty state text from "No recent activity" to "No recent parent issues" and apply a neutral/default gray color (`StatusColor.GRAY`) for items with undefined or unavailable project board status.
**Rationale**: The sidebar already renders an empty state (`<p className="px-3 text-xs text-muted-foreground/60">No recent activity</p>`). Updating the text to mention "parent issues" aligns with the filtered behavior and meets FR-009. For the fallback color (FR-010), using GRAY is consistent with GitHub's default status color for undefined states and is already the fallback in `statusColorToCSS()` (`STATUS_COLOR_MAP[color] || STATUS_COLOR_MAP.GRAY`). For network errors (FR-011), the existing TanStack Query cache retains the last successful `BoardDataResponse`, so the hook naturally returns the last known valid state when a fetch fails — no additional error handling is needed in the hook.
**Alternatives considered**:
- Custom empty state illustration/icon — Adds visual complexity for a low-priority feature (P3). Simple text is consistent with the existing pattern.
- Hide the "Recent Interactions" section entirely when empty — Would cause layout shifts when items appear/disappear. Keeping the section with a message is more stable.
- Transparent/invisible fallback instead of gray — Would make items without status appear broken. A neutral gray communicates "no status" clearly.
