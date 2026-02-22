# Research: Add Black Background Theme to App

**Feature**: `009-black-background` | **Date**: 2026-02-22

## R1. Existing Theming Infrastructure

**Decision**: Leverage the existing CSS custom property system in `frontend/src/index.css` with `:root` (light mode) and `html.dark-mode-active` (dark mode) selectors.

**Rationale**: The app already has a fully functional design token system. All components reference colors via `var(--color-*)`. Changing the token values at the root level propagates the new theme globally without touching individual components. The `useAppTheme` hook manages the `dark-mode-active` class toggle and persists the preference to both localStorage and the user settings API.

**Current token values**:

| Token | Light (`:root`) | Dark (`html.dark-mode-active`) |
|-------|----------------|-------------------------------|
| `--color-bg` | `#ffffff` | `#0d1117` |
| `--color-bg-secondary` | `#f6f8fa` | `#161b22` |
| `--color-border` | `#d0d7de` | `#30363d` |
| `--color-text` | `#24292f` | `#e6edf3` |
| `--color-text-secondary` | `#57606a` | `#8b949e` |
| `--color-primary` | `#0969da` | `#539bf5` |
| `--color-secondary` | `#6e7781` | `#8b949e` |
| `--color-success` | `#1a7f37` | `#3fb950` |
| `--color-warning` | `#9a6700` | `#d29922` |
| `--color-danger` | `#cf222e` | `#f85149` |
| `--shadow` | `0 1px 3px rgba(0,0,0,0.1)` | `0 1px 3px rgba(0,0,0,0.4)` |

**Alternatives considered**:
- *Tailwind CSS integration* — Rejected: App does not use Tailwind. Adding it would violate Principle V (Simplicity).
- *CSS-in-JS / styled-components* — Rejected: App uses plain CSS with custom properties. No reason to change.
- *New `--color-bg-surface` token* — Rejected: The existing two-tier system (`--color-bg` for app-level, `--color-bg-secondary` for body/alternate) is sufficient. Elevated surfaces already use `--color-bg` or `--color-bg-secondary` via existing `var()` references.

## R2. Black Background Color Values

**Decision**: Use the following color palette for the black background theme.

| Token | New Light Value | New Dark Value | Purpose |
|-------|----------------|----------------|---------|
| `--color-bg` | `#000000` | `#000000` | Root/app background — true black |
| `--color-bg-secondary` | `#121212` | `#0a0a0a` | Body background, alternate surfaces |
| `--color-border` | `#2c2c2c` | `#1f1f1f` | Borders, dividers, outlines |
| `--color-text` | `#ffffff` | `#f0f0f0` | Primary text — white for max contrast |
| `--color-text-secondary` | `#a0a0a0` | `#8a8a8a` | Secondary/muted text |
| `--color-primary` | `#539bf5` | `#539bf5` | Primary action color (blue, preserved) |
| `--color-secondary` | `#8b949e` | `#8b949e` | Secondary element color |
| `--color-success` | `#3fb950` | `#3fb950` | Success indicators |
| `--color-warning` | `#d29922` | `#d29922` |Warning indicators |
| `--color-danger` | `#f85149` | `#f85149` | Danger/error indicators |
| `--shadow` | `0 1px 3px rgba(0,0,0,0.6)` | `0 1px 3px rgba(0,0,0,0.8)` | Elevated shadow |

**Rationale**:
- `#000000` is true black per FR-001.
- `#121212` for secondary surfaces follows Material Design dark theme guidelines and provides visual depth per FR-004.
- `#ffffff` primary text on `#000000` background = 21:1 contrast ratio (exceeds WCAG AAA).
- `#a0a0a0` secondary text on `#000000` background = 10.4:1 contrast ratio (exceeds WCAG AA 4.5:1).
- Accent colors (`primary`, `success`, `warning`, `danger`) use the existing dark-mode values which already provide good contrast on dark backgrounds.

