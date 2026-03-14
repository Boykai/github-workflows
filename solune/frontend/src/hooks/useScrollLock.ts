/**
 * useScrollLock — centralized scroll-lock hook with reference-counting.
 *
 * Multiple modal components can independently request a scroll lock by calling
 * `useScrollLock(true)`. A module-level counter tracks how many consumers
 * currently hold a lock. `document.body.style.overflow` is set to `'hidden'`
 * when the first lock is acquired and restored to its original value only when
 * the **last** lock is released.
 *
 * This eliminates the race condition where independent modals each set/reset
 * `overflow` on open/close, potentially leaving the body in an inconsistent
 * scroll state when modals overlap or close in an unexpected order.
 *
 * @example
 * ```tsx
 * import { useScrollLock } from '@/hooks/useScrollLock';
 *
 * // Always locked while mounted (modal rendered only when open)
 * function MyModal() {
 *   useScrollLock(true);
 *   return <div>…</div>;
 * }
 *
 * // Conditionally locked based on open state
 * function MyDialog({ isOpen }: { isOpen: boolean }) {
 *   useScrollLock(isOpen);
 *   if (!isOpen) return null;
 *   return <div>…</div>;
 * }
 * ```
 */
import { useEffect } from 'react';

let lockCount = 0;
let originalOverflow = '';
let lockedElement: HTMLElement | null = null;

/**
 * Returns the app's primary scroll container.
 * The SPA uses `<main>` (overflow-auto) as the scroll container, not the body.
 * Locking `<main>` directly prevents background scroll while a modal is open,
 * and avoids the CSS viewport-propagation side-effect of locking `body`
 * (browsers propagate body.overflow to the viewport when html.overflow is
 * default/visible, which can freeze overscroll at `<main>`'s boundaries).
 */
function getScrollContainer(): HTMLElement {
  return (document.querySelector('main') as HTMLElement | null) ?? document.body;
}

export function useScrollLock(isLocked: boolean): void {
  useEffect(() => {
    if (!isLocked) return;

    if (lockCount === 0 || lockedElement == null) {
      lockedElement = getScrollContainer();
      originalOverflow = lockedElement.style.overflow;
    }

    const el = lockedElement;
    lockCount++;
    el.style.overflow = 'hidden';

    return () => {
      lockCount = Math.max(0, lockCount - 1);
      if (lockCount === 0) {
        el.style.overflow = originalOverflow;
        if (lockedElement === el) {
          lockedElement = null;
        }
      }
    };
  }, [isLocked]);
}

/**
 * @internal Test-only reset function. Do not use in production code.
 * Allows resetting module state between tests.
 */
export function _resetForTesting(): void {
  lockCount = 0;
  originalOverflow = '';
  lockedElement = null;
  document.body.style.overflow = '';
  const mainEl = document.querySelector('main') as HTMLElement | null;
  if (mainEl) mainEl.style.overflow = '';
}
