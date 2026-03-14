# Research: Frontend Theme Audit — Light/Dark Mode Contrast & Style Consistency

**Feature**: `037-theme-contrast-audit` | **Date**: 2026-03-12 | **Phase**: 0

## Research Tasks

### R-01: Theming Architecture and Token System

**Context**: Understand how the Celestial design system implements Light/Dark theming.

**Decision**: The application uses a CSS custom property–based theming system with Tailwind CSS v4's `@theme` block. Theme tokens are HSL values defined in `:root` (Light) and `.dark` (Dark) selectors in `frontend/src/index.css`. The `ThemeProvider` React context toggles `.light`/`.dark` classes on `<html>`, persists to `localStorage`, and supports `'system'` mode via `prefers-color-scheme`.

**Rationale**: This architecture ensures theme changes propagate through CSS inheritance — any component using `hsl(var(--token))` or Tailwind color utilities automatically adapts. The 600ms transition class (`theme-transitioning`) prevents FOUC.

**Alternatives considered**:
- CSS-in-JS theming (styled-components/emotion): Rejected — project already established on Tailwind + CSS custom properties.
- Data attribute theming (`[data-theme="dark"]`): Viable but `.dark` class is already integrated with Tailwind's `dark:` variant prefix.

---

### R-02: Hardcoded Color Inventory

**Context**: Identify all color values that bypass the theming system (FR-001).

**Decision**: The audit identified four categories of hardcoded colors requiring attention:

1. **Agent Avatar SVGs** (`AgentAvatar.tsx`): ~30 hardcoded hex fill/stroke values for 12 avatar variants. These are decorative/illustrative and use intentionally fixed colors (gold suns, silver moons). **Acceptable exception** — avatar icons are theme-independent visual identifiers that must remain recognizable in both modes.

2. **GitHub Status Colors** (`colorUtils.ts`): 8 hex colors and 8 rgba background variants for GitHub issue status labels. These represent external GitHub API colors and must remain recognizable. **Requires audit** — verify contrast in both themes; consider adding subtle dark-mode opacity adjustments.

3. **Issue Card Badges** (`IssueCard.tsx`): Pipeline badge `#0052cc` and Agent badge `#7057ff` with 18% alpha backgrounds. **Requires audit** — verify these maintain ≥3:1 contrast against card backgrounds in both themes.

4. **GitHub Labels** (`IssueCard.tsx`): Dynamic `#${safeColor}` from GitHub API data with 18% alpha backgrounds. **Requires audit** — verify label color + alpha combinations maintain contrast in both themes.

**Rationale**: Not all hardcoded colors are defects. External data colors (GitHub labels/statuses) and decorative SVG illustrations are valid exceptions when they maintain contrast in both themes. The key requirement is that no hardcoded color causes a contrast failure.

