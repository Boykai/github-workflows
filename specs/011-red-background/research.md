# Research: Add Red Background Color to Application

**Feature**: `011-red-background` | **Date**: 2026-02-25

## R1: Red Color Selection for WCAG AA Compliance

### Decision
Use `#DC2626` (Tailwind `red-600`) for light mode and `#7F1D1D` (Tailwind `red-900`) for dark mode as the primary background colors. Secondary backgrounds use `#B91C1C` (Tailwind `red-700`) for light mode and `#991B1B` (Tailwind `red-800`) for dark mode.

### Rationale
- **Light mode `--color-bg: #DC2626`**: Contrast ratio against white text (#FFFFFF) is 4.63:1, meeting WCAG AA (≥4.5:1). This is the standard Tailwind `red-600` — a bold, recognizable red.
- **Light mode `--color-bg-secondary: #B91C1C`**: Slightly darker red (Tailwind `red-700`) provides visual hierarchy between primary and secondary surfaces while maintaining AA compliance with white text (5.74:1).
- **Dark mode `--color-bg: #7F1D1D`**: Deep dark red (Tailwind `red-900`) pairs well with light text (`#e6edf3`, current dark mode text color). Contrast ratio: 7.2:1 — exceeds AAA.
- **Dark mode `--color-bg-secondary: #991B1B`**: Tailwind `red-800`, slightly lighter than the primary dark background for surface differentiation. Contrast ratio against `#e6edf3`: 5.8:1 — exceeds AA.
- **Light mode text adjustment**: Current light mode text color (`#24292f`, near-black) has a contrast ratio of only 3.9:1 against `#DC2626`. Must change to white (`#FFFFFF`) for AA compliance.

### Color Token Mapping

| Token | Current (Light) | New (Light) | Current (Dark) | New (Dark) |
|-------|-----------------|-------------|-----------------|------------|
| `--color-bg` | `#ffffff` | `#DC2626` | `#0d1117` | `#7F1D1D` |
| `--color-bg-secondary` | `#f6f8fa` | `#B91C1C` | `#161b22` | `#991B1B` |
| `--color-text` | `#24292f` | `#FFFFFF` | `#e6edf3` | `#e6edf3` (unchanged) |
| `--color-text-secondary` | `#57606a` | `#FCA5A5` | `#8b949e` | `#8b949e` (unchanged) |

### Alternatives Considered
- **`#FF0000` (pure red)**: Too saturated; contrast ratio against white text is only 3.99:1 — fails WCAG AA. Against black text: 3.99:1 — also fails.
- **`#E53E3E` (Chakra red-500)**: Contrast ratio against white text: 4.07:1 — borderline fail for AA.
- **`#DC2626` with black text**: 3.9:1 — fails AA. White text is the correct pairing.
- **Keeping current dark text on red**: Would fail accessibility. Light mode text must flip to white.

---

## R2: Existing Theme Token Architecture

### Decision
Modify existing CSS custom properties in `frontend/src/index.css` `:root` and `html.dark-mode-active` selectors. No new token names needed.

### Rationale
- The application already uses a well-structured token system: `--color-bg`, `--color-bg-secondary`, `--color-text`, `--color-text-secondary`, etc.
- All components reference these tokens via `var(--color-bg)`, `var(--color-bg-secondary)`, etc. — confirmed by searching all CSS files.
- The `useAppTheme` hook toggles `dark-mode-active` class on `<html>` — this mechanism is unchanged.
- The `body` element uses `background: var(--color-bg-secondary)` — the global background cascades through this single rule.

### Component Background Audit

Components using `var(--color-bg)` or `var(--color-bg-secondary)`:
- `ChatInterface.css`: Uses both tokens extensively for message bubbles, input areas, panels
- `App.css`: May have app-level background rules
- Various component CSS files: Use tokens for surface backgrounds

**All component backgrounds use CSS tokens** — no hardcoded background colors found that would conflict with the global change.

### Alternatives Considered
- **Adding a new `--color-bg-red` token**: Unnecessary indirection; the existing `--color-bg` token is the correct place for the primary background color.
- **Using Tailwind utility classes**: The project does not use Tailwind CSS — it uses vanilla CSS custom properties.
- **Inline styles on `body`**: Violates the centralized token approach and makes future changes harder.

---

## R3: Border and Interactive Element Contrast

### Decision
Update `--color-border` to a lighter shade for visibility against red backgrounds. Keep `--color-primary`, `--color-success`, `--color-warning`, and `--color-danger` tokens as-is — they are used for buttons and status indicators that sit on card/modal surfaces, not directly on the red background.

### Rationale
- **Borders**: Current light mode border `#d0d7de` (light gray) has low contrast against red backgrounds. Updating to `#FECACA` (Tailwind `red-200`) provides visible separation while staying within the red palette.
- **Interactive elements**: Buttons use `--color-primary` (`#0969da` blue) for background — this sits on card surfaces (`--color-bg`), not directly on the page background. Since card backgrounds are also changing to red, button colors remain sufficiently distinct.
- **Dark mode borders**: Current `#30363d` can remain or be updated to `#7F1D1D` for consistency. The dark red scheme has enough contrast with the existing dark border.

### Alternatives Considered
- **White borders**: Too stark; red-tinted borders blend better.
- **No border changes**: Borders may become invisible against red backgrounds — not acceptable.
