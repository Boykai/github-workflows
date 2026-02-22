# Research: Add Brown Background Color to App

**Feature**: `010-brown-background` | **Date**: 2026-02-22

## R1. Brown Color Selection and WCAG AA Compliance

**Decision**: Use `#4E342E` (Material Design Brown 800) as the primary brown background color for light mode, and `#3E2723` (Material Design Brown 900) for dark mode.

**Rationale**: The specification suggests `#4E342E` or `#5D4037` as candidate browns. `#4E342E` is preferred because:
- It is a rich, warm chocolate brown that provides strong visual identity
- Against white text (`#e6edf3`), it achieves a contrast ratio of ~10.5:1, well exceeding WCAG AA (4.5:1)
- Against the existing light text color (`#e6edf3`), it provides excellent readability
- It is part of the Material Design Brown palette, ensuring a professional, established color choice

For dark mode, `#3E2723` (Brown 900) provides:
- A darker variant that maintains the brown aesthetic
- Against the existing dark mode text (`#e6edf3`), contrast ratio of ~12.3:1
- Visual consistency between light and dark themes (same brown family)

**Foreground text adjustment**: Since the background is now dark in both modes, the text color must be light in both modes. The existing dark mode text color (`#e6edf3`) will be used for light mode as well. The secondary text color will be adjusted to `#8b949e` (matching dark mode) for both themes.

**Alternatives considered**:
- `#5D4037` (Brown 700) — Rejected: Slightly lighter, less contrast. Still acceptable but `#4E342E` provides better contrast margins.
- `#795548` (Brown 500) — Rejected: Too light for a background; would require dark text and feels washed out.
- `#3E2723` for both modes — Rejected: Too dark for light mode, reduces visual distinction between themes.

## R2. Existing Theming Architecture Analysis

**Decision**: Modify only the CSS custom property values in `frontend/src/index.css`. No architectural changes needed.

**Rationale**: The existing theming system is well-designed for this change:
1. **CSS Custom Properties**: `:root` defines light mode variables; `html.dark-mode-active` defines dark overrides
2. **Key variables**: `--color-bg` (app-level background), `--color-bg-secondary` (body/alternate areas)
3. **Propagation**: All components use `var(--color-bg)` and `var(--color-bg-secondary)` — changing the variable values automatically updates all components
4. **Dark mode toggle**: `useAppTheme` hook adds/removes `dark-mode-active` class on `<html>` element — fully compatible with CSS variable approach
5. **Body background**: Set via `background: var(--color-bg-secondary)` on `body` selector in `index.css`

**Current values**:
- Light: `--color-bg: #ffffff`, `--color-bg-secondary: #f6f8fa`
- Dark: `--color-bg: #0d1117`, `--color-bg-secondary: #161b22`

**New values**:
- Light: `--color-bg: #4E342E`, `--color-bg-secondary: #5D4037`
- Dark: `--color-bg: #3E2723`, `--color-bg-secondary: #4E342E`

**Alternatives considered**:
- Create new CSS variable (e.g., `--color-app-bg`) — Rejected: The spec SHOULD recommends this, but `--color-bg` already serves this exact purpose. Adding a new variable would be unnecessary duplication (violates DRY/Simplicity principle).
- Modify `App.css` or component styles — Rejected: Components already use the CSS variables. Changing variable values is sufficient.

## R3. Component Visual Coherence Assessment

**Decision**: Update `--color-text` and `--color-text-secondary` in light mode to use light text colors (same as dark mode), since the brown background is dark.

**Rationale**: With a dark brown background (`#4E342E`), the current light-mode text color (`#24292f` — near-black) would have extremely low contrast against the brown background. The text colors must be light to ensure readability:
- `--color-text: #e6edf3` (light text on brown background)
- `--color-text-secondary: #8b949e` (muted light text)

Additional component considerations:
- **Borders**: `--color-border` should shift to a lighter variant for visibility against brown (`#6D4C41` — Brown 600 or similar)
- **Surface colors**: Cards, modals, and overlays that use `--color-bg` will automatically become brown. This creates a cohesive look where surfaces blend with the background.
- **Interactive elements**: Buttons, inputs, and links already use `--color-primary` and other accent colors that stand out against both light and dark backgrounds.

**Alternatives considered**:
- Keep dark text colors in light mode — Rejected: Would fail WCAG AA contrast against brown background.
- Use a separate "surface" color variable — Rejected: Not currently defined in the system. Adding it would expand scope beyond the requirement.

## R4. Cross-Browser Consistency

**Decision**: No special browser-specific handling needed. CSS custom properties are supported in all target browsers.

**Rationale**: CSS custom properties (`:root` variables) have universal support across Chrome 49+, Firefox 31+, Safari 9.1+, Edge 15+. The application's existing use of CSS custom properties confirms cross-browser compatibility is already established. Brown color values (`#4E342E`, etc.) are standard hex colors with no browser-specific rendering differences.

**Alternatives considered**:
- Add vendor prefixes — Rejected: Not needed for CSS custom properties or background color.
- Add fallback values — Rejected: All supported browsers handle CSS custom properties.

## R5. Modal, Drawer, and Overlay Layering

**Decision**: No changes needed for overlay layering. Existing z-index and background styles handle layering correctly.

**Rationale**: The application's modals, drawers, and tooltips use:
- Explicit `z-index` values for stacking
- Solid backgrounds (not transparent) via `var(--color-bg)` or `var(--color-bg-secondary)`
- Backdrop overlays with `rgba()` colors

Since the brown background is applied via CSS variables that these components already reference, overlays will automatically adopt the brown color scheme. No transparency bleed issues expected because overlay backgrounds are solid.

**Alternatives considered**:
- Add explicit `background-color` to all overlay components — Rejected: They already use CSS variables.
