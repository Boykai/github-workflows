# Component Remediation Contracts: Pipelines Page UI Audit

**Feature**: 033-audit-pipelines-ux | **Date**: 2026-03-10

## Overview

This document defines the interface contracts for component modifications required to remediate open audit findings. Each contract specifies the exact changes needed, the affected component interface, and the verification criteria.

---

## PIPE-004: PipelineBoard Validation Accessibility

**Finding**: Pipeline name validation feedback is visual-only; the name input does not expose `aria-invalid` / `aria-describedby` for assistive technologies.

**Affected File**: `frontend/src/components/pipeline/PipelineBoard.tsx`

**Severity**: Medium | **Category**: Accessibility | **WCAG**: 3.3.1, 4.1.2

### Current Interface (Name Input — Edit Mode)

```tsx
// Lines ~124-162 (compact layout) and ~218-256 (full layout)
<input
  ref={nameInputRef}
  type="text"
  value={editNameValue}
  onChange={handleNameChange}
  onBlur={handleNameConfirm}
  onKeyDown={handleNameKeyDown}
  aria-label="Pipeline name"
  className={cn(
    "h-7 w-full rounded border bg-background/50 px-2 text-sm ...",
    validationErrors.name ? "border-red-500" : "border-primary/30"
  )}
  maxLength={100}
  autoFocus
/>
{validationErrors.name && (
  <p className="mt-1 text-xs text-red-500">{validationErrors.name}</p>
)}
```

### Required Changes

1. **Add `id` to the error paragraph** for `aria-describedby` linkage
2. **Add `aria-invalid`** to the input when validation error exists
3. **Add `aria-describedby`** to the input pointing to the error paragraph ID
4. **Apply to both layouts** (compact and full) in PipelineBoard

### Target Interface (Name Input — Edit Mode)

```tsx
<input
  ref={nameInputRef}
  type="text"
  value={editNameValue}
  onChange={handleNameChange}
  onBlur={handleNameConfirm}
  onKeyDown={handleNameKeyDown}
  aria-label="Pipeline name"
  aria-invalid={validationErrors.name ? "true" : undefined}
  aria-describedby={validationErrors.name ? "pipeline-name-error" : undefined}
  className={cn(
    "h-7 w-full rounded border bg-background/50 px-2 text-sm ...",
    validationErrors.name ? "border-red-500" : "border-primary/30"
  )}
  maxLength={100}
  autoFocus
/>
{validationErrors.name && (
  <p id="pipeline-name-error" className="mt-1 text-xs text-red-500">
    {validationErrors.name}
  </p>
)}
```

### Verification Criteria

- [ ] Screen reader announces the error message when the input receives focus and has a validation error
- [ ] `aria-invalid="true"` is present on the input only when `validationErrors.name` is truthy
- [ ] `aria-describedby="pipeline-name-error"` links the input to the error paragraph
- [ ] Both compact and full layout variants include the new attributes
- [ ] Existing visual behavior (red border, error text) is unchanged
- [ ] Existing keyboard behavior (Enter to confirm, Escape to cancel) is unchanged

---

## PIPE-005: SavedWorkflowsList Skeleton Upgrade

**Finding**: Loading skeletons use generic pulse blocks that feel flatter and less intentional than the app's celestial panel skeletons.

**Affected File**: `frontend/src/components/pipeline/SavedWorkflowsList.tsx`

**Severity**: Low | **Category**: Visual consistency

### Current Interface (Loading State)

```tsx
// Lines ~61-70
{isLoading && (
  <div className="grid gap-3 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
    {[1, 2, 3].map((i) => (
      <div
        key={i}
        className="h-32 rounded-xl border border-border/50 bg-muted/20 animate-pulse"
      />
    ))}
  </div>
)}
```

### Required Changes

1. **Upgrade skeleton cards** to use structured placeholders matching the workflow card layout
2. **Apply `celestial-panel`-aligned styling** (border radius, border opacity, background)
3. **Include placeholder shapes** for: name bar, description lines, stats row

### Target Interface (Loading State)

```tsx
{isLoading && (
  <div className="grid gap-3 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
    {[1, 2, 3].map((i) => (
      <div
        key={i}
        className="flex flex-col gap-3 rounded-[1.3rem] border border-border/50 bg-card/80 p-4 animate-pulse"
      >
        {/* Name placeholder */}
        <div className="h-4 w-2/3 rounded bg-muted/40" />
        {/* Description placeholder */}
        <div className="h-3 w-full rounded bg-muted/30" />
        <div className="h-3 w-4/5 rounded bg-muted/30" />
        {/* Stats row placeholder */}
        <div className="mt-auto flex gap-3">
          <div className="h-3 w-12 rounded bg-muted/20" />
          <div className="h-3 w-12 rounded bg-muted/20" />
          <div className="h-3 w-16 rounded bg-muted/20" />
        </div>
      </div>
    ))}
  </div>
)}
```

### Verification Criteria

- [ ] Skeleton cards have the same border radius as loaded workflow cards (`rounded-[1.3rem]`)
- [ ] Skeleton cards show placeholder shapes that preview the card structure
- [ ] The `animate-pulse` animation is retained for loading indication
- [ ] Visual transition from skeleton to loaded cards feels smooth
- [ ] Grid layout matches the loaded state grid (1-col mobile, 2-col tablet, 3-col desktop)

---

## PIPE-006: Recent Activity Overflow Indicator

**Finding**: Recent Activity hard-caps to the three newest pipelines without an affordance or explanatory copy for seeing older activity.

**Affected File**: `frontend/src/pages/AgentsPipelinePage.tsx`

**Severity**: Low | **Category**: UX clarity

### Current Interface (Recent Activity Section)

```tsx
// Recent activity section renders up to 3 pipelines
{recentPipelines.slice(0, 3).map((pipeline) => (
  // ... pipeline card rendering
))}
```

### Required Changes

1. **Add conditional overflow text** below the 3 recent pipelines when total count exceeds 3
2. **Include anchor link** to `#saved-pipelines` for navigation to full list

### Target Interface (Recent Activity Overflow)

```tsx
{recentPipelines.slice(0, 3).map((pipeline) => (
  // ... pipeline card rendering (unchanged)
))}
{totalPipelineCount > 3 && (
  <p className="mt-2 text-center text-xs text-muted-foreground">
    Showing 3 of {totalPipelineCount} —{" "}
    <a href="#saved-pipelines" className="text-primary/70 hover:text-primary underline-offset-2 hover:underline">
      see all in Saved Pipelines
    </a>
  </p>
)}
```

### Verification Criteria

- [ ] Text appears only when total pipeline count exceeds 3
- [ ] Text shows correct total count
- [ ] "Saved Pipelines" link scrolls to the `#saved-pipelines` section
- [ ] Text styling uses `text-muted-foreground` consistent with other helper text
- [ ] No visual change when pipeline count is ≤ 3
