# Data Model: Add Green Background Color to App

**Feature**: 001-green-background | **Date**: 2026-02-20  
**Purpose**: Define entities and their relationships for feature implementation

## Model Overview

This feature involves no data model in the traditional sense (no database entities, API models, or state management). The "data" being changed consists of CSS custom property values in the global stylesheet. This document exists to satisfy Phase 1 requirements but is intentionally minimal due to the feature's lack of programmatic data structures.

## Entities

### Entity: CSSDesignTokens

**Type**: CSS Custom Properties (Style Layer Only)  
**Purpose**: Define application color scheme including background and text colors  
**Lifecycle**: Loaded at page render via stylesheet; no runtime mutations (dark mode toggled via class selector)

**Attributes (Light Mode — `:root`)**:

| Attribute | Type | Current Value | New Value | Description |
|-----------|------|---------------|-----------|-------------|
| `--color-bg-secondary` | `color` | `#f6f8fa` | `#2D6A4F` | Body background color (green) |
| `--color-text` | `color` | `#24292f` | `#ffffff` | Primary text color (white for contrast) |
| `--color-text-secondary` | `color` | `#57606a` | `#d4e7d0` | Secondary text color (light green-white) |
| `--color-bg` | `color` | `#ffffff` | `#ffffff` | Component background (unchanged) |
| `--color-primary` | `color` | `#0969da` | `#0969da` | Primary action color (unchanged) |
| `--color-border` | `color` | `#d0d7de` | `#d0d7de` | Border color (unchanged) |

**Attributes (Dark Mode — `html.dark-mode-active`)**: No changes — dark mode retains existing values per spec assumptions.

**Location**: `frontend/src/index.css` lines 2-15 (`:root` block)

**Validation Rules**:
1. All color values must be valid CSS hex colors
2. `--color-text` against `--color-bg-secondary` must meet WCAG AA 4.5:1 contrast ratio
3. `--color-text-secondary` against `--color-bg-secondary` must meet WCAG AA 4.5:1 contrast ratio
4. All variables must be defined in a single `:root` block for maintainability (FR-002, SC-005)

**State Transitions**: None — static values with no runtime changes in light mode. Dark mode applied via `html.dark-mode-active` class toggle (existing behavior, unchanged).

---

### Entity: BodyStyles

**Type**: CSS Rule (Style Layer Only)  
**Purpose**: Apply green background to root viewport element  
**Lifecycle**: Applied on page load; persists throughout session

**Attributes**:

| Property | Current Value | New Value | Description |
|----------|---------------|-----------|-------------|
| `background` | `var(--color-bg-secondary)` | `#2D6A4F` (fallback) + `var(--color-bg-secondary)` | Green background with hardcoded fallback |
| `min-height` | *(not set)* | `100vh` | Full viewport height coverage |

**Location**: `frontend/src/index.css` lines 38-44 (`body` rule)

**Validation Rules**:
1. Hardcoded fallback must precede variable-based declaration
2. `min-height: 100vh` ensures no white gaps below content (edge case from spec)

---

## Entity Relationships

**Diagram**: Minimal — single-file change with CSS cascade dependency

```
:root (CSS Custom Properties)
    │
    ├── --color-bg-secondary: #2D6A4F
    │       │
    │       └── Referenced by: body { background: var(--color-bg-secondary) }
    │
    ├── --color-text: #ffffff
    │       │
    │       └── Referenced by: body { color: var(--color-text) }
    │
    └── --color-text-secondary: #d4e7d0
            │
            └── Referenced by: various component selectors
```

Components (cards, buttons, modals) reference `--color-bg` (#ffffff, unchanged) for their own backgrounds. The green body background is visible only in areas without overlapping component backgrounds.

---

## Data Flow

```
Developer edits CSS variables in index.css
       ↓
Git commit with updated color values
       ↓
Vite build process (frontend)
       ↓
Static CSS served to browser
       ↓
Browser applies :root variables at document level
       ↓
body element renders green background via var(--color-bg-secondary)
       ↓
Text elements inherit white color via var(--color-text)
```

**Flow Characteristics**:
- **Unidirectional**: Source → Build → Deploy → Display
- **No user input**: Users cannot change background color (read-only display)
- **No persistence layer**: No database, localStorage, or cookies involved
- **CSS cascade**: Variables defined in `:root` are inherited by all child elements

---

## Security Considerations

**Threat Model**: None — static CSS values with no user input or dynamic generation

- **No XSS risk**: Hardcoded color values, not user-generated content
- **No injection risk**: CSS custom properties cannot execute code
- **No authentication impact**: Visual styling is public information
- **No data exposure**: No sensitive data involved

---

## Performance Characteristics

**Size Impact**:
- CSS variable value changes: ~30 bytes difference (negligible)
- Added `min-height: 100vh`: ~20 bytes (negligible)
- Added fallback declaration: ~30 bytes (negligible)

**Runtime Impact**:
- CSS variable resolution: O(1) — native browser capability
- No additional paint cycles beyond initial render
- No JavaScript execution for color application

---

## Phase 1 Data Model Completion Checklist

- [x] All entities identified (2 entities: CSSDesignTokens, BodyStyles)
- [x] Entity attributes documented with current/new values
- [x] Validation rules defined (contrast ratios, CSS validity)
- [x] Relationships documented (variable cascade)
- [x] Data flow described (source → build → display)
- [x] Security considerations addressed (no risks)
- [x] Performance impact assessed (negligible)

**Status**: ✅ **DATA MODEL COMPLETE** - Ready for contracts and quickstart generation
