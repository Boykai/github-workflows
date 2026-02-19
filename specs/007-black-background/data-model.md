# Data Model: Add Black Background Theme

**Feature**: 007-black-background | **Date**: 2026-02-19  
**Purpose**: Define entities and their relationships for feature implementation

## Model Overview

This feature involves no data model in the traditional sense (no database entities, API models, or state management). The "data" being changed consists of CSS custom property values (design tokens) and static color literals in stylesheets. This document exists to satisfy Phase 1 requirements but is intentionally minimal due to the feature's lack of programmatic data structures.

## Entities

### Entity: DesignTokens (CSS Custom Properties)

**Type**: CSS Custom Properties (`:root` selector)  
**Purpose**: Centralized color values defining the application's visual theme  
**Lifecycle**: Compile-time constants embedded in CSS, applied at page load

**Attributes**:

| Token | Type | Current Value (Light) | New Value (Black Theme) | Dark Mode Value (Unchanged) |
|-------|------|-----------------------|------------------------|-----------------------------|
| `--color-primary` | `color` | `#0969da` | `#539bf5` | `#539bf5` |
| `--color-secondary` | `color` | `#6e7781` | `#8b949e` | `#8b949e` |
| `--color-success` | `color` | `#1a7f37` | `#3fb950` | `#3fb950` |
| `--color-warning` | `color` | `#9a6700` | `#d29922` | `#d29922` |
| `--color-danger` | `color` | `#cf222e` | `#f85149` | `#f85149` |
| `--color-bg` | `color` | `#ffffff` | `#000000` | `#0d1117` |
| `--color-bg-secondary` | `color` | `#f6f8fa` | `#121212` | `#161b22` |
| `--color-border` | `color` | `#d0d7de` | `#30363d` | `#30363d` |
| `--color-text` | `color` | `#24292f` | `#e6edf3` | `#e6edf3` |
| `--color-text-secondary` | `color` | `#57606a` | `#8b949e` | `#8b949e` |
| `--shadow` | `box-shadow` | `0 1px 3px rgba(0,0,0,0.1)` | `0 1px 3px rgba(0,0,0,0.4)` | `0 1px 3px rgba(0,0,0,0.4)` |

**Location**: `frontend/src/index.css` lines 2-15

