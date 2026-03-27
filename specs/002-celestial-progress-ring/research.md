# Research: Celestial Loading Progress Ring

**Feature**: 002-celestial-progress-ring  
**Date**: 2026-03-27  
**Status**: Complete — all unknowns resolved

---

## Research Task 1: SVG Circular Progress Ring Technique

**Unknown**: Best approach for rendering a circular progress ring with smooth CSS-driven fill.

**Decision**: Use SVG `<circle>` with `stroke-dasharray` and `stroke-dashoffset`, animated via CSS `transition` property.

**Rationale**: This is the standard, well-supported technique for SVG circular progress indicators. The ring is drawn as a circle with `stroke-dasharray` set to the circle's circumference. Progress is controlled by adjusting `stroke-dashoffset` — a value of `circumference` means 0% fill, and `0` means 100% fill. CSS `transition: stroke-dashoffset 0.6s ease` provides smooth animation without any JavaScript animation loop.

**Formula**:
```
circumference = 2 × π × radius
offset = circumference × (1 - progress)
```

Where `progress` is a value from 0 to 1.

**Alternatives considered**:
- **Canvas-based ring**: Rejected — requires JS animation loop, harder to style with CSS tokens, no CSS transitions
- **CSS `conic-gradient` on a `<div>`**: Rejected — less semantic, harder to apply gradient strokes, poor SVG interop for embedding CelestialLoader
- **Third-party library (e.g., react-circular-progressbar)**: Rejected — adds dependency for a simple SVG pattern; violates simplicity principle

---

## Research Task 2: Time-Based Minimum Progress Animation

**Unknown**: Best pattern for a time-based progress floor that runs in parallel with real completions.

**Decision**: Use a `useEffect` with `setInterval` (every ~100ms) incrementing a `minProgress` state variable from 0 to 0.15 over 3 seconds, continuing to cap at 0.30.

**Rationale**: This mirrors the "fake progress" pattern used by GitHub's loading bar, Vercel's deployment progress, and Linear's page transitions. The interval provides smooth visual increments. The cap at 30% prevents misleading users if real completions are slow. The `max(minProgress, realProgress)` formula ensures real completions always jump past the floor.

**Implementation pattern**:
```typescript
const [minProgress, setMinProgress] = useState(0);

useEffect(() => {
  const start = Date.now();
  const id = setInterval(() => {
    const elapsed = Date.now() - start;
    if (elapsed <= 3000) {
      // 0 → 0.15 over 3 seconds (linear interpolation)
      setMinProgress(Math.min(0.15, elapsed / 3000 * 0.15));
    } else {
      // 3s–∞: continue toward cap of 0.30, slower rate
      setMinProgress((prev) => Math.min(0.30, prev + 0.001));
    }
  }, 100);
  return () => clearInterval(id);
}, []);
```

**Alternatives considered**:
- **`requestAnimationFrame` loop**: Rejected — overkill for ~10 updates/second; `setInterval` is simpler and sufficient since the ring itself uses CSS transitions
- **CSS-only animation on `stroke-dashoffset`**: Rejected — can't synchronize with React state for the `max()` computation
- **Single `setTimeout` chain**: Rejected — less predictable timing, harder to clean up

---

## Research Task 3: Gold Gradient Stroke on SVG Ring

**Unknown**: How to apply a gradient stroke to an SVG circle using existing design tokens.

**Decision**: Use an SVG `<linearGradient>` (or `<radialGradient>`) defined in `<defs>`, referenced via `stroke="url(#ring-gradient)"`. Colors use the existing `--gold` and `--primary` CSS custom properties.

**Rationale**: SVG gradients are the standard way to apply multi-color strokes. Using CSS custom properties (`hsl(var(--gold))`, `hsl(var(--primary))`) ensures the gradient respects the theme's design tokens and adapts to dark/light mode. The gradient is defined once in the SVG `<defs>` block and referenced by ID.

**Implementation**:
```xml
<defs>
  <linearGradient id="celestial-ring-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" stopColor="hsl(var(--gold))" />
    <stop offset="100%" stopColor="hsl(var(--primary))" />
  </linearGradient>
</defs>
<circle stroke="url(#celestial-ring-gradient)" ... />
```

**Alternatives considered**:
- **Solid gold stroke**: Rejected — spec explicitly calls for gold/primary gradient
- **CSS `stroke` with `linear-gradient()`**: Not supported — SVG strokes require `<linearGradient>` definitions
- **Multiple overlapping circles**: Rejected — overly complex for a simple gradient

---

## Research Task 4: Embedding CelestialLoader Inside SVG Ring

**Unknown**: How to embed a React component (CelestialLoader) centered inside an SVG circle without modifying CelestialLoader.tsx.

**Decision**: Use SVG `<foreignObject>` to embed the CelestialLoader HTML content inside the SVG, centered within the ring.

