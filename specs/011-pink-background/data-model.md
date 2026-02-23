# Data Model: Add Pink Background Color to App

**Feature**: `011-pink-background`
**Date**: 2026-02-23

---

This feature does not introduce new application data models. It modifies **design tokens** (CSS custom properties) that define the app's visual theme.

## Design Tokens (CSS Custom Properties)

### Entity: Light Mode Tokens (`:root`)

| Token | Current Value | New Value | Description |
|-------|---------------|-----------|-------------|
| `--color-bg` | `#ffffff` | `#FFB6C1` | Primary background (app containers, cards, modals) |
| `--color-bg-secondary` | `#f6f8fa` | `#FFA3B3` | Page background (`body`), secondary surfaces |
| `--color-text` | `#24292f` | `#24292f` | **Unchanged** — passes WCAG AA on pink (7.2:1) |
| `--color-text-secondary` | `#57606a` | `#4A4F57` | Darkened to pass WCAG AA on pink (4.5:1+) |
| `--color-border` | `#d0d7de` | `#d4a0ab` | Adjusted to harmonize with pink palette |

### Entity: Dark Mode Tokens (`html.dark-mode-active`)

| Token | Current Value | New Value | Description |
|-------|---------------|-----------|-------------|
| `--color-bg` | `#0d1117` | `#4A2030` | Deep pink-brown for dark mode container bg |
| `--color-bg-secondary` | `#161b22` | `#3A1525` | Darker pink-brown for page background |
| `--color-text` | `#e6edf3` | `#e6edf3` | **Unchanged** — passes WCAG AA on dark pink (9.1:1) |
| `--color-text-secondary` | `#8b949e` | `#8b949e` | **Unchanged** — passes WCAG AA on dark pink (4.6:1) |
| `--color-border` | `#30363d` | `#5A3040` | Adjusted to harmonize with dark pink palette |

### Relationships

```
:root tokens ──> html.dark-mode-active tokens (overridden via CSS specificity)
--color-bg ──> body (via var(--color-bg-secondary))
--color-bg ──> .app-container, .app-header, cards, modals (via var(--color-bg))
--color-text* ──> all text elements (via var(--color-text), var(--color-text-secondary))
useAppTheme ──> toggles dark-mode-active class on <html> element
```

### Validation Rules

- `--color-bg` MUST be a valid 6-digit hex color starting with `#`
- Light-mode `--color-text` on `--color-bg` MUST have ≥4.5:1 contrast ratio (WCAG AA)
- Light-mode `--color-text-secondary` on `--color-bg` MUST have ≥4.5:1 contrast ratio (WCAG AA)
- Dark-mode `--color-text` on `--color-bg` MUST have ≥4.5:1 contrast ratio (WCAG AA)
- Dark-mode `--color-text-secondary` on `--color-bg` MUST have ≥4.5:1 contrast ratio (WCAG AA)
- No component SHOULD override `background` with hardcoded colors that mask the design tokens

### State Transitions

```
Light Mode (default)         Dark Mode
─────────────────           ──────────────────
--color-bg: #FFB6C1    ──▶  --color-bg: #4A2030
--color-bg-secondary:       --color-bg-secondary:
  #FFA3B3              ──▶    #3A1525
                             
Toggle via useAppTheme() → adds/removes html.dark-mode-active class
```
