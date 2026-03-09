# Quickstart: Full Frontend Responsiveness & Mobile-Friendly Audit

**Feature**: 031-frontend-responsive-audit | **Date**: 2026-03-09

## Prerequisites

- Node.js 20+ and npm
- The repository cloned and on the feature branch

```bash
git checkout 031-frontend-responsive-audit
```

## Setup

### Frontend

```bash
cd frontend
npm install
npm run dev
# App available at http://localhost:5173
```

No backend changes are needed for this feature. If you need the full app experience (data in the UI), also start the backend:

```bash
cd backend
pip install -e ".[dev]"
uvicorn src.main:app --reload --port 8000
```

## New Files to Create

### New Frontend Files

| File | Purpose |
|------|---------|
| `frontend/src/hooks/useMediaQuery.ts` | NEW: Programmatic media query hook for viewport detection |

## Files to Modify

### Core Infrastructure

| File | Changes |
|------|---------|
| `frontend/src/index.css` | Add responsive breakpoint CSS custom properties (`--bp-*`), `.touch-target` utility |
| `frontend/src/constants.ts` | Add `BREAKPOINTS` constant object |
| `frontend/src/hooks/useSidebarState.ts` | Add `isMobileOpen`, `openMobile`, `closeMobile` state for mobile drawer |

### Layout Components

| File | Changes |
|------|---------|
| `frontend/src/layout/AppLayout.tsx` | Mobile drawer overlay, backdrop, conditional sidebar rendering |
| `frontend/src/layout/Sidebar.tsx` | Mobile drawer mode (`hidden md:flex`, fixed overlay when mobile open) |
| `frontend/src/layout/TopBar.tsx` | Hamburger menu button (`md:hidden`), responsive padding |

### UI Primitives

| File | Changes |
|------|---------|
| `frontend/src/components/ui/Button.tsx` | Add `touch` size variant (min 44×44px) |
| `frontend/src/components/ui/Input.tsx` | Add `max-sm:min-h-[44px]` for mobile touch friendliness |

### Page Components

| File | Changes |
|------|---------|
| `frontend/src/pages/AppPage.tsx` | Responsive padding, typography scaling |
| `frontend/src/pages/ProjectsPage.tsx` | Board horizontal scroll on mobile |
| `frontend/src/pages/AgentsPipelinePage.tsx` | Pipeline horizontal scroll, responsive stage cards |
| `frontend/src/pages/AgentsPage.tsx` | Touch targets, responsive grid (already partial) |
| `frontend/src/pages/ToolsPage.tsx` | Touch targets, responsive grid |
| `frontend/src/pages/ChoresPage.tsx` | Touch targets, responsive grid |
| `frontend/src/pages/SettingsPage.tsx` | Responsive tab navigation, form layouts |
| `frontend/src/pages/LoginPage.tsx` | Centered mobile layout |

### Feature Components

| File | Changes |
|------|---------|
| `frontend/src/components/agents/AgentsPanel.tsx` | Responsive grid, mobile search, touch targets |
| `frontend/src/components/agents/AgentCard.tsx` | Touch-friendly action buttons |
| `frontend/src/components/agents/AddAgentModal.tsx` | Full-screen on mobile |
| `frontend/src/components/board/ProjectBoard.tsx` | Horizontal scroll container on mobile |
| `frontend/src/components/board/BoardColumn.tsx` | Responsive column width |
| `frontend/src/components/board/IssueCard.tsx` | Touch targets, responsive content |
| `frontend/src/components/board/IssueDetailModal.tsx` | Full-screen on mobile |
| `frontend/src/components/chat/ChatInterface.tsx` | Touch-friendly controls |
| `frontend/src/components/chat/MentionInput.tsx` | Touch-friendly input |
| `frontend/src/components/chores/AddChoreModal.tsx` | Full-screen on mobile |
| `frontend/src/components/chores/ChoreScheduleConfig.tsx` | Responsive form |
| `frontend/src/components/pipeline/PipelineBoard.tsx` | Horizontal scroll on mobile |
| `frontend/src/components/pipeline/StageCard.tsx` | Responsive card content |
| `frontend/src/components/pipeline/PipelineFlowGraph.tsx` | Horizontal scroll |
| `frontend/src/components/tools/ToolSelectorModal.tsx` | Full-screen on mobile |
| `frontend/src/components/settings/*.tsx` | Responsive form layouts |

### E2E Tests

| File | Changes |
|------|---------|
| `frontend/e2e/viewports.ts` | Add mobileSmall (320), mobileLarge (390), desktopLarge (1440) |
| `frontend/e2e/responsive-home.spec.ts` | Extend with new viewport breakpoints |
| `frontend/e2e/responsive-board.spec.ts` | Extend with new viewport breakpoints |
| `frontend/e2e/responsive-settings.spec.ts` | Extend with new viewport breakpoints |

## Implementation Order

### Phase 1: Infrastructure — Breakpoint Tokens + useMediaQuery + Touch Utility (FR-009, FR-002)