**Rationale**: `<foreignObject>` is the standard SVG element for embedding HTML content within an SVG document. It allows the existing CelestialLoader (which renders HTML `<div>` elements) to be placed inside the SVG without any modifications. The `<foreignObject>` is sized and positioned to center its content within the ring.

**Implementation**:
```xml
<foreignObject x={cx - loaderSize/2} y={cy - loaderSize/2} width={loaderSize} height={loaderSize}>
  <CelestialLoader size="lg" label="Loading…" />
</foreignObject>
```

**Alternatives considered**:
- **Absolute positioning outside SVG**: Viable but creates z-index complexity and requires manual centering relative to SVG viewBox
- **Recreating CelestialLoader as SVG elements**: Rejected — violates requirement not to modify CelestialLoader.tsx and would duplicate component logic
- **Using a wrapper `<div>` with CSS overlay**: Viable alternative, but `<foreignObject>` keeps the visual hierarchy within a single SVG element

**Note**: After further review, using a wrapper `<div>` with CSS `position: absolute` overlay is actually simpler and more reliable across browsers than `<foreignObject>`. `<foreignObject>` can have inconsistent behavior in some browsers. The recommended approach is to wrap the entire component in a `relative` container and place both the SVG ring and the CelestialLoader as siblings with the loader absolutely centered.

**Revised Decision**: Use a `<div className="relative">` container with the SVG ring and the CelestialLoader as siblings. The CelestialLoader is absolutely positioned and centered using `absolute inset-0 flex items-center justify-center`.

---

## Research Task 5: Accessibility for SVG Progress Rings

**Unknown**: Correct ARIA attributes for an SVG-based circular progress indicator.

**Decision**: Apply `role="progressbar"`, `aria-valuenow`, `aria-valuemin="0"`, `aria-valuemax="100"` on the SVG element. The `aria-valuenow` reflects the computed progress percentage (0–100).

**Rationale**: WAI-ARIA 1.2 specifies `role="progressbar"` for elements that display progress. The `aria-valuenow` attribute must reflect the current value as a number. Since the visual progress is a percentage, `aria-valuemin="0"` and `aria-valuemax="100"` define the range, and `aria-valuenow` is the current percentage rounded to the nearest integer.

**Implementation**:
```xml
<svg
  role="progressbar"
  aria-valuenow={Math.round(progress * 100)}
  aria-valuemin={0}
  aria-valuemax={100}
  aria-label="Loading progress"
>
```

**Alternatives considered**:
- **`aria-valuetext` with phase label**: Could be added for richer screen reader announcements, but `aria-valuenow` is the minimum required attribute per spec
- **`role="status"` with live region**: The existing CelestialLoader uses `role="status"` — but the new component is explicitly a progress indicator, so `role="progressbar"` is more semantically correct

---

## Research Task 6: Dark Mode Visibility for Gold Ring

**Unknown**: Ensuring gold ring and twinkling stars are visible in dark mode.

**Decision**: The existing `--gold` and `--glow` CSS custom properties already have dark-mode-aware values defined in `index.css`. The gold gradient and glow effects will automatically adapt. No additional dark mode overrides are needed.

**Rationale**: The codebase already uses HSL-based CSS custom properties (`--gold`, `--glow`, `--primary`) that are defined with theme-appropriate values. The existing `celestial-pulse-glow`, `celestial-twinkle`, and glow box-shadows all use these tokens and are already visible in dark mode (as verified by existing CelestialLoader usage). The new `.celestial-ring-glow` class uses `filter: drop-shadow()` with `hsl(var(--gold))`, which inherits the same dark-mode values.

**Alternatives considered**:
- **Explicit `.dark` overrides**: Not needed — design tokens handle theme switching
- **Increased opacity/brightness in dark mode**: Not needed — existing celestial animations are already calibrated for dark backgrounds

---

## Research Task 7: Phase Label Animation Pattern

**Unknown**: Best approach for animating phase label transitions.

**Decision**: Use a React `key` prop tied to the current phase label to trigger the existing `celestial-fade-in` CSS animation class on each label change.

**Rationale**: When React sees a new `key`, it unmounts the old element and mounts a new one, re-triggering any CSS animation applied to it. The existing `celestial-fade-in` class applies `cosmic-fade-in 0.5s ease-out both`, which provides a subtle slide-up + fade-in effect. This requires zero additional CSS or JavaScript.

**Implementation**:
```tsx
<p key={currentPhaseLabel} className="celestial-fade-in text-sm text-muted-foreground">
  {currentPhaseLabel}
</p>
```

**Alternatives considered**:
- **React Transition Group / Framer Motion**: Rejected — adds dependency for a simple animation already available via CSS
- **Manual opacity state management**: Rejected — unnecessary complexity when `key` + CSS handles it
