# Quickstart: Deep UI/UX Tooltip & Hover Coverage

**Feature**: `002-tooltip-hover-coverage` | **Date**: 2026-03-15 | **Plan**: [plan.md](plan.md)

## Prerequisites

- Node.js 20+ with `npm`
- Git repository cloned with full history
- Access to `solune/frontend/` directory

## Setup

### Frontend Environment

```bash
cd solune/frontend
npm ci
```

### Install New Dependencies (Phase 1)

```bash
cd solune/frontend
npm install @radix-ui/react-hover-card @radix-ui/react-popover
```

## Development Workflow

### Running the Dev Server

```bash
cd solune/frontend
npm run dev
```

The development server starts at `http://localhost:5173` with hot module replacement.

### Running Tests

```bash
cd solune/frontend

# Run all unit tests
npx vitest run

# Run tests in watch mode (recommended during development)
npx vitest

# Run tests for a specific file
npx vitest run src/components/ui/hover-card.test.tsx
npx vitest run src/components/ui/popover.test.tsx

# Run tests matching a pattern
npx vitest run --reporter=verbose tooltip
```

### Type Checking

```bash
cd solune/frontend
npm run type-check
```

### Linting

```bash
cd solune/frontend
npm run lint
```

### Building

```bash
cd solune/frontend
npm run build
```

## Implementation Guide

### Phase 1: Creating New UI Primitives

#### Step 1: Create `hover-card.tsx`

**File**: `solune/frontend/src/components/ui/hover-card.tsx`

Reference the existing `tooltip.tsx` for patterns. The hover card wrapper should:

1. Import from `@radix-ui/react-hover-card`
2. Re-export `HoverCard` (Root) and `HoverCardTrigger`
3. Create a styled `HoverCardContent` with `forwardRef`
4. Apply Celestial design tokens (border, bg-popover, shadow-md)
5. Gate animations behind `motion-safe:` Tailwind modifier
6. Render in a portal (Radix default)

#### Step 2: Create `popover.tsx`

**File**: `solune/frontend/src/components/ui/popover.tsx`

1. Import from `@radix-ui/react-popover`
2. Re-export `Popover` (Root), `PopoverTrigger`, `PopoverAnchor`, `PopoverClose`
3. Create a styled `PopoverContent` with `forwardRef`
4. Match hover card styling pattern
5. Include `PopoverArrow` as an optional export

#### Step 3: Add Unit Tests

**Files**:
- `solune/frontend/src/components/ui/hover-card.test.tsx`
- `solune/frontend/src/components/ui/popover.test.tsx`

Use the existing `tooltipAwareRender` (aliased as `render`) from `src/test/test-utils.tsx`. Test:
- Renders without crashing
- Shows content on hover (hover card) / click (popover)
- Hides content on mouse leave / Escape
- Applies custom className
- Respects side/align props

### Phase 2: Extending the Tooltip Registry

**File**: `solune/frontend/src/constants/tooltip-content.ts`

Add new entries following the existing pattern:

```typescript
// Example: Pipeline drag handles
'pipeline.agent.dragHandle': {
  summary: 'Drag to reorder this agent within the execution group',
},
'pipeline.agent.clone': {
  summary: 'Create a copy of this agent configuration',
},

// Example: Navigation
'nav.projects': {
  summary: 'View and manage your projects',
},
'nav.agents': {
  summary: 'Configure AI agents and their tools',
},
```

### Phase 2: Wrapping Components with Tooltips

Replace `title=` attributes with `<Tooltip>` wrappers:

**Before**:
```tsx
<button title="Drag to reorder">
  <GripVertical className="h-4 w-4" />
</button>
```

**After**:
```tsx
<Tooltip contentKey="pipeline.agent.dragHandle">
  <button aria-label="Drag to reorder this agent within the execution group">
    <GripVertical className="h-4 w-4" />
  </button>
</Tooltip>
```

### Phase 2: Adding Hover Cards

Wrap entity elements with `<HoverCard>`:

```tsx
<HoverCard openDelay={300} closeDelay={150}>
  <HoverCardTrigger asChild>
    <div className="agent-node">{/* existing content */}</div>
  </HoverCardTrigger>
  <HoverCardContent side="right" align="start">
    <AgentPreview agent={agent} />
  </HoverCardContent>
</HoverCard>
```

### Phase 4: Migrating Manual Popovers

For each manual popover (AddAgentPopover, ModelSelector, AgentPresetSelector):

1. Replace `useState(isOpen)` + toggle logic with `<Popover>` + `<PopoverTrigger>`
2. Replace absolute-positioned div with `<PopoverContent>`
3. Remove manual Escape key handler (Radix handles it)
4. Remove manual outside click handler (Radix handles it)
5. Remove manual positioning/collision detection (Radix handles it)
6. Remove portal rendering code (Radix handles it)
7. Keep all internal logic (search, filtering, selection, recent tracking)
8. Verify ARIA attributes are correct

## Verification

### Automated Checks

```bash
# Run all tests
cd solune/frontend && npx vitest run

# Type check
cd solune/frontend && npm run type-check

# Lint
cd solune/frontend && npm run lint

# Build (ensures no compilation errors)
cd solune/frontend && npm run build
```

### Manual Verification

1. **Tooltip coverage**: Navigate to each page, hover over every icon-only button → tooltip appears within 300ms
2. **Hover cards**: Hover over agent nodes, agent cards, issue cards, mention chips → rich preview appears
3. **Popovers**: Click model selector, add-agent, preset selector → popover opens, Escape closes, focus returns
4. **Keyboard**: Tab through all interactive elements → tooltips appear on focus, popovers are focus-trapped
5. **Reduced motion**: Enable OS reduced-motion setting → no animations on hover cards or popovers
6. **Registry audit**: Search for `title=` on interactive elements → zero results (except allowlisted truncated text)
