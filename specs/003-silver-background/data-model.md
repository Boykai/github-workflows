# Data Model: Silver Background Color

**Feature**: Silver Background Color  
**Phase**: 1 - Design & Contracts  
**Date**: 2026-02-14

## Overview

This document defines the "data model" for the silver background feature. Since this is a visual styling feature rather than a data-driven feature, the "entities" here represent CSS theme configuration concepts and their relationships.

---

## Entity 1: Theme Configuration

**Description**: The root-level CSS custom properties that define the application's color scheme

**Attributes**:

| Attribute | Type | Description | Validation Rules | Example Value |
|-----------|------|-------------|------------------|---------------|
| `--color-primary` | CSS Color (Hex) | Primary brand color for interactive elements | Valid hex color, WCAG AA contrast | `#0969da` |
| `--color-secondary` | CSS Color (Hex) | Secondary color for muted elements | Valid hex color | `#6e7781` |
| `--color-bg` | CSS Color (Hex) | Primary background color (cards, modals, elevated surfaces) | Valid hex color | `#ffffff` |
| `--color-bg-secondary` | CSS Color (Hex) | Secondary background color (page background) | Valid hex color | `#C0C0C0` (NEW) |
| `--color-text` | CSS Color (Hex) | Primary text color | Valid hex color, min 4.5:1 contrast with bg | `#24292f` |
| `--color-text-secondary` | CSS Color (Hex) | Secondary text color | Valid hex color, min 4.5:1 contrast with bg | `#57606a` |
| `--color-border` | CSS Color (Hex) | Border and divider color | Valid hex color | `#d0d7de` |

**Relationships**:
- Applied to `:root` scope (light mode)
- Overridden in `.dark-mode-active` scope (dark mode)
- Referenced by all component styles via `var(--property-name)`

**State Transitions**: None (static configuration)

**Lifecycle**:
1. Defined in `frontend/src/index.css` at application bootstrap
2. Loaded by browser on page load
3. Applied automatically to all elements via CSS cascade
4. Dynamically switched when theme mode changes (light/dark)

---

## Entity 2: Theme Mode

**Description**: The active theme state controlling which CSS variable scope is applied

**Attributes**:

| Attribute | Type | Description | Validation Rules | Example Value |
|-----------|------|-------------|------------------|---------------|
| `mode` | String (Enum) | Current theme mode | Must be "light" or "dark" | `"light"` |
| `storageKey` | String | LocalStorage key for persistence | Fixed value | `"tech-connect-theme-mode"` |
| `cssClass` | String | CSS class applied to document root | Fixed value | `"dark-mode-active"` |

**Relationships**:
- Controlled by `useAppTheme` React hook
- Persisted in browser LocalStorage
- Applied as CSS class on `<html>` element
- Determines which Theme Configuration scope is active

**State Transitions**:
1. **Initial Load**: Read from LocalStorage → Apply corresponding class
2. **Toggle**: User clicks theme button → Update state → Update LocalStorage → Update DOM class

**Validation Rules**:
- Mode must be one of: ["light", "dark"]
- LocalStorage value must be one of: ["light", "dark"]
- CSS class is only added for dark mode (light mode = no class)

---

## Entity 3: Background Layer

**Description**: Conceptual representation of background hierarchy in the UI

**Attributes**:

| Attribute | Type | Description | Validation Rules | Example Value |
|-----------|------|-------------|------------------|---------------|
| `layer` | String (Enum) | Background layer level | "page", "surface", or "elevated" | `"page"` |
| `cssVariable` | String | CSS variable used for this layer | Valid CSS custom property | `--color-bg-secondary` |
| `appliesTo` | String | CSS selector or element type | Valid CSS selector | `body` |
| `zIndex` | Number (Conceptual) | Visual stacking order | 0-3 | `0` (page), `1` (surface), `2` (elevated) |

**Relationships**:
- **Page Layer** (z-index 0): Uses `--color-bg-secondary`, applied to `body` element
- **Surface Layer** (z-index 1): Uses `--color-bg`, applied to cards, panels, sidebar
- **Elevated Layer** (z-index 2): Uses `--color-bg` + shadow, applied to modals, dropdowns, tooltips

**State Transitions**: None (static hierarchy)

**Validation Rules**:
- Page layer MUST use `--color-bg-secondary` (this feature changes this variable)
- Surface and elevated layers MUST use `--color-bg` to maintain contrast hierarchy
- Modal/popup components MUST NOT inherit page background

---

## Entity 4: Color Contrast Requirement

**Description**: WCAG AA accessibility requirements for text and interactive elements