**Alternatives considered**:
- Converting all hardcoded colors to theme tokens: Rejected for GitHub-sourced colors (would lose visual consistency with GitHub's own UI).
- Creating dark-mode token variants for every hardcoded color: Viable for status colors; excessive for SVG decorative illustrations.

---

### R-03: WCAG 2.1 AA Contrast Compliance

**Context**: Determine approach for programmatically verifying contrast ratios (FR-002, FR-003).

**Decision**: Use a two-pronged approach:
1. **Automated scanning**: Implement a contrast-checking script that computes the WCAG relative luminance formula against all token pairs (foreground vs. background) for both Light and Dark modes. Thresholds: ≥4.5:1 for normal text, ≥3:1 for large text and UI boundaries.
2. **Manual review**: Systematically inspect each component category (buttons, badges, inputs, cards, modals, etc.) in both themes for interactive-state contrast.

**Rationale**: Automated checks can verify the token-level contrast pairs exhaustively. Manual review catches context-dependent issues (layered overlays, dynamic content, gradient backgrounds) that automated tools miss.

**Alternatives considered**:
- axe-core runtime scanning: Good for rendered DOM but requires a running application and doesn't catch all token pairs.
- Storybook a11y addon: Project does not use Storybook (no setup exists).
- Pure manual review: Insufficient for 146+ component files; too error-prone.

---

### R-04: Shadow Definitions and Dark Mode

**Context**: The `@theme` block defines shadows with hardcoded `rgba()` values that do not change in dark mode.

**Decision**: The four shadow tokens use warm brown tones (`rgba(41, 29, 12, ...)`) optimized for Light mode. In Dark mode, these shadows may appear as visible dark spots against the navy background rather than subtle elevation indicators. **Requires correction**: Either define dark-mode shadow overrides in the `.dark` selector or use `color-mix()` with theme tokens.

**Rationale**: Shadows serve as elevation indicators. In dark themes, shadows should be deeper/more opaque against the dark background, using cooler tones that complement the navy palette.

**Alternatives considered**:
- Removing shadows in dark mode: Rejected — elevation hierarchy is important for UI depth.
- Using `box-shadow` with `hsl(var(--night))` opacity variants: Viable and consistent with existing token system.
- Using Tailwind's `dark:shadow-*` utilities: Would require per-component overrides rather than a single token fix.

---

### R-05: Interactive State Styling Best Practices

**Context**: Ensure hover, focus, active, and disabled states meet contrast requirements (FR-004).

**Decision**: Follow a systematic approach:
- **Focus indicators**: Must use `ring` token (already mapped to `--ring`) with ≥3:1 contrast against adjacent backgrounds. The `celestial-focus` class is already applied to interactive elements on the Agents page — verify this pattern is used consistently across all pages.
- **Hover states**: Must produce a visible change (color shift, background change, or border emphasis) while maintaining text contrast.
- **Disabled states**: Must appear visually muted (reduced opacity or contrast) while maintaining ≥3:1 text-to-background contrast.
- **Active states**: Must provide immediate feedback (pressed effect, color intensification).

**Rationale**: The existing `celestial-focus` pattern and Tailwind's `hover:`, `focus:`, `disabled:` variants provide the infrastructure. The audit verifies consistent application.

**Alternatives considered**:
- Global focus-visible stylesheet: Could miss component-specific styling needs.
- CSS `:focus-within` only: Insufficient — direct `:focus-visible` indicators are required for keyboard accessibility.

---

### R-06: Third-Party Component Theme Inheritance

**Context**: Verify Radix UI and other third-party components adopt theme context (FR-010).

**Decision**: The project uses Radix UI primitives (Tooltip, Slot) which render in portals attached to `document.body`. Since the ThemeProvider applies `.dark` to `<html>`, all portaled content inherits theme context through CSS. **Verified safe**: All 9 identified `createPortal` usages mount to `document.body`, which is a descendant of the themed `<html>` element.

**Rationale**: Radix UI's portal strategy is compatible with the CSS class–based theming approach. No CSS encapsulation (Shadow DOM) is used, so theme inheritance is guaranteed.

**Alternatives considered**:
- Wrapping portals in separate ThemeProvider instances: Unnecessary — DOM inheritance handles it.
- Using Radix UI's built-in theming: The project uses custom Celestial tokens rather than Radix's default theme.

---

### R-07: Theme Transition and FOUC Prevention

**Context**: Verify that theme-switching produces no visual glitches (FR-009).

**Decision**: The ThemeProvider uses a `theme-transitioning` class with 600ms duration to smooth color transitions. The implementation correctly:
1. Adds transition class before toggling theme
2. Removes `light`/`dark` class
3. Adds new theme class
4. Removes transition class after 600ms timeout

**Risk area**: The class removal and re-addition happens synchronously within the same effect, which means the browser should batch the change. However, the transition class is added on every theme change except the first render (`isFirstRender` ref). This is correct behavior.

**Rationale**: The existing implementation follows best practices for CSS-class-based theme transitions. No FOUC risk detected in the current architecture.

**Alternatives considered**:
- `View Transitions API`: Modern but limited browser support; overkill for class-toggle transitions.
- `prefers-color-scheme` media query only (no JS toggle): Would lose user preference override capability.

---

### R-08: Solar Utility Classes Dark Mode Coverage

**Context**: Verify all `solar-*` classes have proper `.dark` overrides.

**Decision**: The 28 solar-* utility classes include explicit `.dark` overrides for:
- `.solar-chip-success` → `.dark .solar-chip-success`
- `.solar-chip-warning` → `.dark .solar-chip-warning`
- `.solar-chip-danger` → `.dark .solar-chip-danger`
- `.solar-chip-violet` → `.dark .solar-chip-violet`
- `.solar-text-success` → `.dark .solar-text-success`
- `.solar-action-danger` → `.dark .solar-action-danger`

**Requires verification**: The base `solar-chip`, `solar-chip-soft`, `solar-chip-neutral`, `solar-action`, and `solar-halo` classes use `hsl(var(...))` and `border-primary/30` patterns that should automatically adapt. Need to confirm all border/bg/text combinations meet contrast thresholds in dark mode.

**Rationale**: Classes using CSS custom property references are inherently theme-aware. Classes using hardcoded `rgb()` values for semantic colors correctly provide `.dark` overrides with appropriate lighter values.

**Alternatives considered**:
- Converting all rgb() values to CSS custom properties: Would centralize but add indirection; current approach with explicit .dark overrides is clear and maintainable.

---

### R-09: Scrollbar and Browser Chrome Styling

**Context**: Determine if custom scrollbar styling is needed (Edge case from spec).

**Decision**: No custom scrollbar styling exists in the project. The application uses default system scrollbars. This is **acceptable** — system scrollbars automatically adapt to the OS dark/light mode preference. Custom scrollbar styling (`::-webkit-scrollbar`) is non-standard and adds maintenance burden.

**Rationale**: System scrollbars provide the most consistent cross-browser experience and automatically respect the user's OS theme preference.

**Alternatives considered**:
- Custom `::-webkit-scrollbar` styling with theme tokens: Would only work in WebKit/Blink browsers.
- `scrollbar-color` CSS property: Standardized but limited browser support.
- Overlay scrollbar libraries: Adds dependency for minimal visual benefit.

---

### R-10: Priority and Sync Status Colors

**Context**: The priority (P0-P3) and sync status tokens are identical in Light and Dark modes.

**Decision**: The priority tokens (`--priority-p0` through `--priority-p3`) and sync tokens (`--sync-connected`, etc.) share the same HSL values between `:root` and `.dark`, with only sync tokens getting slightly adjusted lightness values in dark mode. **Requires verification**: These colors are used for badges and status indicators that appear against various backgrounds. Need to confirm ≥3:1 contrast in both themes.

**Rationale**: Status/priority colors need to remain recognizable across themes (red = critical, green = good). Slight lightness adjustments in dark mode maintain recognition while improving contrast against dark backgrounds.

**Alternatives considered**:
- Significantly different hues per theme: Would confuse users who associate colors with severity levels.
- Adding background token pairs for each status: More robust but increases token count.
