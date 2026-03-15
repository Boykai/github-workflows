# Contract: Hover Card Component

**Feature**: `002-tooltip-hover-coverage` | **Date**: 2026-03-15 | **Data Model**: [data-model.md](../data-model.md)

## Overview

This contract defines the API for the new `<HoverCard>` component to be created in `solune/frontend/src/components/ui/hover-card.tsx`. The component wraps `@radix-ui/react-hover-card` and provides a styled, accessible hover card for rich entity previews.

## Component API

### Exported Parts

```tsx
// Named re-exports from Radix (for advanced composition)
export const HoverCard: typeof HoverCardPrimitive.Root;
export const HoverCardTrigger: typeof HoverCardPrimitive.Trigger;

// Styled content wrapper
export const HoverCardContent: React.ForwardRefExoticComponent<HoverCardContentProps>;
```

### `<HoverCardContent>` Props

```tsx
interface HoverCardContentProps
  extends React.ComponentPropsWithoutRef<typeof HoverCardPrimitive.Content> {
  /** Preferred placement side relative to trigger. Default: 'bottom' */
  side?: 'top' | 'right' | 'bottom' | 'left';
  /** Alignment along the placement side. Default: 'center' */
  align?: 'start' | 'center' | 'end';
  /** Distance from trigger element in pixels. Default: 4 */
  sideOffset?: number;
  /** Additional CSS classes */
  className?: string;
  /** Hover card body content (supports JSX) */
  children: React.ReactNode;
}
```

### `<HoverCard>` (Root) Props

```tsx
interface HoverCardRootProps {
  /** Delay in ms before card opens on hover. Default: 300 */
  openDelay?: number;
  /** Delay in ms before card closes on mouse leave. Default: 150 */
  closeDelay?: number;
  /** Controlled open state */
  open?: boolean;
  /** Callback when open state changes */
  onOpenChange?: (open: boolean) => void;
  /** Trigger and content elements */
  children: React.ReactNode;
}
```

## Usage Patterns

### Agent Node Hover Card (Pipeline)

```tsx
import { HoverCard, HoverCardTrigger, HoverCardContent } from '@/components/ui/hover-card';

<HoverCard openDelay={300} closeDelay={150}>
  <HoverCardTrigger asChild>
    <div className="agent-node">
      {/* existing agent node content */}
    </div>
  </HoverCardTrigger>
  <HoverCardContent side="right" align="start">
    <div className="space-y-2">
      <h4 className="text-sm font-semibold">{agent.name}</h4>
      <p className="text-xs text-muted-foreground">{agent.description}</p>
      <div className="flex items-center gap-2">
        <Badge variant="outline">{agent.model}</Badge>
        <span className="text-xs">{agent.tools.length} tools</span>
      </div>
      {agent.lastRunStatus && (
        <StatusBadge status={agent.lastRunStatus} />
      )}
    </div>
  </HoverCardContent>
</HoverCard>
```

### Issue Card Hover Card (Board)

```tsx
<HoverCard>
  <HoverCardTrigger asChild>
    <div className="issue-card">{/* truncated title */}</div>
  </HoverCardTrigger>
  <HoverCardContent side="right" className="w-80">
    <div className="space-y-2">
      <p className="text-sm font-medium">{issue.fullTitle}</p>
      <div className="flex flex-wrap gap-1">
        {issue.labels.map(label => (
          <Badge key={label.name} style={{ backgroundColor: label.color }}>
            {label.name}
          </Badge>
        ))}
      </div>
      {issue.assignees.length > 0 && (
        <div className="flex items-center gap-1">
          {issue.assignees.map(a => <Avatar key={a} name={a} size="xs" />)}
        </div>
      )}
      {issue.pipelineStage && (
        <p className="text-xs text-muted-foreground">Stage: {issue.pipelineStage}</p>
      )}
    </div>
  </HoverCardContent>
</HoverCard>
```

## Behavior Contract

| Behavior | Specification |
|----------|--------------|
| Trigger | Hover over trigger element |
| Open delay | 300ms (default, configurable per instance) |
| Close delay | 150ms (allows cursor movement into card body) |
| Max width | 320px (configurable via className) |
| Z-index | 50 (rendered in portal) |
| Animation | `fade-in-0 zoom-in-95` with directional slide, gated behind `motion-safe:` |
| Reduced motion | Instant show/hide with no animation when `prefers-reduced-motion` is active |
| Collision | Repositions to stay within viewport (Radix built-in) |
| Portal | Renders in document body to avoid z-index stacking |
| Focus | No focus trap (informational overlay, not interactive modal) |
| Loading state | Consumer responsible for rendering skeleton/spinner inside `<HoverCardContent>` |
| No global provider | Unlike Tooltip, HoverCard does not require a provider wrapper in App.tsx |

## Styling Contract

```tsx
// Base HoverCardContent classes (matches tooltip.tsx pattern)
const baseClasses = cn(
  // Layout
  'z-50 w-64 rounded-md border bg-popover p-4 text-popover-foreground shadow-md outline-none',
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
