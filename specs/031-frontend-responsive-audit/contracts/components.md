# Component Contracts: Full Frontend Responsiveness & Mobile-Friendly Audit

**Feature**: 031-frontend-responsive-audit | **Date**: 2026-03-09

## New Components

### useMediaQuery Hook

**Location**: `frontend/src/hooks/useMediaQuery.ts`
**Purpose**: Provides programmatic viewport detection using native `window.matchMedia`. Returns a boolean indicating whether the viewport matches the given media query. Used primarily to conditionally render the mobile sidebar drawer vs. desktop sidebar.

```typescript
/**
 * @param query - CSS media query string (e.g., '(max-width: 767px)')
 * @returns boolean - true if the viewport matches the query
 */
function useMediaQuery(query: string): boolean;

/**
 * Convenience hook: returns true when viewport width < 768px (md breakpoint).
 * Uses the `md` value from the BREAKPOINTS constant in constants.ts.
 */
function useIsMobile(): boolean;
```

**Behavior**:

- Subscribes to `window.matchMedia(query).addEventListener('change', ...)` on mount
- Returns initial match state synchronously (no flash of wrong content)
- Cleans up listener on unmount
- SSR-safe: returns `false` when `window` is undefined
- Uses the `md` value (768) from the `BREAKPOINTS` constant for the mobile threshold

**Usage**:

```tsx
import { useIsMobile } from '@/hooks/useMediaQuery';

function AppLayout() {
  const isMobile = useIsMobile();
  return (
    <div className="flex h-screen">
      {!isMobile && <Sidebar />}
      {isMobile && isMobileOpen && <MobileDrawer />}
    </div>
  );
}
```

---

## Modified Components

### AppLayout.tsx

**Location**: `frontend/src/layout/AppLayout.tsx`
**Purpose**: Master authenticated layout — modified to support mobile drawer overlay and responsive main content padding.

**Changes**:

1. Import `useIsMobile` from `@/hooks/useMediaQuery`
2. Import `isMobileOpen`, `openMobile`, `closeMobile` from extended `useSidebarState`
3. Conditionally render Sidebar:
   - Desktop (≥768px): Render `<Sidebar>` inline (existing behavior)
   - Mobile (<768px): Render Sidebar as overlay drawer when `isMobileOpen` is true
4. Add backdrop overlay: `<div className="fixed inset-0 z-30 bg-black/50" onClick={closeMobile} />`
5. Adjust main content padding: `px-2 md:px-4` for more content space on mobile

**Desktop Layout** (≥768px, unchanged):
```text
┌──────────────────────────────────────────┐
│ Sidebar │  TopBar                        │
│ (w-60   │──────────────────────────────│
│  or     │                                │
│  w-16)  │  Main Content (Outlet)         │
│         │                                │
│         │                                │
│         │──────────────────────────────│
│         │  ChatPopup (floating)          │
└──────────────────────────────────────────┘
```

**Mobile Layout** (<768px):
```text
┌──────────────────────────────────────────┐
│ TopBar (with ☰ hamburger)                │
│──────────────────────────────────────────│
│                                          │
│  Main Content (Outlet, full width)       │
│                                          │
│──────────────────────────────────────────│
│  ChatPopup (full-width drawer)           │
└──────────────────────────────────────────┘

When ☰ tapped:
┌──────────────────────────────────────────┐
│ ┌─────────────┐ Backdrop (bg-black/50)   │
│ │  Sidebar    │                          │
│ │  Drawer     │                          │
│ │  (w-72)     │                          │
│ │             │                          │
│ │  Nav items  │                          │
│ │  Project    │                          │
│ │  Recent     │                          │
│ └─────────────┘                          │
└──────────────────────────────────────────┘
```

---

### Sidebar.tsx

**Location**: `frontend/src/layout/Sidebar.tsx`
**Purpose**: Left navigation panel — modified to support dual rendering modes (desktop inline + mobile drawer overlay).

**Changes**:

1. Accept new props: `isMobileOpen?: boolean`, `onCloseMobile?: () => void`
2. **Desktop mode** (≥768px): Current behavior — inline sidebar, collapsible
3. **Mobile mode** (<768px): Renders as fixed overlay drawer
   - `fixed inset-y-0 left-0 z-40 w-72` when open
   - Hidden entirely when closed (conditionally rendered)
   - `transition-transform duration-300` for slide animation
   - Auto-close on route change via `useLocation` effect

**Accessibility**:
- `role="navigation"` and `aria-label="Main navigation"` on nav container
- Hamburger trigger has `aria-expanded` and `aria-controls` attributes linking to the mobile drawer `id`

**Styling (Mobile Drawer)**:
```text
Position: fixed, inset-y-0, left-0
Width: w-72 (288px)
Z-index: z-40 (above content, below modals)
Background: celestial-panel (existing theme)
Border: border-r border-border/70 (existing)
Shadow: shadow-lg (for overlay depth)
Transform: -translate-x-full (closed) → translate-x-0 (open)
Transition: 300ms ease
```

---

### TopBar.tsx

**Location**: `frontend/src/layout/TopBar.tsx`
**Purpose**: Header bar — modified to include hamburger menu toggle for mobile viewports.

**Changes**:

1. Accept new prop: `onMenuToggle: () => void` (triggers mobile drawer open)
2. Add hamburger button: `<button className="md:hidden touch-target" onClick={onMenuToggle}><Menu /></button>`
3. Hamburger button positioned at the left of TopBar (before breadcrumb)
4. Responsive padding: `px-3 md:px-6` (reduced on mobile)
5. Breadcrumb: add `truncate` on mobile to prevent overflow

