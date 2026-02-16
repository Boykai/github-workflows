# Data Model: Red Background Interface

**Feature**: Red Background Interface  
**Branch**: `copilot/apply-red-background-interface-again`  
**Date**: 2026-02-16

## Purpose

This document defines the data structures and state management for implementing the red background feature. Since this is a CSS-only change, the "data model" focuses on CSS custom properties and their scope.

## CSS Custom Properties (Theme Variables)

### Background Color Variable

**Variable**: `--color-bg-secondary`

**Purpose**: Controls the main page/body background color across the application

**Scope**: Global (defined in `:root` for light mode, `html.dark-mode-active` for dark mode)

**Type**: CSS color value (hex, rgb, or named color)

**Current Values**:
```css
/* Light mode */
:root {
  --color-bg-secondary: #f6f8fa;  /* Light gray */
}

/* Dark mode */
html.dark-mode-active {
  --color-bg-secondary: #161b22;  /* Dark gray */
}
```

**New Values** (This Feature):
```css
/* Light mode */
:root {
  --color-bg-secondary: #FF0000;  /* Red */
}

/* Dark mode */
html.dark-mode-active {
  --color-bg-secondary: #FF0000;  /* Red */
}
```

### Related Variables (Not Modified)

These variables remain unchanged but are documented for context:

**Variable**: `--color-bg`  
**Purpose**: Component background color (cards, panels, chat bubbles)  
**Current Values**: `#ffffff` (light), `#0d1117` (dark)  
**Status**: NO CHANGE - component backgrounds remain as-is

**Variable**: `--color-text`  
**Purpose**: Primary text color  
**Current Values**: `#24292f` (light), `#e6edf3` (dark)  
**Status**: NO CHANGE - text colors remain as-is (may need future adjustment for contrast)

**Variable**: `--color-text-secondary`  
**Purpose**: Secondary/muted text color  
**Current Values**: `#57606a` (light), `#8b949e` (dark)  
**Status**: NO CHANGE - secondary text colors remain as-is

## CSS Selectors and Rules

### Primary Target Rule

**Selector**: `body`

**Current Rule**:
```css
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif;
  font-size: 14px;
  line-height: 1.5;
  color: var(--color-text);
  background: var(--color-bg-secondary);  /* Uses the variable we're changing */
}
```

**Impact**: When `--color-bg-secondary` changes to red, this rule automatically applies red background to the entire page.

**Status**: NO DIRECT MODIFICATION - rule stays the same, only the variable value changes

### Affected UI Components

Components that also use `--color-bg-secondary` (side effects of the change):

1. **Theme Toggle Button** (`.theme-toggle-btn`)
   ```css
   .theme-toggle-btn {
     background: var(--color-bg-secondary);  /* Will become red */
   }
   ```

2. **Task Preview** (`.task-preview`)
   ```css
   .task-preview {
     background: var(--color-bg-secondary);  /* Will become red */
   }
   ```

3. **Rate Limit Bar** (`.rate-limit-bar`)
   ```css
   .rate-limit-bar {
     background: var(--color-bg-secondary);  /* Will become red */
   }
   ```

**Note**: These component background changes are acceptable side effects per spec assumption: "Text and UI elements will be adjusted separately if needed to maintain readability"

## Theme State Management

### Theme Mode State

**Location**: `frontend/src/hooks/useAppTheme.ts`

**State Variable**: Not directly accessible (encapsulated in hook)

**Storage Key**: `tech-connect-theme-mode`

**Storage Type**: localStorage

**Values**: 
- `'light'` - Light mode active (uses `:root` CSS variables)
- `'dark'` - Dark mode active (uses `html.dark-mode-active` CSS variables)

**Persistence Mechanism**:
1. User toggles theme via button
2. Hook updates localStorage: `localStorage.setItem('tech-connect-theme-mode', newMode)`
3. Hook toggles CSS class: `document.documentElement.classList.toggle('dark-mode-active')`
4. Browser re-applies CSS rules based on new class

**Impact on Red Background**:
- No code changes needed to theme hook
- CSS variable updates in both scopes ensure red background persists across theme switches
- Theme toggle behavior remains unchanged

## Data Flow

### Page Load Sequence

1. **HTML Parse**: Browser loads `index.html`
2. **CSS Load**: Browser loads `frontend/src/index.css` (synchronous, in `<head>`)
3. **CSS Parse**: Browser parses CSS custom properties including `--color-bg-secondary: #FF0000`
4. **React Mount**: React app initializes
5. **Theme Hook Init**: `useAppTheme` reads localStorage, applies theme class if needed
6. **First Paint**: Browser renders with red background already applied

**Timing**: Background appears in first paint (no flicker) because CSS loads before React

