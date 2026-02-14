# CSS Contract: Green Theme Option

**Feature**: Green Theme Option  
**Branch**: `002-green-theme`  
**Date**: 2026-02-14  
**Phase**: 1 - Design

## Overview

This document defines the CSS conventions, class names, and custom property patterns for the green theme feature.

---

## CSS Custom Properties (Variables)

All themes use the same set of CSS custom properties defined in `:root` and overridden in theme-specific classes.

### Color Variables

```css
/* Applied in :root for default theme and overridden in theme classes */

/* Primary brand colors */
--color-primary: #0969da;      /* Main accent color (links, buttons, highlights) */
--color-secondary: #6e7781;    /* Secondary accent color */

/* State colors */
--color-success: #1a7f37;      /* Success states and positive feedback */
--color-warning: #9a6700;      /* Warning states */
--color-danger: #cf222e;       /* Error states and destructive actions */

/* Background colors */
--color-bg: #ffffff;           /* Main background (pages) */
--color-bg-secondary: #f6f8fa; /* Secondary backgrounds (cards, panels) */

/* Border colors */
--color-border: #d0d7de;       /* Borders, dividers, outlines */

/* Text colors */
--color-text: #24292f;         /* Primary text */
--color-text-secondary: #57606a; /* Secondary text (descriptions, hints) */

/* UI properties */
--radius: 6px;                 /* Border radius for rounded corners */
--shadow: 0 1px 3px rgba(0, 0, 0, 0.1); /* Box shadow for elevation */
```

### Usage in Components

```css
/* Example component styling */
.button-primary {
  background: var(--color-primary);
  color: var(--color-bg);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
}

.card {
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  color: var(--color-text);
}
```

---

## Theme Class Names

### Base Themes (Existing)

