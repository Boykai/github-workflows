# Component Contracts: Onboarding Tour

**Feature**: `042-onboarding-help-faq` | **Date**: 2026-03-15

## useOnboarding Hook

**File**: `solune/frontend/src/hooks/useOnboarding.ts`

```typescript
interface UseOnboardingReturn {
  /** Whether the tour overlay is currently displayed */
  isActive: boolean;
  /** Whether the user has previously completed or skipped the tour */
  hasCompleted: boolean;
  /** Current step index (0-based) */
  currentStep: number;
  /** Total number of steps */
  totalSteps: number;
  /** Advance to the next step; closes tour if on last step */
  next: () => void;
  /** Return to the previous step; no-op if on first step */
  prev: () => void;
  /** Close the tour and mark as completed */
  skip: () => void;
  /** Restart the tour from step 0 (does not reset hasCompleted) */
  restart: () => void;
}

function useOnboarding(): UseOnboardingReturn;
```

**localStorage key**: `solune-onboarding-completed`  
**Total steps**: 9 (constant)

---

## SpotlightOverlay

**File**: `solune/frontend/src/components/onboarding/SpotlightOverlay.tsx`

```typescript
interface SpotlightOverlayProps {
  /** Bounding rect of the element to cut out, or null for centered welcome */
  targetRect: DOMRect | null;
  /** Whether the overlay is visible */
  isVisible: boolean;
}
```

**Renders**: Fixed full-viewport div with `clip-path` polygon cutout.  
**z-index**: 100  
**Backdrop**: `bg-night/60` (dark) / `bg-background/70` (light)

---

## SpotlightTooltip

**File**: `solune/frontend/src/components/onboarding/SpotlightTooltip.tsx`

```typescript
interface SpotlightTooltipProps {
  /** Current step definition */
  step: TourStep;
  /** Bounding rect of the target element, or null for centered */
  targetRect: DOMRect | null;
  /** Current step index (0-based) */
  currentStep: number;
  /** Total steps */
  totalSteps: number;
  /** Advance to next step or finish */
  onNext: () => void;
  /** Return to previous step */
  onBack: () => void;
  /** Skip/close the tour */
  onSkip: () => void;
}
```

**Renders**: Positioned tooltip with icon, title, description, step counter, nav buttons, TourProgress.  
**Positioning**: Viewport-aware (top/bottom/left/right with fallback).  
**Mobile**: Fixed bottom sheet on viewports <768px.  
**Accessibility**: `role="dialog"`, `aria-modal="true"`, focus trap, `aria-live="polite"` announcer.

---

## TourProgress

**File**: `solune/frontend/src/components/onboarding/TourProgress.tsx`

```typescript
interface TourProgressProps {
  /** Current step index (0-based) */
  currentStep: number;
  /** Total steps */
  totalSteps: number;
}
```

**Renders**: Row of dots. Active dot: gold with `celestial-pulse-glow`. Completed: solid gold. Upcoming: muted border.

---

## SpotlightTour

**File**: `solune/frontend/src/components/onboarding/SpotlightTour.tsx`

```typescript
interface SpotlightTourProps {
  /** Sidebar collapsed state — tour expands sidebar for sidebar steps */
  isSidebarCollapsed: boolean;
  /** Toggle sidebar collapse */
  onToggleSidebar: () => void;
}
```

**Renders**: Composes `SpotlightOverlay`, `SpotlightTooltip`, and `useOnboarding` hook.  
**Mount point**: Inside `AppLayout`, after `ChatPopup`.  
**Step definitions**: Static array of 9 `TourStep` objects defined within this component.  
**Keyboard**: Escape → skip, ArrowRight → next, ArrowLeft → back.
