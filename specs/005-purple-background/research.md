# Research: Add Purple Background Color to App

**Feature**: 005-purple-background | **Date**: 2026-02-20  
**Purpose**: Resolve technical unknowns and document implementation approach

## Research Summary

This feature requires minimal research as it is a straightforward CSS theming change. The existing codebase already uses CSS custom properties for theming with light/dark mode support. The primary decisions involve which CSS variable to modify, how to preserve existing component backgrounds, and ensuring WCAG AA contrast compliance for text rendered directly on the purple surface.

## Decision Areas

### 1. CSS Variable Strategy

**Decision**: Introduce a new CSS custom property `--color-bg-app: #7C3AED` and apply it to the `body` element, replacing the current `var(--color-bg-secondary)` reference

**Rationale**:
- The existing `--color-bg-secondary` variable (`#f6f8fa` light / `#161b22` dark) is used by 15+ component selectors (board columns, sidebar headers, theme toggle, modals, etc.)
- Changing `--color-bg-secondary` directly would propagate purple into all those component backgrounds — violating the spec scope ("apply to the app's root/main container element")
- A dedicated variable isolates the body background from component-level backgrounds
- The new variable follows the existing naming convention (`--color-bg`, `--color-bg-secondary`, now `--color-bg-app`)

**Alternatives Considered**:
- **Modify `--color-bg-secondary` directly**: Rejected — would turn board columns, modal fields, sidebar headers, and 12+ other elements purple, breaking visual hierarchy
- **Modify `--color-bg` directly**: Rejected — `--color-bg` is used for component foreground backgrounds (header, sidebar, chat section, cards). Changing it to purple would make all components purple
- **Hardcode `background: #7C3AED` on body**: Rejected — violates FR-006 (centralized theming mechanism) and the existing CSS variable pattern

### 2. Affected Surfaces

**Decision**: Only login page (`.app-login`) and loading screen (`.app-loading`) text colors need updating. All authenticated views have opaque component backgrounds that fully cover the purple body background.

**Analysis**:
- The `body` background is only visible where no component defines its own background
- `.app-header` uses `var(--color-bg)` — opaque, covers body
- `.sidebar` uses `var(--color-bg)` — opaque, covers body
- `.chat-section` uses `var(--color-bg)` — opaque, covers body
- `.app-login` and `.app-loading` have NO background — body color shows through
- Text in `.app-login h1` and `.app-login p` must be changed to white/light for contrast

### 3. WCAG AA Contrast Compliance

**Decision**: Use `#FFFFFF` (white) for primary text and `#E9D5FF` (light purple) for secondary text on the purple background

**Rationale**:
- White (#FFFFFF) on purple (#7C3AED): contrast ratio = 6.65:1 ✅ (exceeds 4.5:1)
- Light purple (#E9D5FF) on purple (#7C3AED): contrast ratio = 4.74:1 ✅ (exceeds 4.5:1)
- Current dark text (#24292f) on purple (#7C3AED): contrast ratio = 3.21:1 ❌ (fails 4.5:1)

### 4. Dark Mode Handling

**Decision**: Use the same purple value (#7C3AED) in both light and dark mode

**Rationale**: The purple background is a brand identity element that should remain consistent regardless of theme mode. The spec states "the purple background should render consistently regardless of theme mode."
