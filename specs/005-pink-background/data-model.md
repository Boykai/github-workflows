# Data Model: Pink Background Color

**Feature**: 005-pink-background | **Date**: 2026-02-19  
**Purpose**: Define entities and their relationships for feature implementation

## Model Overview

This feature involves no data model in the traditional sense (no database entities, API models, or state management). The "data" being changed consists of CSS custom property values in the application's theme system. This document exists to satisfy Phase 1 requirements but is intentionally minimal due to the feature's lack of programmatic data structures.

## Entities

### Entity: ThemeColorToken

**Type**: CSS Custom Property (Design Token)  
**Purpose**: Centralized color variable controlling the application's page background color  
**Lifecycle**: Compile-time / runtime CSS variable applied via browser's CSSOM

**Attributes**:

| Attribute | Type | Constraints | Current Value | New Value |
|-----------|------|-------------|---------------|-----------|
| `--color-bg-secondary` (light) | CSS color | Valid CSS color value | `#f6f8fa` | `#FFC0CB` |
| `--color-bg-secondary` (dark) | CSS color | Valid CSS color value | `#161b22` | `#2d1a1e` |

**Locations**:
- Light mode: `frontend/src/index.css` `:root` block (line 9)
- Dark mode: `frontend/src/index.css` `html.dark-mode-active` block (line 25)

**Validation Rules**:
1. **Valid CSS color**: Must be a valid hex color value parseable by browsers
2. **WCAG AA contrast**: Text colors (`--color-text`, `--color-text-secondary`) must maintain ≥4.5:1 contrast ratio against this background
3. **Theme consistency**: Both light and dark mode values must be recognizably "pink" while appropriate for their respective modes

**State Transitions**: 
- Light mode ↔ Dark mode toggle (managed by `useAppTheme` hook adding/removing `dark-mode-active` class on `<html>`)
- Variable value changes instantly via CSS specificity when class toggles

**Relationships**:
- **Consumed by**: `body` element (`background: var(--color-bg-secondary)` in index.css)
- **Consumed by**: Multiple component styles in App.css that reference `var(--color-bg-secondary)` for section backgrounds (status columns, board columns, etc.)
- **Sibling token**: `--color-bg` (#ffffff / #0d1117) — used by cards, headers, panels for elevated surface backgrounds. NOT modified in this feature.

---

## Entity Relationships

```text
:root / html.dark-mode-active
  └── --color-bg-secondary: #FFC0CB / #2d1a1e
        ├── body { background: var(--color-bg-secondary) }     ← Page background
        ├── .status-column { background: var(--color-bg-secondary) }
        ├── .board-column { background: var(--color-bg-secondary) }
        ├── .agent-config-row { background: var(--color-bg-secondary) }
        └── [other components using var(--color-bg-secondary)]
  
  └── --color-bg: #ffffff / #0d1117   ← NOT CHANGED
        ├── .app-header { background: var(--color-bg) }
        ├── .task-card { background: var(--color-bg) }
        ├── .board-issue-card { background: var(--color-bg) }
        └── [cards, panels, elevated surfaces]
```

**Key Insight**: The visual hierarchy is preserved because `--color-bg` (white/dark) remains unchanged. Components using `--color-bg` appear elevated above the pink `--color-bg-secondary` background.

---

## Data Validation

### Compile-Time Validation

- **CSS Syntax**: Hex color values are valid CSS (no linting issues)
- **Vite Build**: CSS custom properties are passed through as-is (no transformation needed)

### Runtime Validation

None required. CSS custom properties are static declarations with no user input or dynamic generation.

### Human Validation (Acceptance Criteria)

From spec.md acceptance scenarios:
1. Application displays pink background on all primary screens (visual inspection)
2. Text maintains ≥4.5:1 contrast ratio against pink background (contrast checker tool)
3. Buttons, icons, input fields remain visually distinct (visual inspection)
4. Pink background renders on mobile, tablet, desktop (responsive check)
5. Changing `--color-bg-secondary` value propagates across all screens (developer verification)

---

## Data Storage

**Storage Mechanism**: Git repository source code (CSS file)  
**Format**: CSS custom properties in `frontend/src/index.css`  
**Persistence**: Version controlled via git  
**Runtime**: Browser CSSOM (CSS Object Model) — parsed once on page load  
**Backup**: GitHub remote repository

---

## Data Flow

```text
Developer updates CSS variable value in index.css
       ↓
Git commit with new color values
       ↓
Vite build process (frontend) — CSS bundled
       ↓
Browser loads CSS, parses :root variables
       ↓
body { background: var(--color-bg-secondary) } resolves to #FFC0CB
       ↓
All elements referencing var(--color-bg-secondary) update
       ↓
User toggles dark mode → html.dark-mode-active class added
       ↓
--color-bg-secondary resolves to #2d1a1e (dark pink)
```

**Flow Characteristics**:
- **Declarative**: CSS cascade handles variable resolution automatically
- **No JavaScript**: Theme toggle already handled by existing `useAppTheme` hook
- **Instant**: CSS variable changes apply synchronously when class toggles
- **No persistence layer**: No database, API, or localStorage changes (theme preference storage already exists)

---

## Data Constraints

### Technical Constraints

- **Browser support**: CSS custom properties supported in all modern browsers (Chrome 49+, Firefox 31+, Safari 9.1+, Edge 15+)
- **Color gamut**: sRGB hex colors — universally supported
- **Specificity**: `html.dark-mode-active` selector overrides `:root` via specificity (existing pattern)

### Business Constraints

From spec.md requirements:
- **FR-001**: MUST apply pink (#FFC0CB) to root application container
- **FR-002**: MUST define as centralized variable (CSS custom property)
- **FR-003**: MUST maintain ≥4.5:1 text contrast ratio
- **FR-005**: MUST render correctly across all screen sizes
- **FR-008**: SHOULD support dark mode variant

### Accessibility Constraints

- **WCAG 2.1 AA 1.4.3**: Contrast ratio ≥4.5:1 for normal text (verified in research.md)
- **WCAG 2.1 AA 1.4.11**: Non-text contrast ≥3:1 for UI components (borders/icons maintain contrast)

---

## Security Considerations

**Threat Model**: None — static CSS color values with no user input or dynamic generation

**Security Properties**:
- **No XSS risk**: Hardcoded CSS values, not user-generated content
- **No injection risk**: No dynamic CSS generation or template rendering
- **No data exposure**: Color values are public styling information

---

## Performance Characteristics

**Size Impact**:
- Old value: `#f6f8fa` (7 chars) → New value: `#FFC0CB` (7 chars) — zero net change
- Old dark value: `#161b22` (7 chars) → New dark value: `#2d1a1e` (7 chars) — zero net change

**Runtime Impact**: None — CSS custom property resolution is O(1)

**Memory Impact**: Negligible — identical memory footprint as previous color values

---

## Phase 1 Data Model Completion Checklist

- [x] All entities identified (1 design token: --color-bg-secondary)
- [x] Entity attributes documented with current/new values
- [x] Validation rules defined (valid CSS color, WCAG contrast)
- [x] Relationships documented (body background, component backgrounds)
- [x] Data flow described (CSS variable → browser rendering)
- [x] Storage mechanism identified (CSS file in git)
- [x] Security considerations addressed (no risks)
- [x] Performance impact assessed (zero impact)
- [x] Accessibility constraints documented

**Status**: ✅ **DATA MODEL COMPLETE** - Ready for contracts and quickstart generation
