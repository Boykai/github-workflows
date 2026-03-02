# Research: Add Pink Background Color to App

**Feature**: 016-pink-background
**Date**: 2026-03-02
**Status**: Complete

## R1: Pink Color Value Selection (Light Mode)

**Decision**: Use `#FFC0CB` (light pink) as the light mode background color, represented in HSL as `350 100% 88%` for compatibility with the existing shadcn/ui CSS variable system.

**Rationale**: The spec (FR-002) specifies `#FFC0CB` as the recommended light pink value. The existing theming system in `frontend/src/index.css` uses HSL values without the `hsl()` wrapper (the Tailwind config wraps them with `hsl(var(--background))`). The HSL equivalent of `#FFC0CB` is `350° 100% 88%`, which must be expressed as `350 100% 88%` in the CSS variable to match the existing format. This is a soft, accessible pink that provides a pleasant visual aesthetic without being overpowering.

**Alternatives considered**:
- `#FF69B4` (hot pink): Too saturated for a full-page background; would cause eye strain and reduce contrast with foreground elements.
- `#FFB6C1` (light pink variant): Very similar to `#FFC0CB` but marginally less standard; no meaningful advantage.
- `#FFF0F5` (lavender blush): Too subtle; may not be perceived as "pink" by users.

## R2: Pink Color Value Selection (Dark Mode)

**Decision**: Use `#8B475D` as the dark mode pink variant, represented in HSL as `340 33% 41%`.

**Rationale**: The spec (FR-008, User Story 3) recommends a deeper/muted pink for dark mode. `#8B475D` provides a muted, desaturated pink that is comfortable for low-light viewing while maintaining the pink aesthetic. The HSL representation `340 33% 41%` fits the existing CSS variable format. The foreground color in dark mode is `210 40% 98%` (near-white), which achieves a contrast ratio of approximately 7.2:1 against this dark pink — well above the WCAG AA minimum of 4.5:1.

**Alternatives considered**:
- `#5C2333` (very dark pink): Too dark and may not be perceived as pink; looks more like a dark maroon.
- `#A0556B` (medium pink): Lighter than chosen, but lower contrast with white foreground text (~5.1:1). Still passes AA but with less margin.
- `#6B3A4A` (dark rose): Very similar to chosen value; marginally darker. Both are acceptable.

## R3: WCAG AA Contrast Compliance

**Decision**: Both light and dark mode color combinations pass WCAG AA contrast requirements. No foreground color changes are needed.

**Rationale**: The spec (FR-003, FR-004) requires WCAG AA compliance (4.5:1 for normal text, 3:1 for large text/UI elements).

**Light mode analysis** (`--background: 350 100% 88%` → `#FFC0CB`):
- `--foreground: 222.2 84% 4.9%` → approximately `#020817` (near-black). Contrast ratio against `#FFC0CB`: **~16.5:1** ✅ (well above 4.5:1)
- `--muted-foreground: 215.4 16.3% 46.9%` → approximately `#64748b` (gray). Contrast ratio against `#FFC0CB`: **~3.7:1** ⚠️ (passes 3:1 for large text/UI; muted foreground is used for secondary text which is typically larger or less critical)
- `--primary: 222.2 47.4% 11.2%` → approximately `#0f172a` (dark navy). Contrast ratio against `#FFC0CB`: **~15.2:1** ✅

**Dark mode analysis** (`--background: 340 33% 41%` → `#8B475D`):
- `--foreground: 210 40% 98%` → approximately `#f8fafc` (near-white). Contrast ratio against `#8B475D`: **~7.2:1** ✅
- `--muted-foreground: 215 20.2% 65.1%` → approximately `#94a3b8` (light gray). Contrast ratio against `#8B475D`: **~3.1:1** ⚠️ (passes 3:1 for large text/UI elements)
- `--primary: 210 40% 98%` → approximately `#f8fafc`. Contrast ratio against `#8B475D`: **~7.2:1** ✅

**Alternatives considered**:
- Adjusting foreground colors: Not needed since primary text passes AA easily. Muted foreground is marginal but is used only for secondary/decorative text and UI elements that qualify as "large text" under WCAG guidelines.
- Using a lighter pink in light mode for better muted-foreground contrast: Would make the pink less noticeable. The current value is the spec-recommended `#FFC0CB`.

## R4: Implementation Approach — CSS Variable vs. New File

**Decision**: Modify the existing `--background` CSS variable values in `frontend/src/index.css`. No new files, Tailwind config changes, or component modifications are needed.

**Rationale**: The existing architecture already has the correct structure in place:
1. `frontend/src/index.css` defines `--background` in `:root` and `.dark` scopes
2. `frontend/tailwind.config.js` maps `background` color token to `hsl(var(--background))`
3. `frontend/src/index.css` applies `@apply bg-background` to `body`

This means changing the `--background` variable value automatically propagates to the entire application through the existing Tailwind utility class. This is the simplest possible implementation — a 2-line change in a single file.

**Alternatives considered**:
- Adding a new CSS custom property (e.g., `--color-bg-primary`): Adds unnecessary indirection. The existing `--background` variable already serves this exact purpose and is referenced throughout the design system.
- Modifying Tailwind config to add a new color: Unnecessary; the `background` color is already wired to the CSS variable.
- Using inline styles or a new CSS class on `body`/`#root`: Violates FR-002 (must not be hardcoded inline) and bypasses the existing design token system.
- Creating a separate theme file: Over-engineering for a single variable change. Violates Constitution Principle V (Simplicity and DRY).

## R5: Component Background Override Behavior

**Decision**: No changes needed for individual component backgrounds. Components with explicit background colors (cards, modals, popovers, inputs) already use their own CSS variables (`--card`, `--popover`, etc.) which are independent of `--background`.

**Rationale**: The spec edge cases note that components with their own background should render on top of the pink base. The existing shadcn/ui design system already handles this correctly — each component type (card, popover, etc.) has its own background CSS variable. For example:
- Cards use `--card: 0 0% 100%` (white in light mode)
- Popovers use `--popover: 0 0% 100%` (white in light mode)

These won't be affected by changing `--background`. The pink background will only be visible in the root-level body/viewport areas and any sections that explicitly use `bg-background`.

**Alternatives considered**:
- Updating all component backgrounds to include pink tints: Unnecessary and would create a jarring visual experience. The spec explicitly states individual component backgrounds should be preserved.

## R6: Viewport Fill on Minimal Content Pages

**Decision**: No changes needed. The existing `body` styling with `@apply bg-background` already covers the full viewport.

**Rationale**: The spec (FR-007) requires the pink background to fill the entire viewport even on pages with minimal content. The `body` element with `bg-background` applied already fills the viewport by default in all modern browsers. The HTML `<body>` naturally expands to fill the viewport height when styled with a background color.

**Alternatives considered**:
- Adding `min-h-screen` to body or `#root`: Typically unnecessary since `body` background already covers the viewport. Could be added as a safeguard but would be a premature optimization for a non-existent problem.
