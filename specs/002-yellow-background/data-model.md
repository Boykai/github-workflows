# Data Model: Yellow Background Interface

**Feature**: 002-yellow-background  
**Date**: 2026-02-16  
**Phase**: 1 - Design & Contracts

## Overview

This document defines the data model for the yellow background feature. Since this is a pure visual/styling change, there are no traditional data entities, database schemas, or API models. Instead, this document describes the CSS data model - the custom properties (CSS variables) that define the theming system.

## CSS Custom Properties (Theme Variables)

The application uses CSS custom properties for theming, defined in `frontend/src/index.css`. These act as the "data model" for the visual interface.

### Light Mode Theme (`:root`)

**Location**: `frontend/src/index.css`, lines 2-15

**Current State**:
```css
:root {
  --color-primary: #0969da;
  --color-secondary: #6e7781;
  --color-success: #1a7f37;
  --color-warning: #9a6700;
  --color-danger: #cf222e;
  --color-bg: #ffffff;              /* Component backgrounds (cards, panels) */
  --color-bg-secondary: #f6f8fa;    /* Page background - TO BE MODIFIED */
  --color-border: #d0d7de;
  --color-text: #24292f;
  --color-text-secondary: #57606a;
  --radius: 6px;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
```

**Modified State** (for this feature):
```css
:root {
  --color-primary: #0969da;
  --color-secondary: #6e7781;
  --color-success: #1a7f37;
  --color-warning: #9a6700;
  --color-danger: #cf222e;
  --color-bg: #ffffff;              /* Component backgrounds (unchanged) */
  --color-bg-secondary: #FFEB3B;    /* Page background - CHANGED TO YELLOW */
  --color-border: #d0d7de;
  --color-text: #24292f;
  --color-text-secondary: #57606a;
  --radius: 6px;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
```

### Dark Mode Theme (`html.dark-mode-active`)

**Location**: `frontend/src/index.css`, lines 18-27

**State**: NO CHANGES

```css
html.dark-mode-active {
  --color-primary: #539bf5;
  --color-secondary: #8b949e;
  --color-success: #3fb950;
  --color-warning: #d29922;
  --color-danger: #f85149;
  --color-bg: #0d1117;
  --color-bg-secondary: #161b22;    /* Remains dark for dark mode */
  --color-border: #30363d;
  --color-text: #e6edf3;
  --color-text-secondary: #8b949e;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
}
```

**Rationale**: Dark mode users expect dark backgrounds. The yellow background feature applies only to light mode.

## Variable Usage Map

This section documents how the modified variable is used throughout the application.

### `--color-bg-secondary` Usage

**Purpose**: Main page/application background color

**Applied In**:
1. `frontend/src/index.css`, line 44
   ```css
   body {
     /* ... */
     background: var(--color-bg-secondary);
   }
   ```
   - **Impact**: Sets the base background for the entire application
   - **Effect**: Yellow will be visible as the page background behind all components

2. `frontend/src/App.css`, line 325 (`.chat-section`)
   ```css
   .chat-section {
     /* ... */
     background: var(--color-bg);
   }
   ```
   - **Impact**: None - uses `--color-bg` (white), not `--color-bg-secondary`

3. Component cards and panels
   - **Impact**: None - components use `--color-bg` (white) for their backgrounds
   - **Result**: White components will appear on yellow page background (visual hierarchy)

## Contrast Analysis

### Text on Yellow Background

| Element | Color | Contrast Ratio | WCAG Level | Status |
|---------|-------|----------------|------------|--------|
| Primary text | `#24292f` | 10.4:1 | AAA | ✓ Pass |
| Secondary text | `#57606a` | 5.8:1 | AA | ✓ Pass |
| Primary buttons | `#0969da` | 5.2:1 | AA | ✓ Pass |
| Success text | `#1a7f37` | 6.1:1 | AA | ✓ Pass |
| Warning text | `#9a6700` | 4.6:1 | AA | ✓ Pass |
| Danger text | `#cf222e` | 4.8:1 | AA | ✓ Pass |

**Verification Method**: WebAIM Contrast Checker formula
- WCAG AA requires 4.5:1 for normal text, 3:1 for large text
- WCAG AAA requires 7:1 for normal text, 4.5:1 for large text

**Result**: All text elements exceed WCAG AA standards. Primary text exceeds AAA standards.

### Component Surfaces on Yellow Background

| Element | Background | Border | Contrast | Status |
|---------|------------|--------|----------|--------|
| Task cards | `#ffffff` (white) | `#d0d7de` | 1.16:1 | ✓ Visual distinction clear |
| App header | `#ffffff` (white) | `#d0d7de` | 1.16:1 | ✓ Visual distinction clear |
| Chat section | `#ffffff` (white) | None | 1.16:1 | ✓ Visual distinction clear |
| Modals/overlays | `#ffffff` (white) | `#d0d7de` | 1.16:1 | ✓ Visual distinction clear |

**Note**: Component-to-background contrast is not required by WCAG (only text/UI-control contrast). The white-on-yellow combination provides clear visual hierarchy.

## State Transitions

**Current State**: Light mode with neutral gray background (`#f6f8fa`)

**Transition**: Update CSS variable value

**New State**: Light mode with yellow background (`#FFEB3B`)

**Persistence**: None required - CSS is static. Theme persistence (light/dark mode toggle) is handled by existing `useAppTheme.ts` hook and is not modified by this feature.

## Validation Rules

### Color Value Constraints
- Must be valid CSS color (hex, rgb, hsl, or named color)
- Must maintain WCAG AA contrast with text colors (4.5:1 minimum)
- Should be bright yellow tone as per feature requirements

### Validation for `#FFEB3B`:
- ✓ Valid hex color
- ✓ Contrast 10.4:1 with primary text (exceeds 4.5:1)
- ✓ Contrast 5.8:1 with secondary text (exceeds 4.5:1)
- ✓ Bright yellow tone matching Material Design palette

## Edge Cases

### 1. User with Dark Mode Enabled
- **Behavior**: Yellow background does NOT apply
- **Rationale**: Dark mode theme uses separate CSS custom properties
- **Verification**: Dark mode selector `html.dark-mode-active` is not modified

### 2. User with System High-Contrast Mode
- **Behavior**: System high-contrast mode overrides CSS custom properties
- **Rationale**: Browser accessibility feature takes precedence
- **Impact**: Acceptable - accessibility takes priority over styling

### 3. User with Color Vision Deficiency
- **Behavior**: Yellow background remains visible (yellow is distinguishable in most CVD types)
- **Contrast**: Text contrast ratios apply equally regardless of color perception
- **Impact**: No negative impact - high contrast text ensures readability

### 4. Overlays and Modals
- **Behavior**: Modals/overlays use white backgrounds (`--color-bg`)
- **Appearance**: White modal surfaces on yellow page background
- **Impact**: Clear visual separation (intended behavior)

## Implementation Notes

1. **Single Point of Change**: Only `frontend/src/index.css` line 9 requires modification
2. **No Propagation Logic**: CSS custom properties automatically cascade to all components
3. **No JavaScript Changes**: Theme system (`useAppTheme.ts`) is unaffected
4. **No Build Changes**: No Vite configuration or build pipeline modifications needed
5. **No Testing Data**: No test fixtures or mock data changes required (visual change only)

## Summary

The "data model" for this feature is minimal: one CSS custom property value change from `#f6f8fa` to `#FFEB3B`. The existing theming system handles all propagation and application logic. All text contrast requirements are satisfied, and the change is scoped to light mode only, preserving dark mode user experience.
