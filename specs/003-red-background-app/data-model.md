# Data Model: Apply Red Background Color to App

**Feature**: 003-red-background-app | **Date**: 2026-02-18  
**Purpose**: Define entities and their relationships for feature implementation

## Model Overview

This feature involves no data model in the traditional sense (no database entities, API models, or state management). The "data" being changed consists of 4 CSS custom property values in the presentation layer theme file. This document exists to satisfy Phase 1 requirements but is intentionally minimal due to the feature's lack of programmatic data structures.

## Entities

### Entity: ThemeBackgroundColor

**Type**: CSS Custom Property Value (Theme Layer Only)  
**Purpose**: Define background colors for the application's light and dark themes  
**Lifecycle**: Compile-time constant embedded in CSS; applied at runtime via CSS custom properties

**Attributes**:

| Attribute | CSS Variable | Selector | Current Value | New Value | Contrast with Text |
|-----------|-------------|----------|---------------|-----------|-------------------|
| `lightSurfaceBg` | `--color-bg` | `:root` | `#ffffff` | `#fff5f5` | 13.70:1 with `#24292f` |
| `lightPageBg` | `--color-bg-secondary` | `:root` | `#f6f8fa` | `#ffebee` | 12.82:1 with `#24292f` |
| `darkSurfaceBg` | `--color-bg` | `html.dark-mode-active` | `#0d1117` | `#2d0a0a` | 15.33:1 with `#e6edf3` |
| `darkPageBg` | `--color-bg-secondary` | `html.dark-mode-active` | `#161b22` | `#1a0505` | 16.64:1 with `#e6edf3` |

**Locations**:
- All 4 values in `frontend/src/index.css` (lines 8-9 for `:root`, lines 24-25 for `html.dark-mode-active`)

**Validation Rules**:
1. **Valid hex color**: Each value must be a valid 6-digit hex color prefixed with `#`
2. **WCAG AA contrast**: Each background value must achieve minimum 4.5:1 contrast ratio with corresponding text color
3. **Theme consistency**: Surface background (`--color-bg`) should be lighter than page background in dark mode (layering pattern) and darker (more red-tinted) than page background in light mode
4. **Lowercase hex**: Values must use lowercase hex format (per project convention)

**State Transitions**: 
- Light ↔ Dark mode toggle: CSS custom properties switch between `:root` and `html.dark-mode-active` values when the user toggles the theme

**Relationships**:

| Related Variable | Relationship | Impact |
|-----------------|--------------|--------|
| `--color-text` (`#24292f` / `#e6edf3`) | Foreground on background | Must maintain 4.5:1+ contrast ratio |
| `--color-text-secondary` (`#57606a` / `#8b949e`) | Secondary foreground | Must maintain 4.5:1+ contrast ratio |
| `--color-border` (`#d0d7de` / `#30363d`) | Visual separator | Must remain visible against new backgrounds |

---

## Entity Relationships

**Diagram**:

```
:root / html.dark-mode-active
  ├── --color-bg ──────────────► Used by: App.css surface backgrounds (header, cards, modals)
  ├── --color-bg-secondary ────► Used by: body background (index.css line 43)
  ├── --color-text ────────────► Foreground contrast partner for --color-bg
  └── --color-text-secondary ──► Secondary foreground contrast partner
```

The background color tokens have a direct contrast relationship with text color tokens. Changing background values requires verifying that all text remains readable.

---

## Data Validation

### Compile-Time Validation

- **CSS**: Custom property values are valid CSS color values (hex format)
- **Linter**: Prettier formats CSS but does not enforce color value rules
- **Build**: Vite processes CSS without transforming custom property values

### Runtime Validation

None required. CSS custom properties are static values defined in the stylesheet. No user input or dynamic generation involved.

### Human Validation (Acceptance Criteria)

From spec.md acceptance scenarios:
1. Red-themed background visible across all screens (visual inspection)
2. Text readable on red background in both light and dark modes (contrast check)
3. Dark mode displays dark red variant (visual inspection after toggle)
4. Component-level backgrounds not overridden (visual inspection of cards, modals)

---

## Data Flow

```
Developer edits CSS custom property values in index.css
       ↓
Git commit with new color values
       ↓
Vite build process (frontend)
       ↓
CSS served to browser with updated custom property values
       ↓
Browser applies --color-bg-secondary to body background
Browser applies --color-bg to surface elements (via App.css references)
       ↓
User sees red-themed background across all screens
```

**Flow Characteristics**:
- **Cascading**: CSS custom properties cascade from `:root` to all child elements
- **Theme-aware**: `html.dark-mode-active` selector overrides `:root` values when active
- **No user input**: Users cannot change background color (read-only theme)
- **No persistence layer**: No database, localStorage, or cookies involved for color values

---

## Security Considerations

**Threat Model**: None — static CSS color values with no user input or dynamic generation

**Security Properties**:
- **No XSS risk**: Hardcoded CSS values, not user-generated content
- **No injection risk**: No dynamic CSS generation or template rendering
- **No data exposure**: Color values are non-sensitive public information

---

## Phase 1 Data Model Completion Checklist

- [x] All entities identified (1 theme entity: ThemeBackgroundColor with 4 attributes)
- [x] Entity attributes documented with current/new values and contrast ratios
- [x] Validation rules defined (hex format, WCAG contrast, lowercase convention)
- [x] Relationships documented (contrast with text color tokens)
- [x] Data flow described (CSS → build → browser → display)
- [x] Security considerations addressed (no risks)
- [x] Alternative models not applicable (CSS variable values have no alternatives)

**Status**: ✅ **DATA MODEL COMPLETE** - Ready for contracts and quickstart generation
