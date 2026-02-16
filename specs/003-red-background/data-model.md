# Data Model: Red Background Color

**Branch**: `copilot/apply-red-background-color-again` | **Date**: 2026-02-16 | **Spec**: [spec.md](./spec.md)

## Overview

This feature modifies CSS custom properties to implement a red background color for the application. The data model describes the CSS theming structure that controls visual presentation.

---

## Entity 1: CSS Theme Configuration

**Description**: The CSS custom property system in `frontend/src/index.css` that defines color variables for the application's visual theme.

**Purpose**: Centralized color management through CSS variables, enabling consistent theming across all components and support for both light and dark modes.

**Location**: `frontend/src/index.css` (lines 1-30)

### Properties

| Property | Type | Current Value (Light) | Current Value (Dark) | New Value (Light) | New Value (Dark) | Description |
|----------|------|---------------------|--------------------|--------------------|-------------------|-------------|
| `--color-bg-secondary` | CSS Color | `#f6f8fa` | `#161b22` | `#ff0000` | `#8b0000` | Page/body background color (PRIMARY CHANGE) |
| `--color-text` | CSS Color | `#24292f` | `#e6edf3` | `#ffffff` | `#e6edf3` | Primary text color (ADJUSTED for contrast) |
| `--color-bg` | CSS Color | `#ffffff` | `#0d1117` | `#ffffff` | `#0d1117` | Component surface backgrounds (UNCHANGED) |
| `--color-text-secondary` | CSS Color | `#57606a` | `#8b949e` | `#f0f0f0` | `#8b949e` | Secondary text color (MAY NEED ADJUSTMENT) |

### Relationships

- **Used By**: `body` element (line 43), various components in `App.css`, `ChatInterface.css`
- **Defined In**: `:root` selector (light mode, lines 2-15), `html.dark-mode-active` selector (dark mode, lines 18-30)
- **Theme Switching**: Controlled by `useAppTheme.ts` hook via localStorage

### Validation Rules

1. Color values MUST be valid hex color codes
2. Hex values MUST use lowercase letters (per codebase convention)
3. Light mode text on light mode background MUST meet WCAG AA contrast (4.5:1 for normal, 3:1 for large)
4. Dark mode text on dark mode background MUST meet WCAG AA contrast (4.5:1 for normal, 3:1 for large)

### State Transitions

```
Initial State (Light): --color-bg-secondary: #f6f8fa
                      --color-text: #24292f
         ↓
Modified State (Light): --color-bg-secondary: #ff0000
                       --color-text: #ffffff

Initial State (Dark): --color-bg-secondary: #161b22
                     --color-text: #e6edf3
         ↓
Modified State (Dark): --color-bg-secondary: #8b0000
                      --color-text: #e6edf3 (may stay the same)
```

**Transition Trigger**: Developer modifies CSS custom property values in `index.css`

**Side Effects**: 
- All elements using `var(--color-bg-secondary)` automatically inherit new red color
- Text contrast may become insufficient, requiring additional color adjustments
- UI components using `--color-bg-secondary` for their surfaces will also become red

---

## Entity 2: Body Element Background

**Description**: The main body element that displays the page background color.

**Purpose**: Primary visual container for the entire application, providing the base background that should be red.

**Location**: Defined in `frontend/src/index.css` line 43

### Properties

| Property | Type | Value | Description |
|----------|------|-------|-------------|
| `background` | CSS Property | `var(--color-bg-secondary)` | References CSS custom property |

### Relationships

- **Depends On**: `--color-bg-secondary` CSS custom property
- **Parent**: `html` element
- **Children**: All application content

### Validation Rules

