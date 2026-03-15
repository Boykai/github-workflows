# Contract: Tooltip Component

**Feature**: `002-tooltip-hover-coverage` | **Date**: 2026-03-15 | **Data Model**: [data-model.md](../data-model.md)

## Overview

This contract documents the existing `<Tooltip>` component API for reference. No changes are required to the component itself — this feature extends its usage across the application and expands the content registry.

## Component API

### `<Tooltip>` (Convenience Wrapper)

**File**: `solune/frontend/src/components/ui/tooltip.tsx`

```tsx
interface TooltipProps {
  /** Registry key to look up tooltip content. Format: {area}.{section}.{element} */
  contentKey?: string;
  /** Direct content string (escape hatch when registry is not appropriate) */
  content?: string;
  /** Bold heading displayed above the summary */
  title?: string;
  /** "Learn more →" link URL */
  learnMoreUrl?: string;
  /** Placement side relative to trigger */
  side?: 'top' | 'right' | 'bottom' | 'left';
  /** Alignment along the placement side */
  align?: 'start' | 'center' | 'end';
  /** Override the global delay duration (ms) */
  delayDuration?: number;
  /** Trigger element(s) */
  children: React.ReactNode;
}
```

### Usage Patterns

**Registry-based (preferred)**:
```tsx
<Tooltip contentKey="pipeline.agent.dragHandle">
  <button aria-label="Drag to reorder agent">
    <GripVertical className="h-4 w-4" />
  </button>
</Tooltip>
```

**Direct content (escape hatch)**:
```tsx
<Tooltip content={`Temperature: ${value}`} title="AI Temperature">
  <span>{value}</span>
</Tooltip>
```

**Zero delay for dense areas**:
```tsx
<Tooltip contentKey="pipeline.agent.clone" delayDuration={0}>
  <button aria-label="Clone agent">
    <Copy className="h-4 w-4" />
  </button>
</Tooltip>
```

### Behavior Contract

| Behavior | Specification |
|----------|--------------|
| Appears on | Hover and keyboard focus |
| Default delay | 300ms (inherited from `<TooltipProvider>` in App.tsx) |
| Skip delay | 300ms between consecutive tooltips in same session |
| Max width | 280px with text wrapping |
| Z-index | 50 (rendered in portal) |
| Missing content | Renders `<>{children}</>` with no tooltip (graceful degradation) |
| Animation | `fade-in-0 zoom-in-95` with directional slide |
| Collision | Repositions to stay within viewport |

### Registry Entry Format

**File**: `solune/frontend/src/constants/tooltip-content.ts`

```typescript
interface TooltipEntry {
  summary: string;          // Required — primary tooltip text
  title?: string;           // Optional — bold heading
  learnMoreUrl?: string;    // Optional — "Learn more →" link
}

export const tooltipContent: Record<string, TooltipEntry> = {
  'pipeline.agent.dragHandle': {
    summary: 'Drag to reorder this agent within the execution group',
  },
  'settings.ai.temperature': {
    title: 'Temperature',
    summary: 'Controls randomness in AI responses. Lower values (0.0) produce more focused output; higher values (2.0) increase creativity.',
  },
  // ...
};
```
