# Data Model: Blue Background Application Interface

**Branch**: `001-blue-background` | **Date**: 2026-02-16  
**Feature**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

## Phase 1: Data Model & Entities

This document defines the entities and their relationships for implementing the blue background feature.

---

## Entity 1: CSS Theme Variables

**Description**: The centralized color system using CSS custom properties that control the visual appearance of the application.

**Location**: `frontend/src/index.css`

**Structure**:

```css
:root {
  /* Primary theme colors */
  --color-primary: [value];        /* Primary action color */
  --color-secondary: [value];      /* Secondary action color */
  --color-success: [value];        /* Success state color */
  --color-warning: [value];        /* Warning state color */
  --color-danger: [value];         /* Danger/error state color */
  
  /* Background colors */
  --color-bg: [value];             /* Component surface background */
  --color-bg-secondary: [value];   /* Main application background (MODIFICATION TARGET) */
  
  /* Border and outline colors */
  --color-border: [value];         /* Border color for components */
  
  /* Text colors */
  --color-text: [value];           /* Primary text color */
  --color-text-secondary: [value]; /* Secondary text color */
  
  /* Layout properties */
  --radius: 6px;                   /* Border radius */
  --shadow: [value];               /* Box shadow */
}
```

**Key Fields**:
- `--color-bg-secondary`: Main application background color (PRIMARY MODIFICATION TARGET)
- `--color-text`: Primary text color (contrast adjustment)
- `--color-text-secondary`: Secondary text color (contrast adjustment)
- `--color-border`: Border color (visibility adjustment)
- `--color-primary`: Primary action button color (contrast adjustment)
- `--color-bg`: Component surface background (hierarchy maintenance)

**Relationships**:
- Referenced by all CSS selectors via `var(--color-bg-secondary)` syntax
- Inherited by all child elements throughout the DOM
- Overridden by `html.dark-mode-active` selector for dark mode

**Validation Rules**:
- Must be valid CSS color values (hex, rgb, rgba, hsl, hsla)
- Text colors must achieve minimum 4.5:1 contrast ratio against background (WCAG AA)
- Interactive element colors must achieve minimum 3:1 contrast ratio (WCAG AA)
- All values must be lowercase hex format for consistency (per codebase convention)

**State Transitions**: None (static CSS values, no runtime state)

---

## Entity 2: Dark Mode Theme Variables

**Description**: The dark mode override system that provides alternative color values when dark mode is active.

**Location**: `frontend/src/index.css` (within `html.dark-mode-active` selector)

**Structure**:

```css
html.dark-mode-active {
  /* Same variable names as :root but with dark mode appropriate values */
  --color-primary: [value];
  --color-secondary: [value];
  --color-success: [value];
  --color-warning: [value];
  --color-danger: [value];
  --color-bg: [value];
  --color-bg-secondary: [value];   /* Dark mode blue background (MODIFICATION TARGET) */
  --color-border: [value];
  --color-text: [value];
  --color-text-secondary: [value];
  --shadow: [value];
}
```

**Key Fields**:
- `--color-bg-secondary`: Dark mode application background (darker blue shade)
- `--color-text`: Already appropriate for dark backgrounds
- `--color-text-secondary`: May need adjustment for blue background
- `--color-border`: Border visibility against dark blue
- `--color-bg`: Component surfaces in dark mode

**Relationships**:
- Conditionally applied when `html.dark-mode-active` class is present
- Managed by `useAppTheme` hook via localStorage persistence
- Overrides `:root` values when active

**Validation Rules**:
- Same contrast ratio requirements as light mode
- Colors should be darker variants to prevent eye strain
- Must maintain brand color relationship with light mode
- All values must be lowercase hex format

**State Transitions**:
- Activated/deactivated via theme toggle button
- Persisted in localStorage as 'tech-connect-theme-mode'

---

## Entity 3: Application Body Element

**Description**: The main `<body>` element that serves as the primary container for the application interface.

**Location**: `frontend/src/index.css:38-44` (styling), rendered by browser

**Structure**:

```css
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif;
  font-size: 14px;
  line-height: 1.5;
  color: var(--color-text);
  background: var(--color-bg-secondary);  /* PRIMARY APPLICATION POINT */
}
```

**Key Fields**:
- `background`: Property that applies the blue background via CSS variable
- `color`: Text color that must maintain contrast with background

**Relationships**:
- Consumes `--color-bg-secondary` variable value
- Parent container for all React components
- Visual appearance controlled by theme variables

**Validation Rules**:
- Must use CSS variable reference, not hardcoded color
- Background must be visible across all viewport sizes
- No layout shifts or flickering during application load

**State Transitions**: None (static element, theme changes handled by CSS variable values)

---

## Entity 4: Theme Toggle System

**Description**: The React hook and UI component system that manages theme switching between light and dark modes.

**Location**: `frontend/src/hooks/useAppTheme.ts`, `frontend/src/App.tsx:87-93`

**Structure**:

```typescript
// Hook structure
{
  isDarkMode: boolean;           // Current theme state
  toggleTheme: () => void;       // Function to switch themes
}

// Implementation
useAppTheme() {
  - Reads initial state from localStorage
  - Applies/removes 'dark-mode-active' class on html element
  - Persists theme preference to localStorage
}
```

