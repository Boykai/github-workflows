# Research: Fix Screen Scrolling Getting Stuck Intermittently

## R1: Root Cause of Intermittent Scroll Freezing

**Task**: Determine the root cause of scroll becoming unresponsive across the application.

**Decision**: The primary root cause is a **modal scroll-lock race condition**. Six modal components independently manipulate `document.body.style.overflow`:

| Component | On Open | On Close | Bug |
|-----------|---------|----------|-----|
| `IssueDetailModal.tsx` | Sets `'hidden'` | Sets `''` | ⚠️ Resets to empty string |
| `CleanUpConfirmModal.tsx` | Sets `'hidden'` | Sets `''` | ⚠️ Resets to empty string |
| `CleanUpSummary.tsx` | Sets `'hidden'` | Sets `''` | ⚠️ Resets to empty string |
| `CleanUpAuditHistory.tsx` | Sets `'hidden'` | Sets `''` | ⚠️ Resets to empty string |
| `AgentIconPickerModal.tsx` | Sets `'hidden'` | Restores previous | ✅ Correct |
| `PipelineToolbar.tsx` | Sets `'hidden'` | Restores previous | ✅ Correct |

When multiple modals are open simultaneously or in rapid succession:

1. Modal A opens → sets `document.body.style.overflow = 'hidden'`
2. Modal B opens → sets `document.body.style.overflow = 'hidden'` (overwrites, no stacking)
3. Modal B closes → sets `document.body.style.overflow = ''`
4. **Result**: Modal A is still open, but body overflow is now empty — the page is stuck because the layout expects `overflow: hidden` from the root `h-screen overflow-hidden` container but the body is now in an inconsistent state.

A secondary issue compounds the problem: the root layout container in `AppLayout.tsx` uses `h-screen overflow-hidden` on the outer shell, with the main content area using `overflow-auto`. When `document.body.style.overflow` is toggled between `'hidden'` and `''` by modal open/close, it can temporarily override the layout's intended scroll behavior, causing the `<main>` scrollable area to lose its scroll position or become unscrollable.

**Rationale**: The fix must ensure that `document.body.style.overflow` is only restored when ALL scroll-locking consumers have released their locks. A reference-counting mechanism (similar to how operating systems handle resource locks) solves this cleanly.

**Alternatives Considered**:

- **Per-modal fix (store previous value) (rejected)**: Already implemented in `AgentIconPickerModal` and `PipelineToolbar`, but doesn't handle the case where two modals both store `'hidden'` as their previous value and both try to restore it — the order-of-close still matters and can produce wrong results.
- **CSS-only approach using `overflow: clip` (rejected)**: Would require changing the root layout structure and could introduce regressions with existing scroll-dependent components.
- **Using a third-party library like `body-scroll-lock` (rejected)**: Adds an external dependency for a problem that can be solved with ~30 lines of shared code. Violates Constitution V (Simplicity).

## R2: Centralized Scroll Lock Strategy

**Task**: Determine the best architectural approach to manage scroll locking across all modal components.

**Decision**: Create a `useScrollLock` custom hook in `frontend/src/hooks/useScrollLock.ts` that uses a module-level reference counter:

```typescript
// Module-level state (singleton across all hook instances)
let lockCount = 0;
let originalOverflow = '';

export function useScrollLock(isLocked: boolean): void {
  useEffect(() => {
    if (!isLocked) return;

    if (lockCount === 0) {
      originalOverflow = document.body.style.overflow;
    }
    lockCount++;
    document.body.style.overflow = 'hidden';

    return () => {
      lockCount--;
      if (lockCount === 0) {
        document.body.style.overflow = originalOverflow;
      }
    };
  }, [isLocked]);
}
```

Each modal calls `useScrollLock(isOpen)`. When the first modal opens, the hook saves the original overflow and sets `'hidden'`. When subsequent modals open, the counter increments but no additional work is done. When modals close, the counter decrements. Only when the last modal closes does the hook restore the original overflow value.

**Rationale**: This pattern is simple (Constitution V), DRY (replaces 6 independent implementations), and handles all ordering edge cases (FIFO, LIFO, random close order). The module-level counter is intentional — it must be shared across all component instances, not per-component.

**Alternatives Considered**:

- **React Context provider (rejected)**: Would require wrapping the app in a `ScrollLockProvider` and would be heavier than necessary. The module-level counter achieves the same result without any provider hierarchy changes.
- **CSS class toggle (`body.scroll-locked`) (rejected)**: Would work for a single lock level but doesn't handle nesting. Also mixes concerns — the lock logic should be in JS, not CSS.
- **Event-based system with EventEmitter (rejected)**: Over-engineered for a simple counter. Violates YAGNI.

## R3: Scroll Event Listener Performance

**Task**: Determine whether capture-phase scroll event listeners contribute to scroll freezing.

**Decision**: Four components use `window.addEventListener('scroll', handler, true)` (capture phase) for popover repositioning: `NotificationBell.tsx`, `AddAgentPopover.tsx`, `ModelSelector.tsx`, and `StageCard.tsx`. These listeners fire on every scroll event and trigger DOM reads (`getBoundingClientRect()`) which can cause layout thrashing. While not the primary cause of scroll "sticking", they contribute to scroll jank.

