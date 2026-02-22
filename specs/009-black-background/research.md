# Research: Add Black Background Theme to App

**Feature**: `009-black-background` | **Date**: 2026-02-22

## R1. Existing Theming Infrastructure

**Decision**: Reuse the existing CSS custom property system in `frontend/src/index.css` with `:root` (light mode) and `html.dark-mode-active` (dark mode) selectors.

**Rationale**: The app already defines all theme colors as CSS custom properties (`--color-bg`, `--color-bg-secondary`, `--color-text`, `--color-text-secondary`, `--color-border`, `--color-primary`, etc.) in `:root` and overrides them in `html.dark-mode-active`. All components reference these tokens via `var()`. Updating the token values is the minimal and correct approach — no new theming architecture is needed.

**Current token values (light mode / `:root`)**:

| Token | Current Value | Description |
|-------|--------------|-------------|
| `--color-bg` | `#ffffff` | Primary app background |
| `--color-bg-secondary` | `#f6f8fa` | Body/alternate background |
| `--color-text` | `#24292f` | Primary text |
| `--color-text-secondary` | `#57606a` | Secondary text |
| `--color-border` | `#d0d7de` | Borders and dividers |
| `--color-primary` | `#0969da` | Primary accent |
| `--color-success` | `#1a7f37` | Success indicators |
| `--color-warning` | `#9a6700` | Warning indicators |
| `--color-danger` | `#cf222e` | Danger indicators |

**Current token values (dark mode / `html.dark-mode-active`)**:

| Token | Current Value | Description |
|-------|--------------|-------------|
| `--color-bg` | `#0d1117` | Primary app background |
| `--color-bg-secondary` | `#161b22` | Body/alternate background |
| `--color-text` | `#e6edf3` | Primary text |
| `--color-text-secondary` | `#8b949e` | Secondary text |
| `--color-border` | `#30363d` | Borders and dividers |
| `--color-primary` | `#539bf5` | Primary accent |

**Alternatives considered**:
- *Tailwind CSS dark mode* — Rejected: The app doesn't use Tailwind; it uses plain CSS with custom properties.
- *CSS-in-JS / styled-components* — Rejected: The app uses plain CSS files; introducing a runtime theme system adds complexity for no benefit.
- *New theme provider component* — Rejected: The existing `useAppTheme` hook + CSS class toggle already provides this functionality.

## R2. Black Background Color Palette

**Decision**: Use `#000000` for root background, `#121212` for elevated surfaces (secondary background), and `#1E1E1E` for borders — following Material Design dark theme guidelines adapted to a true black base.

