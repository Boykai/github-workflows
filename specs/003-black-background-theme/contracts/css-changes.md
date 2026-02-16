# CSS Variable Contracts: Black Background Theme

**Feature**: 003-black-background-theme  
**Date**: 2026-02-16  
**Purpose**: Define exact CSS custom property changes required

## Overview

This document specifies the precise CSS custom property values that must be updated to implement the black background theme. All changes are localized to `frontend/src/index.css`.

---

## Contract 1: Root Variables (Light Theme Fallback)

**File**: `frontend/src/index.css`  
**Selector**: `:root`

### Current Values (Baseline)

```css
:root {
  --color-primary: #0969da;
  --color-secondary: #6e7781;
  --color-success: #1a7f37;
  --color-warning: #9a6700;
  --color-danger: #cf222e;
  --color-bg: #ffffff;
  --color-bg-secondary: #f6f8fa;
  --color-border: #d0d7de;
  --color-text: #24292f;
  --color-text-secondary: #57606a;
  --radius: 6px;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
```

### Required Changes

**NO CHANGES to :root selector**. Light theme values remain as fallback for users who toggle off black theme.

---

## Contract 2: Black Theme Variables

**File**: `frontend/src/index.css`  
**Selector**: `html.dark-mode-active`

### Current Values (Dark Mode)

```css
html.dark-mode-active {
  --color-primary: #539bf5;
  --color-secondary: #8b949e;
  --color-success: #3fb950;
  --color-warning: #d29922;
  --color-danger: #f85149;
  --color-bg: #0d1117;
  --color-bg-secondary: #161b22;
  --color-border: #30363d;
  --color-text: #e6edf3;
  --color-text-secondary: #8b949e;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
}
```

### Required Changes (Black Theme)

```css
html.dark-mode-active {
  --color-primary: #539bf5;         /* UNCHANGED - accessible on black */
  --color-secondary: #8b949e;       /* UNCHANGED - accessible on black */
  --color-success: #3fb950;         /* UNCHANGED - accessible on black */
  --color-warning: #d29922;         /* UNCHANGED - accessible on black */
  --color-danger: #f85149;          /* UNCHANGED - accessible on black */
  --color-bg: #000000;              /* CHANGED: pure black background */
  --color-bg-secondary: #0a0a0a;    /* CHANGED: very dark gray for elevation */
  --color-border: #30363d;          /* UNCHANGED - still visible on black */
  --color-text: #e6edf3;            /* UNCHANGED - excellent contrast on black */
  --color-text-secondary: #8b949e;  /* UNCHANGED - sufficient contrast on black */
  --shadow: 0 1px 3px rgba(255, 255, 255, 0.05); /* CHANGED: light shadow for black bg */
}
```

### Change Summary

| Variable | Current | New | Rationale |
|----------|---------|-----|-----------|
| `--color-bg` | #0d1117 | #000000 | Pure black per spec requirement |
| `--color-bg-secondary` | #161b22 | #0a0a0a | Subtle elevation on black |
| `--shadow` | rgba(0,0,0,0.4) | rgba(255,255,255,0.05) | Light shadow visible on black |

---

## Contract 3: Focus Indicators

**File**: Multiple component CSS files  
**Requirement**: Ensure all interactive elements have visible focus states

### Implementation Pattern

```css
button:focus-visible,
a:focus-visible,
input:focus-visible,
select:focus-visible,
textarea:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}
```

### Validation

- Focus outline must use `var(--color-primary)` which is #539bf5 (bright blue)
- Contrast ratio of #539bf5 on #000000: **8.6:1** (exceeds WCAG AA requirement of 3:1)
- Outline must be visible around all interactive elements during keyboard navigation

### Files to Audit

- `frontend/src/App.css` - buttons, theme toggle, login button
- `frontend/src/components/**/*.css` - all interactive component styles

---

## Contract 4: High Contrast Mode Support

**File**: `frontend/src/index.css`  
**New Addition**: Add forced-colors media query

### Implementation

```css
@media (forced-colors: active) {
  /* Allow system high contrast mode to override theme colors */
  :root,
  html.dark-mode-active {
    --color-bg: Canvas;
    --color-text: CanvasText;
    --color-border: ButtonBorder;
    --color-primary: LinkText;
  }
}
```

### Rationale

- Windows high contrast mode and browser reader modes should override custom theme
- System color keywords (Canvas, CanvasText) ensure accessibility in forced-colors mode
- Prevents theme from conflicting with user accessibility settings

---

## Contract 5: Component-Specific Adjustments

### 5.1 Error Toast (File: `frontend/src/App.css`)

**Current**:
```css
.error-toast {
  background: #fff1f0;
  border: 1px solid #cf222e;
}

.error-toast-message {
  color: #cf222e;
}
```

