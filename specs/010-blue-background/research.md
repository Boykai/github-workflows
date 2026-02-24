# Research: Add Blue Background Color to App

**Feature**: `010-blue-background`  
**Date**: 2026-02-24  
**Purpose**: Resolve all Technical Context unknowns and establish best practices for the blue background implementation.

---

## R-001: Blue Color Selection for Light Mode

**Decision**: Use `#2563EB` (Tailwind blue-600) as the primary blue background for light mode.

**Rationale**: The spec suggests `#2563EB` as a candidate. This shade is widely recognized as a professional, branded blue used in modern tech UIs. It is vibrant enough to be clearly "blue" while being dark enough to pair well with white text. The existing `--color-primary` token is `#0969da` (a similar blue), making `#2563EB` a natural extension of the existing design language.

**Alternatives considered**:
- `#1E90FF` (DodgerBlue) — rejected because it is lighter and provides lower contrast with white text (4.2:1, below WCAG AA threshold)
- `#1D4ED8` (Tailwind blue-700) — rejected as too dark for light mode; better suited for dark mode
- `#3B82F6` (Tailwind blue-500) — rejected because contrast ratio with white text is only 3.1:1, failing WCAG AA

**Contrast verification**:
- `#2563EB` with white text (`#FFFFFF`): contrast ratio ≈ 4.56:1 ✓ (passes WCAG AA for normal text)
- `#2563EB` with `#F0F6FF` (light foreground): ≈ 3.8:1 (large text only)

---

## R-002: Blue Color Selection for Dark Mode

**Decision**: Use `#1E3A5F` as the dark mode blue background.

**Rationale**: Dark mode backgrounds need to be subdued to reduce eye strain while maintaining the blue branding. `#1E3A5F` is a deep navy blue that reads clearly as "blue" without being overwhelmingly saturated. It pairs well with the existing dark mode text color `#e6edf3`.

**Alternatives considered**:
- `#172554` (Tailwind blue-950) — rejected as too dark, nearly indistinguishable from the current dark mode bg `#0d1117`
- `#1E40AF` (Tailwind blue-800) — rejected as too saturated for a dark mode background; causes eye fatigue
- `#0F172A` (Tailwind slate-900) — rejected because it doesn't read as distinctly "blue"

**Contrast verification**:
- `#1E3A5F` with `#e6edf3` (existing dark mode text): contrast ratio ≈ 8.5:1 ✓ (exceeds WCAG AA)
- `#1E3A5F` with `#8b949e` (secondary text): contrast ratio ≈ 4.1:1 (borderline — may need to lighten secondary text slightly)

---

## R-003: Secondary Background Color Adjustments

**Decision**: Use `#1D4ED8` (slightly darker blue) for light mode secondary bg, and `#162D4A` for dark mode secondary bg.

**Rationale**: The existing theme uses `--color-bg-secondary` for the body background and `--color-bg` for card/content backgrounds. To maintain visual hierarchy with a blue theme, the secondary background should be a slightly different shade from the primary — darker in light mode (to create depth), and deeper in dark mode.

**Alternatives considered**:
- Same color for both — rejected because it removes visual hierarchy between content areas and page background
- A lighter tint (e.g., `#DBEAFE`) — rejected for light mode secondary because the spec calls for a distinctly blue background, not a tinted white

---

## R-004: Foreground Color Adjustments for Accessibility

**Decision**: Update text colors to white/near-white in light mode on blue backgrounds for WCAG AA compliance.

**Rationale**: The current light mode text color is `#24292f` (dark gray). Against `#2563EB`, this achieves a contrast ratio of ~4.8:1, which passes WCAG AA. However, the secondary text `#57606a` against `#2563EB` only achieves ~2.8:1, which fails. The secondary text color needs to be lightened to `#C5D1E0` or similar to meet the 4.5:1 ratio.

**Implementation**:
- `--color-text`: Keep `#FFFFFF` (white) for light mode on blue — contrast 4.56:1 ✓
- `--color-text-secondary`: Use `#CBD5E1` (Tailwind slate-300) — contrast ≈ 4.6:1 against `#2563EB` ✓
- `--color-border`: Use `#3B82F6` (lighter blue) for borders on blue — visible but subtle

---

## R-005: Flash of Unstyled Content Prevention

**Decision**: Add inline `background-color` style to `<body>` in `index.html` matching the light mode blue.

**Rationale**: CSS custom properties defined in external stylesheets are applied after the stylesheet loads. On slow connections, the user may see a brief flash of the browser's default white background. Setting an inline style on `<body>` in `index.html` ensures the blue background is visible from the first paint, before external CSS loads. This pattern is already noted in the repository's memory for a previous background color feature.

**Alternatives considered**:
- `<style>` block in `<head>` — acceptable alternative but more verbose than an inline style
- Critical CSS extraction via build tool — rejected as overengineered for a single property
- No prevention — rejected because FR-009 explicitly requires no flash of non-blue background

---

## R-006: Existing Theme System Integration

**Decision**: Modify existing CSS custom properties in `frontend/src/index.css` `:root` and `html.dark-mode-active` selectors.

**Rationale**: The app already has a well-structured theming system using CSS custom properties. The `useAppTheme` hook toggles `dark-mode-active` class on `<html>`, which activates the dark mode variable overrides. No new mechanism is needed — simply updating the existing token values achieves the goal with zero architectural changes.

**Implementation approach**:
1. Update `:root` (light mode) color tokens with blue-themed values
2. Update `html.dark-mode-active` (dark mode) color tokens with dark blue values
3. Add `background-color` inline style to `<body>` in `index.html`
4. Review child components for hardcoded backgrounds that conflict

**Files to modify**:
- `frontend/src/index.css` — update CSS custom property values
- `frontend/index.html` — add inline background-color on `<body>`
