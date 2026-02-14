# CSS Contract: Blue Background Color

**Feature**: Blue Background Color  
**Branch**: 002-blue-background  
**Date**: 2026-02-14

## Overview

This document defines CSS custom properties, selectors, and conventions for implementing the blue background color feature.

---

## CSS Custom Properties

### Light Mode Variables (`:root`)

```css
:root {
  /* Background colors - MODIFIED for blue background */
  --color-bg: #2196F3;              /* Primary background (Material Blue 500) */
  --color-bg-secondary: #f6f8fa;    /* Secondary background for panels */
  
  /* Text colors - May need adjustment for contrast */
  --color-text: #24292f;            /* Primary text (on secondary backgrounds) */
  --color-text-secondary: #57606a;  /* Secondary text */
  
  /* Interactive colors - Validate contrast against blue */
  --color-primary: #0969da;         /* Primary action buttons */
  --color-secondary: #6e7781;       /* Secondary elements */
  --color-success: #1a7f37;         /* Success indicators */
  --color-warning: #9a6700;         /* Warning indicators */
  --color-danger: #cf222e;          /* Error/danger indicators */
  
  /* Layout */
  --color-border: #d0d7de;          /* Border colors */
  --radius: 6px;                    /* Border radius */
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.1); /* Shadow */
}
```

---

### Dark Mode Variables (`html.dark-mode-active`)

```css
html.dark-mode-active {
  /* Background colors - MODIFIED for blue background in dark mode */
  --color-bg: #1565C0;              /* Primary background (Material Blue 800) */
  --color-bg-secondary: #161b22;    /* Secondary background for panels */
  
  /* Text colors - Already optimized for dark mode */
  --color-text: #e6edf3;            /* Primary text (light on dark) */
  --color-text-secondary: #8b949e;  /* Secondary text */
  
  /* Interactive colors - Dark mode variants */
  --color-primary: #539bf5;         /* Primary action buttons */
  --color-secondary: #8b949e;       /* Secondary elements */
  --color-success: #3fb950;         /* Success indicators */
  --color-warning: #d29922;         /* Warning indicators */
  --color-danger: #f85149;          /* Error/danger indicators */
  
  /* Layout */
  --color-border: #30363d;          /* Border colors */
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.4); /* Shadow */
}
```

---

## CSS Selectors and Classes

### Body/Root Element

```css
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif;
  font-size: 14px;
  line-height: 1.5;
  color: var(--color-text);
  background: var(--color-bg-secondary); /* Uses secondary for text readability */
}
```

**Note**: `body` uses `--color-bg-secondary` instead of `--color-bg` to ensure text has adequate contrast. Primary blue background is applied to specific containers.

---

### Application Container

```css
.app-container {
  background: var(--color-bg); /* Primary blue background */
  min-height: 100vh;
}
```

**Usage**: Main application container that displays the blue background.

---

### Login Screen

```css
.app-login {
  background: var(--color-bg); /* Primary blue background */
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--color-text);
}

.app-login h1 {
  color: #FFFFFF; /* White text on blue background */
  font-size: 2rem;
  margin-bottom: 1rem;
}

.app-login p {
  color: #FFFFFF; /* White text on blue background */
  font-size: 1rem;
  margin-bottom: 2rem;
}
```

