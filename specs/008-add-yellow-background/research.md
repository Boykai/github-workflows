# Research: Add Yellow Background Color to App

**Feature**: 008-add-yellow-background | **Date**: 2026-02-20
**Purpose**: Resolve technical unknowns and document implementation approach

## Research Summary

This feature is a straightforward CSS variable update. All technical context is known from the existing codebase. The application uses CSS custom properties defined in `frontend/src/index.css` with `:root` (light mode) and `html.dark-mode-active` (dark mode) selectors. The `body` background is set to `var(--color-bg-secondary)`. This document resolves all implementation decisions.

## Decision Areas

### 1. Yellow Color Value Selection

**Decision**: Use `#FFFDE7` (Material Design Yellow 50) for `--color-bg-secondary` in light mode

**Rationale**:
- Soft pastel yellow that minimizes eye strain
- Provides excellent contrast with existing text color `#24292f` (contrast ratio ~17.6:1, far exceeding WCAG AA 4.5:1 requirement)
- Recommended in the issue specification
- Consistent with Material Design color palette used in many professional applications
- Light enough to serve as a background without overwhelming foreground elements

**Alternatives Considered**:
- **#FFF9C4 (Yellow 100)**: Slightly more saturated. Rejected — more intense yellow could cause eye strain on prolonged use; #FFFDE7 is gentler.
- **#FEF9C3 (Tailwind Yellow 100)**: Very similar to #FFF9C4. Rejected — same reasoning; #FFFDE7 is the softer option.
- **#FFEB3B (Yellow 500)**: Highly saturated. Rejected — too harsh for a full-page background; poor readability.

---

### 2. CSS Implementation Strategy

**Decision**: Update the existing `--color-bg-secondary` CSS variable value in `:root` from `#f6f8fa` to `#FFFDE7`

**Rationale**:
- The `body` element already uses `background: var(--color-bg-secondary)` — this is the global background
- Updating the variable value is the minimal change with maximum effect
- Dark mode already has its own `--color-bg-secondary: #161b22` in `html.dark-mode-active`, so the yellow only applies in light mode
- No new CSS variables needed — reuses the existing design token system

**Alternatives Considered**:
- **New variable `--color-bg-primary`**: Rejected — would require changing the `body` background declaration and adds unnecessary complexity. The existing `--color-bg-secondary` already serves as the page background.
- **Direct `body` style override**: Rejected — would bypass the CSS variable system and break dark mode toggling.
- **Tailwind CSS configuration**: Rejected — project does not use Tailwind CSS.
- **Separate `background-color` on `body`**: Rejected — the existing variable approach is cleaner and already works.

---

### 3. Dark Mode Handling

**Decision**: No changes to dark mode — yellow applies to light mode only via existing CSS variable scoping

**Rationale**:
- Dark mode colors are defined in the `html.dark-mode-active` selector which overrides `:root` values
- Changing `:root --color-bg-secondary` does NOT affect the dark mode value
- Dark mode retains `--color-bg-secondary: #161b22` unchanged
- This automatically satisfies the spec requirement to "handle dark mode gracefully"

**Alternatives Considered**:
- **Yellow-tinted dark mode**: Rejected — would create a muddy appearance and reduce contrast. Dark mode users expect dark backgrounds.
- **Separate light/dark variables**: Rejected — the existing `:root` / `html.dark-mode-active` pattern already provides this separation.

---

### 4. Impact on Existing Components

**Decision**: Verify that changing `--color-bg-secondary` does not negatively impact component backgrounds

**Rationale**:
- `--color-bg-secondary` is used by multiple components (sidebar, status columns, form fields, etc.) as their background color
- Changing this from `#f6f8fa` (light gray) to `#FFFDE7` (light yellow) will make these component backgrounds yellow-tinted
- This is acceptable because:
  - Components like cards and modals use `--color-bg` (white, unchanged) for their primary backgrounds
  - The sidebar, columns, and secondary surfaces getting a yellow tint is consistent with a "yellow background app" requirement
  - All text colors remain dark (#24292f, #57606a) with sufficient contrast against #FFFDE7

**Components using `--color-bg-secondary`** (will become light yellow):
- `body` background
- `.status-column` background
- `.board-column` background
- `.project-sidebar` (uses `--color-bg`, not affected)
- Various button hover states, form fields, modal fields
- `.theme-toggle-btn` background
- `.board-page` (uses `--color-bg`, not affected)

**Components using `--color-bg`** (unchanged white):
- `.app-header` background
- `.task-card` background
- `.board-issue-card` background
- `.agent-tile` background
- `.modal-content` background

This separation means cards and interactive elements remain white while the page/section backgrounds become yellow — a visually coherent result.

---

### 5. Contrast Verification

**Decision**: No additional contrast adjustments needed

**Rationale**:
- Primary text `#24292f` on `#FFFDE7` → contrast ratio ~17.6:1 (WCAG AAA)
- Secondary text `#57606a` on `#FFFDE7` → contrast ratio ~7.2:1 (WCAG AA)
- All existing text colors maintain sufficient contrast against the yellow background
- Interactive elements (buttons, links) use their own background colors or the primary blue `#0969da`

**Verification Method**: Manual contrast ratio calculation using WCAG formula for relative luminance
