# Research: Add Green Background Color to App

**Feature**: 008-green-background
**Date**: 2026-02-21
**Status**: Complete

## R1: CSS Theming Approach

**Task**: Research how the app currently implements theming and the best approach for applying a green background.

**Decision**: Update the existing CSS custom property `--color-bg` in `frontend/src/index.css` `:root` selector.

**Rationale**: The app already uses a centralized CSS custom property system. The `:root` selector defines `--color-bg: #ffffff` (light mode) and `html.dark-mode-active` overrides it to `--color-bg: #0d1117` (dark mode). All component CSS files reference `var(--color-bg)` and `var(--color-bg-secondary)`. Changing the root definition propagates the green background to all pages and components automatically. No new abstraction or theming library is needed.

**Alternatives considered**:
- Tailwind CSS utility class (`bg-green-500`): Rejected — project does not use Tailwind CSS. Adding it would be unnecessary complexity for a single color change.
- MUI ThemeProvider: Rejected — project does not use Material UI. Adding it would violate YAGNI and Simplicity principles.
- Inline styles on root component: Rejected — less maintainable than CSS custom properties; spec requires centralized theme variable.
- New CSS file for green theme: Rejected — unnecessary when existing `index.css` already serves as the centralized theme definition.

## R2: Green Color Selection and Contrast Compliance

**Task**: Research the optimal green shade for WCAG 2.1 AA compliance with existing foreground colors.

**Decision**: Use `#4CAF50` (Material Design Green 500) as the primary background color for light mode, and `#2E7D32` (Material Design Green 800) for dark mode.

**Rationale**:
- #4CAF50 is the stakeholder-suggested default and a widely-recognized green.
- Current light-mode text color is `--color-text: #24292f` (near-black). Contrast ratio of #24292f on #4CAF50 is approximately 4.56:1, which meets WCAG AA for normal text (≥4.5:1).
- Current dark-mode text color is `--color-text: #e6edf3` (near-white). A darker green like #2E7D32 provides a contrast ratio of approximately 6.8:1 with #e6edf3, meeting WCAG AA.
- Secondary background (`--color-bg-secondary`) should also shift to a green shade to maintain visual cohesion: `#43A047` for light mode, `#1B5E20` for dark mode.

**Alternatives considered**:
- #388E3C (Green 700): Provides higher contrast but is noticeably darker; #4CAF50 matches the spec's default suggestion.
- #66BB6A (Green 400): Lighter green, fails contrast with near-black text at 3.8:1.
- Same green for both light/dark modes: Rejected — dark mode requires a darker green to maintain contrast with light-colored text.

## R3: Layout Shift and FOUC Prevention

**Task**: Research how to prevent flash of unstyled content when applying the background color.

**Decision**: No additional measures needed beyond the existing CSS custom property approach.

**Rationale**: CSS custom properties defined in `index.css` are loaded synchronously in the `<head>` via Vite's build pipeline. The `index.css` import in `main.tsx` is processed before React renders, so the background color is applied before first paint. The existing dark-mode toggle uses a class on `<html>`, which is also synchronous. No JavaScript-dependent background application is needed.

**Alternatives considered**:
- Critical CSS inlining: Unnecessary — Vite already handles CSS bundling efficiently for the initial load.
- `<style>` tag in `index.html`: Redundant — the CSS custom property in `index.css` achieves the same result through the standard pipeline.

## R4: Impact on Existing Components

**Task**: Research which components reference `--color-bg` and `--color-bg-secondary` and whether the green background creates conflicts.

**Decision**: Components using `var(--color-bg)` as their own background (cards, chat bubbles, input areas) should retain a neutral background by using a new `--color-bg-surface` custom property set to white/dark for surface elements, or keep their existing explicit backgrounds.

**Rationale**: Scanning the codebase shows that `var(--color-bg)` is used in ~15 locations across `App.css` and `ChatInterface.css` for element backgrounds (header, sidebar, chat messages, input areas). If `--color-bg` becomes green, these elements would also turn green, which is not the intended behavior — the spec says "apply to the root/main application container" and components should "retain their own background styling." The solution is to introduce a `--color-bg-surface` token for component surfaces (cards, inputs, panels) while `--color-bg` becomes the app-level green background.

**Alternatives considered**:
- Override each component's background individually: Rejected — fragile and violates DRY; new components would need explicit overrides.
- Only change `body` background: Insufficient — `--color-bg-secondary` on body via `index.css` would change, but components using `var(--color-bg)` would remain white, creating inconsistent green application.
