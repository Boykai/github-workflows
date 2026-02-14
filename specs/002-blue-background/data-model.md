# Data Model: Blue Background Color

**Feature**: Blue Background Color  
**Branch**: 002-blue-background  
**Date**: 2026-02-14

## Overview

This document defines the data entities, types, and validation rules for the blue background color feature. Since this is primarily a CSS/theming change, the data model focuses on theme configuration, color values, and accessibility validation entities.

---

## 1. Theme Color Configuration

### Entity: `ColorTheme`

**Purpose**: Represents the color scheme for light and dark modes

**Properties**:

| Property | Type | Required | Validation | Description |
|----------|------|----------|------------|-------------|
| `mode` | `'light' \| 'dark'` | Yes | Enum validation | Theme mode identifier |
| `backgroundColor` | `string` | Yes | CSS color hex format (#RRGGBB) | Primary background color |
| `backgroundSecondary` | `string` | Yes | CSS color hex format (#RRGGBB) | Secondary background for panels/cards |
| `textColor` | `string` | Yes | CSS color hex format (#RRGGBB) | Primary text color |
| `textColorSecondary` | `string` | Yes | CSS color hex format (#RRGGBB) | Secondary text color |

**Validation Rules**:
- All color values must be valid 6-digit hex codes (e.g., `#2196F3`)
- `backgroundColor` must differ from `textColor` by at least 4.5:1 contrast ratio
- `mode` must be either `'light'` or `'dark'`

**Example Light Mode**:
```typescript
{
  mode: 'light',
  backgroundColor: '#2196F3',      // Material Blue 500
  backgroundSecondary: '#FFFFFF',  // White for content panels
  textColor: '#FFFFFF',            // White text (for headers)
  textColorSecondary: '#1565C0'    // Darker blue for secondary text
}
```

**Example Dark Mode**:
```typescript
{
  mode: 'dark',
  backgroundColor: '#1565C0',      // Material Blue 800 (darker for dark mode)
  backgroundSecondary: '#0D1117',  // Near-black for content panels
  textColor: '#E6EDF3',            // Off-white text
  textColorSecondary: '#8B949E'    // Muted gray for secondary text
}
```

**State Transitions**:
- User toggles theme → `mode` changes between `'light'` and `'dark'`
- All color properties update to match the selected mode
- Transition is instant via CSS class change on `document.documentElement`

---

## 2. Accessibility Validation

### Entity: `ContrastValidation`

**Purpose**: Validates WCAG AA contrast compliance for color combinations

**Properties**:

| Property | Type | Required | Validation | Description |
|----------|------|----------|------------|-------------|
| `foregroundColor` | `string` | Yes | CSS color hex format | Text or interactive element color |
| `backgroundColor` | `string` | Yes | CSS color hex format | Background color |
| `contrastRatio` | `number` | Computed | 1.0 - 21.0 range | Calculated contrast ratio |
| `wcagLevel` | `'AA' \| 'AAA' \| 'fail'` | Computed | Based on contrast ratio | WCAG compliance level |
| `textSize` | `'normal' \| 'large'` | Yes | Enum validation | Text size category |
| `elementType` | `'text' \| 'interactive'` | Yes | Enum validation | UI element type |
| `isCompliant` | `boolean` | Computed | Based on WCAG rules | Whether combination passes WCAG AA |

**Validation Rules**:
- `contrastRatio` calculated using WCAG formula: `(L1 + 0.05) / (L2 + 0.05)` where L1 > L2
- For `textSize: 'normal'` and `elementType: 'text'`: `contrastRatio` must be ≥ 4.5:1 for WCAG AA
- For `textSize: 'large'` and `elementType: 'text'`: `contrastRatio` must be ≥ 3:1 for WCAG AA
- For `elementType: 'interactive'`: `contrastRatio` must be ≥ 3:1 for WCAG AA
- `wcagLevel` is `'AA'` if meets AA threshold, `'AAA'` if meets AAA (7:1 normal, 4.5:1 large), `'fail'` otherwise
- `isCompliant` is `true` if `wcagLevel` is `'AA'` or `'AAA'`

**Example**:
```typescript
{
  foregroundColor: '#FFFFFF',      // White text
  backgroundColor: '#2196F3',      // Blue background
  contrastRatio: 3.15,             // Calculated
  wcagLevel: 'fail',               // Below 4.5:1 for normal text
  textSize: 'normal',
  elementType: 'text',
  isCompliant: false               // Fails WCAG AA
}
```

**Contrast Pass Example**:
```typescript
{
  foregroundColor: '#FFFFFF',      // White text
  backgroundColor: '#1565C0',      // Darker blue
  contrastRatio: 5.98,             // Calculated
  wcagLevel: 'AA',                 // Meets AA (≥4.5:1)
  textSize: 'normal',
  elementType: 'text',
  isCompliant: true                // Passes WCAG AA
}
```

**State Transitions**:
- When colors change → recompute `contrastRatio`, `wcagLevel`, `isCompliant`
- Validation runs during development/testing phase
- No runtime state changes (validation is design-time only)

---

## 3. CSS Custom Property Mapping

### Entity: `CSSVariableMap`

**Purpose**: Maps logical theme properties to CSS custom property names

**Properties**:

| Property | Type | Required | Validation | Description |
|----------|------|----------|------------|-------------|
| `variableName` | `string` | Yes | Must start with `--` | CSS custom property name |
| `value` | `string` | Yes | CSS color value | Color value (hex, rgb, etc.) |
| `scope` | `':root' \| 'html.dark-mode-active'` | Yes | Enum validation | CSS selector scope |
| `description` | `string` | No | - | Human-readable purpose |

**Validation Rules**:
- `variableName` must start with `--` (CSS custom property syntax)
- `value` must be valid CSS color value
- `scope` determines which CSS selector the variable is defined under
- Each `variableName` should be unique within a given `scope`

**Light Mode Variables** (`scope: ':root'`):
```typescript
[
  {
    variableName: '--color-bg',
    value: '#2196F3',
    scope: ':root',
    description: 'Primary background color (Material Blue 500)'
  },
  {
    variableName: '--color-bg-secondary',
    value: '#FFFFFF',
    scope: ':root',
    description: 'Secondary background for content panels'
  },
  {
    variableName: '--color-text',
    value: '#24292F',
    scope: ':root',
    description: 'Primary text color (on secondary backgrounds)'
  }
]
```

**Dark Mode Variables** (`scope: 'html.dark-mode-active'`):
```typescript
[
  {
    variableName: '--color-bg',
    value: '#1565C0',
    scope: 'html.dark-mode-active',
    description: 'Primary background color (Material Blue 800 for dark mode)'
  },
  {
    variableName: '--color-bg-secondary',
    value: '#161B22',
    scope: 'html.dark-mode-active',
    description: 'Secondary background for content panels'
  },
  {
    variableName: '--color-text',
    value: '#E6EDF3',
    scope: 'html.dark-mode-active',
    description: 'Primary text color (on secondary backgrounds)'
  }
]
```

**State Transitions**:
- Variables are static (defined in CSS file)
- No runtime state changes
- User theme toggle applies/removes `html.dark-mode-active` class → browser applies correct variable set

---

## 4. Theme State (Existing - No Changes)

### Entity: `ThemeState`

**Purpose**: Runtime theme preference state (existing in `useAppTheme` hook)

**Note**: This entity exists in the current application and requires **no modifications** for the blue background feature. Documented here for completeness.

**Properties**:

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `isDarkMode` | `boolean` | Yes | Whether dark mode is active |

**Persistence**:
- Stored in `localStorage` with key `'tech-connect-theme-mode'`
- Value: `'light'` or `'dark'` (string)
- Read on application initialization
- Updated when user toggles theme

**State Transitions**:
- User clicks theme toggle button → `isDarkMode` inverts
- `isDarkMode` change → localStorage updated
- `isDarkMode` change → CSS class `dark-mode-active` added/removed on `document.documentElement`

**Unchanged for Blue Background**:
- No new properties needed
- No changes to `useAppTheme` hook
- Blue background colors are pure CSS via custom properties

---

## 5. Component Color Props (Implicit)

### Entity: `ComponentColorProps`

**Purpose**: Color-related props that components may receive (implicit, not explicitly defined)

**Note**: Components in the application use CSS classes and inherit colors from CSS custom properties. No explicit color props are passed. Documented here to clarify the color application mechanism.

**Pattern**:
- Components apply CSS classes (e.g., `className="app-container"`)
- CSS rules reference custom properties: `background: var(--color-bg);`
- Browser resolves custom property values based on current theme (`:root` or `html.dark-mode-active`)

**No Changes Required**:
- Existing components continue using `var(--color-bg)`, `var(--color-text)`, etc.
- Blue background automatically applies when CSS custom properties are updated
- No component refactoring needed

---

## 6. Test Data Structures

### Entity: `ColorTestCase`

**Purpose**: Test case for validating color combinations during E2E/accessibility tests

**Properties**:

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `testName` | `string` | Yes | Human-readable test case name |
| `element` | `string` | Yes | CSS selector for element to test |
| `expectedBackground` | `string` | Yes | Expected background color (hex) |
| `expectedText` | `string` | Yes | Expected text color (hex) |
| `minContrastRatio` | `number` | Yes | Minimum required contrast (4.5 or 3.0) |
| `mode` | `'light' \| 'dark'` | Yes | Theme mode to test |

**Example Test Cases**:
```typescript
[
  {
    testName: 'Login screen background (light mode)',
    element: '.app-login',
    expectedBackground: '#2196F3',
    expectedText: '#FFFFFF',
    minContrastRatio: 4.5,
    mode: 'light'
  },
  {
    testName: 'Dashboard background (dark mode)',
    element: '.app-container',
    expectedBackground: '#1565C0',
    expectedText: '#E6EDF3',
    minContrastRatio: 4.5,
    mode: 'dark'
  },
  {
    testName: 'Primary button (light mode)',
    element: 'button.primary',
    expectedBackground: '#0969DA',
    expectedText: '#FFFFFF',
    minContrastRatio: 3.0,
    mode: 'light'
  }
]
```

**Usage**:
- Test runner (Playwright) iterates through test cases
- For each case: toggle theme, select element, measure colors, validate contrast
- Fail test if `actualContrastRatio < minContrastRatio`

---

## Entity Relationships

```
ColorTheme (light/dark)
  ↓ maps to
CSSVariableMap (multiple variables per theme)
  ↓ applied via
ThemeState (isDarkMode boolean)
  ↓ triggers
CSS class on document.documentElement
  ↓ validated by
ContrastValidation (multiple validations per theme)
  ↓ tested via
ColorTestCase (E2E/accessibility tests)
```

**Flow**:
1. Developer defines `ColorTheme` for light and dark modes
2. Values are translated to `CSSVariableMap` entries in `index.css`
3. User preference stored in `ThemeState` (localStorage)
4. Theme toggle updates `ThemeState` → CSS class change → browser applies correct `CSSVariableMap` values
5. During development: `ContrastValidation` entities verify WCAG compliance
6. During testing: `ColorTestCase` entities automate visual/accessibility validation

---

## Validation Summary

| Entity | Validation Type | Critical Rules |
|--------|-----------------|----------------|
| `ColorTheme` | Structural | Valid hex colors, 4.5:1 contrast min |
| `ContrastValidation` | Computed | WCAG AA thresholds (4.5:1 text, 3:1 interactive) |
| `CSSVariableMap` | Structural | Valid CSS syntax, unique names per scope |
| `ThemeState` | Behavioral | Persists to localStorage, syncs with DOM |
| `ColorTestCase` | Test | Expected colors match actual, contrast meets min |

---

## Implementation Notes

### File Locations
- **Color definitions**: `frontend/src/index.css` (`:root` and `html.dark-mode-active` selectors)
- **Theme state hook**: `frontend/src/hooks/useAppTheme.ts` (unchanged)
- **Component styles**: `frontend/src/App.css` and component CSS files (contrast adjustments if needed)
- **Test cases**: `frontend/e2e/ui.spec.ts` (optional visual validation)

### Key Constraints
- All color values must be 6-digit hex codes for consistency
- Light mode background: `#2196F3` (per spec requirement)
- Dark mode background: `#1565C0` (chosen for contrast/aesthetics)
- Text must meet WCAG AA: 4.5:1 for normal text, 3:1 for large text/interactive elements
- No JavaScript color calculations required (pure CSS)

### No Database/API Changes
- This feature involves no backend changes
- No new API endpoints or database schemas
- All state is frontend-only (CSS + localStorage)

---

## Glossary

- **WCAG AA**: Web Content Accessibility Guidelines Level AA (4.5:1 contrast for normal text, 3:1 for large text)
- **CSS Custom Property**: CSS variable (e.g., `--color-bg`) that can be referenced with `var(--color-bg)`
- **Contrast Ratio**: Measurement of luminance difference between foreground and background colors (1:1 to 21:1 scale)
- **Material Blue 500**: Google Material Design blue color `#2196F3`
- **Material Blue 800**: Google Material Design darker blue color `#1565C0`
- **Theme Mode**: Light or dark appearance mode for the application

---

**End of Data Model**