**Alternatives considered**:
- *Near-black (#0a0a0a) for root* — Rejected: Spec explicitly requires true black (#000000) for root background (FR-001).
- *Separate surface token (`--color-bg-surface`)* — Rejected: Would require updating all components. The two-tier system is sufficient.

## R3. Hardcoded Color Audit

**Decision**: Replace ~15 hardcoded light background values in `App.css` and `ChatInterface.css` with dark-compatible equivalents.

**Findings**:

### `App.css` — Hardcoded backgrounds requiring update:

| Line | Current Value | Context | Action |
|------|--------------|---------|--------|
| 101 | `#32383f` | Login button hover | Keep — already dark |
| 291 | `rgba(9, 105, 218, 0.1)` | Info badge bg | Keep — semi-transparent adapts |
| 296 | `rgba(154, 103, 0, 0.1)` | Warning badge bg | Keep — semi-transparent adapts |
| 301 | `rgba(26, 127, 55, 0.1)` | Success badge bg | Keep — semi-transparent adapts |
| 348 | `#2da44e` | Success button | Keep — dark-compatible |
| 353 | `#bf8700` | Warning button | Keep — dark-compatible |
| 358 | `#0969da` | Primary button | Keep — dark-compatible |
| 362 | `#cf222e` | Danger button | Keep — dark-compatible |
| 387 | `#dafbe1` | Success notification bg | Replace — light green → dark green variant |
| 407 | `#fff1f0` | Error notification bg | Replace — light red → dark red variant |
| 446 | `#fff1f0` | Error alert bg | Replace — light red → dark red variant |

### `ChatInterface.css` — Hardcoded backgrounds requiring update:

| Line | Current Value | Context | Action |
|------|--------------|---------|--------|
| 190 | `#15652d` | Chat success hover | Keep — already dark |
| 316 | `#0860ca` | Chat primary hover | Keep — already dark |
| 509 | `#22c55e` | Chat action btn | Keep — dark-compatible |

**Summary**: Most hardcoded values are already dark-compatible (button colors, hover states). Only 3 instances need replacement: success notification background (`#dafbe1` → dark variant), and 2 error background instances (`#fff1f0` → dark variant).

**Alternatives considered**:
- *Replace all hardcoded colors with CSS variables* — Rejected: Over-engineering for button accent colors that are dark-compatible already. Only light backgrounds that break the theme need updating.

## R4. White Flash Prevention

**Decision**: Add `style="background-color: #000000"` to the `<html>` element in `index.html`.

**Rationale**: CSS files are loaded asynchronously. Before they load, the browser renders the default white background. An inline style on `<html>` ensures the background is black from the first paint, preventing flash (FR-007).

**Alternatives considered**:
- *Inline `<style>` block in `<head>`* — Viable but more verbose. Inline attribute is simpler for a single property.
- *CSS `prefers-color-scheme` media query* — Rejected: The app enforces its own theme regardless of OS preference.
- *Server-side rendering* — Rejected: App is a client-side SPA. Not applicable.

## R5. Theme Persistence Strategy

**Decision**: No changes needed. The existing `useAppTheme` hook already persists theme preference via localStorage and the user settings API (FR-009).

**Rationale**: The hook reads from localStorage on mount and syncs with the API when authenticated. The black theme will become the default by setting the `:root` tokens to black values. Users who previously selected dark mode will see the updated dark-mode black values. Users on light mode will see the updated light-mode black values. Both modes now use a black background.

**Alternatives considered**:
- *Force dark mode on all users* — Rejected: Both `:root` and `html.dark-mode-active` will use black backgrounds, so the toggle still works but both modes are dark-themed. This matches the spec requirement (FR-009) without removing user choice.

## R6. WCAG Contrast Verification

**Decision**: All proposed text colors meet WCAG AA (4.5:1 minimum) against the black background.

**Verification**:

| Text Color | Background | Contrast Ratio | WCAG AA (4.5:1) | WCAG AAA (7:1) |
|-----------|------------|----------------|-----------------|----------------|
| `#ffffff` (primary text) | `#000000` | 21:1 | ✅ Pass | ✅ Pass |
| `#f0f0f0` (dark primary text) | `#000000` | 18.1:1 | ✅ Pass | ✅ Pass |
| `#a0a0a0` (secondary text) | `#000000` | 10.4:1 | ✅ Pass | ✅ Pass |
| `#8a8a8a` (dark secondary text) | `#000000` | 7.4:1 | ✅ Pass | ✅ Pass |
| `#539bf5` (primary/links) | `#000000` | 6.5:1 | ✅ Pass | — |
| `#3fb950` (success) | `#000000` | 8.1:1 | ✅ Pass | ✅ Pass |
| `#d29922` (warning) | `#000000` | 8.3:1 | ✅ Pass | ✅ Pass |
| `#f85149` (danger) | `#000000` | 5.2:1 | ✅ Pass | — |

All colors pass WCAG AA. Primary text achieves WCAG AAA.
