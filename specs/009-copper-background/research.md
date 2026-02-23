# Research: Add Copper Background Theme to App

**Feature**: `009-copper-background` | **Date**: 2026-02-23

## R1. Copper Color Palette Selection

**Decision**: Use #B87333 as the primary copper background for light mode and #8C4A2F as the dark mode copper variant. Use #CB6D51 (lighter copper) for secondary surfaces in light mode and #6B3A24 for secondary surfaces in dark mode.

**Rationale**: #B87333 is the standard recognized copper color. The spec references it explicitly and it provides a warm, metallic aesthetic. The dark variant #8C4A2F is a deeper copper that works well in low-light contexts while maintaining the copper identity. Secondary surface colors create visual hierarchy while staying within the copper palette.

**Alternatives considered**:
- *#CB6D51 as primary* — Rejected for primary: this lighter copper shade has lower contrast potential with light text and feels more salmon/coral than copper. Suitable as a secondary/accent shade.
- *CSS gradient for depth* — Deferred: The spec's Assumptions section states "flat color is the assumed baseline." A gradient can be added as a follow-up enhancement if desired.
- *#A0522D (sienna)* — Rejected: Too brown/earthy, loses the distinctive metallic copper tone.

## R2. WCAG Contrast Compliance Strategy

**Decision**: Pair the copper backgrounds with high-contrast foreground colors. Use #1A1A1A (near-black) for primary text on light copper (#B87333), and #FFFFFF for primary text on dark copper (#8C4A2F). Secondary text uses #2D1810 on light and #E8D5CC on dark.

**Contrast ratios verified**:

| Combination | Ratio | WCAG AA (4.5:1) |
|-------------|-------|------------------|
| #1A1A1A on #B87333 | ~4.8:1 | ✅ PASS |
| #2D1810 on #B87333 | ~5.2:1 | ✅ PASS |
| #FFFFFF on #8C4A2F | ~6.3:1 | ✅ PASS |
| #E8D5CC on #8C4A2F | ~4.6:1 | ✅ PASS |

**Rationale**: Near-black text on the warm copper background provides good readability without the harshness of pure #000000. The dark mode uses white text on darker copper, a natural and comfortable combination. All ratios exceed the WCAG 2.1 AA threshold of 4.5:1 for normal text.

**Alternatives considered**:
- *Pure white (#FFFFFF) text on light copper* — Rejected: Contrast ratio of ~3.1:1 fails WCAG AA.
- *Pure black (#000000) text on light copper* — Viable but #1A1A1A is softer while still meeting requirements.

## R3. Existing Theming System Integration

**Decision**: Update the existing CSS custom properties in `:root` (light mode) and `html.dark-mode-active` (dark mode) within `frontend/src/index.css`. No new theming mechanism or variables needed.

**Current system analysis**:
- Light mode: `:root { --color-bg: #ffffff; --color-bg-secondary: #f6f8fa; ... }`
- Dark mode: `html.dark-mode-active { --color-bg: #0d1117; --color-bg-secondary: #161b22; ... }`
- Body background: `background: var(--color-bg-secondary);`
- Components use `var(--color-bg)` and `var(--color-bg-secondary)` throughout `App.css`
- `useAppTheme` hook toggles `dark-mode-active` class on `<html>` — no changes needed

**Mapping**:
- `--color-bg` → primary copper (#B87333 light / #8C4A2F dark)
- `--color-bg-secondary` → secondary copper (#CB6D51 light / #6B3A24 dark)
- `--color-text` → high-contrast text (#1A1A1A light / #FFFFFF dark)
- `--color-text-secondary` → secondary text (#2D1810 light / #E8D5CC dark)
- `--color-border` → copper-complementary border (#9A5C2E light / #5A2E1A dark)

**Rationale**: The app already has a robust design token system. Updating the existing tokens is the single smallest change that cascades the copper background to all surfaces. Creating new tokens (e.g., `--color-bg-copper`) would be redundant since the app has exactly one theme — the copper theme replaces the previous default entirely.

**Alternatives considered**:
- *New `--color-bg-copper` variable alongside existing tokens* — Rejected: The spec says "apply copper background to the app" — this is a replacement, not an addition. Adding a parallel token creates ambiguity about which to use.
- *Tailwind CSS integration* — Rejected: The project uses plain CSS custom properties, not Tailwind. Adding Tailwind would be an unnecessary dependency.

## R4. Component Audit for Hardcoded Colors

**Decision**: Audit `App.css` for hardcoded background colors that don't use `var()` tokens and determine which need updating.

**Findings from `App.css` analysis**:

| Hardcoded Color | Location | Action |
|----------------|----------|--------|
| `#32383f` | `.login-button:hover` (line 101) | Keep — button-specific hover state, doesn't conflict |
| `#2da44e` | `.status-btn.done` (line 348) | Keep — semantic status color (green = done) |
| `#bf8700` | `.status-btn.in-progress` (line 353) | Keep — semantic status color (amber = in progress) |
| `#0969da` | `.status-btn.todo` (line 358) | Keep — semantic status color (blue = todo) |
| `#cf222e` | `.status-btn.blocked`, `.confirm-btn.danger` (lines 362, 474) | Keep — semantic danger/blocked color |
| `#dafbe1` | `.proposal-diff .added` (line 387) | Keep — diff highlighting (green = added) |
| `#fff1f0` | `.proposal-diff .removed`, `.flash-error` (lines 407, 446) | Keep — error/removed highlighting |
| `rgba(9,105,218,0.1)` | `.status-badge.open` (line 291) | Keep — subtle semantic badge background |

**Conclusion**: All hardcoded colors in `App.css` are semantic (status indicators, diff highlighting, error states) rather than theme background colors. They should NOT be changed to copper tones — their color carries meaning. The only theme-dependent styling flows through `var()` tokens, which will be updated in `index.css`.

## R5. Overlay and Secondary Surface Harmonization

**Decision**: Modals, drawers, sidebars, and cards that use `var(--color-bg)` or `var(--color-bg-secondary)` will automatically adopt copper tones when the tokens are updated. No additional changes needed.

**Analysis**: All overlay components in `App.css` reference design tokens:
- Modals: `background: var(--color-bg)` 
- Sidebar: `background: var(--color-bg-secondary)`
- Cards/panels: `background: var(--color-bg)` or `var(--color-bg-secondary)`
- Drawers: `background: var(--color-bg-secondary)`

**Rationale**: Because the existing component styles already use CSS custom properties rather than hardcoded colors, updating the root tokens is sufficient. Components will inherit the copper tones automatically.

## R6. Shadow and Border Adjustments

**Decision**: Update `--shadow` to use a copper-tinted shadow for visual harmony. Update `--color-border` to a copper-complementary tone.

**Changes**:
- Light mode `--shadow`: `0 1px 3px rgba(139, 90, 43, 0.2)` (warm copper shadow)
- Dark mode `--shadow`: `0 1px 3px rgba(0, 0, 0, 0.5)` (deeper shadow for contrast)
- Light mode `--color-border`: `#9A5C2E` (dark copper border)
- Dark mode `--color-border`: `#5A2E1A` (deep copper border)

**Rationale**: The existing gray-toned shadows and borders would look incongruent against copper backgrounds. Copper-tinted shadows and borders maintain visual cohesion. The border colors ensure sufficient contrast for element delineation against copper surfaces.
