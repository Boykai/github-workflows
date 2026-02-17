# Data Model: Apply Red Background Color to Entire App Interface

**Feature**: 003-red-background | **Date**: 2026-02-17  
**Purpose**: Define entities and their relationships for feature implementation

## Model Overview

This feature involves no data model in the traditional sense (no database entities, API models, or state management). The "data" being changed consists of CSS custom property values in the global stylesheet. This document exists to satisfy Phase 1 requirements but is intentionally minimal due to the feature's lack of programmatic data structures.

## Entities

### Entity: ThemeColorVariables

**Type**: CSS Custom Properties (Presentation Layer Only)  
**Purpose**: Define the global color scheme applied across the entire application  
**Lifecycle**: Compile-time values embedded in CSS, toggled at runtime by class swap

**Attributes (Light Mode - `:root`)**:

| Attribute | Type | Current Value | New Value | Rationale |
|-----------|------|---------------|-----------|-----------|
| `--color-bg` | CSS color | `#ffffff` | `#FF0000` | Primary red background (FR-001) |
| `--color-bg-secondary` | CSS color | `#f6f8fa` | `#CC0000` | Secondary red for body/depth |
| `--color-text` | CSS color | `#24292f` | `#FFFFFF` | White text for contrast (FR-003) |
| `--color-text-secondary` | CSS color | `#57606a` | `#FFD700` | Gold secondary text for hierarchy |
| `--color-border` | CSS color | `#d0d7de` | `#FF6666` | Red-tinted borders |
| `--shadow` | CSS shadow | `0 1px 3px rgba(0,0,0,0.1)` | `0 1px 3px rgba(139,0,0,0.3)` | Red-tinted shadows |

**Attributes (Dark Mode - `html.dark-mode-active`)**:

| Attribute | Type | Current Value | New Value | Rationale |
|-----------|------|---------------|-----------|-----------|
| `--color-bg` | CSS color | `#0d1117` | `#8B0000` | Dark red background (FR-004) |
| `--color-bg-secondary` | CSS color | `#161b22` | `#5C0000` | Deeper dark red for body/depth |
| `--color-border` | CSS color | `#30363d` | `#B22222` | Firebrick borders for dark mode |
| `--shadow` | CSS shadow | `0 1px 3px rgba(0,0,0,0.4)` | `0 1px 3px rgba(0,0,0,0.6)` | Deeper shadow for dark mode |

