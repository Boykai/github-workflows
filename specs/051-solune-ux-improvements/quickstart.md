# Quickstart: Solune UX Improvements

**Feature Branch**: `051-solune-ux-improvements`
**Date**: 2026-03-19
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

## Prerequisites

- Node.js 18+ with dependencies installed in `solune/frontend/`
- Frontend dev dependencies: `cd solune/frontend && npm install`
- Browser dev tools for responsive testing (Chrome recommended for device emulation)

## Quick Verification

Run these commands to verify the current state of the frontend:

```bash
# 1. Frontend type check
cd solune/frontend
npx tsc --noEmit

# 2. Frontend lint
cd solune/frontend
npx eslint .

# 3. Frontend unit tests
cd solune/frontend
npx vitest run

# 4. Frontend E2E tests (requires running dev server)
cd solune/frontend
npm run dev &
npx playwright test

# 5. Build verification
cd solune/frontend
npm run build
```

## Implementation Order

### Phase 2: Mobile Responsiveness (P1–P2)
*(Sequential — shared `useMediaQuery` hook must be created first)*

1. **Create `useMediaQuery` hook** (foundation for all responsive behaviors)
   - **File**: `solune/frontend/src/hooks/useMediaQuery.ts` (new)
   - **Pattern**: `matchMedia` wrapper with `change` event listener and SSR safety
   - **Verify**: `npx vitest run src/hooks/useMediaQuery.test.ts`

2. **Make ChatPopup responsive** (US-1)
   - **File**: `solune/frontend/src/components/chat/ChatPopup.tsx`
   - **Changes**: Import `useMediaQuery`, conditionally render full-screen layout when mobile
   - **Verify**: Open chat at 320px viewport → full-screen overlay, no horizontal scroll

3. **Auto-collapse sidebar on mobile** (US-2)
   - **Files**: `solune/frontend/src/layout/Sidebar.tsx`, `solune/frontend/src/layout/AppLayout.tsx` (or parent)
   - **Changes**: Use `useMediaQuery` in parent, force collapse on mobile, overlay when expanded
   - **Verify**: Load page at 375px → sidebar collapsed; tap toggle → overlay with backdrop

4. **Make IssueDetailModal responsive** (US-3)
   - **File**: `solune/frontend/src/components/board/IssueDetailModal.tsx`
   - **Changes**: Import `useMediaQuery`, apply `fixed inset-0` on mobile, fixed header + scrollable body
   - **Verify**: Open issue modal at 375px → full-screen with sticky header

5. **Make BoardToolbar mobile-friendly** (US-4)
   - **File**: `solune/frontend/src/components/board/BoardToolbar.tsx`
   - **Changes**: Import `useMediaQuery`, switch to icon-only buttons or collapsible menu on mobile
   - **Verify**: View toolbar at 375px → compact layout, no horizontal overflow

### Phase 3: Perceived Performance (P2–P3)
*(Steps 6–9 can be parallelized across developers)*

6. **Add skeleton loaders to AgentsPage**
   - **File**: `solune/frontend/src/pages/AgentsPage.tsx`
   - **Changes**: Replace `CelestialLoader` with `Skeleton` grid matching agent list layout
   - **Verify**: Throttle network → skeleton rows visible during load, smooth transition to content

7. **Add skeleton loaders to ToolsPage, ChoresPage, AppsPage**
   - **Files**: `solune/frontend/src/pages/ToolsPage.tsx`, `ChoresPage.tsx`, `AppsPage.tsx`
   - **Changes**: Same pattern as step 6, adapted to each page's layout
   - **Verify**: Throttle network → skeletons visible on each page

8. **Implement optimistic updates for drag-drop**
   - **File**: `solune/frontend/src/hooks/useBoardDragDrop.ts`
   - **Changes**: Add `onMutate` (snapshot + cache update), `onError` (rollback + error toast), `onSettled` (invalidate)
   - **Verify**: Drag card with 2s network delay → card moves instantly; fail server → card snaps back

9. **Implement optimistic updates for app start/stop**
   - **File**: `solune/frontend/src/hooks/useApps.ts`
   - **Changes**: Add `onMutate`/`onError`/`onSettled` to start/stop mutations
   - **Verify**: Click "Start" with network delay → instant "Starting" state; fail → reverts

### Phase 4: Interaction Consistency (P3)
*(Steps 10–11 can be parallelized)*

