# Quickstart: Global Search / Command Palette

**Feature Branch**: `053-global-command-palette`
**Date**: 2026-03-20
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

## Prerequisites

- Node.js 18+ with dependencies installed in `solune/frontend/`
- Frontend dev dependencies: `cd solune/frontend && npm install`
- Understanding of existing hooks: `useGlobalShortcuts`, `useAppTheme`, `useAgentsList`, `useApps`, `useChoresList`, `useToolsList`, `usePipelineConfig`
- Understanding of existing constants: `NAV_ROUTES` in `src/constants.ts`

## Quick Verification

Run these commands to verify the current baseline state:

```bash
# 1. Frontend type-check (expect clean)
cd solune/frontend
npx tsc --noEmit

# 2. Frontend lint
cd solune/frontend
npx eslint src/hooks/useGlobalShortcuts.ts src/layout/AppLayout.tsx src/layout/TopBar.tsx

# 3. Frontend tests (expect passing)
cd solune/frontend
npx vitest run
```

## Implementation Order

### Phase A: Foundation — Command Palette Hook and Component (User Stories 1 & 4)
*(Core palette overlay with keyboard navigation)*

1. Create `useCommandPalette` hook:
   - State: `query`, `selectedIndex`, `filteredResults`, `isLoading`
   - Search: case-insensitive substring match against `label` and `keywords`
   - Keyboard: `moveUp()`, `moveDown()`, `selectCurrent()` functions
   - Data sources: `NAV_ROUTES` for pages (static), entity hooks for dynamic data
   - Focus management: `useRef` to save/restore `document.activeElement`

2. Create `CommandPalette` component:
   - Overlay: `fixed inset-0 z-50` backdrop with centered dialog panel
   - Input: auto-focused search input with `placeholder="Type to search..."`
   - Results: scrollable list grouped by category with icons and labels
   - Keyboard handlers: ArrowUp, ArrowDown, Enter, Escape
   - ARIA: `role="dialog"`, `aria-modal="true"`, `role="listbox"`, `role="option"`
   - Styling: celestial theme (dark glass effect, glow, consistent with existing modals)

3. Modify `useGlobalShortcuts`:
   - Change Ctrl+K handler: dispatch `solune:open-command-palette` instead of `solune:focus-chat`
   - Add modal conflict check: skip if `isModalOpen()` returns true

4. Integrate in `AppLayout`:
   - Add `isCommandPaletteOpen` state
   - Listen for `solune:open-command-palette` event
   - Render `<CommandPalette>` with open/close props
   - Pass `selectedProjectId` for entity data fetching

**⚠️ GATE**: Palette opens/closes, search filters pages, keyboard navigation works.

### Phase B: Entity Search (User Story 2)
*(Cross-entity result aggregation)*

5. Wire entity hooks into `useCommandPalette`:
   - `useAgentsList(projectId)` → Agents category
   - `usePipelineConfig()` → Pipelines category (extract pipeline list)
   - `useToolsList(projectId)` → Tools category
   - `useChoresList(projectId)` → Chores category
   - `useApps()` → Apps category

6. Update `CommandPalette` component:
   - Add category headers with icons for each entity type
   - Add entity-type icons per result item
   - Add "No results found" message
   - Add loading spinner/skeleton when data is loading

**⚠️ GATE**: Search returns categorized results from all entity types.

### Phase C: Quick Actions and UI Trigger (User Story 3 + FR-013)

7. Add quick actions to `useCommandPalette`:
   - "Toggle Theme" → calls `toggleTheme()` from `useAppTheme`
   - "Focus Chat" → dispatches `solune:focus-chat` event
   - "Help" → navigates to `/help`

8. Add search trigger to `TopBar`:
   - `Search` icon button with tooltip showing keyboard shortcut
   - Dispatches `solune:open-command-palette` on click
   - `aria-label="Open command palette"`

9. Update keyboard shortcut modal:
   - Change Ctrl+K description from "Focus Chat" to "Command Palette"

### Phase D: Polish and Edge Cases

10. Edge case handling:
    - Prevent palette open when modal is active (FR-012)
    - Focus restore on close (FR-009)
    - Cap results at 15 visible with scrolling (performance)
    - Handle rapid typing smoothly (no jank)
    - Handle Ctrl+K when palette is already open (no-op or select all text)

## Key Files Reference

| Area | File | Purpose |
|------|------|---------|
| New hook | `solune/frontend/src/hooks/useCommandPalette.ts` | Search logic and state management |
| New component | `solune/frontend/src/components/command-palette/CommandPalette.tsx` | Palette UI overlay |
| Modified shortcut hook | `solune/frontend/src/hooks/useGlobalShortcuts.ts` | Ctrl+K → open palette |
| Modified layout | `solune/frontend/src/layout/AppLayout.tsx` | Render palette globally |
| Modified top bar | `solune/frontend/src/layout/TopBar.tsx` | Clickable search trigger |
| Modified shortcut modal | `solune/frontend/src/components/ui/keyboard-shortcut-modal.tsx` | Updated shortcut text |
| Navigation constants | `solune/frontend/src/constants.ts` | NAV_ROUTES used as page search source |
| Theme hook | `solune/frontend/src/hooks/useAppTheme.ts` | Used by Toggle Theme quick action |

## Verification Checklist

- [ ] Ctrl+K opens the command palette overlay
- [ ] Cmd+K opens the command palette on macOS
- [ ] Palette opens with search input auto-focused
- [ ] Typing filters results in real-time
- [ ] Results are grouped by category (Pages, Agents, Tools, etc.)
- [ ] Arrow keys navigate results with visible highlight
- [ ] Enter selects the highlighted result and closes the palette
- [ ] Clicking a result selects it and closes the palette
- [ ] Escape closes the palette
- [ ] Clicking outside the palette closes it
- [ ] Focus returns to previously focused element on close
- [ ] "No results found" shown for empty queries
- [ ] Loading indicator shown while entity data loads
- [ ] Palette does not open over existing modal dialogs
- [ ] Search trigger button in top bar opens the palette
- [ ] Quick actions (Toggle Theme, Focus Chat) work correctly
- [ ] Keyboard shortcut modal shows "Command Palette" for Ctrl+K
- [ ] TypeScript type-check passes: `npx tsc --noEmit`
- [ ] ESLint passes: `npx eslint . --max-warnings=0`