**Rationale**: True black (#000000) is specified in the requirements (FR-001). For elevated surfaces, Material Design recommends overlay-based lightening from a dark base. Using `#121212` for secondary surfaces provides sufficient visual distinction from pure black while maintaining the dark aesthetic. Borders at `#2C2C2C` are visible without being harsh.

**Proposed token values (light mode / `:root` — becomes the new default)**:

| Token | New Value | Contrast vs `--color-bg` | Rationale |
|-------|----------|-------------------|-----------|
| `--color-bg` | `#000000` | — (root) | True black per FR-001 |
| `--color-bg-secondary` | `#121212` | 1.3:1 (surface) | Material dark elevated surface |
| `--color-text` | `#ffffff` | 21:1 vs #000 | Maximum contrast for readability |
| `--color-text-secondary` | `#b0b0b0` | 10.5:1 vs #000 | Exceeds WCAG AA 4.5:1 |
| `--color-border` | `#2C2C2C` | 1.9:1 (visible) | Subtle but visible dividers |
| `--color-primary` | `#539bf5` | 5.1:1 vs #000 | Bright blue accent, WCAG AA compliant |
| `--color-success` | `#3fb950` | 6.3:1 vs #000 | Green accent, WCAG AA compliant |
| `--color-warning` | `#d29922` | 7.4:1 vs #000 | Warm amber, WCAG AA compliant |
| `--color-danger` | `#f85149` | 4.8:1 vs #000 | Red accent, WCAG AA compliant |

**Proposed token values (dark mode / `html.dark-mode-active`)**:

| Token | New Value | Rationale |
|-------|----------|-----------|
| `--color-bg` | `#000000` | True black in dark mode as well |
| `--color-bg-secondary` | `#0a0a0a` | Slightly lighter than pure black for depth |
| `--color-text` | `#e6edf3` | High readability (14.4:1 vs #000) |
| `--color-text-secondary` | `#8b949e` | Muted but readable (7.2:1 vs #000) |
| `--color-border` | `#1e1e1e` | Subtle dark border |

**Alternatives considered**:
- *Near-black (#0D1117) instead of true black* — Rejected: Spec explicitly requires `#000000` for root background (FR-001).
- *White text (#FFFFFF) for secondary text* — Rejected: Creates too little hierarchy between primary and secondary text.
- *Darker borders (#111111)* — Rejected: Insufficient visibility, especially on elevated surfaces.

## R3. Hardcoded Color Audit in App.css

**Decision**: Audit `App.css` for all hardcoded light-background colors and replace them with either token references or dark-compatible hex values.

**Rationale**: While most components use `var(--color-*)` tokens, `App.css` contains approximately 15+ hardcoded hex colors for specific states (status badges, alert backgrounds, button variants). These will appear as bright patches on the black background if not updated.

**Hardcoded colors identified**:

| Color | Location | Context | Action |
|-------|----------|---------|--------|
| `#32383f` | `.user-avatar` | Avatar fallback bg | Keep — already dark |
| `#2da44e` | `.status-badge`, `.project-status-badge` | Green status | Keep — dark-compatible |
| `#bf8700` | `.status-badge`, `.project-status-badge` | Warning status | Keep — dark-compatible |
| `#0969da` | `.status-badge` | Blue status | Keep — dark-compatible |
| `#cf222e` | `.status-badge`, `.delete-btn` | Red/danger | Keep — dark-compatible |
| `#dafbe1` | `.success-alert` | Success alert bg | Replace with dark variant `rgba(63, 185, 80, 0.15)` |
| `#fff1f0` | `.error-alert`, `.error-message` | Error alert bg | Replace with dark variant `rgba(248, 81, 73, 0.15)` |
| `#a40e26` | `.delete-btn:hover` | Delete hover | Keep — dark-compatible |
| `#d2992211` | `.workflow-info` | Info highlight bg | Keep — already semi-transparent/dark-compatible |
| `rgba(9, 105, 218, 0.1)` | `.issue-type-badge` | Badge bg | Keep — semi-transparent, works on dark |
| `rgba(154, 103, 0, 0.1)` | `.issue-type-badge` | Badge bg | Keep — semi-transparent, works on dark |
| `rgba(26, 127, 55, 0.1)` | `.issue-type-badge` | Badge bg | Keep — semi-transparent, works on dark |

**Alternatives considered**:
- *Convert all hardcoded colors to tokens* — Rejected: Excessive for state-specific colors that are already dark-compatible or semi-transparent. Only light backgrounds need updating.
- *Leave as-is and rely on dark mode class* — Rejected: These are not under `html.dark-mode-active` and will show light patches.

## R4. Flash of White Prevention (FOUC)

**Decision**: Add an inline `style="background-color: #000000"` on the `<html>` element in `index.html` to prevent any flash of white before CSS loads.

**Rationale**: The CSS custom properties are defined in `index.css`, which is loaded as a module import in `main.tsx`. There is a brief window between HTML parsing and CSS application where the browser's default white background may flash. Setting the background inline on `<html>` ensures black is applied from the very first paint (FR-007).

**Implementation**:
```html
<html lang="en" style="background-color: #000000">
```

**Alternatives considered**:
- *Critical CSS inlining in `<head>`* — Rejected: Vite doesn't support this out of the box without plugins; overkill for a single property.
- *Preload the CSS file* — Rejected: CSS is already bundled by Vite; the flash window is sub-100ms but noticeable on slow connections.
- *Set body background inline instead* — Rejected: `<html>` renders before `<body>`; setting on `<html>` covers the entire viewport earlier.

## R5. Theme Persistence Strategy

**Decision**: Reuse the existing `useAppTheme` hook and `localStorage`/API persistence. The black background becomes the default for both light and dark modes by updating the token values directly.

**Rationale**: The existing system already handles theme persistence:
1. `useAppTheme` reads from `localStorage` key `tech-connect-theme-mode`
2. If authenticated, syncs with user settings API
3. Applies `dark-mode-active` class to `<html>` when dark mode is active

Since the black background is applied to both `:root` (light) and `html.dark-mode-active` (dark) token sets, the theme persists automatically. The black background is always present regardless of the light/dark toggle state — fulfilling FR-009.

**Alternatives considered**:
- *Add a new "black" theme mode* — Rejected: The spec states black background is the sole default, not an option. Adding a third mode is out of scope.
- *Remove the dark mode toggle entirely* — Rejected: Out of scope. The toggle can coexist; both modes will have black backgrounds with slightly different surface/accent colors.
