# Data Model: Yellow Background Color for App

**Feature**: 003-yellow-background-app | **Date**: 2026-02-18  
**Purpose**: Define entities and their relationships for feature implementation

## Model Overview

This feature involves no data model in the traditional sense (no database entities, API models, or state management). The "data" being changed consists of CSS custom property values in a single stylesheet. This document exists to satisfy Phase 1 requirements but is intentionally minimal due to the feature's lack of programmatic data structures.

## Entities

### Entity: DesignToken (CSS Custom Property)

**Type**: CSS Custom Property Value (Style Layer Only)  
**Purpose**: Theming tokens controlling background colors across the entire application  
**Lifecycle**: Loaded at stylesheet parse time; applied via CSS cascade

**Attributes**:

| Attribute | Type | Selector | Current Value | New Value |
|-----------|------|----------|---------------|-----------|
| `--color-bg` (light) | `color` | `:root` | `#ffffff` | `#FFFFF0` |
| `--color-bg-secondary` (light) | `color` | `:root` | `#f6f8fa` | `#FFFDE7` |
| `--color-bg` (dark) | `color` | `html.dark-mode-active` | `#0d1117` | `#0D0A00` |
| `--color-bg-secondary` (dark) | `color` | `html.dark-mode-active` | `#161b22` | `#1A1500` |

**Location**: `frontend/src/index.css` lines 8-9 (`:root`) and lines 24-25 (`html.dark-mode-active`)

**Validation Rules**:
1. **Valid hex color**: Must be a valid 6-digit hex color code
2. **WCAG AA contrast**: Each background must achieve ≥4.5:1 contrast ratio against its corresponding text color
3. **Consistency**: Light-mode values should be visually warm/yellow; dark-mode values should be dark yellow-tinted

**Contrast Verification**:

| Background | Text Color | Ratio | WCAG AA (4.5:1) |
|------------|-----------|-------|------------------|
| #FFFDE7 (light page) | #24292f (primary text) | 14.27:1 | ✅ Pass |
| #FFFFF0 (light surface) | #24292f (primary text) | 14.52:1 | ✅ Pass |
| #1A1500 (dark page) | #e6edf3 (primary text) | 15.44:1 | ✅ Pass |
| #0D0A00 (dark surface) | #e6edf3 (primary text) | 16.76:1 | ✅ Pass |

**State Transitions**: None — values are static once loaded. Theme mode switching is handled by toggling the `dark-mode-active` class on `<html>`, which the existing application code already manages.

**Relationships**:
- `--color-bg` is consumed by: header background, card backgrounds, modal backgrounds, chat container background (via `var(--color-bg)` in `App.css`)
- `--color-bg-secondary` is consumed by: `body` element background (via `var(--color-bg-secondary)` in `index.css`)
- Both are independent of: `--color-primary`, `--color-text`, `--color-border`, and other design tokens

---

## Entity Relationships

```
:root / html.dark-mode-active
  ├── --color-bg ──────────► App.css: header, cards, modals, chat container
  └── --color-bg-secondary ──► index.css: body background
```

The relationship is unidirectional: CSS custom properties are defined in `index.css` and consumed by `App.css` and `index.css` via `var()` references. Changing the property values automatically propagates to all consumers through the CSS cascade.

---

## Data Validation

### Compile-Time Validation

- **CSS syntax**: Hex color values are validated by CSS parsers at build time (Vite/PostCSS)
- **Linter**: Stylelint/ESLint may flag invalid color values (project-dependent)

### Runtime Validation

None required. CSS custom properties are applied by the browser's rendering engine with no user input or dynamic generation.

### Human Validation (Acceptance Criteria)

From spec.md acceptance scenarios:
1. Page background displays soft yellow color (#FFFDE7) in light mode (visual inspection)
2. Yellow background consistent across all routes and devices (visual inspection)
3. All text meets WCAG AA contrast ratio against yellow backgrounds (accessibility audit)
4. Components (cards, modals, navigation) remain visually distinct (visual inspection)
5. Dark mode displays dark warm-yellow tint (#1A1500) background (visual inspection)

---

## Data Storage

**Storage Mechanism**: Git repository source code (CSS file)  
**Format**: Plain text CSS  
**Persistence**: Version controlled via git  
**Backup**: GitHub remote repository  
**Encryption**: Not applicable (public source code)

---

## Data Flow

```
Developer edits CSS custom property values in index.css
       ↓
Git commit with new color values
       ↓
Vite build process (frontend) — CSS bundled
       ↓
Browser loads stylesheet, parses :root / html.dark-mode-active
       ↓
CSS cascade applies --color-bg and --color-bg-secondary via var() references
       ↓
body background = var(--color-bg-secondary) → yellow (#FFFDE7 or #1A1500)
Components background = var(--color-bg) → yellow (#FFFFF0 or #0D0A00)
```

**Flow Characteristics**:
- **Declarative**: CSS cascade handles propagation — no imperative code
- **No user input**: Users cannot change background color (read-only display)
- **No persistence layer**: No database, localStorage, or cookies involved
- **Theme switching**: Existing dark-mode toggle adds/removes `dark-mode-active` class, which CSS handles natively

---

## Security Considerations

**Threat Model**: None — static CSS color values with no user input or dynamic generation

**Security Properties**:
- **No XSS risk**: Hardcoded hex values, not user-generated content
- **No injection risk**: No dynamic CSS, template literals, or runtime style generation
- **No authentication impact**: Background color is public visual property
- **No data exfiltration**: CSS values do not contain or transmit sensitive data

---

## Performance Characteristics

**Size Impact**:
- Old values: 28 chars total (`#ffffff`, `#f6f8fa`, `#0d1117`, `#161b22`)
- New values: 28 chars total (`#FFFFF0`, `#FFFDE7`, `#0D0A00`, `#1A1500`)
- **Net change**: 0 bytes (identical character count)

**Runtime Impact**:
- CSS custom property resolution: O(1) per property — no change
- No repaints beyond initial page load
- No layout shifts — background color change only

**Memory Impact**: Negligible — CSS property storage unchanged

---

## Alternative Data Models Considered

### Alternative 1: New CSS Custom Properties

```css
:root {
  --color-yellow-bg: #FFFDE7;
  --color-yellow-surface: #FFFFF0;
}
```

**Rejected Rationale**: Adds unnecessary properties. Existing `--color-bg` and `--color-bg-secondary` serve the exact same purpose. Adding new properties would require updating all `var()` consumers.

### Alternative 2: CSS Variables in JavaScript

```typescript
document.documentElement.style.setProperty('--color-bg', '#FFFFF0');
```

**Rejected Rationale**: Runtime manipulation adds unnecessary complexity. Static CSS values are simpler and more performant.

### Alternative 3: Theme Configuration Object

```typescript
const theme = { bg: '#FFFFF0', bgSecondary: '#FFFDE7' };
```

**Rejected Rationale**: Project uses vanilla CSS custom properties, not a JS-based theming system. Adding one would be a significant architectural change out of scope.

---

## Phase 1 Data Model Completion Checklist

- [x] All entities identified (1 entity: DesignToken with 4 attributes)
- [x] Entity attributes documented with current/new values
- [x] Validation rules defined (valid hex, WCAG AA contrast)
- [x] Relationships documented (CSS cascade: index.css → App.css consumers)
- [x] Data flow described (source → build → cascade → display)
- [x] Storage mechanism identified (git source code)
- [x] Security considerations addressed (no risks)
- [x] Performance impact assessed (zero net change)
- [x] Alternative models evaluated and rejected

**Status**: ✅ **DATA MODEL COMPLETE** - Ready for contracts and quickstart generation
