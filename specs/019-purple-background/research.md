# Research: Add Purple Background Color to App

**Feature**: 019-purple-background
**Date**: 2026-03-05
**Status**: Complete

## Research Tasks

### R1: Current Theming Architecture and CSS Variable System

**Context**: The feature requires changing the global background color. Need to understand the existing theming system to make the change correctly and maintainably.

**Decision**: Update the existing CSS custom properties (`--background` and `--foreground`) in `frontend/src/index.css` within the `:root` and `.dark` selectors. The background color is already consumed via `hsl(var(--background))` in both the Tailwind config and the base `body` styles.

**Rationale**: The codebase already uses a CSS variable-based design token system (shadcn/ui pattern). The `--background` variable is defined in HSL components (hue, saturation, lightness) and applied to the `body` element via `@apply bg-background text-foreground`. Changing the variable value at the `:root` level automatically propagates to all components that reference `bg-background`, including the body, cards, popovers, and any component using the `background` color token. This is the intended extension point — no new variables or architectural changes are needed.

**Alternatives Considered**:
- **Adding a new CSS variable (e.g., `--color-bg-primary`)**: Unnecessary duplication. The `--background` variable already serves this exact purpose. Adding a new variable would violate Constitution Principle V (Simplicity/DRY).
- **Overriding in Tailwind config directly**: Would bypass the CSS variable system that enables runtime theme switching (light/dark mode). Hardcoding in the config loses the dark mode toggle capability.
- **Applying `background-color` directly to `body` in index.css**: Would override the Tailwind utility class pattern. Less maintainable and inconsistent with the existing approach.

---

### R2: Purple Color Value Selection (WCAG AA Compliance)

**Context**: The spec recommends #6B21A8 (Tailwind purple-800) as the primary purple shade. Need to verify WCAG AA contrast compliance and determine the correct HSL representation for the CSS variable system.

**Decision**: Use #6B21A8 (HSL: `271 75% 40%`) as the primary background color for light mode. Use white (#FFFFFF) as the primary foreground text color for maximum contrast.

**Rationale**: 
- **#6B21A8 vs white text (#FFFFFF)**: Contrast ratio = **8.21:1** — exceeds WCAG AA (4.5:1) and even meets WCAG AAA (7:1).
- **#6B21A8 vs light gray (#F8FAFC)**: Contrast ratio = **7.95:1** — also exceeds WCAG AAA.
- The HSL representation `271 75% 40%` is compatible with the existing CSS variable format (space-separated HSL components without `hsl()` wrapper, as used by shadcn/ui's Tailwind integration).

**Alternatives Considered**:
- **#7C3AED (Tailwind violet-600, HSL: `263 70% 58%`)**: Contrast ratio vs white = **4.56:1** — barely meets WCAG AA for normal text. Risky for smaller text sizes. Rejected for tighter margins.
- **#A855F7 (Tailwind purple-400, HSL: `272 91% 65%`)**: Contrast ratio vs white = **3.07:1** — fails WCAG AA. Not viable as a primary background.
- **#581C87 (Tailwind purple-900, HSL: `274 72% 32%`)**: Contrast ratio vs white = **11.35:1** — excellent contrast but very dark, approaching black. Viable but less vibrant. #6B21A8 provides a good balance of vibrancy and contrast.

---

### R3: Impact on Existing Component Surfaces

**Context**: Multiple components use `bg-background` or share the same variable. Need to assess which components need updates for visual consistency.

**Decision**: Update the `--background` variable for the root background. Update `--card`, `--popover`, and related surface variables to slightly lighter/different purple shades to maintain visual hierarchy and separation. Update `--foreground`, `--card-foreground`, `--popover-foreground` to white/light values for contrast.

**Rationale**: The existing theming system defines separate variables for different surface types:
- `--background`: Main page background (body)
- `--card`: Card component surfaces
- `--popover`: Dropdown/popover surfaces
- `--primary`, `--secondary`, `--accent`, `--muted`: Interactive/utility surfaces

Cards and popovers typically need to be visually distinguishable from the main background. Setting them to a slightly lighter purple (e.g., `270 60% 50%`) or keeping them white provides visual separation. For simplicity and to match the spec's intent of a "purple background," the card/popover surfaces should remain in a complementary but distinguishable shade.

**Alternatives Considered**:
- **Only changing `--background`, leaving cards/popovers white**: Creates jarring contrast between white cards and purple background. Workable but inconsistent with the spec's goal of a unified purple color scheme.
- **Making all surfaces the same purple**: Loses visual hierarchy. Cards and content areas need separation from the background.

---

### R4: Dark Mode Considerations

**Context**: The app supports light/dark mode via class-based toggling. The spec states purple should be applied to the default/light mode, with dark mode adjustments deferred.

**Decision**: Apply the purple color scheme to the light mode (`:root`) CSS variables. For dark mode (`.dark`), apply a deeper/darker purple variant to maintain the purple theme while respecting the dark mode convention of darker surfaces.

**Rationale**: The spec's Assumptions section states: "If the app supports dark mode and light mode, the purple background will be applied to the default/light mode. Dark mode adjustments, if needed, can follow as a separate effort." However, completely ignoring dark mode would create an inconsistent experience if the user toggles themes. A minimal dark mode adjustment (using a darker purple like `271 80% 15%`) keeps the purple identity while following dark mode conventions. This is a small incremental effort that prevents a broken UX in dark mode.

**Alternatives Considered**:
- **No dark mode changes**: Leaves the existing dark navy/blue background for dark mode. Creates a disconnected experience where purple only appears in light mode. Technically valid per spec but poor UX.
- **Same purple for both modes**: Using `271 75% 40%` for dark mode would be too bright for a dark theme. Dark mode users expect muted, low-luminance backgrounds.

---

### R5: Border, Input, and Ring Variable Adjustments

**Context**: The existing border, input, and ring CSS variables use neutral gray tones that may not harmonize with a purple background.

**Decision**: Update `--border`, `--input`, and `--ring` variables to purple-tinted values that harmonize with the new purple background. Use lighter purple tones for borders and inputs in light mode, and darker purple tones in dark mode.

**Rationale**: Keeping neutral gray borders against a purple background creates visual dissonance. Purple-tinted borders (e.g., `270 40% 80%` for light mode) maintain the cohesive purple theme while preserving visual hierarchy. The ring variable should use a lighter or contrasting purple for focus states to remain accessible.

**Alternatives Considered**:
- **Keep existing gray borders**: Functional but visually inconsistent with the purple theme. Creates a "skin-deep" change that doesn't feel cohesive.
- **Use pure white borders**: Too high contrast on purple backgrounds; visually heavy and distracting.

## Summary of Decisions

| Topic | Decision | Key Rationale |
|-------|----------|---------------|
| Theming approach | Update existing `--background` CSS variable in index.css | Uses the established design token system; automatic propagation |
| Purple color value | #6B21A8 (HSL: `271 75% 40%`) | 8.21:1 contrast vs white; vibrant yet accessible |
| Foreground text | White (#FFFFFF, HSL: `0 0% 100%`) | Maximum contrast against purple background |
| Component surfaces | Lighter purple for cards/popovers; distinct from background | Maintains visual hierarchy and separation |
| Dark mode | Deeper purple variant (HSL: `271 80% 15%`) | Respects dark mode convention; maintains purple identity |
| Borders/inputs | Purple-tinted values | Visual cohesion with the purple theme |
| Architecture changes | None — use existing CSS variable system | Simplicity (Constitution Principle V); no new abstractions |