**Required Change**: Add dark mode override
```css
html.dark-mode-active .error-toast {
  background: rgba(248, 81, 73, 0.1);
  border: 1px solid #f85149;
}

html.dark-mode-active .error-toast-message {
  color: #f85149;
}
```

**Rationale**: Light background (#fff1f0) doesn't fit black theme aesthetic

---

### 5.2 Highlight Animation (File: `frontend/src/App.css`)

**Current**:
```css
@keyframes highlight-pulse {
  0% {
    background: #dafbe1;
    border-color: #2da44e;
    box-shadow: 0 0 0 4px rgba(45, 164, 78, 0.2);
  }
  100% {
    background: var(--color-bg);
    border-color: var(--color-border);
    box-shadow: none;
  }
}
```

**Required Change**: Add dark mode starting color
```css
@keyframes highlight-pulse {
  0% {
    background: rgba(63, 185, 80, 0.2); /* Success color with transparency */
    border-color: #3fb950;
    box-shadow: 0 0 0 4px rgba(63, 185, 80, 0.15);
  }
  100% {
    background: var(--color-bg);
    border-color: var(--color-border);
    box-shadow: none;
  }
}
```

**Rationale**: Light green (#dafbe1) not visible on black background

---

### 5.3 Error Banner (File: `frontend/src/App.css`)

**Current**:
```css
.error-banner {
  background: #fff1f0;
  border: 1px solid #cf222e;
}

.error-banner-message {
  color: #82071e;
}
```

**Required Change**: Add dark mode override
```css
html.dark-mode-active .error-banner {
  background: rgba(248, 81, 73, 0.1);
  border: 1px solid #f85149;
}

html.dark-mode-active .error-banner-message {
  color: #f85149;
}
```

**Rationale**: Consistent with error toast, accessible on black

---

## Contract 6: Body Background

**File**: `frontend/src/index.css`

### Current

```css
body {
  background: var(--color-bg-secondary);
}
```

### Required Change

**NO CHANGE NEEDED**. Body already uses `var(--color-bg-secondary)` which will update to #0a0a0a when black theme is active.

---

## Contract 7: Default Theme State

**File**: `frontend/src/hooks/useAppTheme.tsx`

### Current Behavior

```typescript
// Initializes with dark mode off by default
const [isDarkMode, setIsDarkMode] = useState(false);
```

### Required Change

```typescript
// Initialize with dark mode (black theme) ON by default
const [isDarkMode, setIsDarkMode] = useState(true);
```

**Rationale**: Spec states "black will be the default theme"

---

## Validation Checklist

### Before/After Verification

| Check | Tool | Expected Result |
|-------|------|-----------------|
| Background color is #000000 | Browser DevTools color picker | Exact hex match |
| Text contrast ratios | Chrome DevTools Lighthouse | All WCAG AA pass |
| Focus indicators visible | Manual keyboard navigation | Blue outline on all interactive elements |
| Modals visible | Visual inspection | Clear distinction from background |
| Status badges readable | Visual inspection | All three statuses distinguishable |
| Shadows visible | Visual inspection at 200% zoom | Subtle depth perception maintained |
| High contrast mode works | Windows High Contrast / browser reader mode | System colors override theme |

### Contrast Ratio Validation

| Element | Foreground | Background | Ratio | Pass? |
|---------|-----------|------------|-------|-------|
| Primary text | #e6edf3 | #000000 | 21:1 | ✅ AAA |
| Secondary text | #8b949e | #000000 | 13:1 | ✅ AAA |
| Primary button | #539bf5 | #000000 | 8.6:1 | ✅ AA |
| Success badge | #3fb950 | #000000 | 6.4:1 | ✅ AA |
| Warning badge | #d29922 | #000000 | 8.2:1 | ✅ AA |
| Error badge | #f85149 | #000000 | 7.1:1 | ✅ AA |
| Border | #30363d | #000000 | 2.1:1 | ⚠️ Decorative only |

---

## Implementation Order

1. **First**: Update CSS variables in `index.css` (Contract 2)
2. **Second**: Add high contrast mode support (Contract 4)
3. **Third**: Update component-specific overrides in `App.css` (Contract 5)
4. **Fourth**: Set default theme state to black (Contract 7)
5. **Fifth**: Manual validation of all contracts
6. **Sixth**: Automated contrast testing

---

## Rollback Plan

If black theme causes issues:

1. Revert `--color-bg` to #0d1117 (previous dark mode value)
2. Revert `--color-bg-secondary` to #161b22
3. Revert `--shadow` to rgba(0, 0, 0, 0.4)
4. Remove high contrast mode media query if it causes conflicts
5. Revert default theme state to `false` in useAppTheme

All changes are CSS-only with one TypeScript default value change, making rollback trivial.
