# Research: Add Yellow Background to App

**Feature**: `009-yellow-background`
**Date**: 2026-02-23
**Purpose**: Resolve all Technical Context unknowns and establish best practices for the yellow background implementation.

---

## R-001: Yellow Shade Selection

**Decision**: Use `#FFF9C4` (Material Design Yellow 100) as the app background color.

**Rationale**: The spec recommends #FFF9C4 as a soft/warm yellow. This shade is light enough to serve as a background without causing visual strain, while still being clearly identifiable as yellow. It is a well-known Material Design token (Yellow 100) with established accessibility characteristics. Pure yellow (#FFFF00) is too saturated for a full-page background and causes eye strain. Gold (#FFD700) is too dark/saturated for a neutral background.

**Alternatives considered**:
- `#FFFF00` (pure yellow) — Rejected: too saturated, causes visual strain on large surfaces, poor readability
- `#FFD700` (gold) — Rejected: too dark/warm, gives an amber rather than yellow appearance
- `#FFFDE7` (Yellow 50) — Considered viable but almost indistinguishable from white; #FFF9C4 provides a clearer yellow identity

---

## R-002: Contrast Ratio Compliance (WCAG 2.1 AA)

**Decision**: The existing dark text color `#24292f` against `#FFF9C4` achieves a contrast ratio of approximately 12.6:1, which significantly exceeds the WCAG 2.1 AA minimum of 4.5:1.

**Rationale**: Calculated using the WCAG relative luminance formula:
- `#FFF9C4` luminance ≈ 0.929
- `#24292f` luminance ≈ 0.028
- Contrast ratio = (0.929 + 0.05) / (0.028 + 0.05) ≈ 12.6:1

The secondary text color `#57606a` against `#FFF9C4` yields approximately 6.3:1, also well above 4.5:1. No text color changes are required.

**Alternatives considered**:
- Changing text colors to achieve higher contrast — Rejected: existing text colors already exceed AA thresholds
- Using a darker yellow to reduce contrast needs — Rejected: unnecessary since current text colors work

---

## R-003: Which CSS Custom Properties to Update

**Decision**: Update `--color-bg` and `--color-bg-secondary` in the `:root` block of `frontend/src/index.css`.

**Rationale**: The app's body background uses `var(--color-bg-secondary)` (set in the `body` rule in `index.css`). The `--color-bg` token is the primary app-level background used by components. Both must be set to yellow shades to ensure full coverage:
- `--color-bg`: `#FFF9C4` (primary yellow)
- `--color-bg-secondary`: `#FFF9C4` (same yellow for body and secondary areas, ensuring consistency)

Using the same value for both ensures the yellow background is uniform across all surfaces. If differentiation is desired in the future, `--color-bg-secondary` could be made slightly different (e.g., `#FFF8B8`), but the spec requires a single consistent yellow.

**Alternatives considered**:
- Only updating `--color-bg-secondary` — Rejected: components using `--color-bg` would remain white, creating inconsistency
- Adding a new `--color-bg-yellow` token — Rejected: violates DRY; the existing tokens serve this purpose
- Modifying `body` background directly — Rejected: bypasses the design token system

---

## R-004: Dark Mode Behavior

**Decision**: Do not modify the `html.dark-mode-active` block. Yellow applies only in light mode.

**Rationale**: The spec (FR-005, User Story 3) explicitly states that dark mode MUST retain its existing dark background colors. The app already separates light and dark themes via `:root` (light) and `html.dark-mode-active` (dark) in `index.css`. The `useAppTheme` hook toggles the `dark-mode-active` class on `<html>`. By only changing `:root` values, dark mode is automatically unaffected.

**Alternatives considered**:
- Applying a dark-yellow (e.g., #5C4813) in dark mode — Rejected: spec requires dark mode to retain existing colors
- Adding a `prefers-color-scheme` media query — Rejected: app uses class-based theme switching, not media queries

---

## R-005: Component-Level Background Compatibility

**Decision**: No changes to component-level styles. Existing component backgrounds (cards, modals, inputs) remain as-is.

**Rationale**: The spec states that component-level backgrounds take precedence and should remain unchanged to preserve readability. Components like cards and modals already use `--color-bg` or explicit white backgrounds that provide visual separation from the page background. After changing the root background to yellow, these components will appear as white/light surfaces on a yellow page — which is the expected visual hierarchy.

**Alternatives considered**:
- Making component backgrounds transparent to show yellow through — Rejected: would reduce readability and visual hierarchy
- Auditing every component style — Rejected: unnecessary since component backgrounds are independent of the root background

---

## R-006: Cross-Browser CSS Custom Property Support

**Decision**: No fallback needed. CSS custom properties are supported by all target browsers.

**Rationale**: CSS custom properties (`:root` variables) are supported by Chrome 49+, Firefox 31+, Safari 9.1+, and Edge 15+. All current stable versions far exceed these minimums. The spec's edge case about browsers without CSS custom property support is addressed by the existing codebase — it already uses custom properties throughout, so there is no regression from this change.

**Alternatives considered**:
- Adding a `background-color: #FFF9C4` fallback before the `var()` declaration — Rejected: would add unnecessary code for browsers the app already doesn't support