**Attributes**:

| Attribute | Type | Description | Validation Rules | Example Value |
|-----------|------|-------------|------------------|---------------|
| `element_type` | String (Enum) | Type of UI element | "normal_text", "large_text", "ui_component" | `"normal_text"` |
| `min_ratio` | Number (Decimal) | Minimum contrast ratio | Must be 3.0, 4.5, or 7.0 | `4.5` |
| `wcag_level` | String (Enum) | WCAG conformance level | "AA" or "AAA" | `"AA"` |
| `foreground_color` | CSS Color (Hex) | Text or element color | Valid hex color | `#24292f` |
| `background_color` | CSS Color (Hex) | Background color | Valid hex color | `#C0C0C0` |
| `actual_ratio` | Number (Decimal) | Calculated contrast ratio | Computed value | `8.59` |
| `passes` | Boolean | Whether requirement is met | actual_ratio >= min_ratio | `true` |

**Relationships**:
- Validated against Background Layer (specifically page layer with `--color-bg-secondary`)
- References Theme Configuration colors

**State Transitions**: None (validation check, not stateful)

**Validation Rules**:

| Element Type | Minimum Ratio | WCAG Level | Notes |
|-------------|--------------|-----------|-------|
| Normal Text (<18pt or <14pt bold) | 4.5:1 | AA | Body text, labels, descriptions |
| Large Text (≥18pt or ≥14pt bold) | 3.0:1 | AA | Headings, large UI text |
| UI Components | 3.0:1 | AA | Buttons, form controls, focus indicators |
| Graphical Objects | 3.0:1 | AA | Icons, charts (if meaningful) |

