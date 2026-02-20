# Data Model: Add Green Background Color to App

**Feature**: 007-green-background | **Date**: 2026-02-20
**Purpose**: Define entities and their relationships for feature implementation

## Model Overview

This feature involves no data model in the traditional sense (no database entities, API models, or state management). The "data" being changed consists of CSS custom properties and style declarations in the global stylesheet. This document exists to satisfy Phase 1 requirements but is intentionally minimal due to the feature's lack of programmatic data structures.

## Entities

### Entity: GreenBackgroundColor

**Type**: CSS Custom Property (Design Token)
**Purpose**: Reusable green background color value for the application root
**Lifecycle**: Compile-time constant embedded in CSS; available at runtime via `var()` function

**Attributes**:

| Attribute | Type | Constraints | Current Value | New Value |
|-----------|------|-------------|---------------|-----------|
| `--color-bg-primary` | CSS color | Valid CSS color value | *(does not exist)* | `#2D6A4F` |
| `body.background` | CSS shorthand | Valid CSS background | `var(--color-bg-secondary)` | `var(--color-bg-primary)` with `#2D6A4F` fallback |

**Locations**:
- `--color-bg-primary`: `frontend/src/index.css` `:root` block (new property)
- `--color-bg-primary`: `frontend/src/index.css` `html.dark-mode-active` block (new property, same value)
- `body.background`: `frontend/src/index.css` `body` rule (modified)

**Validation Rules**:
1. **Valid hex color**: Must be a 6-digit hexadecimal color code
2. **Non-empty**: Variable must have a value assigned
3. **Consistency**: Same variable name used in both light and dark mode blocks
4. **Fallback present**: Body background must include hardcoded fallback before `var()` usage

**State Transitions**: None — static CSS values with no runtime changes

**Relationships**: None — no dependencies on JavaScript state, API models, or database records

---

## CSS Custom Property Hierarchy

```
:root
├── --color-bg-primary: #2D6A4F    (NEW — green background)
├── --color-bg: #ffffff             (existing — component backgrounds)
├── --color-bg-secondary: #f6f8fa   (existing — secondary backgrounds)
└── [other existing variables...]

html.dark-mode-active
├── --color-bg-primary: #2D6A4F    (NEW — same green for dark mode)
├── --color-bg: #0d1117             (existing — dark component backgrounds)
├── --color-bg-secondary: #161b22   (existing — dark secondary backgrounds)
└── [other existing variables...]

body
└── background: var(--color-bg-primary)  (CHANGED — was var(--color-bg-secondary))
```

---

## Existing Entities (unchanged, for reference)

| Entity | Location | Relevance |
|--------|----------|-----------|
| `--color-bg` | `frontend/src/index.css` `:root` | Component backgrounds layer on top of green body background |
| `--color-bg-secondary` | `frontend/src/index.css` `:root` | Previously used as body background; replaced by `--color-bg-primary` |
| `--color-text` | `frontend/src/index.css` `:root` | Primary text color (`#24292f`); rendered on component backgrounds, not directly on green |
| `--color-text-secondary` | `frontend/src/index.css` `:root` | Secondary text color (`#57606a`); rendered on component backgrounds |
| `.app-container` | `frontend/src/App.css` | Root app container with `height: 100vh`; does not set its own background |
| `.app-header` | `frontend/src/App.css` | Header with `background: var(--color-bg)` — layers above green |
| `.board-page` | `frontend/src/App.css` | Board page with `background: var(--color-bg)` — layers above green |
| `.chat-section` | `frontend/src/App.css` | Chat section with `background: var(--color-bg)` — layers above green |

---

## Data Flow

```
CSS file parsed by browser
       ↓
:root block defines --color-bg-primary: #2D6A4F
       ↓
body rule applies background: var(--color-bg-primary)
       ↓
Green background visible as base layer
       ↓
Component CSS applies their own backgrounds (var(--color-bg), var(--color-bg-secondary))
       ↓
Components layer on top of green; green visible in gaps/edges/overlays
```

---

## Security Considerations

**Threat Model**: None — static CSS color values with no user input or dynamic generation

- **No XSS risk**: Hardcoded CSS values, not user-generated content
- **No injection risk**: No dynamic CSS generation or template rendering
- **No data exposure**: Public visual styling only

---

## Phase 1 Data Model Completion Checklist

- [x] All entities identified (1 CSS custom property entity)
- [x] Entity attributes documented with current/new values
- [x] Validation rules defined (valid hex, non-empty, fallback)
- [x] Relationships documented (layers with existing variables)
- [x] Data flow described (CSS cascade)
- [x] Security considerations addressed (no risks)
- [x] Existing related entities documented for context

**Status**: ✅ **DATA MODEL COMPLETE** — Ready for contracts and quickstart generation
