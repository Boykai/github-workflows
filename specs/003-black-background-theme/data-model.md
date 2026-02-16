# Data Model: Black Background Theme

**Feature**: 003-black-background-theme  
**Date**: 2026-02-16  
**Purpose**: Define theme-related data structures and state management

## Overview

This feature primarily involves CSS styling changes with minimal data model impact. The existing theme state management (via `useAppTheme` hook) will be adapted to control the black background theme instead of the current dark mode.

---

## Entity 1: Theme State

**Purpose**: Manage application theme state (light vs black background)

**Location**: Frontend state management (React hook: `useAppTheme`)

### Fields

| Field Name | Type | Required | Default | Description |
|------------|------|----------|---------|-------------|
| `isDarkMode` | boolean | Yes | true | Controls whether black theme is active. Despite the name, this will control the black background theme. Renaming avoided to maintain existing interface. |
| `toggleTheme` | function | Yes | N/A | Function to toggle between light and black themes |

### Validation Rules

- `isDarkMode` must be a boolean value
- Theme state should be initialized on component mount
- Theme changes should apply immediately (no delay or loading state)

### State Transitions

```
[Initial Load] → isDarkMode = true (black theme active)
     ↓
[User clicks theme toggle] → isDarkMode = !isDarkMode
     ↓
[DOM updated] → html class changes (dark-mode-active added/removed)
     ↓
[CSS variables applied] → Black background visible
```

### Relationships

- Theme state affects all visual components via CSS custom properties
- No persistence layer (theme resets on page reload per spec out-of-scope)
- No API interaction required

---

## Entity 2: CSS Custom Properties (Theme Variables)

**Purpose**: Define color values for black background theme

**Location**: `frontend/src/index.css`

### Properties (Black Theme)

| Property Name | Value | Purpose | Contrast Ratio |
|---------------|-------|---------|----------------|
| `--color-bg` | #000000 | Primary background (pure black) | N/A (base) |
| `--color-bg-secondary` | #0a0a0a | Secondary/elevated backgrounds | Subtle depth |
| `--color-text` | #e6edf3 | Primary text color | 21:1 (AAA) |
| `--color-text-secondary` | #8b949e | Secondary text color | 13:1 (AAA) |
| `--color-border` | #30363d | Border color | Visible on black |
| `--color-primary` | #539bf5 | Primary actions/links | 8.6:1 (AA) |
| `--color-success` | #3fb950 | Success indicators | 6.4:1 (AA) |
| `--color-warning` | #d29922 | Warning indicators | 8.2:1 (AA) |
| `--color-danger` | #f85149 | Error indicators | 7.1:1 (AA) |
| `--shadow` | 0 1px 3px rgba(255, 255, 255, 0.05) | Subtle elevation shadow | N/A |

### Properties (Light Theme - Fallback)

| Property Name | Value | Purpose |
|---------------|-------|---------|
| `--color-bg` | #ffffff | White background |
| `--color-bg-secondary` | #f6f8fa | Light gray background |
| `--color-text` | #24292f | Dark text |
| `--color-text-secondary` | #57606a | Gray text |

### Validation Rules

- All color values must be valid CSS color codes (hex, rgb, rgba)
- Contrast ratios must meet WCAG 2.1 Level AA standards:
  - Normal text: minimum 4.5:1
  - Large text: minimum 3:1
  - Interactive elements: minimum 3:1
- Shadow values must be valid CSS box-shadow syntax

### Usage Pattern

```css
:root {
  /* Light theme (default fallback) */
  --color-bg: #ffffff;
  --color-text: #24292f;
  /* ... other light theme values */
}

html.dark-mode-active {
  /* Black theme (applied when isDarkMode = true) */
  --color-bg: #000000;
  --color-text: #e6edf3;
  /* ... other black theme values */
}
```

---

## Entity 3: Focus State

**Purpose**: Define visual indicators for keyboard navigation focus

**Location**: CSS focus-visible pseudo-class styles

### Fields

| Field Name | Type | Description |
|------------|------|-------------|
| `outlineColor` | CSS Color | Color of focus outline (--color-primary) |
| `outlineWidth` | CSS Length | Width of focus ring (2px) |
| `outlineOffset` | CSS Length | Distance from element (2px) |

### Validation Rules

- Focus indicators must be visible on black background
- Minimum contrast ratio of 3:1 for focus indicators
- Must apply to all interactive elements (buttons, links, form controls)

### Affected Components

- All `<button>` elements
- All `<a>` elements (links)
- All form controls (`<input>`, `<select>`, `<textarea>`)
- Custom interactive components (task cards, project selector)

---

## Entity 4: Modal Overlay State

**Purpose**: Define visual styling for modal dialogs and overlays

**Location**: Component CSS for modals

### Fields