1. Background MUST use `var(--color-bg-secondary)` to maintain theme consistency
2. Background MUST be red (#ff0000 or #8b0000) after implementation
3. Background MUST be consistent across all pages/screens

---

## Entity 3: Component Surface Backgrounds

**Description**: Various UI components (buttons, panels, cards, chat bubbles) that use `--color-bg-secondary` for their background styling.

**Purpose**: Provide visual surfaces for interactive elements and content containers.

**Locations**: 
- `frontend/src/App.css` (lines 73, 130, 177, 209, 234, 494)
- `frontend/src/components/chat/ChatInterface.css` (multiple occurrences)

### Properties

| Property | Type | Current Behavior | New Behavior | Impact |
|----------|------|------------------|--------------|--------|
| `background` | CSS Property | Uses `var(--color-bg-secondary)` | Will inherit red color | Components become red |

### Relationships

- **Depends On**: `--color-bg-secondary` CSS custom property
- **Affected Components**: Buttons, chat messages, panels, input fields (if they use this variable)

### Validation Rules

1. Components MUST remain visually distinguishable on red background
2. Interactive elements MUST maintain sufficient contrast for accessibility
3. Visual hierarchy MUST be preserved (foreground vs background distinction)

### State Considerations

**Important**: Research shows that `--color-bg-secondary` is used extensively across components, not just the body background. This means:

1. Many UI surfaces will become red along with the page background
2. This may affect visual hierarchy and usability
3. Some components may need individual style adjustments to use `--color-bg` instead
4. Need to verify in implementation phase whether this is acceptable

**Potential Mitigation**: If components becoming red is problematic:
- Option A: Change affected components to use `--color-bg` instead of `--color-bg-secondary`
- Option B: Introduce a new CSS variable `--color-page-bg` specifically for body background
- Option C: Accept the behavior as-is if visual hierarchy is maintained

---

## Entity 4: Text Content

**Description**: All text elements in the application that must maintain readability on the new red background.

**Purpose**: Display information to users with sufficient contrast for accessibility compliance.

**Locations**: All components using `var(--color-text)` and `var(--color-text-secondary)`

### Properties

| Property | Type | Current Value | New Value | Reason |
|----------|------|---------------|-----------|--------|
| `color` | CSS Property | `var(--color-text)` | `var(--color-text)` | Inherits from variable |
| `--color-text` (light) | CSS Variable | `#24292f` (dark gray) | `#ffffff` (white) | Contrast requirement |

### Relationships

- **Depends On**: `--color-text` and `--color-text-secondary` CSS custom properties
- **Affected By**: Background color change (red requires light text)

### Validation Rules

1. Text on red background MUST meet WCAG AA contrast ratio:
   - Normal text (< 18pt): 4.5:1 minimum
   - Large text (≥ 18pt): 3:1 minimum
2. Text MUST remain readable in both light and dark themes

### Contrast Analysis

**Light Mode**:
- Red background: `#ff0000`
- White text: `#ffffff`
- Contrast ratio: ~4.0:1 (marginal, may need font-weight adjustment)

**Dark Mode**:
- Dark red background: `#8b0000`
- Light text: `#e6edf3`
- Contrast ratio: ~8.5:1 (excellent)

---

## Entity 5: Theme Toggle State

**Description**: The application's theme mode state (light vs dark) that determines which set of CSS custom property values is active.

**Purpose**: Allow users to switch between light and dark visual themes, with red background adapting to each mode.

**Location**: Managed by `useAppTheme.ts` hook, persisted in localStorage

### Properties

| Property | Type | Values | Description |
|----------|------|--------|-------------|
| `theme` | String | `"light"` \| `"dark"` | Current theme mode |
| `html.className` | String | `""` \| `"dark-mode-active"` | CSS class controlling theme |

### Relationships

- **Controls**: Which CSS custom property set is active (`:root` vs `html.dark-mode-active`)
- **Persisted In**: Browser localStorage
- **Affects**: All CSS custom properties including `--color-bg-secondary`

### State Transitions

```
Light Mode (html class = "")
  → Uses :root CSS variables
  → --color-bg-secondary: #ff0000

Dark Mode (html class = "dark-mode-active")
  → Uses html.dark-mode-active CSS variables
  → --color-bg-secondary: #8b0000
```

### Validation Rules

1. Theme state MUST persist across page reloads
2. Both themes MUST have red background with appropriate color values
3. Theme switching MUST instantly update all CSS custom properties

---

## Data Flow

```
User Opens Application
         ↓
useAppTheme.ts reads localStorage
         ↓
Sets html.className ("" or "dark-mode-active")
         ↓
CSS selects :root or html.dark-mode-active
         ↓
--color-bg-secondary applies (#ff0000 or #8b0000)
         ↓
body { background: var(--color-bg-secondary) }
         ↓
Red background displayed
         ↓
Components inherit --color-bg-secondary if they use it
         ↓
Text uses --color-text for contrast
```

---

## Implementation Impact

### Files Modified

1. **frontend/src/index.css** (2 lines changed)
   - Line 9: `--color-bg-secondary: #ff0000;` (was `#f6f8fa`)
   - Line 25: `--color-bg-secondary: #8b0000;` (was `#161b22`)
   - Line 11: `--color-text: #ffffff;` (was `#24292f`)
   - Line 13: `--color-text-secondary: #f0f0f0;` (was `#57606a`) - if needed

### Components Affected

- **Body**: Primary change - background becomes red
- **Buttons**: May become red if using `--color-bg-secondary`
- **Chat Interface**: Chat bubbles may become red if using `--color-bg-secondary`
- **Panels/Cards**: Any surface using `--color-bg-secondary` becomes red
- **Text**: All text inherits new contrast-adjusted colors

### Testing Points

1. Verify red background appears on page load (both themes)
2. Verify red background persists across page navigation
3. Verify text readability and contrast in both themes
4. Verify UI components remain usable and distinguishable
5. Verify theme switching maintains red background
6. Verify no visual regressions in modals/overlays

---

## Accessibility Considerations

### WCAG AA Compliance

**Requirements**:
- Normal text contrast: 4.5:1 minimum
- Large text contrast: 3:1 minimum
- Interactive elements: Clearly distinguishable

**Strategy**:
1. Use white text (#ffffff) on red background for light mode
2. May need to increase font-weight for some text to improve perception
3. Verify all interactive elements have sufficient contrast
4. Test with accessibility tools (e.g., axe DevTools, WAVE)

### Color Blindness Considerations

- Red-green color blindness may affect perception of red background
- Text contrast more important than specific hue
- White text on red maintains high luminance contrast regardless of color perception

---

## Summary

This feature modifies 2-4 lines of CSS custom properties in `frontend/src/index.css` to achieve a red background color across the entire application. The implementation leverages the existing CSS variable system, requiring minimal code changes while maintaining theme consistency and accessibility standards.

**Key Changes**:
- `--color-bg-secondary`: `#ff0000` (light), `#8b0000` (dark)
- `--color-text`: `#ffffff` (light), keep existing (dark)
- All components automatically inherit new colors via CSS cascade
- Manual verification required for accessibility and usability
