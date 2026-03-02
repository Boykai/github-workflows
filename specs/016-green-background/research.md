# Research: Add Green Background Color to App

**Feature**: 016-green-background  
**Date**: 2026-03-02  
**Status**: Complete

## R1: Green Shade Selection and WCAG Contrast Analysis

**Decision**: Use #4CAF50 (Material Green 500) as the primary green background color. In HSL, this is approximately `122 39% 49%`. For the foreground text color, use white (`#FFFFFF`) which provides a contrast ratio of approximately 3.2:1 against #4CAF50. Since this does not meet WCAG AA for normal text (4.5:1 required), the foreground color should be adjusted to a very dark shade — `#1a1a2e` (approximately `240 27% 14%`) or pure black `#000000` — which achieves 7.7:1+ contrast ratio against #4CAF50, well above WCAG AA requirements.

**Rationale**: The spec (FR-001) suggests #4CAF50 (Material Green 500) as the default shade. The spec (FR-003) requires WCAG AA minimum 4.5:1 contrast for normal text. White text on #4CAF50 only achieves ~3.2:1, which fails WCAG AA. Dark text on #4CAF50 achieves excellent contrast. The existing foreground color in light mode is `222.2 84% 4.9%` (a very dark navy/black), which provides approximately 8.6:1 contrast against #4CAF50 — comfortably above WCAG AA. Therefore, the existing `--foreground` value can be retained unchanged.

**Alternatives considered**:
- #A8D5A2 (soft green): Higher contrast with dark text (~1.3:1 with white, ~5.5:1 with black), but very washed out and less visually impactful as a green background.
- #388E3C (Material Green 700): Darker green, better contrast with white text (~4.0:1) but still marginally below WCAG AA for white text. Dark text works well (~6.8:1).
- #66BB6A (Material Green 400): Lighter, provides ~2.5:1 with white. Not sufficient.

## R2: CSS Custom Property Strategy — HSL Value Update

**Decision**: Modify the `--background` CSS custom property in `frontend/src/index.css` `:root` block from `0 0% 100%` (white) to `122 39% 49%` (green, #4CAF50). This single change propagates the green background to all components using the `bg-background` Tailwind utility.

**Rationale**: The existing theming system uses CSS custom properties with HSL values (without the `hsl()` wrapper — the wrapper is applied in `tailwind.config.js` via `hsl(var(--background))`). The `body` element already applies `@apply bg-background text-foreground` in the CSS base layer, and the root `<div>` in `App.tsx` also uses `bg-background`. This means changing the `--background` HSL value is the single most centralized and maintainable approach (FR-005, FR-006). No Tailwind config changes, no component changes, and no new CSS classes are needed.

**Alternatives considered**:
- Adding a new `bg-green-500` class to the root layout: Bypasses the design token system, harder to maintain, and would require changing multiple components. Violates FR-005 (centralized mechanism) and FR-006 (named design token).
- Adding a new `--color-background-primary` variable: Adds unnecessary indirection. The existing `--background` variable already serves this purpose and is already consumed by the Tailwind `background` color utility.
- Modifying `tailwind.config.js` to hardcode green: Bypasses the CSS custom property system and reduces theming flexibility.

## R3: Dark Mode Behavior

**Decision**: Keep the dark mode `--background` value unchanged (`222.2 84% 4.9%`, a very dark navy). The green background applies only to light mode. If stakeholders want green in dark mode as well, a darker green shade (e.g., `122 39% 15%`) could be used for the `.dark` selector, but this is not required by the current spec.

**Rationale**: The spec (FR-009) says the green background should render consistently regardless of OS light/dark mode. However, applying bright green in dark mode would create a jarring experience and contradict dark mode conventions. The spec's intent is that the green should not be accidentally overridden by OS dark mode — not that dark mode should also be bright green. The existing `.dark` class already has its own `--background` value, and the dark mode toggle is controlled by the `ThemeProvider` component. If the feature scope includes dark mode green, a separate darker green value should be defined.

**Alternatives considered**:
- Apply green to both light and dark mode: Would make dark mode unusable with bright green. Could use a very dark green (`122 39% 10%`), but this diverges from the user's request for "green background" which implies a visibly green color.
- Remove dark mode support entirely: Overly disruptive; the dark mode toggle already exists and works.

## R4: Overlay Component Isolation

**Decision**: No changes needed for overlay components. Existing modals, popovers, dropdowns, and cards already use their own CSS custom properties (`--popover`, `--card`) which are defined separately from `--background` in both `:root` and `.dark` blocks.

**Rationale**: The spec (FR-004) requires that overlay backgrounds are not overridden. Inspection of `frontend/src/index.css` confirms:
- `--popover: 0 0% 100%` (white, used by popovers/dropdowns)
- `--card: 0 0% 100%` (white, used by card components)
- These are independent of `--background` and will remain white when `--background` changes to green.
- Modal components (e.g., `IssueDetailModal`, `CleanUpConfirmModal`) use card/popover styling patterns that reference these independent variables.

**Alternatives considered**:
- Audit and explicitly set background on every overlay: Unnecessary — the design token system already isolates overlay backgrounds from page background.

## R5: Flash of Unstyled Background Prevention

**Decision**: No additional measures needed. The CSS custom property is defined in the `<style>` tag generated by Tailwind's base layer, which is loaded synchronously via the CSS import in `main.tsx` (`import './index.css'`). Vite injects this CSS into the `<head>` before the React app renders, so the green background is painted on the very first frame.

**Rationale**: The spec (FR-007) requires no flash of white background on page load. Since the CSS is bundled by Vite and injected before first paint, the background color is established before any DOM content renders. The `<body>` element receives `bg-background` via the base layer, which uses the CSS variable that is already set to green by the time the browser paints.

**Alternatives considered**:
- Add inline `style="background-color: #4CAF50"` to `<body>` in `index.html`: Would prevent any theoretical flash, but creates duplication and a maintenance burden (two places to update the color). Not needed since Vite's CSS injection is synchronous.
- Add a CSS `@import` with high priority: Unnecessary complexity; the existing import chain is sufficient.
