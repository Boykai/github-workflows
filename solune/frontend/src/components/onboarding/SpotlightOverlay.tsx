/**
 * SpotlightOverlay — full-viewport translucent backdrop with CSS clip-path cutout.
 * Renders a rectangular hole around the target element for the spotlight tour.
 */

interface SpotlightOverlayProps {
  targetRect: DOMRect | null;
  isVisible: boolean;
}

export function SpotlightOverlay({ targetRect, isVisible }: SpotlightOverlayProps) {
  if (!isVisible) return null;

  const clipPath = targetRect
    ? buildClipPath(targetRect)
    : undefined;

  return (
    <div
      className="fixed inset-0 z-[100] bg-background/70 dark:bg-[hsl(var(--night,230_25%_10%)/0.6)] motion-safe:transition-[clip-path] motion-safe:duration-500 motion-safe:ease-in-out"
      style={{ clipPath }}
      aria-hidden="true"
    />
  );
}

const PADDING = 8;
const RADIUS = 8;

function buildClipPath(rect: DOMRect): string {
  const top = Math.max(0, rect.top - PADDING);
  const left = Math.max(0, rect.left - PADDING);
  const bottom = rect.bottom + PADDING;
  const right = rect.right + PADDING;

  // Outer rectangle covers viewport, inner rectangle is the cutout
  // Using polygon with 8 points to create the hole (clockwise outer, counter-clockwise inner)
  return `polygon(
    0% 0%, 100% 0%, 100% 100%, 0% 100%, 0% 0%,
    ${left}px ${top + RADIUS}px,
    ${left + RADIUS}px ${top}px,
    ${right - RADIUS}px ${top}px,
    ${right}px ${top + RADIUS}px,
    ${right}px ${bottom - RADIUS}px,
    ${right - RADIUS}px ${bottom}px,
    ${left + RADIUS}px ${bottom}px,
    ${left}px ${bottom - RADIUS}px,
    ${left}px ${top + RADIUS}px
  )`;
}
