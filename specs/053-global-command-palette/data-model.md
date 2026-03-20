# Data Model: Global Search / Command Palette

**Feature Branch**: `053-global-command-palette`
**Date**: 2026-03-20
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

## Overview

This feature is entirely client-side and does not introduce new database tables or backend API
endpoints. The entities below represent the TypeScript interfaces and types used within the
command palette component and hook — they are runtime data structures, not persisted models.

## Entities

### 1. CommandPaletteItem

Represents a single searchable item in the command palette results list.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `id` | `string` | Unique identifier for the item | Unique within all items; format: `{category}-{name-slug}` |
| `label` | `string` | Display name shown in the results list | Non-empty, max 100 characters |
| `category` | `CommandCategory` | The group this item belongs to | One of the defined categories |
| `icon` | `LucideIcon` | Lucide icon component for visual identification | Valid Lucide icon reference |
| `description` | `string \| undefined` | Optional subtitle or description text | Max 200 characters |
| `keywords` | `string[]` | Additional search terms beyond the label | Zero or more strings |
| `action` | `() => void` | Callback executed when the item is selected | Must be a valid function |

**Relationships**:
- A CommandPaletteItem *belongs to* exactly one CommandCategory.
- A CommandPaletteItem *is produced by* one SearchSource.

**Validation Rules**:
- `id` must be unique across all items from all sources.
- `label` is the primary field used for search matching.
- `keywords` are secondary search fields (searched if label doesn't match).
- `action` typically calls `navigate(path)` for navigation items or executes a callback for quick actions.

---

### 2. CommandCategory

An enum-like type representing the grouping of search results.

| Value | Label | Icon | Description |
|-------|-------|------|-------------|
| `'pages'` | Pages | `LayoutDashboard` | Navigation targets (routes from NAV_ROUTES) |
| `'agents'` | Agents | `Bot` | Agent configurations |
| `'pipelines'` | Pipelines | `GitBranch` | Pipeline configurations |
| `'tools'` | Tools | `Wrench` | MCP tool configurations |
| `'chores'` | Chores | `ListChecks` | Chore definitions |
| `'apps'` | Apps | `Boxes` | Application definitions |
| `'actions'` | Actions | `Zap` | Quick actions (Toggle Theme, Focus Chat, etc.) |

**Display Order**: Categories are displayed in the order listed above. Within each category,
items are sorted alphabetically by `label`.

---

### 3. SearchSource

A conceptual entity representing a data provider for the command palette. Each source
produces `CommandPaletteItem[]` from its underlying data.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `category` | `CommandCategory` | Which category this source produces | Exactly one category |
| `dataHook` | `string` | The TanStack Query hook used to fetch data | Must be an existing hook |
| `isLoading` | `boolean` | Whether the underlying data is still loading | From TanStack Query state |
| `transform` | `(data) => CommandPaletteItem[]` | Maps raw entity data to palette items | Pure function |

**Concrete Sources**:

| Source | Hook | Data Shape | Transform |
|--------|------|-----------|-----------|
| Pages | Static (`NAV_ROUTES`) | `NavRoute[]` | `{ id: page-{path}, label: route.label, icon: route.icon, action: navigate(path) }` |
| Agents | `useAgentsList(projectId)` | `AgentConfig[]` | `{ id: agent-{name}, label: agent.name, icon: Bot, action: navigate('/agents') }` |
| Pipelines | `usePipelineConfig()` | Pipeline config | `{ id: pipeline-{name}, label: pipeline.name, icon: GitBranch, action: navigate('/pipeline') }` |
| Tools | `useToolsList(projectId)` | `McpToolConfig[]` | `{ id: tool-{name}, label: tool.name, icon: Wrench, action: navigate('/tools') }` |
| Chores | `useChoresList(projectId)` | `Chore[]` | `{ id: chore-{name}, label: chore.name, icon: ListChecks, action: navigate('/chores') }` |
| Apps | `useApps()` | `App[]` | `{ id: app-{name}, label: app.name, icon: Boxes, action: navigate('/apps/{name}') }` |
| Actions | Static definitions | Hardcoded | `{ id: action-{name}, label: action.label, icon: Zap, action: callback }` |

---

### 4. CommandPaletteState

The internal state managed by the `useCommandPalette` hook.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `isOpen` | `boolean` | Whether the palette overlay is visible | Default: `false` |
| `query` | `string` | Current search input value | Default: `''` |
| `selectedIndex` | `number` | Index of the currently highlighted result | 0 ≤ index < filteredResults.length; wraps or clamps |
| `filteredResults` | `CommandPaletteItem[]` | Results after applying search filter | Subset of all items |
| `isLoading` | `boolean` | Whether any data source is still loading | OR of all source loading states |

**State Transitions**:
- `open()` → Sets `isOpen = true`, resets `query = ''`, resets `selectedIndex = 0`
- `close()` → Sets `isOpen = false`, restores focus to previously focused element
- `setQuery(q)` → Updates `query`, recomputes `filteredResults`, resets `selectedIndex = 0`
- `moveUp()` → Decrements `selectedIndex` (wraps to last item if at 0)
- `moveDown()` → Increments `selectedIndex` (wraps to 0 if at last item)
- `select()` → Executes `filteredResults[selectedIndex].action`, then calls `close()`

---

### 5. Quick Action

A predefined action that executes a callback rather than navigating to a page.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `id` | `string` | Unique action identifier | Format: `action-{name}` |
| `label` | `string` | Display name | Non-empty |
| `description` | `string` | Brief explanation of what the action does | Non-empty |
| `icon` | `LucideIcon` | Visual identifier | Valid Lucide icon |
| `callback` | `() => void` | The function to execute | Must be idempotent or clearly side-effecting |

**Predefined Quick Actions**:

| Action | Label | Icon | Callback |
|--------|-------|------|----------|
| Toggle Theme | "Toggle Theme" | `SunMoon` | `toggleTheme()` from `useAppTheme` |
| Focus Chat | "Focus Chat" | `MessageSquare` | Dispatch `solune:focus-chat` custom event |
| Open Help | "Help" | `HelpCircle` | `navigate('/help')` |

## State Transitions

### Command Palette Lifecycle

```text
[Closed] → Ctrl+K / Click Trigger → [Open: Empty]
                                         ↓
                                    User types query
                                         ↓
                                    [Open: Filtering]
                                         ↓
                              Results computed (<200ms)
                                         ↓
                                    [Open: Results Shown]
                                         ↓
                        ┌────────────────┼────────────────┐
                   Arrow keys        Enter/Click        Escape/Backdrop
                        ↓                ↓                    ↓
               [Highlight Moves]   [Action Executed]      [Closed]
                                         ↓
                                      [Closed]
```

- **Closed → Open**: Triggered by Ctrl+K, Cmd+K, or clicking the search trigger. Blocked if
  another modal is active (`isModalOpen()` returns true).
- **Open → Filtering**: User types in the search input. Results update in real-time.
- **Open → Closed**: Escape key, backdrop click, or result selection.
- **Action Executed → Closed**: Palette always closes after executing an action.