| Field Name | Type | Value | Description |
|------------|------|-------|-------------|
| `backdropColor` | CSS Color | rgba(0, 0, 0, 0.8) | Semi-transparent black overlay |
| `modalBackground` | CSS Color | #000000 | Solid black modal content background |
| `modalBorder` | CSS Color | #30363d | Border to distinguish modal edges |
| `modalShadow` | CSS Shadow | 0 4px 12px rgba(255, 255, 255, 0.1) | Subtle shadow for depth |

### Validation Rules

- Backdrop must dim underlying content while maintaining visibility
- Modal must be clearly distinguishable from backdrop
- Modal content must use black background to maintain theme consistency
- Modal must be focusable and keyboard-navigable

---

## Entity 5: Status Badge Colors

**Purpose**: Maintain distinct, accessible colors for task status indicators

**Location**: Component CSS (status badges)

### Status Values

| Status | Background | Text Color | Contrast Ratio |
|--------|-----------|------------|----------------|
| `todo` | rgba(83, 155, 245, 0.15) | #539bf5 | 8.6:1 |
| `in-progress` | rgba(210, 153, 34, 0.15) | #d29922 | 8.2:1 |
| `done` | rgba(63, 185, 80, 0.15) | #3fb950 | 6.4:1 |

### Validation Rules

- Each status must have unique, distinguishable color
- All status colors must meet WCAG AA contrast requirements on black background
- Status indicators must work for colorblind users (rely on text, not just color)

### State Transitions

```
[Task Created] → status = "todo" (blue)
     ↓
[Work Started] → status = "in-progress" (yellow/orange)
     ↓
[Task Completed] → status = "done" (green)
```

---

## Entity 6: Loading State Indicator

**Purpose**: Define visual appearance for loading spinners and indicators

**Location**: App.css (.spinner class)

### Fields

| Field Name | Type | Value | Description |
|------------|------|-------|-------------|
| `spinnerBorder` | CSS Color | var(--color-border) | Gray border for spinner ring |
| `spinnerAccent` | CSS Color | var(--color-primary) | Blue accent for spinning section |
| `animationDuration` | CSS Time | 0.8s | Speed of rotation |

### Validation Rules

- Spinner must be visible on black background
- Animation must be smooth (no jank)
- Should use existing CSS custom properties for theming

---

## Data Flow Diagram

```
User Action (Click Theme Toggle)
     ↓
useAppTheme.toggleTheme()
     ↓
Update isDarkMode state
     ↓
React re-renders with new state
     ↓
useEffect adds/removes "dark-mode-active" class to <html>
     ↓
CSS custom properties update (cascade)
     ↓
All components inherit new colors
     ↓
Black background visible immediately
```

---

## Persistence and Storage

**Persistence**: NONE (per spec out-of-scope)

- Theme state is ephemeral (resets on page reload)
- No localStorage usage
- No API calls to save theme preference
- No user-specific theme settings

**Rationale**: Spec explicitly states "Customizing themes for individual users or persisting theme preferences" is out of scope. Black theme will be the default on every load.

---

## Accessibility Considerations

### Keyboard Navigation

- All interactive elements must have visible focus indicators
- Focus order must be logical and sequential
- Keyboard shortcuts (if any) must work with black theme

### Screen Readers

- Theme changes should not announce to screen readers (visual only)
- All text must remain accessible with proper semantic HTML
- Color should not be the only means of conveying information

### High Contrast Mode

- Detect `@media (forced-colors: active)` for Windows high contrast mode
- Allow system colors to override theme colors when high contrast is active
- Ensure borders and outlines are preserved in high contrast mode

---

## Testing Validation

### Automated Checks

- Contrast ratio validation for all text/background combinations
- CSS custom property presence verification
- Focus indicator visibility tests

### Manual Checks

- Visual inspection of all screens on black background
- Keyboard navigation through entire application
- Modal and overlay visibility verification
- Status indicator distinguishability test

### Edge Case Testing

- High contrast mode interaction
- Browser zoom levels (100%, 150%, 200%)
- Different screen sizes (mobile, tablet, desktop)
- Color blindness simulation (protanopia, deuteranopia, tritanopia)

---

## Implementation Notes

1. **No Database Changes**: This is a pure frontend feature with no backend impact
2. **No API Changes**: No new endpoints or modified responses required
3. **No New State Management**: Reuse existing `useAppTheme` hook structure
4. **CSS-Only Approach**: Minimize JavaScript changes, maximize CSS variable usage
5. **Backward Compatibility**: Light theme remains functional as fallback

---

## Success Metrics

- All screens display black (#000000) background (verifiable via color picker)
- All text meets WCAG AA contrast ratios (verifiable via automated tools)
- No functional regressions (all user workflows still work)
- Theme applies immediately on load with no flash
- 100% of navigation, modals, and overlays use black backgrounds