1. **index.css** — Add responsive breakpoint CSS custom properties to `@theme` block:

   ```css
   @theme {
     --bp-xs: 320px;
     --bp-sm: 640px;
     --bp-md: 768px;
     --bp-lg: 1024px;
     --bp-xl: 1280px;
     --bp-2xl: 1440px;
   }
   ```

   Add `.touch-target` utility class:

   ```css
   .touch-target {
     min-height: 44px;
     min-width: 44px;
   }
   ```

2. **constants.ts** — Add `BREAKPOINTS` constant:

   ```typescript
   export const BREAKPOINTS = {
     xs: 320, sm: 640, md: 768, lg: 1024, xl: 1280, '2xl': 1440,
   } as const;
   ```

3. **useMediaQuery.ts** (new) — `frontend/src/hooks/useMediaQuery.ts`:

   ```typescript
   import { useState, useEffect } from 'react';
   import { BREAKPOINTS } from '@/constants';

   export function useMediaQuery(query: string): boolean {
     const [matches, setMatches] = useState(() => {
       if (typeof window === 'undefined') return false;
       return window.matchMedia(query).matches;
     });

     useEffect(() => {
       const mql = window.matchMedia(query);
       const handler = (e: MediaQueryListEvent) => setMatches(e.matches);
       mql.addEventListener('change', handler);
       setMatches(mql.matches);
       return () => mql.removeEventListener('change', handler);
     }, [query]);

     return matches;
   }

   export function useIsMobile(): boolean {
     return useMediaQuery(`(max-width: ${BREAKPOINTS.md - 1}px)`);
   }
   ```

4. **Button.tsx** — Add `touch` size variant to CVA variants
5. **Input.tsx** — Add `max-sm:min-h-[44px]` to base classes

**Verify**: `npm run type-check` passes. `npm run build` succeeds. No visual changes yet.

### Phase 2: Mobile Navigation — Sidebar Drawer + Hamburger (FR-003)

1. **useSidebarState.ts** — Extend with mobile drawer state:
   - Add `isMobileOpen: boolean` state
   - Add `openMobile()` and `closeMobile()` methods
   - Add `useLocation` effect to auto-close on route change

2. **TopBar.tsx** — Add hamburger menu button:
   - `<button className="md:hidden touch-target" onClick={onMenuToggle}>`
   - Icon: `Menu` from lucide-react (☰)
   - Responsive padding: `px-3 md:px-6`

3. **Sidebar.tsx** — Dual rendering mode:
   - Desktop: `hidden md:flex` (existing inline sidebar)
   - Mobile: `fixed inset-y-0 left-0 z-40 w-72` when `isMobileOpen`
   - Backdrop: `fixed inset-0 z-30 bg-black/50` when open
   - Slide animation: `transition-transform duration-300`

4. **AppLayout.tsx** — Wire mobile state:
   - Pass `useIsMobile()` and drawer state to Sidebar/TopBar
   - Add backdrop overlay when drawer is open

**Verify**: Open app at 375px viewport. Sidebar is hidden. Hamburger visible in TopBar. Tap hamburger → drawer slides in from left. Tap backdrop → drawer closes. Navigate to a page → drawer closes automatically. At 768px+, sidebar appears inline (existing behavior).

### Phase 3: Modal Full-Screen Mobile (FR-008)

1. Apply `max-sm:` full-screen overrides to all 16 modal components:
   - `max-sm:max-w-none max-sm:h-full max-sm:rounded-none max-sm:m-0`
   - Scrollable content area
   - Touch-friendly close button (44×44px)

2. Priority order: IssueDetailModal, AddAgentModal, ToolSelectorModal (most content-heavy), then remaining modals

**Verify**: Open any modal at 375px → fills viewport. Content scrolls. Close button is tap-friendly. No horizontal scrollbar.

### Phase 4: Board + Pipeline Horizontal Scroll (FR-005)

1. **ProjectBoard.tsx** — Horizontal scroll container:
   - `overflow-x-auto snap-x snap-mandatory md:overflow-visible`
   - Column width: `w-[85vw] shrink-0 snap-center md:w-auto`

2. **PipelineBoard.tsx** — Horizontal scroll for stages:
   - `overflow-x-auto md:overflow-visible`
   - Stage cards: min-width for scrollable row

3. **PipelineFlowGraph.tsx** — Horizontal scroll container:
   - `overflow-x-auto touch-action-pan-x`

**Verify**: At 375px, board columns swipe horizontally with snap. Pipeline stages scroll horizontally. No vertical collapse of columns.

### Phase 5: Touch Targets + Typography Audit (FR-002, FR-010)

1. **All interactive elements**: Audit icon buttons across components. Ensure padding creates 44×44px hit area:
   - Icon buttons: add `p-2.5` (10px padding + 24px icon = 44px)
   - Menu items: add `min-h-[44px]`
   - Links: ensure sufficient tap area

2. **Typography scaling**: Audit headings and body text on mobile:
   - Headings: ensure responsive modifiers (e.g., `text-xl md:text-2xl lg:text-3xl`)
   - Body text: minimum 16px on mobile (`text-base`)
   - Reduce padding: `px-2 md:px-4 lg:px-6`