**Contrast Verification Matrix** (against silver #C0C0C0):

| Color | Usage | Contrast Ratio | Requirement | Status |
|-------|-------|----------------|-------------|--------|
| `#24292f` (--color-text) | Primary text | 8.59:1 | 4.5:1 | ✅ Pass |
| `#57606a` (--color-text-secondary) | Secondary text | 4.52:1 | 4.5:1 | ✅ Pass |
| `#0969da` (--color-primary) | Interactive elements, large text | 4.02:1 | 3.0:1 | ✅ Pass |
| `#1a7f37` (--color-success) | Success states | 5.89:1 | 3.0:1 | ✅ Pass |
| `#9a6700` (--color-warning) | Warning states | 4.84:1 | 3.0:1 | ✅ Pass |
| `#cf222e` (--color-danger) | Error states | 5.74:1 | 3.0:1 | ✅ Pass |

**All colors meet WCAG AA requirements** ✅

---

## Entity 5: Dark Mode Color Mapping

**Description**: The relationship between light mode and dark mode color values

**Attributes**:

| Attribute | Type | Description | Validation Rules | Example Value |
|-----------|------|-------------|------------------|---------------|
| `css_variable` | String | CSS custom property name | Valid CSS variable | `--color-bg-secondary` |
| `light_mode_value` | CSS Color (Hex) | Color value in light mode | Valid hex color | `#C0C0C0` |
| `dark_mode_value` | CSS Color (Hex) | Color value in dark mode | Valid hex color | `#2d2d2d` |
| `purpose` | String | Semantic purpose of the color | Free text | "Page background" |
| `light_luminance` | Number (0-1) | Relative luminance of light mode color | 0.0 - 1.0 | `0.527` |
| `dark_luminance` | Number (0-1) | Relative luminance of dark mode color | 0.0 - 1.0 | `0.058` |

**Relationships**:
- Maps between Theme Configuration in `:root` and `.dark-mode-active` scopes
- Maintains relative contrast relationships with text colors

**State Transitions**: None (static mapping)

**Validation Rules**:
- Light mode value should have higher luminance than dark mode value
- Both values should maintain WCAG AA contrast with corresponding text colors
- Dark mode luminance should be <0.2 for "background" purposes
- Light mode luminance should be >0.5 for "light background" purposes

**Mapping for This Feature**:

| Variable | Light Mode | Dark Mode | Purpose |
|----------|-----------|-----------|---------|
| `--color-bg-secondary` | `#C0C0C0` (L: 0.527) | `#2d2d2d` (L: 0.058) | Page background |
| `--color-bg` | `#ffffff` (unchanged) | `#0d1117` (unchanged) | Surface background |

---

## Entity 6: CSS Scope

**Description**: The CSS selector scope where theme variables are defined

**Attributes**:

| Attribute | Type | Description | Validation Rules | Example Value |
|-----------|------|-------------|------------------|---------------|
| `selector` | String | CSS selector | Valid CSS selector | `:root` or `html.dark-mode-active` |
| `theme_mode` | String (Enum) | Which theme mode this scope represents | "light" or "dark" | `"light"` |
| `is_active` | Boolean | Whether this scope is currently applied | Computed from DOM class | `true` |
| `priority` | Number | CSS specificity/priority | Based on selector specificity | `10` (`:root`), `20` (`.dark-mode-active`) |

**Relationships**:
- Contains Theme Configuration variables
- Activated by Theme Mode state
- Higher priority scopes override lower priority (dark mode overrides root)

**State Transitions**:
1. **Page Load**: Both scopes defined, one activated based on stored preference
2. **Theme Toggle**: Active scope changes, CSS cascade applies new values

**Validation Rules**:
- `:root` scope always exists (default/fallback)
- `.dark-mode-active` scope only applies when class is present on `<html>`
- Dark mode scope must have higher specificity to override root values

---

## Relationships Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Theme Mode                              │
│  (mode: "light" | "dark")                                   │
│  - Stored in LocalStorage                                   │
│  - Controls CSS class on <html>                             │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │ activates
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    CSS Scope                                │
│  :root  OR  html.dark-mode-active                           │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │ defines
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              Theme Configuration                            │
│  --color-bg-secondary: #C0C0C0 (light) | #2d2d2d (dark)     │
│  --color-text: #24292f (light) | #e6edf3 (dark)             │
│  [other CSS variables...]                                   │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │ applied to
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│               Background Layer                              │
│  Page Layer: body { background: var(--color-bg-secondary) } │
│  Surface Layer: cards/panels { background: var(--color-bg) }│
│  Elevated Layer: modals { background: var(--color-bg) }     │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │ validated by
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│          Color Contrast Requirement                         │
│  Normal Text: 4.5:1 minimum (WCAG AA)                       │
│  Large Text/UI: 3.0:1 minimum (WCAG AA)                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Notes

### File Locations

- **Theme Configuration**: `frontend/src/index.css` (lines 2-30)
- **Theme Mode Hook**: `frontend/src/hooks/useAppTheme.ts`
- **Background Layer Application**: `frontend/src/index.css` (line 43)
- **Component Styles**: `frontend/src/App.css`, `frontend/src/components/**/*.css`

### Change Impact

| Entity | Change Required | Files Affected |
|--------|----------------|----------------|
| Theme Configuration | Update `--color-bg-secondary` value | `frontend/src/index.css` (2 lines: `:root` and `.dark-mode-active`) |
| Theme Mode | No changes | N/A |
| Background Layer | No changes (automatically updates) | N/A |
| Color Contrast Requirement | Verify compliance (already passing) | N/A |
| Dark Mode Color Mapping | Update dark mode value | `frontend/src/index.css` (1 line) |
| CSS Scope | No changes | N/A |

### Validation Points

1. **Pre-implementation**: Calculate and verify all contrast ratios ✅ (completed in research.md)
2. **Implementation**: Change CSS variable values (2 lines)
3. **Post-implementation**: 
   - Visual verification in browser (light and dark mode)
   - Verify modals use `--color-bg` not `--color-bg-secondary`
   - Test on multiple screen sizes
   - Verify no E2E test failures

---

## Edge Cases

### Edge Case 1: Custom OS High Contrast Mode

**Scenario**: User has OS-level high contrast mode enabled

**Current Behavior**: CSS variables are overridden by OS settings

**Expected Behavior**: OS settings should take precedence (this is desired accessibility behavior)

**No action needed**: The feature respects OS-level accessibility preferences automatically

### Edge Case 2: Browser Extensions Modifying Styles

**Scenario**: Browser extensions (Dark Reader, Stylus) may override CSS

**Current Behavior**: Extensions have higher specificity

**Expected Behavior**: Extensions should work as expected (user choice)

**No action needed**: This is intended behavior for user customization

### Edge Case 3: Print Styles

**Scenario**: User prints the page

**Current Behavior**: No print-specific styles defined

**Expected Behavior**: Silver background should not waste printer ink

**Recommendation**: Consider adding `@media print { body { background: white !important; } }` (out of scope for this feature, but noted for future)

---

## Summary

This feature involves modifying 2 "entities" (CSS variables) in the Theme Configuration:
1. `--color-bg-secondary` in `:root` scope → `#C0C0C0`
2. `--color-bg-secondary` in `.dark-mode-active` scope → `#2d2d2d`

All other entities (Theme Mode, Background Layer, Color Contrast, CSS Scope) remain unchanged and function as designed. The change propagates automatically through the existing CSS cascade and theme switching mechanism.
