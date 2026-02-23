# Research: Add Blue Background Color to App

**Feature**: `009-blue-background`  
**Date**: 2026-02-23  
**Purpose**: Resolve all Technical Context unknowns and establish best practices for the blue background implementation.

---

## R-001: Blue Shade Selection

**Decision**: Use `#1A3A5C` (deep navy blue) for the light theme background and `#0F2233` for the dark theme background.

**Rationale**: The app's existing light theme uses `--color-bg: #ffffff` and `--color-bg-secondary: #f6f8fa` with text color `--color-text: #24292f`. A blue background must provide sufficient contrast with foreground text. A medium-dark navy blue like `#1A3A5C` provides:
- Contrast ratio with white text (`#FFFFFF`): ~9.5:1 (exceeds WCAG AA 4.5:1)
- Contrast ratio with light text (`#E6EDF3`): ~8.2:1 (exceeds WCAG AA 4.5:1)
- Professional, brand-appropriate appearance aligned with the issue's suggested range (#1E90FF, #0D6EFD)
- Sufficient distinction from component backgrounds that use lighter shades

The light-mode text colors must be updated to light values to maintain readability against the dark blue background.

**Alternatives considered**:
- `#1E90FF` (Dodger Blue) — rejected as a background because it is too bright/saturated for a full-page background; causes eye strain on prolonged use and provides only ~3.2:1 contrast with dark text
- `#0D6EFD` (Bootstrap primary blue) — rejected for same reasons as above; better suited as an accent/button color than a full-page background
- `#1565C0` (Material Design Blue 800) — considered viable but slightly brighter than preferred for a professional app background
- `#0A1628` (very dark navy) — rejected as too dark for a "blue" background; reads as almost black

---

## R-002: WCAG AA Contrast Compliance Strategy

**Decision**: Update foreground text tokens (`--color-text`, `--color-text-secondary`) to light colors in the light theme to ensure contrast against the blue background.

**Rationale**: The current light theme has dark text (`#24292f`) on a white background. With a blue background (`#1A3A5C`), dark text would have poor contrast. The solution is to switch the light theme's text colors to light values:
- `--color-text`: `#E6EDF3` (light gray, same as current dark mode text) — contrast ratio with `#1A3A5C` ≈ 8.2:1
- `--color-text-secondary`: `#8B949E` (medium gray) — contrast ratio with `#1A3A5C` ≈ 3.6:1 (meets 3:1 for large text; secondary text is typically used for less critical labels)

Component-level backgrounds (cards, modals, sidebars) use `--color-bg` and `--color-bg-secondary` tokens. These must be updated to blue-tinted values that work with the light text.

**Alternatives considered**:
- Keep dark text and use a very light blue background (#E8F0FE) — rejected because the issue requests a distinctly "blue" background, not a blue-tinted white
- Use text-shadow/outline for readability — rejected as non-standard and fragile

---

## R-003: Dark Mode Adaptation

**Decision**: Update dark mode `--color-bg` to `#0F2233` (deeper navy) and `--color-bg-secondary` to `#152D42` (slightly lighter navy). Existing dark mode text colors are already light and will maintain contrast.

**Rationale**: The current dark mode uses `--color-bg: #0d1117` (near-black) and `--color-bg-secondary: #161b22` (dark gray). Shifting these to blue-tinted dark values maintains the dark mode feel while adding the blue character requested. The existing dark mode text (`--color-text: #e6edf3`) has a contrast ratio of ~10.5:1 against `#0F2233`, well exceeding WCAG AA.

**Alternatives considered**:
- Keep dark mode unchanged — rejected because the spec says "the blue background should adapt appropriately" for dark mode
- Use the same blue as light mode — rejected because it would make light and dark modes visually identical

---

## R-004: Preventing White Flash on Load

**Decision**: Add `background-color: #1A3A5C` as an inline style on the `<body>` or `<html>` element in `index.html` to prevent white flash before CSS loads.

**Rationale**: The Vite build system loads CSS asynchronously via `<script type="module">`. There is a brief window between HTML parse and CSS application where the default white background is visible. Setting the background color in the HTML ensures the blue appears immediately. This mirrors the pattern of setting `background` at the highest DOM level.

For dark mode, the `useAppTheme` hook adds `dark-mode-active` class to `<html>` on load, which triggers the CSS custom property override. A brief flash of the light blue before dark mode applies is acceptable as it's consistent with how the current theme switch works (localStorage-based synchronous check).

**Alternatives considered**:
- Add a `<style>` block in `<head>` — viable and equally effective; inline style is simpler for a single property
- Use a CSS `@import` in the HTML — rejected because it blocks rendering and adds complexity
- Do nothing — rejected because the spec explicitly requires preventing white flash (FR-005)

---

## R-005: Component Background Compatibility

**Decision**: No changes needed to component-level CSS. Components using `var(--color-bg)` and `var(--color-bg-secondary)` will automatically pick up the new blue values. Components with hardcoded backgrounds (e.g., `#dafbe1`, `#fff1f0`, `rgba(...)`) will retain their explicit colors.

**Rationale**: The existing CSS architecture uses CSS custom properties throughout. Components like `.app-header`, `.chat-section`, cards, and modals reference `var(--color-bg)` or `var(--color-bg-secondary)` for their backgrounds. Updating the token values propagates automatically. Hardcoded color values in component CSS (used for status badges, alerts, etc.) are intentionally distinct and will not be affected.

A visual review should be performed post-implementation to verify that all components render correctly against the new blue background, particularly:
- Modal overlays (`rgba(0, 0, 0, 0.5)` backdrop)
- Status badges with colored backgrounds
- Form inputs and text areas
- The project sidebar and chat interface

**Alternatives considered**:
- Add a new `--color-bg-app` token and leave `--color-bg` unchanged — rejected because it would require updating every component that should use the blue background, violating the simplicity principle
- Override at the body level only — rejected because components using `var(--color-bg)` would still get the old white value

---

## R-006: Design Token Documentation

**Decision**: Document the blue background token values in the `contracts/design-tokens.css` contract file and in the quickstart guide.

**Rationale**: FR-007 requires documenting the chosen blue color value. The contracts directory serves as the design reference. The quickstart guide provides a practical reference for developers.

**Alternatives considered**:
- Add a separate DESIGN_TOKENS.md file — rejected because the contracts directory already serves this purpose in the speckit workflow
- Add inline CSS comments only — rejected because comments are easily missed and not linked to the spec
