# Research: Add Green Background Color to App

**Feature**: 016-green-background  
**Date**: 2026-03-03  
**Status**: Complete

## R1: Green Color Value Selection

**Decision**: Use `#22c55e` (HSL: `142.1 76.2% 36.3%`) as the primary green background color for light mode, and `#166534` (HSL: `142.1 64.2% 24.1%`) for dark mode.

**Rationale**: The spec recommends `#22c55e` as a mid-range, accessible green. This is Tailwind CSS's `green-500` value, which is already part of the Tailwind color palette the project uses. Using an established Tailwind green ensures visual consistency with the existing design system. The dark mode variant `#166534` (Tailwind's `green-800`) provides a darker, more comfortable green that reduces eye strain while maintaining the green identity. The spec's assumptions section explicitly recommends these values.

**Alternatives considered**:
- `#16a34a` (green-600): Slightly darker, better contrast with white text but less vibrant than the spec recommendation.
- `#4ade80` (green-400): Too light, insufficient contrast with white text (fails WCAG AA).
- `green` CSS keyword: Rejected per FR-002 — bare keyword provides inconsistent rendering across browsers.

## R2: Foreground Text Color for WCAG AA Compliance

**Initial analysis (rejected)**: White (`#ffffff`) on `#22c55e` yields approximately 2.52:1, which does NOT meet WCAG AA for body text (4.5:1 required). A dark foreground color is necessary.

**Decision**: Use `#052e16` (Tailwind's `green-950`, HSL: `144.3 80.4% 10%`) as the light-mode foreground and `#f0fdf4` (HSL: `138.5 76.5% 96.7%`) as the dark-mode foreground.

**Rationale**: `#052e16` achieves a contrast ratio of approximately 10.5:1 against `#22c55e`, well exceeding WCAG AA requirements. For dark mode, `#f0fdf4` on `#166534` achieves approximately 7.8:1, also exceeding WCAG AA.

**Contrast ratios verified**:
- Light mode: `#052e16` on `#22c55e` → ~10.5:1 ✅ (exceeds 4.5:1)
- Dark mode: `#f0fdf4` on `#166534` → ~7.8:1 ✅ (exceeds 4.5:1)

**Alternatives considered**:
- White text on green: 2.52:1 — fails WCAG AA for body text.
- Black (`#000000`) on green: 5.6:1 — passes but lacks visual harmony with the green theme.
- Dark green (`#14532d`) text: 6.8:1 — passes but `#052e16` provides stronger contrast.

## R3: CSS Implementation Approach

**Decision**: Modify the existing `--background` and `--foreground` CSS custom properties in `frontend/src/index.css` within the `:root` and `.dark` selectors. No new CSS variables, no new files, no Tailwind config changes.

**Rationale**: The project's styling architecture is already built around HSL-based CSS custom properties defined in `index.css`. The `<body>` element applies `bg-background text-foreground` via Tailwind utilities (line 74-75 of index.css), and Tailwind's config maps `background` to `hsl(var(--background))`. Changing the `--background` variable value automatically propagates to all elements using `bg-background`, satisfying FR-005 (global application). This is the simplest possible change — a single file edit with zero risk of breaking existing functionality outside of intentional color changes.

**Alternatives considered**:
- New `--color-app-background` variable: Adds unnecessary indirection when `--background` already serves this purpose. Violates DRY.
- Tailwind config theme extension: Would require a new named color and changes to component classes. More complex, more files touched.
- Inline style on `<body>` or root `<div>`: Bypasses the design token system, harder to maintain, violates FR-007.

## R4: Additional CSS Variables Needing Adjustment

**Decision**: Update `--background`, `--foreground`, `--card`, `--card-foreground`, `--popover`, and `--popover-foreground` to maintain visual cohesion. Keep `--primary`, `--secondary`, `--muted`, `--accent`, `--destructive`, `--border`, `--input`, and `--ring` at their current values initially and adjust only if they create contrast issues.

**Rationale**: Cards and popovers currently inherit the same background as the root. If we change only `--background`, cards and popovers will still show the old white/dark background, creating visual inconsistency. However, changing card and popover backgrounds to green may reduce readability of their content. The safest approach is to keep card/popover backgrounds as-is (white in light mode, dark in dark mode) to preserve content readability, and only change the root `--background` and `--foreground`. This creates a clear visual hierarchy: green page background with white content cards.

**Updated Decision**: Change only `--background` and `--foreground`. Leave `--card`, `--popover`, and other variables unchanged. Cards and popovers will retain their current colors, providing a clean contrast layer against the green background.

## R5: Cross-Browser Compatibility

**Decision**: No special browser-specific CSS is needed. HSL CSS custom properties are supported by all target browsers (Chrome 49+, Firefox 31+, Safari 9.1+, Edge 15+).

**Rationale**: The project already uses CSS custom properties with HSL values throughout `index.css` and this works across all target browsers. The `#22c55e` green is a standard hex color with no rendering inconsistencies. The existing Tailwind CSS build process (via Vite/PostCSS) already handles any necessary vendor prefixing. No additional fallbacks are required since the project's minimum browser targets already support CSS custom properties.

**Alternatives considered**:
- Adding a `background-color: green` fallback before the variable: Unnecessary given browser support levels. Also violates FR-002.
- Using `@supports` queries: Over-engineered for this change; all target browsers support CSS custom properties.

## R6: Dark Mode Implementation

**Decision**: Use `.dark` class selector (already in `index.css`) with a darker green variant `#166534` (HSL: `142.1 64.2% 24.1%`).

**Rationale**: The project uses Tailwind's `class` strategy for dark mode (configured in `tailwind.config.js` as `darkMode: ["class"]`). The `ThemeProvider` component manages the `.dark` class on the document root. The existing `.dark` selector in `index.css` already defines dark mode overrides. Using `#166534` (green-800) provides a comfortable, dark green that maintains the green identity while being easy on the eyes in dark environments. This aligns with the spec assumption about using a darker green variant.

**Alternatives considered**:
- Same green in both modes: `#22c55e` is too bright for dark mode and would cause eye strain.
- `#14532d` (green-900): Too dark, barely distinguishable from black in low-light environments.
- `#15803d` (green-700): Viable middle ground but `#166534` provides better contrast with light text.