**Note**: Dark mode `--color-text` (#E6EDF3) and `--color-text-secondary` (#8B949E) remain unchanged as they already provide excellent contrast against dark red (#8B0000).

**Location**: `frontend/src/index.css` lines 2-15 (`:root`) and lines 18-30 (`html.dark-mode-active`)

**Validation Rules**:
1. **Valid CSS color**: All values must be valid CSS color values
2. **Contrast compliance**: Text colors must achieve 4.5:1 contrast ratio against background colors per WCAG AA
3. **Red identity**: Both light and dark mode backgrounds must be visually recognizable as "red"
4. **Consistency**: Variable names remain unchanged—only values are modified

**State Transitions**:
- **Light → Dark**: Triggered by `useAppTheme.ts` hook adding `dark-mode-active` class to `<html>` element
- **Dark → Light**: Triggered by removing `dark-mode-active` class
- **No other transitions**: Background color does not change based on route, authentication state, or user interaction

**Relationships**: 
- `--color-bg` → consumed by `.app-header`, component backgrounds
- `--color-bg-secondary` → consumed by `body`, `.theme-toggle-btn`
- `--color-text` → consumed by `body`, `.app-login h1`, `.login-button` background
- `--color-border` → consumed by `.app-header`, `.spinner`, form elements
- `--shadow` → consumed by card and container shadow styles

---

## Entity Relationships

**Diagram**: Single entity with downstream CSS consumption

```
ThemeColorVariables (:root / html.dark-mode-active)
        │
        ├── body { background: var(--color-bg-secondary); color: var(--color-text); }
        ├── .app-header { background: var(--color-bg); border: var(--color-border); }
        ├── .theme-toggle-btn { background: var(--color-bg-secondary); }
        ├── .spinner { border-color: var(--color-border); }
        ├── .login-button { background: var(--color-text); }
        └── [all other components using var(--color-*) references]
```

No cross-entity relationships. All components consume the same set of CSS variables.

---

## Data Validation

### Compile-Time Validation

- **CSS syntax**: Browser CSS parser validates color values (malformed values are ignored)
- **Linter**: Prettier formats CSS but does not enforce color value rules
- **Build**: Vite bundles CSS without color validation

### Runtime Validation

None required. CSS custom properties are static values toggled by class presence.

### Human Validation (Acceptance Criteria)

From spec.md acceptance scenarios:
1. All screens display red (#FF0000) background in light mode (visual inspection)
2. Dark mode displays deep red (#8B0000) background (visual inspection)
3. All text is readable against red backgrounds (contrast checker tool)
4. Background persists during navigation without flickering (visual inspection)
5. Background fills viewport on all device sizes (responsive testing)

---

## Data Storage

**Storage Mechanism**: Git repository source code  
**Format**: CSS stylesheet (`index.css`)  
**Persistence**: Version controlled via git  
**Runtime Toggle**: `localStorage` key `tech-connect-theme-mode` controls light/dark class  
**No server-side storage**: Theme preference is client-side only

---

## Data Flow

```
CSS custom properties defined in index.css
        ↓
Vite build bundles CSS
        ↓
Browser loads CSS, applies :root variables
        ↓
useAppTheme.ts toggles dark-mode-active class
        ↓
CSS specificity overrides :root with html.dark-mode-active values
        ↓
All var(--color-*) references update automatically
        ↓
Red background displayed across entire viewport
```

**Flow Characteristics**:
- **Reactive**: CSS custom property changes propagate instantly to all consumers
- **No JavaScript involvement**: Background color is pure CSS (except theme toggle)
- **No network requests**: No server-side color configuration
- **Bidirectional toggle**: Light ↔ Dark via single class swap

---

## Data Constraints

### Technical Constraints

- **CSS custom property support**: Required (supported in 97%+ of browsers)
- **Color format**: Hex color values (#RRGGBB) for consistency
- **Specificity**: `html.dark-mode-active` must override `:root` (ensured by existing CSS structure)

### Business Constraints

From spec.md requirements:
- **FR-001**: MUST use #FF0000 as primary background color
- **FR-003**: MUST maintain 4.5:1 contrast ratio for text
- **FR-004**: MUST provide dark-mode red variant
- **FR-007**: MUST preserve component-level backgrounds
- **FR-008**: SHOULD allow future theme overrides

### Accessibility Constraints

- **WCAG AA 4.5:1**: Normal text contrast against background
- **WCAG AA 3:1**: Large text and UI component contrast against background
- **Color not sole indicator**: UI elements must not rely solely on red/non-red distinction

---

## Data Migration

**Migration Type**: In-place CSS value replacement  
**Rollback**: Git revert to previous commit  
**Data Loss Risk**: None - no user data involved  
**Backward Compatibility**: N/A - visual change only, no API contracts

**Migration Steps**:
1. Update CSS variable values in `frontend/src/index.css`
2. Commit changes
3. Deploy updated frontend

**No database migrations required** - this is a frontend-only CSS change

---

## Security Considerations

**Threat Model**: None - static CSS values with no user input or dynamic generation

**Security Properties**:
- **No XSS risk**: Hardcoded CSS values, not user-generated content
- **No injection risk**: No dynamic CSS generation
- **No authentication impact**: Background color is public visual property
- **No data exposure**: No sensitive information in color values

---

## Performance Characteristics

**Size Impact**:
- CSS variable values are similar length (hex colors)
- **Net change**: ~0 bytes difference in compiled CSS

**Runtime Impact**:
- CSS custom property resolution: O(1) per property lookup
- No additional repaints beyond existing theme toggle behavior
- No performance degradation expected

**Memory Impact**: Negligible - CSS variable storage unchanged

---

## Alternative Data Models Considered

### Alternative 1: New CSS Variables

```css
:root {
  --color-bg-red: #FF0000;
  --color-bg-red-dark: #8B0000;
}
```

**Rejected Rationale**: Introduces unnecessary new variables. Existing `--color-bg` and `--color-bg-secondary` serve the same purpose. Adding red-specific variables would violate DRY.

### Alternative 2: Inline Styles in React Components

```tsx
<div style={{ backgroundColor: '#FF0000' }}>
```

**Rejected Rationale**: Bypasses theming system, breaks dark mode toggle, requires changes to every component. Massively increases scope.

### Alternative 3: CSS-in-JS (Styled Components / Emotion)

**Rejected Rationale**: App doesn't use CSS-in-JS. Adding it for a single color change would be extreme over-engineering.

---

## Phase 1 Data Model Completion Checklist

- [x] All entities identified (1 entity: ThemeColorVariables)
- [x] Entity attributes documented with current/new values
- [x] Validation rules defined (CSS validity, contrast compliance)
- [x] Relationships documented (CSS variable → component consumption)
- [x] Data flow described (CSS → build → browser → toggle)
- [x] Storage mechanism identified (git source code + localStorage toggle)
- [x] Security considerations addressed (no risks)
- [x] Performance impact assessed (negligible)
- [x] Migration approach defined (value replacement)
- [x] Alternative models evaluated and rejected

**Status**: ✅ **DATA MODEL COMPLETE** - Ready for contracts and quickstart generation
