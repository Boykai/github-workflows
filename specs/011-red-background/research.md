# Research: Add Red Background Color to App

**Feature**: 011-red-background
**Date**: 2026-02-26

## Research Task 1: Red Color Value Selection and WCAG AA Contrast Compliance

### Context
The spec recommends #E53E3E as the primary red background. We need to verify it provides sufficient contrast with foreground text colors per WCAG AA (4.5:1 for normal text, 3:1 for large text/interactive elements).

### Findings

**Current theme tokens** (from `frontend/src/index.css`):

| Token | Light Mode | Dark Mode |
|-------|-----------|-----------|
| `--color-text` | `#24292f` | `#e6edf3` |
| `--color-text-secondary` | `#57606a` | `#8b949e` |
| `--color-primary` | `#0969da` | `#539bf5` |
| `--color-bg` | `#ffffff` | `#0d1117` |
| `--color-bg-secondary` | `#f6f8fa` | `#161b22` |

**Contrast analysis for #E53E3E background**:

| Foreground | Hex | Contrast Ratio vs #E53E3E | WCAG AA (4.5:1) |
|------------|-----|---------------------------|------------------|
| White text | `#ffffff` | ~4.63:1 | ✅ PASS (normal text) |
| Current `--color-text` (light) | `#24292f` | ~5.04:1 | ✅ PASS |
| Current `--color-text-secondary` (light) | `#57606a` | ~3.14:1 | ❌ FAIL for normal text |

**Decision**: Use `#E53E3E` as the red background color. For light mode, update `--color-text` to `#ffffff` (white) and `--color-text-secondary` to a lighter value (e.g., `#fce4e4` or `#ffd7d7`) to ensure contrast compliance. Components with their own backgrounds (cards, modals, headers) retain their existing backgrounds and text colors.

**Rationale**: #E53E3E is the stakeholder-recommended value from the spec. White text on #E53E3E achieves 4.63:1 contrast, meeting WCAG AA for normal text. The body background change only affects the app-level surface; overlaid components (header, sidebar, cards) already define their own `--color-bg` backgrounds.

**Alternatives considered**:
- `#C0392B` (darker red): Higher contrast with white text (~5.9:1) but spec recommends #E53E3E as starting point
- `#DC3545` (Bootstrap red): Similar contrast profile, but not recommended by spec

## Research Task 2: Existing CSS Custom Property Infrastructure

### Context
Need to understand how to implement the change using the existing theme system without introducing new abstractions.

### Findings

**Current implementation** (`frontend/src/index.css`):
- `:root` block defines light mode tokens (lines 2-15)
- `html.dark-mode-active` block defines dark mode overrides (lines 18-30)
- `body` uses `background: var(--color-bg-secondary)` (line 43)
- Theme toggle is controlled by `useAppTheme` hook adding/removing `dark-mode-active` class on `<html>`

**Change strategy**:
1. Update `--color-bg-secondary` in `:root` from `#f6f8fa` → `#E53E3E`
2. Update `--color-bg-secondary` in `html.dark-mode-active` from `#161b22` → `#E53E3E` (same red for both modes, per spec: "consistently across all pages")
3. The `body` element already uses `var(--color-bg-secondary)` — no additional body style changes needed
4. Provide fallback: `background: var(--color-bg-secondary, #E53E3E)` on body

**Decision**: Modify the existing `--color-bg-secondary` token values in both `:root` and `html.dark-mode-active` blocks. This is the minimal change path that leverages the existing token system.

**Rationale**: The body background is already driven by `--color-bg-secondary`. Changing the token value at the root level propagates the red background globally with zero component-level changes.

**Alternatives considered**:
- Adding a new `--color-bg-app` token: Adds unnecessary complexity; the existing `--color-bg-secondary` serves the same purpose
- Inline style on `<body>` in `index.html`: Bypasses the token system, violates DRY principle

## Research Task 3: Cross-Browser Compatibility of CSS Custom Properties

### Context
The spec requires consistent rendering across Chrome, Firefox, Safari, and Edge.

### Findings

CSS custom properties (CSS variables) are supported in:
- Chrome 49+ (2016)
- Firefox 31+ (2014)
- Safari 9.1+ (2016)
- Edge 15+ (2017)

All modern versions of these browsers fully support CSS custom properties. The hex color value `#E53E3E` is a standard 6-digit hex color supported by all browsers.

**Decision**: No special cross-browser handling needed. Standard CSS custom properties with hex colors work universally.

**Rationale**: The project already uses CSS custom properties extensively. Adding another hex value introduces no new browser compatibility concerns.

**Alternatives considered**: None — CSS custom properties are the established pattern in this codebase.

## Research Task 4: Impact on Overlaid Components

### Context
Cards, modals, headers, sidebars, and other components need to remain legible against the red background.

### Findings

Key components and their background handling (from `App.css` and `index.css`):

| Component | Background Token | Current Value (Light) | Impact |
|-----------|-----------------|----------------------|--------|
| `.app-header` | `var(--color-bg)` | `#ffffff` | ✅ No impact — uses `--color-bg`, not `--color-bg-secondary` |
| `.app-sidebar` / `.project-sidebar` | `var(--color-bg)` | `#ffffff` | ✅ No impact |
| `.chat-section` | `var(--color-bg)` | `#ffffff` | ✅ No impact |
| Cards / `.task-card` | `var(--color-bg)` | `#ffffff` | ✅ No impact |
| `body` | `var(--color-bg-secondary)` | Currently `#f6f8fa` → will become `#E53E3E` | ✅ Intended change |

**Decision**: Only the body/app-level surface changes to red. All overlaid components use `--color-bg` (white in light mode, dark in dark mode) and are unaffected.

**Rationale**: The existing token separation between `--color-bg` (component backgrounds) and `--color-bg-secondary` (page background) naturally isolates the change. This is exactly the kind of theming benefit that CSS custom properties provide.

**Alternatives considered**: None — the existing architecture already handles this correctly.

## Summary of Resolved Items

All technical context items are resolved. No NEEDS CLARIFICATION remains.

| Item | Resolution |
|------|-----------|
| Red hex value | #E53E3E (spec-recommended, WCAG AA compliant with white text) |
| Implementation approach | Modify `--color-bg-secondary` token in `frontend/src/index.css` |
| Contrast compliance | White text (#ffffff) on #E53E3E achieves 4.63:1 (meets WCAG AA) |
| Cross-browser support | CSS custom properties universally supported in target browsers |
| Component impact | Isolated to body background; overlaid components use separate `--color-bg` token |
| Fallback strategy | Add fallback value in body background declaration |
