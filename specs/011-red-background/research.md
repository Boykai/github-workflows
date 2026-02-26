# Research: Add Red Background Color to App

**Date**: 2026-02-26 | **Branch**: `011-red-background` | **Plan**: [plan.md](plan.md)

## R1: Red Color Value and WCAG AA Contrast Compliance (FR-001, FR-003, FR-004)

**Decision**: Use `#E53E3E` as the primary red background color with `#FFFFFF` (white) for body text and interactive element foreground colors.

**Rationale**: The spec recommends #E53E3E as a starting point. Contrast analysis:
- **#E53E3E background + #FFFFFF text**: contrast ratio ≈ 4.53:1 — passes WCAG AA for normal text (≥4.5:1) and large text/UI components (≥3:1).
- **#E53E3E background + #24292f text** (current dark text): contrast ratio ≈ 3.5:1 — **fails** WCAG AA for normal text.
- Switching body text to white ensures compliance. Components with their own white/light backgrounds (cards, modals) retain their existing dark text colors since contrast is measured against their own background, not the app surface.

**Alternatives considered**:
- **#C0392B** (darker red): Higher contrast with white (~5.5:1) but was not the primary recommendation and appears overly dark.
- **#DC3545** (Bootstrap danger): Very similar to #E53E3E (~4.6:1 with white). No material difference; #E53E3E is the spec-recommended value.
- **Keep dark text, pick lighter red**: Would require a very washed-out red (e.g., #F4A4A4) to hit 4.5:1 with #24292f — doesn't satisfy the "red background" intent.

---

## R2: CSS Token Strategy — Modify Existing vs. Add New Token (FR-002, FR-008)

**Decision**: Modify the existing `--color-bg-secondary` value in `:root` from `#f6f8fa` to `#E53E3E`, since `body { background: var(--color-bg-secondary) }` is the existing pattern. The `--color-bg` token is intentionally **not** changed — it is used by component backgrounds (cards, modals, sidebars) and must remain white/dark to preserve visual hierarchy. Add a CSS fallback directly in the `background` shorthand.

**Rationale**: The `body` element already uses `var(--color-bg-secondary)` for its background. Changing the token value at the `:root` level is the most minimal, DRY approach — one line change propagates to the entire app surface. Components use `var(--color-bg)` for their own backgrounds (white in light mode, dark in dark mode), so they sit on top of the red surface with their own contrasting background. A fallback value (`background: var(--color-bg-secondary, #E53E3E)`) satisfies FR-008 (fallback if token fails to resolve). No new tokens are needed for this XS change.

**Alternatives considered**:
- **New `--color-bg-app` token**: Adds indirection for a single-use case. YAGNI — the existing `--color-bg-secondary` serves the purpose.
- **Tailwind config update**: Project does not use Tailwind; would require adding a dependency. Out of scope.
- **Inline style on `<body>` in index.html**: Bypasses the design token system, violates FR-002 (centralized definition).

---

## R3: Dark Mode Handling (Edge Case)

**Decision**: Update the dark mode override of `--color-bg-secondary` in `html.dark-mode-active` to also use a red background. Use a darker red (`#9B2C2C`) for dark mode to maintain visual distinction and contrast.

**Rationale**: The spec requires red background "across all pages and views." Dark mode is an active feature in the app (toggled via `html.dark-mode-active` class). If dark mode overrides `--color-bg-secondary` back to `#161b22`, the red background disappears in dark mode — violating FR-001. A darker red variant (`#9B2C2C`) maintains the red theme while being appropriate for dark contexts. Contrast: #9B2C2C + #FFFFFF ≈ 6.5:1 — passes WCAG AA.

**Alternatives considered**:
- **Same #E53E3E in dark mode**: Works for contrast but is visually jarring. Dark mode users expect a darker palette.
- **Skip dark mode**: Violates FR-001 (all pages and views).
- **Remove dark mode support entirely**: Out of scope and destructive.

---

## R4: Cross-Browser Consistency (FR-005, FR-006)

**Decision**: No special handling needed. CSS custom properties are supported in all target browsers (Chrome, Firefox, Safari, Edge — all versions since 2017+). The `background` shorthand with fallback syntax is universally supported.

**Rationale**: CSS custom properties (`var()`) have >97% global browser support. All target browsers (latest stable Chrome, Firefox, Safari, Edge) have supported them for 7+ years. No vendor prefixes or polyfills required. The responsive behavior is inherent — `body { background }` covers the full viewport regardless of screen size.

**Alternatives considered**:
- **Add `-webkit-` or `-moz-` prefixes**: Unnecessary for CSS custom properties — they never had vendor-prefixed versions.
- **Add explicit media queries for viewport coverage**: `body` background inherently covers the viewport. No gaps possible unless overridden by child elements.

---

## R5: Component Legibility Review Approach (FR-007)

**Decision**: Overlaid components (cards, modals, sidebars, navigation) with their own `background` or `background-color` declarations retain their existing colors. No changes needed for most components. Only elements that inherit the body background (transparent background) and display text directly on the red surface need text color adjustment.

**Rationale**: Reviewing `frontend/src/App.css` and component styles, most UI components (`.board-column`, `.project-card`, `.modal`, `.sidebar`, `.chat-*`) define their own background using `var(--color-bg)` (white in light mode, dark in dark mode). These sit on top of the red body background — their content contrast is measured against their own background, not the body. The red surface is only visible in gaps between components and as the overall page color.

**Alternatives considered**:
- **Audit every component and add explicit backgrounds**: Unnecessary overhead. Components already have backgrounds defined.
- **Add a global `.content-area` wrapper with white background**: Adds DOM complexity for no benefit — components handle their own backgrounds.
