# Data Model: Yellow Background Color for App

**Feature**: 003-yellow-background-app | **Date**: 2026-02-18  
**Purpose**: Define entities and their relationships for feature implementation

## Model Overview

This feature involves no data model in the traditional sense (no database entities, API models, or state management). The "data" being changed consists of CSS custom property values (design tokens) in a single stylesheet. This document exists to satisfy Phase 1 requirements but is intentionally minimal due to the feature's lack of programmatic data structures.

## Entities

### Entity: BackgroundColorTokens

**Type**: CSS Custom Properties (Design Tokens)  
**Purpose**: Define the application's background colors for page and surface layers  
**Lifecycle**: Compile-time values embedded in CSS, applied at runtime by browser

**Attributes**:

| Attribute | Type | Selector | Current Value | New Value | Contrast vs Text |
|-----------|------|----------|---------------|-----------|-----------------|
| `--color-bg` (light) | CSS color | `:root` | `#ffffff` | `#FFFFF0` (Ivory) | 14.52:1 vs #24292f |
| `--color-bg-secondary` (light) | CSS color | `:root` | `#f6f8fa` | `#FFFDE7` (Material Yellow 50) | 14.27:1 vs #24292f |
| `--color-bg` (dark) | CSS color | `html.dark-mode-active` | `#0d1117` | `#0D0A00` | 16.76:1 vs #e6edf3 |
| `--color-bg-secondary` (dark) | CSS color | `html.dark-mode-active` | `#161b22` | `#1A1500` | 15.44:1 vs #e6edf3 |

**Location**: `frontend/src/index.css` lines 8-9 (`:root`) and lines 24-25 (`html.dark-mode-active`)

**Usage in Application**:
- `--color-bg`: Used by `App.css` for elevated surfaces — headers (`.app-header`), cards, modals, chat containers
- `--color-bg-secondary`: Used by `body` element as the page-level background color (set in `index.css` line 43)

**Validation Rules**:
1. **Valid CSS color**: Must be a valid hex color value
2. **WCAG AA contrast**: Must achieve minimum 4.5:1 contrast ratio against corresponding text color
3. **Visual consistency**: Light-mode values should be perceptibly yellow; dark-mode values should carry a warm yellow tint
4. **Variable naming**: No changes to variable names — only values change

**State Transitions**: None — values are static CSS declarations applied at page load. Dark mode toggling is handled by existing `html.dark-mode-active` class mechanism.

**Relationships**: 
- `--color-bg` is referenced by component styles in `App.css` for surface backgrounds
- `--color-bg-secondary` is referenced by `body` selector in `index.css` for page background
- Both variables interact with `--color-text` (#24292f light / #e6edf3 dark) for contrast compliance

---

## Entity Relationships

```
:root / html.dark-mode-active (CSS selectors)
    │
    ├── --color-bg ──────────► App.css (.app-header, .chat-container, etc.)
    │                           Surface-level backgrounds
    │
    └── --color-bg-secondary ──► index.css (body selector)
                                  Page-level background
```

Both variables are consumed by existing CSS rules. No new consumers or producers are introduced by this feature. The relationship is read-only: components reference the variables but never modify them.

---

## Data Validation

### Compile-Time Validation

- **CSS Syntax**: Hex color values are validated by CSS parser at build time (Vite/PostCSS)
- **Linter**: Stylelint (if configured) validates CSS property values

### Runtime Validation

None required. CSS custom properties are applied by the browser rendering engine. Invalid values fall back to inherited or initial values per CSS specification.

### Human Validation (Acceptance Criteria)

From spec.md acceptance scenarios:
1. Light mode pages display yellow background (#FFFDE7) — visual inspection
2. Dark mode pages display warm dark-yellow tint (#1A1500) — visual inspection
3. All text remains legible against new backgrounds — visual inspection + contrast verification
4. Existing UI components (cards, modals, buttons) remain visually distinct — visual inspection

---

## Data Flow

```
Developer edits index.css variable values
       ↓
Git commit with new color values
       ↓
Vite build process (frontend)
       ↓
CSS bundle with updated custom properties
       ↓
Browser parses CSS and applies variables
       ↓
body background → --color-bg-secondary (yellow page bg)
Component backgrounds → --color-bg (ivory surface bg)
       ↓
User sees yellow-tinted application
```

**Flow Characteristics**:
- **Unidirectional**: Source → Build → Deploy → Display
- **No user input**: Users cannot change background colors (read-only display)
- **No persistence layer**: No database, localStorage, or cookies involved
- **Automatic propagation**: CSS variables cascade automatically to all consuming selectors

---

## Security Considerations

**Threat Model**: None — static CSS color values with no user input or dynamic generation

**Security Properties**:
- **No XSS risk**: Hardcoded hex values in stylesheet, not user-generated content
- **No injection risk**: CSS custom properties cannot execute code
- **No authentication impact**: Background color is purely visual
- **No authorization impact**: No access control decisions based on colors

---

## Performance Characteristics

**Size Impact**:
- Old values: `#ffffff`, `#f6f8fa`, `#0d1117`, `#161b22` = 28 chars total
- New values: `#FFFFF0`, `#FFFDE7`, `#0D0A00`, `#1A1500` = 28 chars total
- **Net change**: 0 bytes (identical character count)

**Runtime Impact**:
- CSS variable resolution: O(1) per property lookup (browser-native operation)
- No additional repaints beyond initial page load
- No JavaScript execution changes

**Memory Impact**: Negligible — CSS variable storage is identical before and after

---

## Alternative Data Models Considered

### Alternative 1: New CSS Custom Properties

```css
:root {
  --color-bg-yellow-page: #FFFDE7;
  --color-bg-yellow-surface: #FFFFF0;
}
```

**Rejected Rationale**: Violates DRY — existing `--color-bg` and `--color-bg-secondary` serve exactly this purpose. Adding new variables creates naming confusion and requires updating all consuming selectors.

### Alternative 2: CSS Class-Based Theming

```css
body.yellow-theme { background: #FFFDE7; }
```

**Rejected Rationale**: Bypasses the existing CSS custom property architecture. Would require JavaScript changes to toggle classes and wouldn't propagate to components using the variables.

### Alternative 3: Design Token JSON File

```json
{
  "color-bg": "#FFFFF0",
  "color-bg-secondary": "#FFFDE7"
}
```

**Rejected Rationale**: Project has no design token pipeline. Adding one for 4 values violates YAGNI. The CSS variables themselves are the design tokens.

---

## Phase 1 Data Model Completion Checklist

- [x] All entities identified (1 entity: BackgroundColorTokens)
- [x] Entity attributes documented with current/new values
- [x] Validation rules defined (valid CSS, WCAG AA contrast)
- [x] Relationships documented (variable → consumer mapping)
- [x] Data flow described (source → build → display)
- [x] Storage mechanism identified (CSS in git source code)
- [x] Security considerations addressed (no risks)
- [x] Performance impact assessed (zero net change)
- [x] Alternative models evaluated and rejected

**Status**: ✅ **DATA MODEL COMPLETE** - Ready for contracts and quickstart generation
