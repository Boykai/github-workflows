# Research: Add Golden Background to App

**Feature**: `018-golden-background` | **Date**: 2026-03-04

## Research Tasks

### R1: Optimal Gold Color Value in HSL for Existing Theme System

**Decision**: Use `51 100% 50%` (HSL equivalent of #FFD700) as the `:root` `--background` value. The existing theming system stores colors as space-separated HSL values (hue saturation% lightness%) without the `hsl()` wrapper, which is applied by Tailwind via `hsl(var(--background))`. The standard CSS named color "gold" (#FFD700) converts to HSL(51°, 100%, 50%).

**Rationale**: #FFD700 is the spec-recommended gold color and the standard CSS "gold" named color. It is widely recognized, renders identically across all browsers, and provides a rich gold tone. Using the existing HSL variable format ensures zero changes to `tailwind.config.js` — the `hsl(var(--background))` pattern continues to work unchanged.

**Alternatives considered**:
- **#F5C518 (IMDb-style gold)**: Slightly more amber; works but is less standard and deviates from spec recommendation.
- **Gradient (linear-gradient #F5C518 to #C89B00)**: Spec mentions as an option, but the `--background` CSS variable feeds `hsl()` which produces a solid color. A gradient would require restructuring the theme system — rejected as unnecessary complexity for an XS feature.
- **#DAA520 (goldenrod)**: Darker gold with better inherent contrast, but diverges from spec's #FFD700 recommendation without clear benefit.

### R2: WCAG AA Contrast Compliance with Gold Background

**Decision**: The `--foreground` text color must be updated to a dark value that achieves ≥4.5:1 contrast ratio against #FFD700. The current light-mode foreground (`222.2 84% 4.9%` ≈ #020817, very dark blue-black) provides a contrast ratio of approximately 13.6:1 against #FFD700, which far exceeds the 4.5:1 WCAG AA requirement. Therefore, the existing foreground value can remain unchanged.

**Rationale**: #FFD700 has a relative luminance of ~0.70. The existing dark foreground (#020817) has a luminance of ~0.005. The contrast ratio is (0.70 + 0.05) / (0.005 + 0.05) ≈ 13.6:1, well above the 4.5:1 threshold. No foreground adjustment needed.

**Alternatives considered**:
- **Switching to pure black (#000000)**: Marginal improvement (14.5:1 vs 13.6:1) but loses the subtle blue-black character of the existing theme.
- **Switching to lighter text**: Would reduce contrast — rejected.

### R3: Dark Mode Golden Background Strategy

**Decision**: In dark mode, use a deepened dark-gold variant: `43 74% 15%` (HSL for approximately #3D2E0A, a dark amber-brown). This maintains the golden identity while being comfortable for dark mode viewing. The dark-mode foreground remains the existing light value (`210 40% 98%` ≈ #F8FAFC), which provides ~12.5:1 contrast against the dark gold.

**Rationale**: The spec requires explicit dark mode behavior (FR-005). A fully saturated gold (#FFD700) in dark mode would defeat the purpose of dark mode (reducing eye strain). A deepened/darkened gold preserves the golden theme identity while maintaining the ergonomic benefits of dark mode. The chosen value is a very dark gold that reads as "warm dark" rather than "pure dark."

**Alternatives considered**:
- **Suppress gold entirely in dark mode (use existing dark bg)**: Rejected — spec says behavior must be "explicitly defined" and preserving gold identity is preferred.
- **Same #FFD700 in both modes**: Rejected — contradicts dark mode purpose and user expectations.
- **Muted gold (desaturated)**: A muted dark gold (e.g., 40° 30% 12%) was considered but felt too grey. The chosen 74% saturation retains warmth.

### R4: Impact on Card, Popover, and Secondary Background Tokens

**Decision**: The `--card`, `--popover`, and `--secondary` tokens should retain their own values (not inherit the gold) to avoid making all UI surfaces uniformly gold. Cards and popovers should remain their current neutral/white (light mode) or dark (dark mode) values. This ensures modals, dropdowns, and card surfaces are visually distinct from the golden background, maintaining readability and visual hierarchy.

**Rationale**: The spec explicitly states (Edge Cases section): "Inner containers (cards, sidebars, panels) retain their own background styles unless explicitly changed." Overlay components "should retain their own background styling and not inherit the golden color."

**Alternatives considered**:
- **Make all surfaces gold**: Rejected — would eliminate visual hierarchy and make cards indistinguishable from the background.
- **Tint cards with subtle gold**: Over-engineering for an XS feature; can be added later if desired.

### R5: Browser Compatibility of HSL CSS Variables

**Decision**: No special handling needed. HSL color values in CSS custom properties are supported by all target browsers (Chrome 49+, Firefox 31+, Safari 9.1+, Edge 15+). The existing theme system already relies on this pattern for every color token.

**Rationale**: The project already uses `hsl(var(--variable))` for all color tokens. If this pattern had browser compatibility issues, the entire theme would be broken. Since the existing theme works across all target browsers, changing the HSL values within the variables introduces zero new compatibility risk.

**Alternatives considered**:
- **Fallback values**: Unnecessary since the pattern is already used throughout.
- **Hex values instead of HSL**: Would require restructuring the entire Tailwind config — rejected.

## Summary

All research tasks resolved. No NEEDS CLARIFICATION items remain. Key decisions:
1. Use `51 100% 50%` (HSL of #FFD700) for the light-mode `--background` token
2. Existing foreground color provides 13.6:1 contrast — no text color changes needed
3. Dark mode uses deepened dark-gold `43 74% 15%` to preserve golden identity
4. Card, popover, and secondary tokens remain unchanged (visual hierarchy preserved)
5. No browser compatibility concerns — existing HSL pattern is fully supported