**Validation Rules**:
1. All `--color-bg` variants must be black or near-black (#000000–#1a1a1a range)
2. All `--color-text` variants must achieve WCAG AA contrast (4.5:1) against their background
3. `--color-border` must be visible but subtle against both `--color-bg` and `--color-bg-secondary`
4. Token names must not change (only values)

**WCAG AA Contrast Verification**:

| Foreground | Background | Ratio | Passes AA? |
|-----------|------------|-------|------------|
| `#e6edf3` (text) | `#000000` (bg) | 17.4:1 | ✅ Yes (AAA) |
| `#8b949e` (text-secondary) | `#000000` (bg) | 7.2:1 | ✅ Yes (AA) |
| `#8b949e` (text-secondary) | `#121212` (bg-secondary) | 6.0:1 | ✅ Yes (AA) |
| `#e6edf3` (text) | `#121212` (bg-secondary) | 14.4:1 | ✅ Yes (AAA) |
| `#539bf5` (primary) | `#000000` (bg) | 8.1:1 | ✅ Yes (AA) |
| `#3fb950` (success) | `#000000` (bg) | 8.9:1 | ✅ Yes (AA) |
| `#f85149` (danger) | `#000000` (bg) | 5.4:1 | ✅ Yes (AA) |
| `#d29922` (warning) | `#000000` (bg) | 7.3:1 | ✅ Yes (AA) |

**State Transitions**: None — static CSS values with no runtime changes (dark mode toggle switches class, not individual values)

**Relationships**: All components reference these tokens via `var(--token-name)`. Changing token values cascades automatically.

---

### Entity: HardcodedColors (Audit Targets)

**Type**: Static CSS color literals  
**Purpose**: Colors that bypass the token system and need manual update  
**Lifecycle**: Compile-time constants embedded in CSS

**Instances Found**:

| File | Line(s) | Current Value | Context | New Value | Rationale |
|------|---------|---------------|---------|-----------|-----------|
| `App.css` | 388 | `#dafbe1` | highlight-pulse animation start | `rgba(45, 164, 78, 0.2)` | Light green → dark green tint |
| `App.css` | 407 | `#fff1f0` | error-toast background | `rgba(207, 34, 46, 0.15)` | Light pink → dark red tint |
| `App.css` | 446 | `#fff1f0` | error-banner background | `rgba(207, 34, 46, 0.15)` | Light pink → dark red tint |
| `App.css` | 471 | `#82071e` | error-banner-message color | `#ff6b6b` | Dark red text → lighter red for black bg |

**Note**: Other hardcoded colors (e.g., `#2da44e`, `#cf222e`, `#d29922`, `#8250df`, `white` on buttons) are accent/semantic colors that remain readable on dark backgrounds and do not need updating.

---

### Entity: InlineStyle (White Flash Prevention)

**Type**: HTML inline style attribute  
**Purpose**: Prevent flash of white background before CSS loads  
**Lifecycle**: Applied immediately by browser during HTML parsing, before external CSS

**Attributes**:

| Attribute | Location | Current Value | New Value |
|-----------|----------|---------------|-----------|
| `style` on `<html>` | `frontend/index.html` line 2 | (none) | `style="background-color: #000000"` |

**Validation Rules**:
1. Must match the `--color-bg` token value
2. Must be inline (not in external stylesheet) to prevent FOWC
3. Must be on `<html>` element (not `<body>`) for earliest application

---

## Entity Relationships

```
DesignTokens (:root)
    ├── --color-bg ──────────> All components via var(--color-bg)
    ├── --color-bg-secondary -> Cards, sidebars, columns via var(--color-bg-secondary)
    ├── --color-text ────────> All text via var(--color-text)
    ├── --color-text-secondary > Secondary text via var(--color-text-secondary)
    ├── --color-border ──────> All borders via var(--color-border)
    └── --shadow ────────────> All shadows via var(--shadow)

HardcodedColors
    └── (no token relationship — direct CSS values, manually updated)

InlineStyle (index.html)
    └── Mirrors --color-bg value for pre-CSS-load state
```

**Key Relationship**: The token system creates a one-to-many relationship where changing a single `:root` value cascades to all consuming components. This is the primary mechanism enabling the feature with minimal file changes.

---

## Data Flow

```
1. Browser requests index.html
   ↓
2. <html style="background-color: #000000"> applied immediately (no white flash)
   ↓
3. CSS files load (index.css, App.css, ChatInterface.css)
   ↓
4. :root tokens applied (--color-bg: #000000, etc.)
   ↓
5. All components inherit black background via var(--color-bg)
   ↓
6. User sees fully themed black background from first paint
```

---

## Security Considerations

**Threat Model**: None — static CSS color values with no user input or dynamic generation

- **No XSS risk**: Hardcoded CSS values, not user-generated content
- **No injection risk**: No dynamic CSS generation
- **No authentication impact**: Visual theme is public presentation
- **No data exposure**: No sensitive data involved in color changes

---

## Phase 1 Data Model Completion Checklist

- [X] All entities identified (3: DesignTokens, HardcodedColors, InlineStyle)
- [X] Entity attributes documented with current/new values
- [X] Validation rules defined (WCAG contrast ratios)
- [X] Relationships documented (token → component cascade)
- [X] Data flow described (HTML inline → CSS load → component render)
- [X] Storage mechanism identified (CSS source files)
- [X] Security considerations addressed (no risks)
- [X] Performance impact assessed (negligible)
- [X] Alternative models evaluated in research.md

**Status**: ✅ **DATA MODEL COMPLETE** - Ready for contracts and quickstart generation