The fix adds `{ capture: true, passive: true }` to these listeners. Passive listeners cannot call `preventDefault()`, which tells the browser it's safe to scroll immediately without waiting for the handler to complete. None of these handlers call `preventDefault()`, so adding `passive` is safe and improves scroll performance.

**Rationale**: `passive: true` is a zero-risk performance improvement for listeners that don't prevent default behavior. It is recommended by Chrome DevTools and Lighthouse for scroll handlers.

**Alternatives Considered**:

- **Throttling/debouncing scroll handlers (rejected for now)**: Would add complexity and might cause popover positioning to visibly lag. The `passive` flag achieves the performance goal without visible side effects.
- **Using `IntersectionObserver` or `ResizeObserver` instead (rejected)**: These APIs don't directly replace the "reposition on scroll" use case. Would require significant refactoring of the popover positioning logic.
- **Removing capture phase (rejected)**: The capture phase is intentional — it allows the popover to reposition before the scroll event reaches the target element. Removing it could cause visual glitches.

## R4: @dnd-kit Interaction with Scroll Lock

**Task**: Determine whether the @dnd-kit drag-and-drop library interacts with scroll locking in a way that causes freezing.

**Decision**: The @dnd-kit library in `AgentConfigRow.tsx` uses default auto-scroll behavior during drag operations. When `document.body.style.overflow = 'hidden'` is set (e.g., a modal is open), @dnd-kit's auto-scroll cannot detect the scrollable container correctly because the body overflow is locked. However, this is a niche scenario — drag-and-drop is only used on the agents page and would only conflict with scroll locking if a modal opens during a drag operation, which is unlikely in practice.

No changes needed for @dnd-kit. The centralized `useScrollLock` hook resolves the underlying overflow state inconsistency, which indirectly fixes any @dnd-kit confusion about scrollable containers.

**Rationale**: Fixing the root cause (modal scroll-lock race condition) eliminates the downstream effect on @dnd-kit. Adding @dnd-kit-specific scroll configuration would be premature optimization for an unlikely scenario.

**Alternatives Considered**:

- **Explicit `autoScroll` configuration for @dnd-kit (rejected)**: Would add complexity without addressing a real user-facing problem.
- **Disabling drag during modal open (rejected)**: Modals already overlay the drag targets, making this unnecessary.

## R5: Cross-Browser Scroll Behavior Differences

**Task**: Determine if the scroll freeze is browser-specific or universal.

**Decision**: The `document.body.style.overflow` manipulation affects all browsers identically — Chrome, Firefox, and Safari all honor the `overflow` property on the body element. The race condition described in R1 manifests identically across browsers. However, there are minor differences:

- **Safari (iOS)**: Safari has a known issue where `overflow: hidden` on the body does not prevent scroll on iOS. The recommended workaround is to also set `position: fixed` on the body and restore the scroll position on unlock. However, this is a pre-existing limitation and is out of scope for this fix (the current implementation matches the existing behavior).
- **Firefox**: No specific differences.
- **Chrome**: No specific differences.

The fix (centralized `useScrollLock`) is browser-agnostic and resolves the race condition on all platforms.

**Rationale**: The race condition is a logic bug in the application code, not a browser compatibility issue. The fix is browser-agnostic.

**Alternatives Considered**:

- **iOS-specific body scroll lock with `position: fixed` (rejected for now)**: Out of scope — the spec asks to fix intermittent scroll freezing, not to improve iOS scroll-lock behavior. This could be addressed in a separate enhancement.

## R6: handleKeyDown Dependency in useEffect Causing Re-Registration

**Task**: Investigate whether `handleKeyDown` as a `useEffect` dependency causes scroll-lock flickering.

**Decision**: Several modal components (e.g., `IssueDetailModal.tsx`, `CleanUpConfirmModal.tsx`) include `handleKeyDown` in their `useEffect` dependency array for the scroll-lock effect. If `handleKeyDown` is not memoized with `useCallback`, it is recreated on every render, causing the useEffect to re-run — which means the cleanup function runs (resetting `document.body.style.overflow` to `''`) and the effect re-runs (setting it back to `'hidden'`). This creates a brief flicker where overflow is `''`, which can cause a momentary scroll jump.

With the centralized `useScrollLock` hook, this issue is eliminated because the hook depends only on `[isLocked]` (a boolean), which doesn't change between renders unless the modal's open state changes. The keydown listener registration should be separated into its own `useEffect` with appropriate dependencies.

**Rationale**: Separating concerns (scroll lock in one effect, keydown handling in another) is cleaner and avoids the re-registration problem. The `useScrollLock` hook encapsulates the scroll lock concern completely.

**Alternatives Considered**:

- **Memoizing `handleKeyDown` with `useCallback` (partial fix, rejected)**: Would reduce the re-registration frequency but doesn't address the underlying coupling between keyboard handling and scroll locking.
- **Using `eslint-disable` for the dependency (rejected)**: Suppresses the warning without fixing the problem.
