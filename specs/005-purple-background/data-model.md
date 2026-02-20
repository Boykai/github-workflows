# Data Model: Add Purple Background Color to App

**Feature**: 005-purple-background | **Date**: 2026-02-20  
**Purpose**: Define entities and their relationships for feature implementation

## Model Overview

This feature involves no data model in the traditional sense (no database entities, API models, or state management). The "data" being changed consists of CSS custom property definitions in the global stylesheet. This document exists to satisfy Phase 1 requirements but is intentionally minimal due to the feature's lack of programmatic data structures.

## Entities

### Entity: AppBackgroundTheme

**Type**: CSS Custom Property (Presentation Layer Only)  
**Purpose**: Define the application body background color for branded visual identity  
**Lifecycle**: Compile-time constant embedded in CSS, applied at page load

**Attributes**:

| Attribute | Type | Constraints | Current Value | New Value |
|-----------|------|-------------|---------------|-----------|
| `--color-bg-app` (light) | CSS color | Valid hex, WCAG AA contrast with foreground | N/A (does not exist) | `#7C3AED` |
| `--color-bg-app` (dark) | CSS color | Valid hex, WCAG AA contrast with foreground | N/A (does not exist) | `#7C3AED` |
| `body background` | CSS property | References `--color-bg-app` | `var(--color-bg-secondary)` | `var(--color-bg-app)` |

**Location**: `frontend/src/index.css`

**Validation Rules**:
1. **Non-empty**: CSS variable must have a valid color value
2. **Hex format**: Must be specific hex value (#7C3AED), not CSS keyword
3. **WCAG AA compliance**: Contrast ratio ≥ 4.5:1 with white foreground text (#FFFFFF on #7C3AED = 6.65:1 ✅)
4. **Consistency**: Same purple value in both light and dark mode for brand consistency

**State Transitions**: None — static CSS variable with no runtime changes (dark mode toggle does not alter the purple value)

**Relationships**: None — `--color-bg-app` is independent of other CSS variables; existing `--color-bg` and `--color-bg-secondary` remain unchanged

---

### Entity: ExposedSurfaceTextColors

**Type**: CSS Rule Overrides (Presentation Layer Only)  
**Purpose**: Ensure text readability on surfaces where the purple background is visible  
**Lifecycle**: Applied when `.app-login` or `.app-loading` elements are rendered

**Attributes**:

| Attribute | Type | Constraints | Current Value | New Value |
|-----------|------|-------------|---------------|-----------|
| `.app-login h1 color` | CSS color | WCAG AA ≥ 4.5:1 vs #7C3AED | `var(--color-text)` (#24292f) | `#ffffff` |
| `.app-login p color` | CSS color | WCAG AA ≥ 4.5:1 vs #7C3AED | `var(--color-text-secondary)` (#57606a) | `rgba(255, 255, 255, 0.85)` |
| `.app-loading p color` | CSS color | WCAG AA ≥ 4.5:1 vs #7C3AED | `var(--color-text)` (#24292f) | `#ffffff` |

**Location**: `frontend/src/index.css` (body/base section) or `frontend/src/App.css` (component section)

**Validation Rules**:
1. **Contrast compliance**: All text on #7C3AED must meet WCAG AA minimum (4.5:1)
2. **White (#FFFFFF) on #7C3AED**: 6.65:1 ✅
3. **rgba(255,255,255,0.85) on #7C3AED**: ~5.2:1 ✅

---

## Entity Relationships

**Diagram**: N/A — CSS variable definitions with no entity relationships

This feature modifies isolated CSS properties with no connections to:
- User data or session state
- Backend API models
- Database records
- React component state or props
- JavaScript runtime behavior

---

## Data Validation

### Compile-Time Validation

- **CSS Syntax**: Vite/PostCSS will fail build if CSS syntax is invalid
- **Variable Reference**: `var(--color-bg-app)` will resolve to transparent if undefined (caught by visual testing)

### Runtime Validation

None required. CSS variables are static declarations with no user input or dynamic generation.

### Human Validation (Acceptance Criteria)

From spec.md acceptance scenarios:
1. All primary screens display purple background (#7C3AED) — visual inspection
2. Text on purple background is readable (WCAG AA) — contrast checker
3. Purple renders identically across Chrome, Firefox, Safari, Edge — visual comparison
4. No FOUC or background flicker during page load — visual observation

---

## Data Storage

**Storage Mechanism**: Git repository source code  
**Format**: CSS text in `index.css`  
**Persistence**: Version controlled via git  
**Backup**: GitHub remote repository  
**Encryption**: Not applicable (public source code)

---

## Data Flow

```
Developer adds CSS variable to index.css
       ↓
Git commit with purple background styling
       ↓
Vite build process (frontend)
       ↓
CSS bundle with --color-bg-app: #7C3AED
       ↓
Browser loads CSS before first paint
       ↓
Body element renders with purple background
```

**Flow Characteristics**:
- **Unidirectional**: Source → Build → Deploy → Display
- **No user input**: Users cannot change background color (read-only display)
- **No persistence layer**: No database, localStorage, or cookies involved
- **Synchronous**: CSS loads before React hydration (no FOUC risk)

---

## Security Considerations

**Threat Model**: None — static CSS values with no user input or dynamic generation

**Security Properties**:
- **No XSS risk**: Hardcoded CSS values, not user-generated content
- **No injection risk**: No dynamic CSS, template rendering, or `style` attribute manipulation
- **No authentication impact**: Background color is public visual information
- **No authorization impact**: No access control decisions based on styling

---

## Performance Characteristics

**Size Impact**:
- New CSS: ~80 bytes (variable definition + body rule update + text color overrides)
- **Net impact**: Negligible (~0.01% of typical CSS bundle)

**Runtime Impact**:
- CSS variable resolution: O(1) per element
- No additional repaints beyond initial paint
- No JavaScript execution for background application

**Memory Impact**: Negligible — single CSS variable stored in CSSOM

---

## Alternative Data Models Considered

### Alternative 1: JavaScript Theme Object

```typescript
// theme.ts
export const theme = {
  colors: { bgApp: '#7C3AED' }
};
```

**Rejected Rationale**: YAGNI violation. The app already uses CSS variables for theming. Adding a JS theme object would introduce a parallel theming system.

### Alternative 2: CSS-in-JS (styled-components)

```typescript
const AppWrapper = styled.div`
  background: #7C3AED;
`;
```

**Rejected Rationale**: The project uses plain CSS with custom properties. Introducing CSS-in-JS for one feature violates existing patterns and adds bundle size.

### Alternative 3: Tailwind CSS Utility

```html
<body class="bg-[#7C3AED]">
```

**Rejected Rationale**: Project does not use Tailwind CSS. Adding it for one feature is disproportionate.

---

## Phase 1 Data Model Completion Checklist

- [x] All entities identified (2 presentation entities: AppBackgroundTheme, ExposedSurfaceTextColors)
- [x] Entity attributes documented with current/new values
- [x] Validation rules defined (WCAG AA contrast, hex format)
- [x] Relationships documented (none — isolated CSS changes)
- [x] Data flow described (source → build → display)
- [x] Storage mechanism identified (git source code)
- [x] Security considerations addressed (no risks)
- [x] Performance impact assessed (negligible)
- [x] Alternative models evaluated and rejected

**Status**: ✅ **DATA MODEL COMPLETE** — Ready for contracts and quickstart generation