### Theme Toggle Sequence

1. **User Action**: User clicks theme toggle button
2. **State Update**: `useAppTheme` hook updates theme mode
3. **Class Toggle**: Hook toggles `dark-mode-active` class on `<html>` element
4. **CSS Re-application**: Browser switches from `:root` variables to `html.dark-mode-active` variables
5. **Background Remains Red**: Both theme scopes define `--color-bg-secondary: #FF0000`
6. **localStorage Update**: Theme preference saved for next session

**Timing**: Instant CSS class change, background remains red throughout transition

### Navigation Sequence (SPA)

1. **Route Change**: React Router updates current view
2. **Component Unmount/Mount**: Old component unmounts, new component mounts
3. **CSS Persistence**: CSS custom properties remain in browser memory (no reload)
4. **Background Remains Red**: Body background style continues to apply

**Timing**: Zero-delay persistence (CSS never unloads)

### Page Refresh Sequence

1. **Browser Reload**: Full page reload initiated
2. **CSS Reload**: Browser re-fetches and parses `index.css`
3. **Variables Restored**: `--color-bg-secondary: #FF0000` re-parsed from file
4. **Theme Restoration**: `useAppTheme` reads localStorage, re-applies theme class
5. **Background Restored Red**: CSS variables apply as before

**Timing**: Background appears in first paint after reload (no flicker)

## State Validation

### Invariants

These conditions must always be true:

1. `--color-bg-secondary` must be defined in both `:root` and `html.dark-mode-active`
2. Both definitions must have the same value (`#FF0000`) for consistent branding
3. The `body` rule must use `background: var(--color-bg-secondary)`
4. Theme toggle must not modify CSS custom property values (only class names)

### Edge Cases Handled

1. **Missing localStorage**: Theme hook defaults to system preference or light mode
2. **Invalid localStorage Value**: Theme hook falls back to safe default
3. **CSS Load Failure**: Browser uses default styles (white background) - acceptable degradation
4. **JavaScript Disabled**: CSS still loads and applies, red background works (theme toggle broken but background persists)

## Modification Summary

### Files Changed

1. **frontend/src/index.css** (MODIFIED)
   - Line ~8: Change `:root` `--color-bg-secondary` from `#f6f8fa` to `#FF0000`
   - Line ~20: Change `html.dark-mode-active` `--color-bg-secondary` from `#161b22` to `#FF0000`

### Files NOT Changed

- `frontend/src/hooks/useAppTheme.ts` - NO CHANGE (theme logic works as-is)
- `frontend/src/App.css` - NO CHANGE (component styles work as-is)
- `frontend/src/components/chat/ChatInterface.css` - NO CHANGE

### Total Changes

- **Files Modified**: 1
- **Lines Changed**: 2
- **New Files**: 0
- **Deleted Files**: 0

## Accessibility Considerations

### Contrast Ratios

**Light Mode**:
- Text (#24292f) vs Red Background (#FF0000): ~3.9:1
- **Status**: FAILS WCAG AA (4.5:1 minimum)
- **Action**: Document as known issue, plan future text color adjustment

**Dark Mode**:
- Text (#e6edf3) vs Red Background (#FF0000): ~5.2:1
- **Status**: PASSES WCAG AA (4.5:1 minimum)
- **Action**: No changes needed

### Future Improvements

To achieve full WCAG AA compliance in light mode:
- Option 1: Darken text color to `#000000` (pure black) for 5.9:1 contrast
- Option 2: Lighten text slightly and add text-shadow for enhanced readability
- Option 3: Add subtle texture/pattern to background to reduce intensity

**Scope**: Out of scope for this feature per spec assumptions

## Testing Validation

### Visual Verification Points

1. **Initial Load**: Body background is red (#FF0000) on first page load
2. **Theme Toggle**: Background remains red when switching light ↔ dark
3. **Navigation**: Background stays red when navigating between routes
4. **Refresh**: Background is red after page refresh (F5 or Ctrl+R)
5. **Responsive**: Background spans full viewport on mobile, tablet, desktop
6. **Component Side Effects**: Buttons and task previews inherit red background (expected)

### Automated Test Opportunities

While tests are optional per constitution, potential test cases:

1. **Unit Test**: Verify CSS variable value is `#FF0000` in parsed stylesheet
2. **E2E Test**: Screenshot comparison of page background color
3. **Accessibility Test**: Automated contrast ratio verification

**Status**: Tests not required for this feature per constitution principle IV

## Conclusion

The data model is minimal: a single CSS custom property change in two scopes. No JavaScript state management changes required. The existing theme system handles all persistence and switching logic, ensuring the red background works correctly across all user scenarios defined in the spec.