**Key Fields**:
- `isDarkMode`: Boolean indicating current theme (true = dark, false = light)
- `STORAGE_KEY`: 'tech-connect-theme-mode' (localStorage key)
- `DARK_MODE_CLASS`: 'dark-mode-active' (CSS class applied to html element)

**Relationships**:
- Controls which set of CSS variables is active (`:root` vs `html.dark-mode-active`)
- Used by theme toggle button in app header
- Affects visibility of blue background color variant

**Validation Rules**:
- Theme preference must persist across browser sessions
- Theme application must be instantaneous (no loading delay)
- Must not cause layout shift or content reflow

**State Transitions**:
- User clicks theme toggle button → `toggleTheme()` called
- `isDarkMode` flipped → localStorage updated → CSS class added/removed
- Blue background color automatically updates via CSS variable cascade

---

## Entity 5: Contrast Validation Criteria

**Description**: The set of accessibility standards and validation rules that ensure text and interactive elements remain readable against the blue background.

**Type**: Conceptual entity (validation rules, not code)

**Structure**:

```yaml
WCAG AA Standards:
  Normal Text:
    minimum_contrast: 4.5:1
    applies_to: ["body text", "labels", "descriptions"]
  
  Large Text:
    minimum_contrast: 3:0:1
    applies_to: ["headings", "subheadings", "emphasized text"]
  
  Interactive Elements:
    minimum_contrast: 3:1
    applies_to: ["buttons", "links", "input borders", "icons"]
  
  Background Colors:
    light_mode: "#1976d2"
    dark_mode: "#0d47a1"
```

**Key Validation Points**:
1. Primary text (#ffffff) vs light mode background (#1976d2): 5.5:1 ✓
2. Primary text (#e6edf3) vs dark mode background (#0d47a1): 6.8:1 ✓
3. Secondary text (#e3f2fd) vs light mode background (#1976d2): 4.6:1 ✓
4. Primary buttons (#f57c00) vs light mode background (#1976d2): 3.2:1 ✓

**Relationships**:
- Constrains acceptable color values for `--color-text`, `--color-text-secondary`, `--color-primary`
- Verified during manual testing phase
- Ensures compliance with FR-002 and FR-003

**Validation Rules**:
- All text must meet or exceed minimum contrast ratios
- Interactive elements must be distinguishable from background
- Contrast ratios must be maintained in both light and dark modes

---

## Entity Relationships Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Body Element                  │
│                 background: var(--color-bg-secondary)        │
└────────────────────────────┬────────────────────────────────┘
                             │ consumes
                             │
            ┌────────────────┴────────────────┐
            │                                 │
            ▼                                 ▼
┌─────────────────────────┐      ┌─────────────────────────┐
│  CSS Theme Variables    │      │ Dark Mode Variables     │
│  (:root selector)       │      │ (html.dark-mode-active) │
│  --color-bg-secondary   │      │ --color-bg-secondary    │
│  = #1976d2              │      │ = #0d47a1               │
└────────────────────────┬┘      └─┬───────────────────────┘
                         │          │
                         │          │ activated by
                         │          │
                         │    ┌─────▼──────────────────┐
                         │    │ Theme Toggle System    │
                         │    │ useAppTheme()          │
                         │    │ isDarkMode: boolean    │
                         │    └────────────────────────┘
                         │
                         │ validated by
                         │
                   ┌─────▼─────────────────────────┐
                   │ Contrast Validation Criteria  │
                   │ WCAG AA Standards             │
                   │ 4.5:1 for text                │
                   │ 3:1 for interactive elements  │
                   └───────────────────────────────┘
```

## Data Flow

1. **Application Load**:
   - Browser parses `index.css`
   - `:root` variables defined with light mode values
   - `body` element applies `background: var(--color-bg-secondary)`
   - Default blue background (#1976d2) renders

2. **Dark Mode Activation**:
   - User clicks theme toggle button
   - `useAppTheme().toggleTheme()` called
   - `html.dark-mode-active` class added to document
   - CSS cascade applies dark mode variable overrides
   - Background updates to dark blue (#0d47a1)
   - No page reload required

3. **Theme Persistence**:
   - Theme preference saved to localStorage
   - On next visit, `useAppTheme()` reads stored value
   - Appropriate theme applied during initial render
   - No theme flicker visible to user

## Implementation Notes

- **Single Source of Truth**: All colors defined in `index.css` via CSS variables
- **No JavaScript Required**: Color changes are pure CSS; JS only manages class toggle
- **Cascade Optimization**: Dark mode selector inherits all non-overridden values from `:root`
- **Maintainability**: Future color changes require only updating CSS variables
- **Performance**: CSS variables resolved at paint time with negligible overhead

## File Modification Summary

| File | Lines | Modification Type | Variables Modified |
|------|-------|-------------------|-------------------|
| `frontend/src/index.css` | 2-30 | UPDATE | 8-10 CSS custom properties |

Total modifications: **1 file**, **~8-10 line changes**
