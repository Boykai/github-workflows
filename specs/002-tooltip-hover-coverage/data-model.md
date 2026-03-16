# Data Model: Deep UI/UX Tooltip & Hover Coverage

**Feature**: `002-tooltip-hover-coverage` | **Date**: 2026-03-15 | **Plan**: [plan.md](plan.md)

## Entities

### TooltipEntry

Represents a single entry in the centralized tooltip content registry. This is the existing entity, documented here for completeness and to define the contract for new entries.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `key` | `string` | Unique, dot-notation `{area}.{section}.{element}` | Lookup key used by `<Tooltip contentKey="...">`. Maps to object key in `tooltipContent` record |
| `summary` | `string` | Required, non-empty, ≤120 characters recommended | Concise explanation displayed as the primary tooltip text |
| `title` | `string \| undefined` | Optional | Bold heading displayed above the summary for progressive disclosure |
| `learnMoreUrl` | `string \| undefined` | Optional, valid URL | "Learn more →" link displayed below the summary |

**Validation Rules**:
- `key` must follow the `{area}.{section}.{element}` naming convention where `area` is one of: `pipeline`, `agents`, `chat`, `board`, `tools`, `settings`, `chores`, `nav`.
- `summary` text must match the exact UI terminology (e.g., "execution group" not "group", "stage" not "column").
- Every `key` in the registry must have at least one corresponding `contentKey=` usage in a component file.
- No two entries may share the same `key` value.

**State Transitions**: N/A — tooltip entries are static configuration data.

**Relationships**:
- Referenced by `<Tooltip contentKey={key}>` in component files.
- Referenced by `aria-label` attributes on icon-only buttons (text must match `summary`).

---

### HoverCardData

Represents the data structure rendered inside a hover card for different entity types. This is a union type — each entity type has a different shape.

#### AgentHoverCardData

Displayed when hovering over an AgentNode (pipeline) or AgentCard name/avatar (agents page).

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `name` | `string` | Required | Agent display name |
| `description` | `string \| undefined` | Optional | Agent description snippet (first ~100 characters) |
| `model` | `string \| undefined` | Optional | Assigned AI model name (e.g., "GPT-4o", "Claude 3.5") |
| `tools` | `string[]` | Default: `[]` | List of configured tool names |
| `lastRunStatus` | `'success' \| 'failure' \| 'running' \| 'idle' \| undefined` | Optional | Status of the agent's most recent execution |
| `runCount` | `number \| undefined` | Optional | Total number of executions (agents page only) |

**Validation Rules**:
- `name` is always present (sourced from the agent configuration).
- `description` is truncated to ~100 characters if longer, with ellipsis.
- `tools` displays up to 5 items; if more exist, shows "+N more" indicator.
- `lastRunStatus` renders as a colored status badge.
- If data is loading, display a skeleton placeholder inside the hover card.

---

#### IssueHoverCardData

Displayed when hovering over an IssueCard on the board page.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `title` | `string` | Required | Full issue title (not truncated) |
| `number` | `number \| undefined` | Optional | Issue number (e.g., #42) |
| `assignees` | `string[]` | Default: `[]` | List of assignee display names or usernames |
| `labels` | `Array<{ name: string; color: string }>` | Default: `[]` | Issue labels with color codes |
| `pipelineStage` | `string \| undefined` | Optional | Current pipeline stage name |
| `status` | `string \| undefined` | Optional | Issue status (e.g., "Open", "In Progress", "Done") |

**Validation Rules**:
- `title` is the full, untruncated title — this is the primary purpose of the hover card.
- `assignees` displays up to 3 avatars; if more exist, shows "+N" indicator.
- `labels` renders as colored badges matching the board's label rendering.
- If the issue has no labels or assignees, those sections are omitted from the card.

---

#### MentionHoverCardData

Displayed when hovering over an `@agent-name` mention chip in the chat composer.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `name` | `string` | Required | Agent display name |
| `description` | `string \| undefined` | Optional | Brief agent description |
| `tools` | `string[]` | Default: `[]` | List of configured tool names |

**Validation Rules**:
- Compact layout — fewer fields than `AgentHoverCardData`.
- `tools` displays up to 3 items with overflow indicator.

---

### PopoverComponent

Represents the shared popover primitive's API surface. Not a data entity per se, but a component contract.

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `open` | `boolean \| undefined` | Uncontrolled | Controlled open state |
| `onOpenChange` | `(open: boolean) => void \| undefined` | — | Callback when open state changes |
| `modal` | `boolean` | `false` | Whether to render as a modal (with backdrop) |

**PopoverContent Props**:

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `side` | `'top' \| 'right' \| 'bottom' \| 'left'` | `'bottom'` | Preferred placement side |
| `align` | `'start' \| 'center' \| 'end'` | `'center'` | Alignment along the side |
| `sideOffset` | `number` | `4` | Distance from trigger (px) |
| `collisionPadding` | `number` | `8` | Padding from viewport edge (px) |

**Behavior**:
- Focus trapped inside content when open.
- Closes on outside click.
- Closes on Escape key.
- Returns focus to trigger on close.
- Sets `aria-haspopup` and `aria-expanded` on trigger automatically.
- Renders in a portal to avoid z-index stacking issues.

---

### HoverCardComponent

Represents the shared hover card primitive's API surface.

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `openDelay` | `number` | `300` | Milliseconds before card opens on hover |
| `closeDelay` | `number` | `150` | Milliseconds before card closes on mouse leave |

**HoverCardContent Props**:

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `side` | `'top' \| 'right' \| 'bottom' \| 'left'` | `'bottom'` | Preferred placement side |
| `align` | `'start' \| 'center' \| 'end'` | `'center'` | Alignment along the side |
| `sideOffset` | `number` | `4` | Distance from trigger (px) |
| `collisionPadding` | `number` | `8` | Padding from viewport edge (px) |

**Behavior**:
- Opens after `openDelay` ms of hovering over trigger.
- Closes after `closeDelay` ms of mouse leaving trigger AND content (user can move into card).
- Animations gated behind `motion-safe:` Tailwind modifier.
- No focus trapping (hover cards are informational, not interactive modals).
- Renders in a portal.

## Entity Relationships

```text
TooltipEntry (registry)
  └─── Referenced by ──→ <Tooltip contentKey={key}> (component usage)
  └─── Referenced by ──→ aria-label={entry.summary} (icon-only buttons)

AgentHoverCardData
  └─── Rendered inside ──→ <HoverCardContent> on AgentNode (pipeline)
  └─── Rendered inside ──→ <HoverCardContent> on AgentCard (agents page)

IssueHoverCardData
  └─── Rendered inside ──→ <HoverCardContent> on IssueCard (board)

MentionHoverCardData
  └─── Rendered inside ──→ <HoverCardContent> on @agent-name chip (chat)

PopoverComponent
  └─── Wraps ──→ ModelSelector content (pipeline)
  └─── Wraps ──→ AddAgentPopover content (board)
  └─── Wraps ──→ AgentPresetSelector content (board)
  └─── Wraps ──→ Any future manual overlay migrations
```
