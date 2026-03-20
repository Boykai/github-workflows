# Component Interface Contracts: Global Search / Command Palette

**Feature Branch**: `053-global-command-palette`
**Date**: 2026-03-20
**Spec**: [spec.md](../spec.md) | **Plan**: [plan.md](../plan.md)

## 1. CommandPalette Component Props

```typescript
interface CommandPaletteProps {
  /** Whether the palette overlay is visible. */
  isOpen: boolean;

  /** Callback to close the palette. */
  onClose: () => void;

  /** Current project ID for entity data fetching. May be null if no project is selected. */
  projectId: string | null;
}
```

**Usage in AppLayout**:
```tsx
<CommandPalette
  isOpen={isCommandPaletteOpen}
  onClose={() => setIsCommandPaletteOpen(false)}
  projectId={selectedProjectId}
/>
```

**Rendering Contract**:
- When `isOpen` is `false`, the component renders nothing (returns `null`).
- When `isOpen` is `true`, the component renders:
  - A backdrop overlay covering the full viewport (`fixed inset-0 z-50`)
  - A centered dialog panel with `role="dialog"` and `aria-modal="true"`
  - An auto-focused search input with `aria-label="Search commands"`
  - A scrollable results list with `role="listbox"`
  - Each result item with `role="option"` and `aria-selected` for the highlighted item

---

## 2. useCommandPalette Hook API

```typescript
interface UseCommandPaletteOptions {
  /** Current project ID for entity data fetching. */
  projectId: string | null;

  /** Whether the palette is currently open (controls data fetching). */
  isOpen: boolean;
}

interface UseCommandPaletteReturn {
  /** Current search query string. */
  query: string;

  /** Update the search query. Resets selectedIndex to 0. */
  setQuery: (query: string) => void;

  /** Filtered and categorized results based on the current query. */
  results: CommandPaletteItem[];

  /** Index of the currently highlighted result. */
  selectedIndex: number;

  /** Move highlight to the previous result (wraps around). */
  moveUp: () => void;

  /** Move highlight to the next result (wraps around). */
  moveDown: () => void;

  /** Execute the currently highlighted result's action. */
  selectCurrent: () => void;

  /** Whether any entity data source is still loading. */
  isLoading: boolean;
}
```

**Behavioral Contract**:
- `results` is empty when `query` is empty (palette shows no results until user types).
- `results` is grouped by category in display order: Pages, Agents, Pipelines, Tools, Chores, Apps, Actions.
- `results` is capped at 50 total items (excess items are truncated per category).
- `selectedIndex` is always valid: `0 ≤ selectedIndex < results.length` (or 0 if empty).
- `moveUp` on index 0 wraps to `results.length - 1`.
- `moveDown` on last index wraps to 0.
- `selectCurrent` executes the action and is expected to be followed by closing the palette.

---

## 3. useGlobalShortcuts Modification

**Current Contract**:
```typescript
// Ctrl+K → dispatches 'solune:focus-chat' custom event
```

**New Contract**:
```typescript
// Ctrl+K → dispatches 'solune:open-command-palette' custom event
// (only when no modal dialog is already active)
```

**Custom Event**:
```typescript
// Event name: 'solune:open-command-palette'
// Payload: none (CustomEvent with no detail)
// Listener: AppLayout component
```

**Backward Compatibility**:
- The `solune:focus-chat` event is no longer dispatched by Ctrl+K.
- "Focus Chat" is available as a quick action within the command palette.
- Any component listening for `solune:focus-chat` continues to work when the event is dispatched
  from the palette's quick action.

---

## 4. TopBar Search Trigger

**New Element**:
```typescript
// Button element in TopBar
// - Icon: Search (from lucide-react)
// - Tooltip: "Search (Ctrl+K)" or "Search (⌘K)" on macOS
// - onClick: dispatches 'solune:open-command-palette' custom event
// - aria-label: "Open command palette"
// - className: matches existing TopBar button styling
```

**Placement**: After the theme toggle button, before the user profile area.

---

## 5. Keyboard Shortcut Modal Update

**Current Entry**:
```text
Ctrl+K / Cmd+K → Focus Chat
```

**Updated Entry**:
```text
Ctrl+K / Cmd+K → Command Palette
```

---

## 6. ARIA and Accessibility Contract

The command palette implements the WAI-ARIA Combobox pattern:

| Element | Role | ARIA Attributes |
|---------|------|-----------------|
| Dialog container | `dialog` | `aria-modal="true"`, `aria-label="Command palette"` |
| Search input | `combobox` | `aria-expanded="true"`, `aria-controls="palette-results"`, `aria-activedescendant="{selected-id}"` |
| Results list | `listbox` | `id="palette-results"` |
| Result item | `option` | `id="palette-item-{index}"`, `aria-selected="{isHighlighted}"` |
| Category header | — | `role="presentation"` (decorative grouping label) |

**Focus Contract**:
- On open: focus moves to the search input.
- On close: focus returns to the element that was focused before the palette opened.
- Tab key: does not leave the dialog (focus is trapped within the palette).
- Arrow keys: move the highlight within the results list (do not move DOM focus).
