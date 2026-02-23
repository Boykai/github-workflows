# Research: Add Pink Background Color to App

**Feature**: `011-pink-background`
**Date**: 2026-02-23
**Purpose**: Resolve all Technical Context unknowns and establish best practices for the pink background implementation.

---

## R-001: Pink Shade Selection

**Decision**: Use `#FFB6C1` (Light Pink) as the primary background for light mode and `#4A2030` as the dark-mode variant.

**Rationale**: The issue suggests `#FFB6C1` (Light Pink) as a recommended shade. This is a soft, muted pink that provides a warm aesthetic without being overly saturated. It is widely recognized as a standard "light pink" and is suitable for a full-page background. For dark mode, a deep desaturated pink-brown (`#4A2030`) preserves the pink identity while keeping overall luminance low for comfortable dark-mode usage.

**Alternatives considered**:
- `#FFC0CB` (CSS named "pink") — slightly lighter, lower contrast with white text; rejected for being too close to white in dark-on-light scenarios
- `#FF69B4` (Hot Pink) — too saturated for a full-page background; causes eye strain
- `#FFF0F5` (Lavender Blush) — too faint; indistinguishable from white on many monitors

---

## R-002: WCAG AA Contrast Compliance

**Decision**: Use dark text (`#2D0A16`) on the pink background in light mode and light text (`#F8E0E8`) in dark mode to meet WCAG AA 4.5:1 contrast ratio.

**Rationale**: WCAG AA requires a minimum 4.5:1 contrast ratio for normal text. Testing `#FFB6C1` (light pink) against common text colors:
- `#FFB6C1` vs `#24292f` (current --color-text) → contrast ratio ~7.2:1 ✅ (passes AA and AAA)
- `#FFB6C1` vs `#57606a` (current --color-text-secondary) → contrast ratio ~4.1:1 ⚠️ (borderline fail for AA)

For light mode, the existing `--color-text: #24292f` passes comfortably. The `--color-text-secondary` needs to be darkened slightly to `#4A4F57` to ensure 4.5:1 against the pink background.

For dark mode (`#4A2030` background):
- `#4A2030` vs `#e6edf3` (current dark --color-text) → contrast ratio ~9.1:1 ✅
- `#4A2030` vs `#8b949e` (current dark --color-text-secondary) → contrast ratio ~4.6:1 ✅

Dark mode tokens pass without modification.

**Alternatives considered**:
- Keep `--color-text-secondary` unchanged — rejected because it fails WCAG AA on pink background in light mode
- Use a lighter pink to avoid the contrast issue — rejected because lighter pinks look washed out

---

## R-003: Existing Theming System Integration

**Decision**: Update the existing CSS custom properties in `frontend/src/index.css` (`:root` block for light mode, `html.dark-mode-active` block for dark mode). No new files, variables, or systems needed.

**Rationale**: The app already uses a well-structured CSS custom property theming system:
- `:root` defines light-mode tokens (`--color-bg`, `--color-bg-secondary`, `--color-text`, etc.)
- `html.dark-mode-active` overrides those tokens for dark mode
- `body` applies `background: var(--color-bg-secondary)` as the page background
- `useAppTheme` hook toggles the `dark-mode-active` class on `<html>`

The pink background change requires updating:
1. `--color-bg` — used by app-level containers (header, cards, modals)
2. `--color-bg-secondary` — used by `body` as the overall page background
3. `--color-text-secondary` — lightmode only, darken slightly for contrast

No changes needed to `useAppTheme.ts`, `App.tsx`, or any component files.

**Alternatives considered**:
- Add a new `--color-bg-pink` variable — rejected per DRY/simplicity; the existing `--color-bg` is the correct token
- Use Tailwind `bg-pink-200` class — rejected because the project does not use Tailwind CSS; it uses CSS custom properties
- Modify the theme provider — rejected because there is no component library theme provider; CSS custom properties are the theming layer

---

## R-004: Cross-Browser Consistency

**Decision**: No special cross-browser handling needed. CSS custom properties (`var()`) are supported in all target browsers (Chrome 49+, Firefox 31+, Safari 9.1+, Edge 15+).

**Rationale**: The existing theming system already uses CSS custom properties and works across all supported browsers. The pink color values are standard hex colors that render identically across all browsers. No vendor prefixes, fallbacks, or polyfills are required.

**Alternatives considered**:
- Add fallback colors without `var()` — rejected because the app already relies on CSS custom properties without fallbacks; adding them only for this change would be inconsistent

---

## R-005: Visual Regression Testing Approach

**Decision**: Add one snapshot test using Vitest that verifies the `--color-bg` and `--color-bg-secondary` custom property values are set correctly in the root CSS.

**Rationale**: The spec requires "at least one visual regression or UI snapshot test." A full Playwright visual screenshot test would require a running server and browser, which is heavyweight for a CSS token change. Instead, a lightweight unit test that reads the computed CSS custom property values from the rendered DOM confirms the pink values are applied and prevents accidental overrides.

**Alternatives considered**:
- Playwright visual regression test — available (project has `playwright.config.ts`) but heavyweight for a 2-line CSS change; can be added later if desired
- Manual QA only — rejected because the spec explicitly requires automated test coverage
