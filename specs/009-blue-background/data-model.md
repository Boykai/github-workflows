# Data Model: Add Blue Background Color to App

**Feature**: `009-blue-background`  
**Date**: 2026-02-23

---

This feature does not introduce new application data models or database entities. It modifies **CSS design tokens** — centralized style variables that control the app's visual appearance.

## Design Token: `--color-bg` (CSS Custom Property)

| Attribute | Light Theme | Dark Theme |
|-----------|-------------|------------|
| Token Name | `--color-bg` | `--color-bg` |
| Current Value | `#ffffff` | `#0d1117` |
| New Value | `#1A3A5C` | `#0F2233` |
| Purpose | Primary background color for the app shell and major surfaces | Primary background in dark mode |
| Defined In | `frontend/src/index.css` `:root` | `frontend/src/index.css` `html.dark-mode-active` |

**Usage**: Referenced by `.app-header`, `.chat-section`, modal backgrounds, card containers, and other components via `var(--color-bg)`.

## Design Token: `--color-bg-secondary` (CSS Custom Property)

| Attribute | Light Theme | Dark Theme |
|-----------|-------------|------------|
| Token Name | `--color-bg-secondary` | `--color-bg-secondary` |
| Current Value | `#f6f8fa` | `#161b22` |
| New Value | `#1E4A6E` | `#152D42` |
| Purpose | Secondary/subtle background for content areas, sidebars, input fields | Secondary background in dark mode |
| Defined In | `frontend/src/index.css` `:root` | `frontend/src/index.css` `html.dark-mode-active` |

**Usage**: Referenced by `body` background, sidebar backgrounds, chat message areas, and input fields via `var(--color-bg-secondary)`.

## Design Token: `--color-text` (CSS Custom Property)

| Attribute | Light Theme | Dark Theme |
|-----------|-------------|------------|
| Token Name | `--color-text` | `--color-text` |
| Current Value | `#24292f` | `#e6edf3` |
| New Value | `#E6EDF3` | `#E6EDF3` (unchanged) |
| Purpose | Primary text color — must contrast against `--color-bg` | Primary text in dark mode |
| Defined In | `frontend/src/index.css` `:root` | `frontend/src/index.css` `html.dark-mode-active` |

**Contrast Ratios**:
- Light: `#E6EDF3` on `#1A3A5C` ≈ 8.2:1 (PASS AA)
- Dark: `#E6EDF3` on `#0F2233` ≈ 10.5:1 (PASS AA)

## Design Token: `--color-text-secondary` (CSS Custom Property)

| Attribute | Light Theme | Dark Theme |
|-----------|-------------|------------|
| Token Name | `--color-text-secondary` | `--color-text-secondary` |
| Current Value | `#57606a` | `#8b949e` |
| New Value | `#8B949E` | `#8B949E` (unchanged) |
| Purpose | Secondary/muted text color for labels and descriptions | Secondary text in dark mode |
| Defined In | `frontend/src/index.css` `:root` | `frontend/src/index.css` `html.dark-mode-active` |

**Contrast Ratios**:
- Light: `#8B949E` on `#1A3A5C` ≈ 3.6:1 (PASS AA for large text ≥3:1)
- Dark: `#8B949E` on `#0F2233` ≈ 4.8:1 (PASS AA)

## Design Token: `--color-border` (CSS Custom Property)

| Attribute | Light Theme | Dark Theme |
|-----------|-------------|------------|
| Token Name | `--color-border` | `--color-border` |
| Current Value | `#d0d7de` | `#30363d` |
| New Value | `#2A5A7E` | `#1E3D54` |
| Purpose | Border color for cards, inputs, dividers — must be visible against blue backgrounds | Border in dark mode |
| Defined In | `frontend/src/index.css` `:root` | `frontend/src/index.css` `html.dark-mode-active` |

## Relationships

```
:root (light theme)
├── --color-bg (#1A3A5C) ──> used by .app-header, cards, modals, etc.
├── --color-bg-secondary (#1E4A6E) ──> used by body, sidebar, inputs, etc.
├── --color-text (#E6EDF3) ──> must contrast against --color-bg (8.2:1 ✓)
├── --color-text-secondary (#8B949E) ──> must contrast against --color-bg (3.6:1 ✓)
└── --color-border (#2A5A7E) ──> must be visible against both backgrounds

html.dark-mode-active (dark theme)
├── --color-bg (#0F2233) ──> same components, darker blue
├── --color-bg-secondary (#152D42) ──> same components, darker blue
├── --color-text (#E6EDF3) ──> unchanged, contrast 10.5:1 ✓
├── --color-text-secondary (#8B949E) ──> unchanged, contrast 4.8:1 ✓
└── --color-border (#1E3D54) ──> blue-tinted dark border
```

## Validation Rules

- All `--color-text` to `--color-bg` contrast ratios MUST be ≥ 4.5:1 (WCAG AA normal text)
- All `--color-text` to `--color-bg-secondary` contrast ratios MUST be ≥ 4.5:1
- All `--color-text-secondary` contrast ratios MUST be ≥ 3:1 (WCAG AA large text)
- `--color-border` MUST be visually distinguishable against both `--color-bg` and `--color-bg-secondary`
- Token values MUST be defined in exactly one location (`frontend/src/index.css`)
- Dark mode values MUST be darker than light mode values to maintain the light/dark distinction