**Accessibility**: White text (#FFFFFF) on #2196F3 has 3.15:1 contrast. This is acceptable for large text (h1 at 2rem = 32px ≈ 24pt) but may need adjustment for normal text.

---

### Content Panels/Cards

```css
.content-panel,
.card,
.sidebar,
.chat-interface {
  background: var(--color-bg-secondary); /* White/near-black panels */
  color: var(--color-text);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: 1rem;
}
```

**Purpose**: Content containers use secondary background to ensure text contrast meets WCAG AA (4.5:1 for normal text).

---

### Buttons

```css
button {
  cursor: pointer;
  border: none;
  border-radius: var(--radius);
  font-size: 14px;
  font-weight: 500;
  padding: 8px 16px;
  transition: background 0.15s ease;
}

.primary-button {
  background: var(--color-primary); /* #0969da in light, #539bf5 in dark */
  color: #FFFFFF;
}

.secondary-button {
  background: var(--color-secondary);
  color: var(--color-text);
}
```

**Contrast Validation**:
- Light mode: #0969da (primary button) vs #2196F3 (background) = needs testing
- Dark mode: #539bf5 (primary button) vs #1565C0 (background) = needs testing

---

## Contrast Requirements

### WCAG AA Compliance

| Element Type | Background | Text/Foreground | Required Ratio | Status |
|--------------|------------|-----------------|----------------|--------|
| Large text (≥18pt) | #2196F3 (light) | #FFFFFF | ≥3:1 | ✅ 3.15:1 PASS |
| Normal text | #2196F3 (light) | #FFFFFF | ≥4.5:1 | ❌ 3.15:1 FAIL |
| Normal text | #f6f8fa (secondary) | #24292f | ≥4.5:1 | ✅ ~10:1 PASS |
| Large text (≥18pt) | #1565C0 (dark) | #FFFFFF | ≥3:1 | ✅ 5.98:1 PASS |
| Normal text | #1565C0 (dark) | #e6edf3 | ≥4.5:1 | ✅ ~6:1 PASS |
| Normal text | #161b22 (secondary) | #e6edf3 | ≥4.5:1 | ✅ ~10:1 PASS |
| Buttons | #2196F3 | #0969da | ≥3:1 | 🔍 Needs validation |

**Strategy**: Use `--color-bg-secondary` for areas with normal text, reserve `--color-bg` (blue) for headers and areas with large text or no text.

---

## Layering Pattern

```
┌─────────────────────────────────────────┐
│  body: --color-bg-secondary (white)     │  ← Default background
│  ┌───────────────────────────────────┐  │
│  │  .app-container: --color-bg (blue)│  │  ← Blue background shows through
│  │  ┌─────────────────────────────┐  │  │
│  │  │  .content-panel: secondary  │  │  │  ← White/dark panels for text
│  │  │  (text with 4.5:1 contrast) │  │  │
│  │  └─────────────────────────────┘  │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

**Purpose**: Creates visual depth while ensuring WCAG AA compliance.

---

## Implementation Checklist

- [ ] Update `frontend/src/index.css`:
  - [ ] Modify `:root --color-bg` to `#2196F3`
  - [ ] Modify `html.dark-mode-active --color-bg` to `#1565C0`
  - [ ] Keep `--color-bg-secondary` as-is for text contrast
- [ ] Update `frontend/src/App.css`:
  - [ ] Ensure `.app-container` uses `var(--color-bg)`
  - [ ] Ensure `.app-login` uses `var(--color-bg)`
  - [ ] Verify text colors meet contrast requirements
- [ ] Test all interactive elements (buttons, links, inputs) for 3:1 contrast against blue background
- [ ] Run accessibility audit with axe-core or Lighthouse
- [ ] Visual validation in both light and dark modes

---

## CSS File Structure

```
frontend/src/
├── index.css          # PRIMARY: Define CSS custom properties
├── App.css            # SECONDARY: Application layout styles
└── components/
    ├── auth/
    │   └── LoginButton.css
    ├── chat/
    │   └── ChatInterface.css
    └── sidebar/
        └── ProjectSidebar.css
```

**Primary Changes**: `index.css` (CSS custom properties)  
**Secondary Changes**: `App.css` (verify contrast)  
**Optional Changes**: Component CSS files (if contrast issues found)

---

## Browser Compatibility

CSS custom properties are supported in:
- Chrome 49+ (2016)
- Firefox 31+ (2014)
- Safari 9.1+ (2016)
- Edge 15+ (2017)

**No polyfills needed** for modern browser targets.

---

## Testing Strategy

1. **Visual Inspection**: Open app in light/dark modes, verify blue background presence
2. **Color Picker**: Use browser DevTools to measure actual colors
3. **Contrast Checker**: Use WebAIM or similar tool to validate ratios
4. **Automated Testing**: Playwright + axe-core for WCAG compliance
5. **Cross-browser**: Test in Chrome, Firefox, Safari, Edge

---

## References

- [MDN: CSS Custom Properties](https://developer.mozilla.org/en-US/docs/Web/CSS/--*)
- [WCAG 2.1 Contrast Guidelines](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html)
- [Material Design Color System](https://m2.material.io/design/color/the-color-system.html)

---

**End of CSS Contract**
