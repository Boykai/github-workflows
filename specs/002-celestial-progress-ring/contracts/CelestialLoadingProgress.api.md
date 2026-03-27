# Component API Contract: CelestialLoadingProgress

**Feature**: 002-celestial-progress-ring  
**Date**: 2026-03-27  
**Component Path**: `solune/frontend/src/components/common/CelestialLoadingProgress.tsx`

---

## Interface

```typescript
/**
 * A single loading phase with a human-readable label and completion status.
 */
export interface LoadingPhase {
  /** Descriptive label shown to the user (e.g., "Connecting to GitHub…") */
  label: string;
  /** Whether this phase's data source has resolved */
  complete: boolean;
}

/**
 * Props for the CelestialLoadingProgress component.
 */
export interface CelestialLoadingProgressProps {
  /**
   * Ordered list of loading phases. Each phase has a label and a boolean
   * completion status. Progress is computed as (completed / total), interpolated
   * with a time-based minimum floor.
   *
   * @example
   * [
   *   { label: 'Connecting to GitHub…', complete: true },
   *   { label: 'Loading project board…', complete: false },
   *   { label: 'Loading pipelines…', complete: false },
   *   { label: 'Loading agents…', complete: false },
   * ]
   */
  phases: LoadingPhase[];

  /**
   * Optional additional CSS classes for the root container.
   */
  className?: string;
}
```

---

## Rendered Output (semantic structure)

```
<div class="flex flex-col items-center gap-4 {className}">    ← Root container
  <div class="relative">                                        ← Ring + loader wrapper
    <svg                                                        ← Progress ring SVG
      role="progressbar"
      aria-valuenow={progress%}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label="Loading progress"
      class="celestial-ring-glow"
      viewBox="0 0 120 120"
    >
      <defs>
        <linearGradient id="celestial-ring-gradient">          ← Gold→primary gradient
          <stop offset="0%" stop-color="hsl(var(--gold))" />
          <stop offset="100%" stop-color="hsl(var(--primary))" />
        </linearGradient>
      </defs>
      <circle                                                   ← Background track
        cx="60" cy="60" r="52"
        stroke="hsl(var(--muted)/0.2)"
        stroke-width="4"
        fill="none"
      />
      <circle                                                   ← Progress arc
        cx="60" cy="60" r="52"
        stroke="url(#celestial-ring-gradient)"
        stroke-width="4"
        fill="none"
        stroke-dasharray={circumference}
        stroke-dashoffset={offset}
        stroke-linecap="round"
        style="transition: stroke-dashoffset 0.6s ease"
        transform="rotate(-90 60 60)"                          ← Start from top
      />
    </svg>
    <div class="absolute inset-0 flex items-center justify-center">
      <CelestialLoader size="lg" />                            ← Existing loader, centered
    </div>
  </div>

  <!-- Twinkling stars (decorative) -->
  <span class="celestial-twinkle ..." aria-hidden="true">✦</span>
  <span class="celestial-twinkle-delayed ..." aria-hidden="true">✦</span>
  <span class="celestial-twinkle-slow ..." aria-hidden="true">✦</span>

  <!-- Phase label -->
  <p key={label} class="celestial-fade-in text-sm text-muted-foreground">
    {currentPhaseLabel}
  </p>
</div>
```

---

## Behavioral Contract

### Progress Computation

```
INPUT:  phases: LoadingPhase[]
OUTPUT: displayProgress ∈ [0, 1]

completedCount = phases.filter(p => p.complete).length
realProgress   = phases.length > 0 ? completedCount / phases.length : 1
displayProgress = max(minProgress, realProgress)
```

### Time-Based Minimum Floor

```
t=0s    → minProgress = 0.00
t=1s    → minProgress ≈ 0.05
t=2s    → minProgress ≈ 0.10
t=3s    → minProgress ≈ 0.15
t=3s+   → minProgress slowly increments toward 0.30 (cap)
t=∞     → minProgress = 0.30 (never exceeds)
```

### Phase Label Selection

```
currentPhaseLabel = phases.find(p => !p.complete)?.label
                  ?? phases[phases.length - 1]?.label
                  ?? ''
```

### SVG Ring Math

```
radius        = 52
circumference = 2 × π × 52 ≈ 326.73
offset        = circumference × (1 - displayProgress)
```

---

## Accessibility Contract

| Attribute | Value | Description |
|-----------|-------|-------------|
| `role` | `"progressbar"` | Identifies element as a progress indicator |
| `aria-valuenow` | `Math.round(displayProgress * 100)` | Current progress (0–100) |
| `aria-valuemin` | `0` | Minimum value |
| `aria-valuemax` | `100` | Maximum value |
| `aria-label` | `"Loading progress"` | Accessible name |
| Star `aria-hidden` | `"true"` | Decorative elements hidden from assistive technology |

---

## CSS Contract

### New Class: `.celestial-ring-glow`

**Location**: `solune/frontend/src/index.css`  
**Placement**: After existing celestial utility classes (after `.celestial-fade-in`)

```css
.celestial-ring-glow {
  filter: drop-shadow(0 0 6px hsl(var(--gold) / 0.4))
          drop-shadow(0 0 14px hsl(var(--gold) / 0.15));
}
```

### Reused Classes

| Class | Source | Usage |
|-------|--------|-------|
| `celestial-fade-in` | index.css | Phase label entry animation |
| `celestial-twinkle` | index.css | Star decoration animation |
| `celestial-twinkle-delayed` | index.css | Star with 1.5s delay |
| `celestial-twinkle-slow` | index.css | Star with 5s duration |
| `celestial-pulse-glow` | index.css | Used by embedded CelestialLoader |
| `celestial-orbit-spin-fast` | index.css | Used by embedded CelestialLoader |

---

## Usage Examples

### ProjectsPage Integration

```tsx
import { CelestialLoadingProgress } from '@/components/common/CelestialLoadingProgress';

// Inside render:
{selectedProjectId && boardLoading && (
  <div className="flex flex-1 flex-col items-center justify-center gap-4">
    <CelestialLoadingProgress
      phases={[
        { label: 'Connecting to GitHub…', complete: !projectsLoading },
        { label: 'Loading project board…', complete: !boardLoading },
        { label: 'Loading pipelines…', complete: !savedPipelinesLoading },
        { label: 'Loading agents…', complete: !!availableAgents?.length },
      ]}
    />
  </div>
)}
```

### AgentsPipelinePage Integration

```tsx
{projectId && boardLoading && (
  <div className="flex flex-col items-center justify-center flex-1 gap-4">
    <CelestialLoadingProgress
      phases={[
        { label: 'Connecting to GitHub…', complete: !projectsLoading },
        { label: 'Loading board data…', complete: !boardLoading },
        { label: 'Loading agents…', complete: !agentsLoading },
      ]}
    />
  </div>
)}
```

### SettingsPage Integration

```tsx
if (userLoading || globalLoading) {
  return (
    <div className="flex h-full w-full max-w-4xl flex-col overflow-y-auto p-8 mx-auto">
      <div className="flex flex-col items-center justify-center flex-1 gap-4">
        <CelestialLoadingProgress
          phases={[
            { label: 'Loading user settings…', complete: !userLoading },
            { label: 'Loading global settings…', complete: !globalLoading },
          ]}
        />
      </div>
    </div>
  );
}
```
