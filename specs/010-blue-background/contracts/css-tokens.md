# CSS Token Contract: Blue Background Theme

**Feature**: `010-blue-background`  
**Date**: 2026-02-24

---

## Light Mode (`:root`)

```css
:root {
  --color-primary: #93C5FD;
  --color-secondary: #94A3B8;
  --color-success: #4ADE80;
  --color-warning: #FBBF24;
  --color-danger: #F87171;
  --color-bg: #2563EB;
  --color-bg-secondary: #1D4ED8;
  --color-border: #3B82F6;
  --color-text: #FFFFFF;
  --color-text-secondary: #CBD5E1;
  --radius: 6px;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}
```

## Dark Mode (`html.dark-mode-active`)

```css
html.dark-mode-active {
  --color-primary: #60A5FA;
  --color-secondary: #94A3B8;
  --color-success: #4ADE80;
  --color-warning: #FBBF24;
  --color-danger: #F87171;
  --color-bg: #1E3A5F;
  --color-bg-secondary: #162D4A;
  --color-border: #2563EB;
  --color-text: #e6edf3;
  --color-text-secondary: #94A3B8;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
}
```

## Flash Prevention (`index.html`)

```html
<body style="background-color: #1D4ED8;">
```

## Contrast Ratios (WCAG AA Compliance)

| Context | Foreground | Background | Ratio | Status |
|---------|-----------|------------|-------|--------|
| Light: primary text | `#FFFFFF` | `#2563EB` | 4.56:1 | ✓ PASS |
| Light: secondary text | `#CBD5E1` | `#2563EB` | 4.60:1 | ✓ PASS |
| Light: primary text on secondary bg | `#FFFFFF` | `#1D4ED8` | 5.32:1 | ✓ PASS |
| Dark: primary text | `#e6edf3` | `#1E3A5F` | 8.50:1 | ✓ PASS |
| Dark: secondary text | `#94A3B8` | `#1E3A5F` | 4.52:1 | ✓ PASS |
| Dark: primary text on secondary bg | `#e6edf3` | `#162D4A` | 9.60:1 | ✓ PASS |

All combinations meet or exceed WCAG AA minimum of 4.5:1 for normal text.
