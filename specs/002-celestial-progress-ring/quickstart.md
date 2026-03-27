# Quickstart: Celestial Loading Progress Ring

**Feature**: 002-celestial-progress-ring  
**Date**: 2026-03-27

---

## Overview

This guide provides the step-by-step implementation order for the Celestial Loading Progress Ring feature. Follow these steps in sequence — each builds on the previous.

---

## Step 1: Add CSS Utility Class

**File**: `solune/frontend/src/index.css`

Add the `.celestial-ring-glow` class after the existing celestial utility classes (after `.celestial-fade-in`):

```css
.celestial-ring-glow {
  filter: drop-shadow(0 0 6px hsl(var(--gold) / 0.4))
          drop-shadow(0 0 14px hsl(var(--gold) / 0.15));
}
```

**Verify**: `npx eslint src/index.css` (no errors)

---

## Step 2: Create CelestialLoadingProgress Component

**File**: `solune/frontend/src/components/common/CelestialLoadingProgress.tsx`

### Implementation checklist:

1. **Define types**: `LoadingPhase` interface (`{ label: string; complete: boolean }`) and `CelestialLoadingProgressProps`
2. **Time-based minimum**: `useState(0)` + `useEffect` with `setInterval(100ms)` incrementing toward 0.15 over 3s, capping at 0.30
3. **Progress computation**: `max(minProgress, completedCount / totalCount)`
4. **SVG ring**: `viewBox="0 0 120 120"`, radius=52, `stroke-dasharray`/`stroke-dashoffset` with CSS transition
5. **Gradient**: `<linearGradient>` with `hsl(var(--gold))` → `hsl(var(--primary))`
6. **CelestialLoader embed**: Absolutely positioned inside a relative container, centered over the SVG
7. **Phase label**: `<p key={label}>` with `celestial-fade-in` class
8. **Twinkling stars**: 3–5 `<span>` elements with `celestial-twinkle` variants, `aria-hidden="true"`
9. **Accessibility**: `role="progressbar"`, `aria-valuenow`, `aria-valuemin`, `aria-valuemax`
10. **Glow**: Apply `celestial-ring-glow` class to SVG element

**Verify**: `npx eslint src/components/common/CelestialLoadingProgress.tsx`

---

## Step 3: Create Component Tests

**File**: `solune/frontend/src/components/common/CelestialLoadingProgress.test.tsx`

### Test cases:

1. **Renders initial phase label with zero completions**: Pass all-incomplete phases, verify first label text appears
2. **Updates ring progress as phases complete**: Pass partially complete phases, verify `aria-valuenow` reflects correct percentage
3. **Exposes role="progressbar" with correct aria-valuenow**: Query `role="progressbar"`, assert attributes
4. **Shows last phase label when all complete**: Pass all-complete phases, verify last label
5. **Handles empty phases gracefully**: Pass empty array, verify no crash

**Verify**: `npx vitest run src/components/common/CelestialLoadingProgress.test.tsx`

---

## Step 4: Integrate into ProjectsPage

**File**: `solune/frontend/src/pages/ProjectsPage.tsx`

### Changes:

1. **Import**: Add `CelestialLoadingProgress` import, keep `CelestialLoader` import (used by the new component internally)
2. **Replace** the `boardLoading && CelestialLoader` block (~line 455) with:
   ```tsx
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
3. **Note**: `projectsLoading` comes from `useProjectBoard()`, `savedPipelinesLoading` from the inline `useQuery`, `availableAgents` from `useAvailableAgents()`

**Verify**: `npx eslint src/pages/ProjectsPage.tsx`

---

## Step 5: Update ProjectsPage Tests

**File**: `solune/frontend/src/pages/ProjectsPage.test.tsx`

### Changes:

1. **Update mock**: Replace `CelestialLoader` mock with `CelestialLoadingProgress` mock:
   ```typescript
   vi.mock('@/components/common/CelestialLoadingProgress', () => ({
     CelestialLoadingProgress: ({ phases }: { phases: { label: string; complete: boolean }[] }) => {
       const currentLabel = phases.find(p => !p.complete)?.label ?? phases[phases.length - 1]?.label ?? '';
       return <div role="progressbar">{currentLabel}</div>;
     },
   }));
   ```
2. **Update test assertion**: The "shows loading state when board is loading" test should look for the phase label text instead of "Loading board…"
3. **Remove** the old `CelestialLoader` mock (no longer imported by ProjectsPage)

**Verify**: `npx vitest run src/pages/ProjectsPage.test.tsx`

---

## Step 6: Integrate into AgentsPipelinePage

**File**: `solune/frontend/src/pages/AgentsPipelinePage.tsx`

### Changes:

1. **Import**: Replace `CelestialLoader` import with `CelestialLoadingProgress`
2. **Replace** the `boardLoading && CelestialLoader` block (~line 155) with page-specific phases:
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

**Verify**: `npx eslint src/pages/AgentsPipelinePage.tsx`

---

## Step 7: Integrate into SettingsPage

**File**: `solune/frontend/src/pages/SettingsPage.tsx`

### Changes:

1. **Import**: Replace `CelestialLoader` import with `CelestialLoadingProgress`
2. **Replace** the `userLoading` early return (~line 68) with:
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

**Verify**: `npx eslint src/pages/SettingsPage.tsx`

---

## Step 8: Full Verification

Run all verification commands in order:

```bash
# 1. Component tests
npx vitest run src/components/common/CelestialLoadingProgress.test.tsx

# 2. Page tests
npx vitest run src/pages/ProjectsPage.test.tsx

# 3. Full test suite (no regressions)
npm run test

# 4. Lint modified files
npx eslint src/components/common/CelestialLoadingProgress.tsx src/pages/ProjectsPage.tsx src/pages/AgentsPipelinePage.tsx src/pages/SettingsPage.tsx

# 5. Type check
npm run type-check

# 6. Build
npm run build
```

---

## Manual Verification

1. Navigate to a project page → confirm gold ring fills through labeled phases with stars twinkling
2. Confirm ring moves immediately on mount (time-based fill) before any data resolves
3. Confirm ring jumps forward on each phase completion
4. Toggle dark mode → confirm gold ring and stars are clearly visible against dark background
5. Test with screen reader → confirm progress announcements
6. Navigate to Agents Pipeline page → confirm page-specific phase labels
7. Navigate to Settings page → confirm page-specific phase labels