**Layout**:
```text
Mobile (<768px):
┌─────────────────────────────────────┐
│ ☰  Breadcrumb...   🔔  👤          │
└─────────────────────────────────────┘

Desktop (≥768px):
┌─────────────────────────────────────┐
│     Breadcrumb      Rate │ 🔔 user │
└─────────────────────────────────────┘
```

---

### Button.tsx (Size Variant Extension)

**Location**: `frontend/src/components/ui/button.tsx`
**Purpose**: Base button component — modified to add `touch` size variant for mobile-friendly touch targets.

**Changes**:

1. Add `touch` to the `size` CVA variants:

```typescript
const buttonVariants = cva('...', {
  variants: {
    size: {
      default: 'h-9 px-4 py-2',
      sm: 'h-8 rounded-md px-3 text-xs',
      lg: 'h-10 rounded-md px-8',
      icon: 'h-9 w-9',
      touch: 'min-h-[44px] min-w-[44px] px-4 py-2',  // NEW
    },
  },
});
```

**Behavior**: The `touch` size ensures the button meets the 44×44px minimum touch target. It does not override font size or other visual properties — only guarantees minimum dimensions.

---

### Input.tsx (Mobile-Friendly Sizing)

**Location**: `frontend/src/components/ui/input.tsx`
**Purpose**: Base input component — modified to ensure mobile-friendly input height.

**Changes**:

1. Add `min-h-[44px]` to the base input classes on mobile viewports:

```typescript
// Before
className={cn('h-9 ...', className)}

// After  
className={cn('h-9 max-sm:min-h-[44px] ...', className)}
```

**Rationale**: iOS Safari zooms into inputs smaller than 16px font / 44px height. Ensuring 44px minimum height prevents unwanted zoom and meets touch target requirements (FR-002, FR-007).

---

## Modified Page Components

### All Pages — Common Pattern

All 9 pages receive the following responsive adjustments:

1. **Padding**: `px-2 md:px-4 lg:px-6` — reduced padding on mobile to maximize content width
2. **Typography**: Heading sizes scale down on mobile (e.g., `text-2xl md:text-3xl lg:text-4xl`)
3. **Spacing**: Vertical gaps scale with viewport (e.g., `gap-3 md:gap-4 lg:gap-6`)

### AgentsPage / ToolsPage / ChoresPage — Grid Pattern

These pages share the responsive grid pattern:

```tsx
<div className="grid gap-4 grid-cols-1 md:grid-cols-2 xl:grid-cols-3">
  {items.map(item => <Card key={item.id} />)}
</div>
```

Already partially implemented — audit confirms `md:grid-cols-2 xl:grid-cols-3` exists. Remaining work: ensure cards don't have fixed widths, touch targets on card actions, and grid gaps are appropriate on mobile.

### ProjectsPage — Board Horizontal Scroll

```tsx
<div className="flex gap-4 overflow-x-auto snap-x snap-mandatory md:flex-wrap md:overflow-visible">
  {columns.map(col => (
    <div key={col.id} className="w-[85vw] shrink-0 snap-center md:w-auto md:shrink md:snap-align-none">
      <BoardColumn />
    </div>
  ))}
</div>
```

### AgentsPipelinePage — Pipeline Horizontal Scroll

```tsx
<div className="overflow-x-auto md:overflow-visible">
  <div className="flex gap-4 min-w-max md:min-w-0">
    {stages.map(stage => <StageCard key={stage.id} />)}
  </div>
</div>
```

### SettingsPage — Tab/Section Navigation

Settings panels use a tab-based layout that needs mobile adaptation:

```tsx
<div className="flex flex-col md:flex-row gap-4">
  {/* Mobile: tabs as horizontal scrollable pills */}
  <nav className="flex overflow-x-auto md:flex-col md:w-48 md:shrink-0">
    {tabs.map(tab => <TabButton key={tab.id} />)}
  </nav>
  <div className="flex-1">
    <ActivePanel />
  </div>
</div>
```

---

## Modal Components — Full-Screen Mobile Pattern

### Shared Pattern for All Modals

All 16 modals receive the following responsive classes on their container:

```tsx
<div className={cn(
  // Desktop (existing)
  'fixed inset-0 z-50 flex items-center justify-center',
  // Modal content
  'mx-auto w-full max-w-lg rounded-lg bg-background p-6 shadow-xl',
  // Mobile override
  'max-sm:max-w-none max-sm:h-full max-sm:rounded-none max-sm:m-0',
)}>
  {/* Close button: always visible, touch-friendly on mobile */}
  <button className="absolute top-3 right-3 touch-target">
    <X className="h-5 w-5" />
  </button>
  {/* Scrollable content */}
  <div className="overflow-y-auto max-h-[calc(100vh-8rem)] max-sm:max-h-[calc(100vh-4rem)]">
    {children}
  </div>
</div>
```

**Affected Modals**: AddAgentModal, AgentIconPickerModal, AddChoreModal, ConfirmChoreModal, ToolSelectorModal, UploadMcpModal, EditRepoMcpModal, CleanUpConfirmModal, IssueDetailModal, BulkModelUpdateDialog, UnsavedChangesDialog, ConfirmationDialog

---

## No API Contracts Needed

This feature is entirely frontend. No REST API endpoints are added, modified, or consumed beyond what already exists.
