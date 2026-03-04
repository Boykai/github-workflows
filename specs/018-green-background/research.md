# Research: Add Green Background Color to App

**Feature**: 018-green-background | **Date**: 2026-03-04

## Research Tasks

### 1. Existing Design Token System

**Task**: Determine how the project defines and consumes design tokens for background colors.

**Findings**: The project uses CSS custom properties in HSL format defined in `frontend/src/index.css`. Two selector blocks define the full theme:

- `:root` — light mode tokens (default)
- `.dark` — dark mode tokens (applied via class on `<html>`)

The `ThemeProvider` component (`frontend/src/components/ThemeProvider.tsx`) toggles the `dark`/`light` class on `document.documentElement`. Tailwind CSS consumes these via `hsl(var(--background))` mappings in `tailwind.config.js`. The `body` element uses `@apply bg-background text-foreground` which resolves to `background-color: hsl(var(--background))` and `color: hsl(var(--foreground))`.

**Decision**: Modify the `--background` and `--foreground` CSS custom properties in both `:root` and `.dark` selectors.
**Rationale**: This is the established pattern in the codebase. Changing CSS variables at the root propagates automatically to all components via the Tailwind `bg-background` utility.
**Alternatives considered**: (1) Adding a new CSS class on `body` — rejected because it would bypass the existing token system and create maintenance burden. (2) Modifying `tailwind.config.js` color definitions — rejected because the colors are already indirected through CSS vars; the config doesn't need changes.

---

### 2. HSL Conversion for Target Green Colors

**Task**: Convert the specified hex colors (#4CAF50 light, #2E7D32 dark) to HSL format matching the existing token pattern.

**Findings**: The existing CSS variables use "H S% L%" format (space-separated HSL without the `hsl()` wrapper, since Tailwind adds the wrapper via `hsl(var(--background))`).

Color conversions:
- **#4CAF50** (Material Green 500): HSL → `122 39% 49%`
- **#2E7D32** (Material Green 800): HSL → `125 35% 33%`

Foreground colors for contrast:
- Light mode foreground on #4CAF50: Existing near-black (`222.2 84% 4.9%`) gives contrast ratio ~6.6:1 ✅ (passes WCAG AA for normal text)
- Light mode foreground on #4CAF50: White (`0 0% 100%`) gives contrast ratio ~3.0:1 ❌ (fails WCAG AA for normal text)
- Dark mode foreground on #2E7D32: White (`0 0% 100%`) gives contrast ratio ~5.1:1 ✅ (passes WCAG AA for normal text)

**Decision**: Use `122 39% 49%` for light mode `--background` and `125 35% 33%` for dark mode `--background`. Keep existing near-black `--foreground` (`222.2 84% 4.9%`) in light mode; set `--foreground` to white (`0 0% 100%`) in dark mode only.
**Rationale**: Direct HSL conversions of the specified colors. White foreground on #4CAF50 only achieves ~3.0:1 contrast, failing WCAG AA. Keeping the existing dark foreground in light mode provides ~6.6:1 contrast. White foreground on #2E7D32 in dark mode achieves ~5.1:1 contrast.
**Alternatives considered**: (1) Using a lighter green (#81C784) — rejected because it was not requested and would reduce contrast with white text. (2) Using white text on #4CAF50 — rejected because it gives only ~3.0:1 ratio, failing WCAG AA for normal text.

---

### 3. Impact on Existing Components

**Task**: Assess whether changing `--background` affects components beyond the page background.

**Findings**: The `--background` variable is used by:
- `body` via `@apply bg-background` — the intended target
- Any component using `bg-background` Tailwind class — these will also turn green

Components with their own background tokens (`--card`, `--popover`, `--secondary`, `--muted`, `--accent`) are **not affected** since they use separate CSS variables. The shadcn/ui components (Card, Popover, Dialog, etc.) use their own tokens.

**Decision**: Only modify `--background` and `--foreground`. Leave all other tokens (`--card`, `--popover`, `--primary`, etc.) unchanged.
**Rationale**: The spec explicitly states "System MUST NOT break existing layout, component positioning, or functionality." Since cards, popovers, and modals use separate tokens, they will retain their current colors. The green background will be visible as the page-level background behind/around these components.
**Alternatives considered**: Updating all related tokens (card, popover, etc.) to green variants — rejected because the spec only requests the app background, and cascading green to all surfaces would dramatically alter the UI beyond the request scope.

---

### 4. Dark Mode Support

**Task**: Verify that the app supports dark mode and determine the approach for a dark green variant.

**Findings**: The app fully supports dark mode via the `ThemeProvider` component which toggles `.dark` class on `<html>`. The `.dark` selector in `index.css` already defines dark mode tokens. The app also supports a "system" preference that follows `prefers-color-scheme`.

**Decision**: Update the `.dark` selector's `--background` to `125 35% 33%` (#2E7D32) and `--foreground` to `0 0% 100%` (white).
**Rationale**: The spec recommends #2E7D32 for dark mode. The existing dark mode infrastructure requires no code changes — only the CSS variable values need updating.
**Alternatives considered**: N/A — the approach is straightforward given the existing dark mode support.

---

### 5. Responsive Behavior

**Task**: Verify that the green background will render correctly across all viewport sizes.

**Findings**: The `body` element already has `@apply bg-background` applied globally. CSS custom properties and background-color on `body` are inherently responsive — they fill 100% of the viewport regardless of screen size. No media queries or viewport-specific overrides are needed.

**Decision**: No additional responsive handling required.
**Rationale**: The existing CSS architecture already ensures full-viewport coverage.
**Alternatives considered**: N/A.

## Summary of Decisions

| Area | Decision | Confidence |
|------|----------|------------|
| Token system | Modify existing CSS custom properties in `index.css` | High |
| Light mode green | `--background: 122 39% 49%` (#4CAF50) | High |
| Dark mode green | `--background: 125 35% 33%` (#2E7D32) | High |
| Foreground color | Light: `--foreground` unchanged (`222.2 84% 4.9%`, near-black); Dark: `--foreground: 0 0% 100%` (white) | High |
| WCAG compliance | Near-black on #4CAF50 = ~6.6:1 ✅; White on #2E7D32 = ~5.1:1 ✅ | High |
| Component impact | Only page-level background changes; cards/popovers/modals unaffected | High |
| Files modified | `frontend/src/index.css` only | High |
| New dependencies | None | High |
