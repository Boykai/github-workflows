# Contract: Popover Component

**Feature**: `002-tooltip-hover-coverage` | **Date**: 2026-03-15 | **Data Model**: [data-model.md](../data-model.md)

## Overview

This contract defines the API for the new `<Popover>` component to be created in `solune/frontend/src/components/ui/popover.tsx`. The component wraps `@radix-ui/react-popover` and provides a styled, accessible click-triggered overlay for menus, selectors, and interactive content.

## Component API

### Exported Parts

```tsx
// Named re-exports from Radix (for composition)
export const Popover: typeof PopoverPrimitive.Root;
export const PopoverTrigger: typeof PopoverPrimitive.Trigger;
export const PopoverAnchor: typeof PopoverPrimitive.Anchor;
export const PopoverClose: typeof PopoverPrimitive.Close;

// Styled content wrapper
export const PopoverContent: React.ForwardRefExoticComponent<PopoverContentProps>;

// Optional styled arrow
export const PopoverArrow: React.ForwardRefExoticComponent<PopoverArrowProps>;
```

### `<PopoverContent>` Props

```tsx
interface PopoverContentProps
  extends React.ComponentPropsWithoutRef<typeof PopoverPrimitive.Content> {
  /** Preferred placement side relative to trigger. Default: 'bottom' */
  side?: 'top' | 'right' | 'bottom' | 'left';
  /** Alignment along the placement side. Default: 'center' */
  align?: 'start' | 'center' | 'end';
  /** Distance from trigger element in pixels. Default: 4 */
  sideOffset?: number;
  /** Padding from viewport edge for collision detection. Default: 8 */
  collisionPadding?: number;
  /** Additional CSS classes */
  className?: string;
  /** Popover body content (supports JSX, interactive elements) */
  children: React.ReactNode;
}
```

### `<Popover>` (Root) Props

```tsx
interface PopoverRootProps {
  /** Controlled open state */
  open?: boolean;
  /** Callback when open state changes */
  onOpenChange?: (open: boolean) => void;
  /** Whether the popover is modal (locks background interaction). Default: false */
  modal?: boolean;
  /** Trigger and content elements */
  children: React.ReactNode;
}
```

## Usage Patterns

### Model Selector Migration (Pipeline)

```tsx
import { Popover, PopoverTrigger, PopoverContent } from '@/components/ui/popover';

function ModelSelector({ value, onChange, models }) {
  const [search, setSearch] = useState('');
  
  return (
    <Popover>
      <PopoverTrigger asChild>
        <button
          className="flex items-center gap-2 rounded-md border px-3 py-1.5 text-sm"
          aria-label="Select AI model"
        >
          <Bot className="h-4 w-4" />
          <span className="truncate">{value || 'Select model'}</span>
          <ChevronDown className="h-3 w-3 opacity-50" />
        </button>
      </PopoverTrigger>
      <PopoverContent side="bottom" align="start" className="w-72 p-0">
        {/* Search input */}
        <div className="border-b px-3 py-2">
          <Input
            placeholder="Search models..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="h-8"
          />
        </div>
        {/* Model list */}
        <div className="max-h-64 overflow-y-auto p-1">
          {filteredModels.map(model => (
            <PopoverClose key={model.id} asChild>
              <button
                className="w-full rounded px-2 py-1.5 text-left text-sm hover:bg-accent"
                onClick={() => onChange(model.id)}
              >
                {model.name}
              </button>
            </PopoverClose>
          ))}
        </div>
      </PopoverContent>
    </Popover>
  );
}
```

### Add Agent Popover Migration (Board)

```tsx
import { Popover, PopoverTrigger, PopoverContent } from '@/components/ui/popover';

function AddAgentPopover({ columnId, onAgentAdd, agents }) {
  const [filter, setFilter] = useState('');

  return (
    <Popover>
      <PopoverTrigger asChild>
        <button
          className="rounded-md p-1 text-muted-foreground hover:text-foreground"
          aria-label="Add agent to column"
        >
          <Plus className="h-4 w-4" />
        </button>
      </PopoverTrigger>
      <PopoverContent side="bottom" align="start" className="w-64 p-0">
        <div className="border-b px-3 py-2">
          <Input
            placeholder="Filter agents..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="h-8"
            autoFocus
          />
        </div>
        <div className="max-h-80 overflow-y-auto p-1">
          {filteredAgents.map(agent => (
            <button
              key={agent.slug}
              className="w-full rounded px-2 py-1.5 text-left text-sm hover:bg-accent"
              onClick={() => onAgentAdd(agent)}
            >
              {agent.name}
            </button>
          ))}
        </div>
      </PopoverContent>
    </Popover>
  );
}
```

## Behavior Contract

| Behavior | Specification |
|----------|--------------|
| Trigger | Click on trigger element |
| Open | Instant (no delay) |
| Close triggers | Outside click, Escape key, or programmatic `onOpenChange(false)` |
| Focus trap | Focus is trapped inside content when open (Tab cycles within) |
| Focus restore | Focus returns to trigger element on close |
| ARIA | Trigger has `aria-haspopup="dialog"` and `aria-expanded` automatically |
| Z-index | 50 (rendered in portal) |
| Animation | `fade-in-0 zoom-in-95` with directional slide, gated behind `motion-safe:` |
| Reduced motion | Instant show/hide with no animation when `prefers-reduced-motion` is active |
| Collision | Repositions to stay within viewport (Radix built-in) |
| Portal | Renders in document body to avoid z-index stacking |
| Backdrop | Optional via `modal={true}` — adds inert backdrop blocking background interaction |

## Styling Contract

```tsx
// Base PopoverContent classes (matches tooltip.tsx and hover-card.tsx pattern)
const baseClasses = cn(
  // Layout
  'z-50 w-72 rounded-md border bg-popover p-4 text-popover-foreground shadow-md outline-none',
  // Animation (motion-safe only)
  'motion-safe:data-[state=open]:animate-in motion-safe:data-[state=closed]:animate-out',
  'motion-safe:data-[state=closed]:fade-out-0 motion-safe:data-[state=open]:fade-in-0',
  'motion-safe:data-[state=closed]:zoom-out-95 motion-safe:data-[state=open]:zoom-in-95',
  // Directional slide
  'motion-safe:data-[side=bottom]:slide-in-from-top-2',
  'motion-safe:data-[side=left]:slide-in-from-right-2',
  'motion-safe:data-[side=right]:slide-in-from-left-2',
  'motion-safe:data-[side=top]:slide-in-from-bottom-2',
);
```

## Migration Checklist

Each migrated component must verify:

- [ ] `aria-haspopup="dialog"` present on trigger
- [ ] `aria-expanded` toggles correctly
- [ ] Escape key closes popover
- [ ] Outside click closes popover
- [ ] Focus is trapped inside popover content
- [ ] Focus returns to trigger on close
- [ ] Viewport collision detection works (popover flips to available side)
- [ ] All existing features preserved (search, filtering, selection, etc.)
- [ ] No animation under `prefers-reduced-motion`