**Verify**: At 375px, every button/link/menu item has at least 44×44px tap area. All text is readable without zooming.

### Phase 6: Remaining Pages + Components (FR-001, FR-004, FR-006)

1. **SettingsPage**: Responsive tab navigation (horizontal scroll on mobile)
2. **LoginPage**: Centered mobile layout (likely minimal changes)
3. **Forms**: Responsive form layouts (stack on mobile, side-by-side on desktop)
4. **Fixed/Sticky elements**: Verify headers/footers don't obscure content
5. **Chat components**: Verify MentionInput, ChatToolbar touch targets

**Verify**: Every page at every breakpoint (320, 375, 390, 768, 1024, 1280, 1440) has no horizontal scrollbar, readable text, and functional touch targets.

### Phase 7: E2E Test Extension (Optional)

1. **viewports.ts** — Add new viewport definitions:
   - `mobileSmall: { width: 320, height: 568 }`
   - `mobileLarge: { width: 390, height: 844 }`
   - `desktopLarge: { width: 1440, height: 900 }`

2. Extend existing responsive tests to cover new breakpoints

**Verify**: `npx playwright test e2e/responsive-*.spec.ts` — all pass.

## Key Patterns to Follow

### Mobile Drawer (Navigation)

```tsx
// Sidebar.tsx — mobile drawer mode
{isMobile && (
  <>
    {/* Backdrop */}
    {isMobileOpen && (
      <div
        className="fixed inset-0 z-30 bg-black/50 transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />
    )}
    {/* Drawer */}
    <nav
      className={cn(
        'fixed inset-y-0 left-0 z-40 w-72 transform transition-transform duration-300',
        'celestial-panel border-r border-border/70 shadow-lg',
        isMobileOpen ? 'translate-x-0' : '-translate-x-full',
      )}
      role="navigation"
      aria-label="Main navigation"
    >
      {/* Same sidebar content */}
    </nav>
  </>
)}
```

### Modal Full-Screen Mobile

```tsx
// Any modal container
<div className={cn(
  'w-full max-w-lg rounded-lg p-6', // Desktop
  'max-sm:max-w-none max-sm:h-full max-sm:rounded-none max-sm:p-4', // Mobile
)}>
  <button className="absolute top-3 right-3 touch-target">
    <X className="h-5 w-5" />
  </button>
  <div className="overflow-y-auto max-h-[80vh] max-sm:max-h-[calc(100vh-4rem)]">
    {children}
  </div>
</div>
```

### Touch Target (Interactive Elements)

```tsx
// Icon button with touch target
<button className="p-2.5 touch-target rounded-md hover:bg-accent/10">
  <Trash2 className="h-5 w-5" />
</button>

// Or using Button touch variant
<Button size="touch" variant="ghost" onClick={handleDelete}>
  <Trash2 className="h-5 w-5" />
</Button>
```

### Horizontal Scroll Board

```tsx
// Board with horizontal scroll on mobile
<div className="flex gap-4 overflow-x-auto snap-x snap-mandatory md:flex-wrap md:overflow-visible pb-4">
  {columns.map(col => (
    <div key={col.id} className="w-[85vw] shrink-0 snap-center md:w-auto md:shrink md:snap-align-none">
      <Column data={col} />
    </div>
  ))}
</div>
```

### Responsive Grid (Cards)

```tsx
// Card grid with responsive columns
<div className="grid gap-3 md:gap-4 grid-cols-1 md:grid-cols-2 xl:grid-cols-3">
  {items.map(item => <Card key={item.id} />)}
</div>
```

## Verification

After implementation, verify at each breakpoint (320, 375, 390, 768, 1024, 1280, 1440):

1. **No horizontal scrollbar**: `document.documentElement.scrollWidth <= window.innerWidth` on every page
2. **Navigation**: At <768px, hamburger visible → drawer opens → nav items accessible → drawer closes on navigate
3. **Navigation**: At ≥768px, sidebar visible inline, collapse toggle works
4. **Touch targets**: Every button, link, icon at <768px has ≥44×44px hit area
5. **Modals**: Every modal at <640px fills viewport, content scrolls, close button tappable
6. **Boards**: Kanban columns swipe horizontally at <768px with snap behavior
7. **Pipeline**: Stages scroll horizontally at <768px
8. **Chat**: ChatPopup full-width on mobile (already implemented — verify)
9. **Forms**: All inputs are touch-friendly (≥44px height), dropdowns open correctly
10. **Typography**: All text readable without zooming (minimum 16px body text)
11. **Orientation**: Rotate device — layout re-adapts without glitches
12. **Sticky elements**: Headers/toolbars don't obscure content at any viewport
13. **Dark mode**: All responsive changes work in both light and dark themes
14. **Existing tests**: `npm run test` — all existing tests pass
15. **TypeScript**: `npm run type-check` — no type errors
16. **Build**: `npm run build` — successful