10. **Standardize toast notifications**
    - **Files**: `solune/frontend/src/pages/AppsPage.tsx`, `solune/frontend/src/hooks/useApps.ts`, and any hooks using manual state for feedback
    - **Changes**: Remove `successMessage`/`actionError` state from AppsPage; ensure all mutation hooks use `toast.success()`/`toast.error()` from Sonner
    - **Verify**: Perform CRUD on agents, tools, chores, apps → consistent toast notifications

11. **Add empty states for catalog pages**
    - **Files**: `solune/frontend/src/components/common/EmptyState.tsx` (new), `AgentsPage.tsx`, `ToolsPage.tsx`, `ChoresPage.tsx`
    - **Changes**: Create EmptyState component; render when project selected + list empty
    - **Verify**: Select project with no agents → empty state with "Create your first agent" CTA

### Phase 5: Discoverability & Power Users (P4)
*(Steps 12–14 can be parallelized)*

12. **Add text search to board and catalog pages**
    - **Files**: `solune/frontend/src/components/board/BoardToolbar.tsx`, `AgentsPage.tsx`, `ToolsPage.tsx`, `ChoresPage.tsx`
    - **Changes**: Add search input, client-side filtering with 150ms debounce
    - **Verify**: Type search term → matching items shown; clear → all items restored

13. **Extend onboarding tour**
    - **Files**: `solune/frontend/src/components/onboarding/SpotlightTour.tsx`, `solune/frontend/src/hooks/useOnboarding.tsx`
    - **Changes**: Add 4 steps (Tools, Chores, Settings, Apps); update TOTAL_STEPS to 13
    - **Verify**: Trigger tour → walks through all 13 steps including new pages

14. **Add undo/redo to pipeline builder**
    - **File**: `solune/frontend/src/hooks/usePipelineConfig.ts`
    - **Changes**: Wrap `useReducer` with undo/redo stack; register Ctrl+Z/Ctrl+Shift+Z listeners
    - **Verify**: Make changes → Ctrl+Z undoes → Ctrl+Shift+Z redoes; load pipeline → stacks cleared

## Verification Checklist

After all phases complete:

```bash
# 1. Full unit test suite
cd solune/frontend && npx vitest run

# 2. Type check
cd solune/frontend && npx tsc --noEmit

# 3. Lint
cd solune/frontend && npx eslint .

# 4. Build
cd solune/frontend && npm run build

# 5. E2E tests
cd solune/frontend && npx playwright test

# 6. Manual responsive testing
# Open browser dev tools → Device Toolbar
# Test at: 320px, 375px, 768px, 1024px viewports
# Verify: chat, sidebar, modals, toolbar all work correctly

# 7. Keyboard accessibility
# Tab through board → Space to pick up card → Arrow keys → Space to drop
# Verify: drag-drop works with keyboard only

# 8. Perceived performance
# Chrome DevTools → Network → Slow 3G
# Navigate to each catalog page → verify skeleton loaders appear
# Drag a card → verify instant visual feedback
```

## Key Files Changed Summary

| Phase | File | Change Type | User Story |
|-------|------|-------------|------------|
| 2 | `hooks/useMediaQuery.ts` | New | Foundation for US-1,2,3,4 |
| 2 | `components/chat/ChatPopup.tsx` | Modified | US-1 |
| 2 | `layout/Sidebar.tsx` | Modified | US-2 |
| 2 | `layout/AppLayout.tsx` | Modified | US-2 |
| 2 | `components/board/IssueDetailModal.tsx` | Modified | US-3 |
| 2 | `components/board/BoardToolbar.tsx` | Modified | US-4, US-9 |
| 3 | `pages/AgentsPage.tsx` | Modified | US-5, US-8, US-9 |
| 3 | `pages/ToolsPage.tsx` | Modified | US-5, US-8, US-9 |
| 3 | `pages/ChoresPage.tsx` | Modified | US-5, US-8, US-9 |
| 3 | `pages/AppsPage.tsx` | Modified | US-5, US-7 |
| 3 | `hooks/useBoardDragDrop.ts` | Modified | US-6 |
| 3 | `hooks/useApps.ts` | Modified | US-6, US-7 |
| 3 | `hooks/usePipelineBoardMutations.ts` | Modified | US-6 |
| 4 | `components/common/EmptyState.tsx` | New | US-8 |
| 5 | `components/onboarding/SpotlightTour.tsx` | Modified | US-10 |
| 5 | `hooks/useOnboarding.tsx` | Modified | US-10 |
| 5 | `hooks/usePipelineConfig.ts` | Modified | US-11 |