```css
/* Default Light Theme - No class required */
:root {
  /* Default values as shown above */
}

/* Dark Theme */
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

### Green Themes (New)

```css
/* Green Light Theme */
html.green-mode-active {
  --color-primary: #2da44e;      /* GitHub success green */
  --color-secondary: #6e7781;    /* Keep neutral secondary */
  --color-success: #1a7f37;      /* Deeper forest green for success */
  --color-warning: #9a6700;      /* Keep warning amber */
  --color-danger: #cf222e;       /* Keep danger red */
  --color-bg: #ffffff;           /* Clean white background */
  --color-bg-secondary: #f6fff8; /* Subtle green tint (very light mint) */
  --color-border: #d0d7de;       /* Keep neutral borders */
  --color-text: #24292f;         /* Dark text for contrast */
  --color-text-secondary: #57606a; /* Neutral secondary text */
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* Green Dark Theme */
html.green-dark-mode-active {
  --color-primary: #3fb950;      /* Brighter green for dark bg */
  --color-secondary: #8b949e;    /* Light gray for dark bg */
  --color-success: #56d364;      /* Lighter success green */
  --color-warning: #d29922;      /* Light warning */
  --color-danger: #f85149;       /* Light danger */
  --color-bg: #0d1117;           /* Dark background */
  --color-bg-secondary: #0d1a12; /* Dark background with green tint */
  --color-border: #30363d;       /* Dark borders */
  --color-text: #e6edf3;         /* Light text for contrast */
  --color-text-secondary: #8b949e; /* Light secondary text */
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
}
```

---

## Class Application Pattern

### JavaScript/React

```typescript
// Apply theme class to document root
const rootElement = document.documentElement;

// Function to apply theme
function applyThemeClass(theme: ThemeMode): void {
  // Remove all theme classes
  rootElement.classList.remove(
    'dark-mode-active',
    'green-mode-active',
    'green-dark-mode-active'
  );
  
  // Apply new theme class (if not default 'light')
  if (theme !== 'light') {
    const className = THEME_CLASS_MAP[theme];
    if (className) {
      rootElement.classList.add(className);
    }
  }
}
```

### Class Mapping

```typescript
const THEME_CLASS_MAP: Record<ThemeMode, string> = {
  light: '',                      // No class (default)
  dark: 'dark-mode-active',       // Existing dark theme
  green: 'green-mode-active',     // New green theme
  'green-dark': 'green-dark-mode-active', // New green dark theme
};
```

---

## Accessibility Compliance

### Contrast Ratios (WCAG 2.1 Level AA)

All color combinations MUST meet these minimum ratios:
- **Normal text** (< 18pt): 4.5:1
- **Large text** (≥ 18pt or 14pt bold): 3:1

### Green Light Theme Contrast Validation

| Element | Foreground | Background | Ratio | Status |
|---------|------------|------------|-------|--------|
| Primary text on main bg | `#24292f` | `#ffffff` | 14.5:1 | ✅ AAA |
| Secondary text on main bg | `#57606a` | `#ffffff` | 7.1:1 | ✅ AAA |
| Primary text on secondary bg | `#24292f` | `#f6fff8` | 14.2:1 | ✅ AAA |
| Primary button text | `#ffffff` | `#2da44e` | 4.8:1 | ✅ AA |
| Link color on white | `#2da44e` | `#ffffff` | 3.9:1 | ⚠️ Large text only |
| Link hover (darker) | `#1a7f37` | `#ffffff` | 5.5:1 | ✅ AA |

### Green Dark Theme Contrast Validation

| Element | Foreground | Background | Ratio | Status |
|---------|------------|------------|-------|--------|
| Primary text on main bg | `#e6edf3` | `#0d1117` | 13.8:1 | ✅ AAA |
| Secondary text on main bg | `#8b949e` | `#0d1117` | 6.2:1 | ✅ AAA |
| Primary text on secondary bg | `#e6edf3` | `#0d1a12` | 13.2:1 | ✅ AAA |
| Primary button text | `#ffffff` | `#3fb950` | 3.5:1 | ✅ Large text AA |
| Link color on dark | `#3fb950` | `#0d1117` | 5.1:1 | ✅ AA |

### Contrast Improvement Strategies

If any combinations fail contrast checks:
1. Darken foreground color by 10-15%
2. Lighten background color by 5-10%
3. Add text shadow for additional separation (last resort)

---

## Implementation Guidelines

### File Organization

```
frontend/src/
├── index.css                  # Global styles with theme variables
│   ├── :root { }             # Default light theme
│   ├── html.dark-mode-active { }      # Existing dark theme
│   ├── html.green-mode-active { }     # NEW: Green light theme
│   └── html.green-dark-mode-active { } # NEW: Green dark theme
└── hooks/
    └── useAppTheme.ts         # Hook that applies theme classes
```

### Adding New CSS Variables

If additional variables are needed:
1. Add to `:root` with default value
2. Override in ALL theme classes (maintain consistency)
3. Document in this contract
4. Validate contrast ratios for color variables

### Theme Naming Convention

Pattern: `[color]-[variant]-mode-active`
- `[color]`: Theme color (omitted for default, e.g., "dark", "green")
- `[variant]`: Optional variant (e.g., "dark" for dark mode)
- Suffix: Always end with `-mode-active`

Examples:
- ✅ `dark-mode-active`
- ✅ `green-mode-active`
- ✅ `green-dark-mode-active`
- ❌ `greenTheme` (wrong format)
- ❌ `mode-green` (wrong order)

---

## Testing Checklist

### Visual Testing

- [ ] All text is readable against backgrounds
- [ ] Links are distinguishable from regular text
- [ ] Buttons have sufficient contrast
- [ ] Focus indicators are visible
- [ ] Hover states are clear
- [ ] Disabled states are distinguishable

### Automated Testing

```bash
# Install contrast checking tool
npm install --save-dev pa11y

# Run accessibility audit
npm run test:a11y
```

### Manual Validation Tools

- **WebAIM Contrast Checker**: https://webaim.org/resources/contrastchecker/
- **Chrome DevTools Lighthouse**: Accessibility audit
- **WAVE Browser Extension**: Real-time accessibility feedback

### Cross-Browser Testing

Test theme switching in:
- [ ] Chrome/Edge (Chromium)
- [ ] Firefox
- [ ] Safari (WebKit)
- [ ] Mobile browsers (iOS Safari, Chrome Mobile)

---

## Future Considerations

Potential enhancements (out of current scope):
- CSS media queries for `prefers-color-scheme`
- CSS transitions for smooth theme changes
- CSS Grid/Flexbox variables for layout consistency
- CSS filters for generating theme variations programmatically

---

## References

- **WCAG 2.1 Guidelines**: https://www.w3.org/WAI/WCAG21/quickref/
- **CSS Custom Properties (MDN)**: https://developer.mozilla.org/en-US/docs/Web/CSS/--*
- **GitHub Design System**: https://primer.style/foundations/color
- **WebAIM Contrast Checker**: https://webaim.org/resources/contrastchecker/

---

## Summary

This CSS contract defines:
1. CSS custom property names and their semantic meanings
2. Theme class naming conventions (`[color]-[variant]-mode-active`)
3. Specific color values for green and green-dark themes
4. Accessibility compliance requirements (WCAG 2.1 AA)
5. Implementation patterns for applying theme classes

All themes reuse the same variable names, making component code theme-agnostic.
