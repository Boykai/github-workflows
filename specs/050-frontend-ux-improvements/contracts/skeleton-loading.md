# Contract: Skeleton Loading States (Phase 4)

**Feature**: 050-frontend-ux-improvements  
**Requirements**: FR-018 through FR-021

## Component Contracts

### `Skeleton` Primitive (NEW)

**Location**: `solune/frontend/src/components/ui/skeleton.tsx`

```tsx
import { cn } from '@/lib/utils';

interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'pulse' | 'shimmer';
}

function Skeleton({ className, variant = 'pulse', ...props }: SkeletonProps) {
  return (
    <div
      className={cn(
        'rounded bg-muted',
        variant === 'pulse' && 'animate-pulse',
        variant === 'shimmer' && 'celestial-shimmer',
        className
      )}
      role="presentation"
      aria-hidden="true"
      {...props}
    />
  );
}
```

### `BoardColumnSkeleton` (NEW)

**Location**: `solune/frontend/src/components/board/BoardColumnSkeleton.tsx`

```tsx
// Matches BoardColumn layout: h-[72rem] max-h-[72rem]
function BoardColumnSkeleton() {
  return (
    <div className="project-board-column pipeline-column-surface">
      {/* Header */}
      <div className="flex items-center gap-2 p-3">
        <Skeleton className="h-3 w-3 rounded-full" />
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-5 w-8 rounded-full" />
      </div>
      {/* Cards */}
      <div className="flex flex-col gap-3 p-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <IssueCardSkeleton key={i} />
        ))}
      </div>
    </div>
  );
}
```

### `IssueCardSkeleton` (NEW)

**Location**: `solune/frontend/src/components/board/IssueCardSkeleton.tsx`

```tsx
// Matches IssueCard approximate dimensions
function IssueCardSkeleton() {
  return (
    <div className="rounded-lg border border-border bg-card p-3 space-y-2">
      <Skeleton className="h-3 w-20" />          {/* Repo badge */}
      <Skeleton className="h-4 w-3/4" />          {/* Title */}
      <Skeleton className="h-3 w-full" />          {/* Description line 1 */}
      <Skeleton className="h-3 w-2/3" />           {/* Description line 2 */}
      <div className="flex gap-1.5">
        <Skeleton className="h-5 w-14 rounded-full" />  {/* Label pill */}
        <Skeleton className="h-5 w-14 rounded-full" />  {/* Label pill */}
      </div>
      <div className="flex items-center gap-2 pt-1">
        <Skeleton className="h-6 w-6 rounded-full" />   {/* Avatar */}
        <Skeleton className="h-3 w-16" />                {/* Assignee name */}
      </div>
    </div>
  );
}
```

### `ChatMessageSkeleton` (NEW)

**Location**: `solune/frontend/src/components/chat/ChatMessageSkeleton.tsx`

```tsx
// Matches MessageBubble AI message layout
function ChatMessageSkeleton() {
  return (
    <div className="flex items-start gap-3 max-w-[80%]">
      <Skeleton className="h-8 w-8 rounded-full shrink-0" />  {/* Avatar */}
      <div className="flex-1 space-y-2 border border-border bg-background/62 rounded-lg p-3">
        <Skeleton className="h-3 w-full" />
        <Skeleton className="h-3 w-full" />
        <Skeleton className="h-3 w-1/2" />
      </div>
    </div>
  );
}
```

### `AgentCardSkeleton` (NEW)

**Location**: `solune/frontend/src/components/board/AgentCardSkeleton.tsx`

```tsx
// Matches agent card layout in pipeline builder
function AgentCardSkeleton() {
  return (
    <div className="rounded-lg border border-border bg-card p-3 flex items-center gap-3">
      <Skeleton className="h-10 w-10 rounded-full shrink-0" />  {/* Icon */}
      <div className="flex-1 space-y-1.5">
        <Skeleton className="h-4 w-32" />   {/* Name */}
        <Skeleton className="h-3 w-24" />   {/* Model */}
        <Skeleton className="h-3 w-16" />   {/* Tools */}
      </div>
    </div>
  );
}
```

## Integration Points

Replace `<CelestialLoader />` with appropriate skeleton in these locations:

| Location | Current Loading | New Loading |
|----------|----------------|-------------|
| ProjectBoard (data loading) | CelestialLoader | BoardColumnSkeleton ×N |
| ChatInterface (history loading) | CelestialLoader | ChatMessageSkeleton ×5 |
| Agent list (loading) | CelestialLoader | AgentCardSkeleton ×4 |
| Route-level Suspense | CelestialLoader | CelestialLoader (KEEP — FR-020) |

## Accessibility

- Skeleton elements use `role="presentation"` and `aria-hidden="true"` (decorative).
- Parent container should include an `aria-live="polite"` region with `aria-busy="true"` during loading, changing to `aria-busy="false"` when content loads.
- `prefers-reduced-motion`: Both `animate-pulse` and `celestial-shimmer` are disabled via the existing `@media (prefers-reduced-motion: reduce)` block in `index.css`.
