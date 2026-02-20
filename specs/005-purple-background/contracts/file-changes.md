# File Modification Contract: Add Purple Background Color

**Feature**: 005-purple-background | **Date**: 2026-02-20  
**Purpose**: Define exact file changes required for purple background implementation

## Contract Overview

This contract specifies the precise modifications to the global CSS file to apply a purple background (#7C3AED) to the application's body element, and update text colors on exposed surfaces (login and loading screens) for WCAG AA contrast compliance. All changes are limited to CSS custom property definitions and selector rules.

---

## File: `frontend/src/index.css`

**Purpose**: Global CSS variables and base styles  
**Change Type**: Add new CSS variable + update body background + add text color overrides

### Change 1 — Add `--color-bg-app` to `:root`

After `--color-bg-secondary: #f6f8fa;`, add:
```css
  --color-bg-app: #7C3AED;
```

### Change 2 — Add `--color-bg-app` to `html.dark-mode-active`

After `--color-bg-secondary: #161b22;`, add:
```css
  --color-bg-app: #7C3AED;
```

### Change 3 — Update `body` background

Change:
```css
  background: var(--color-bg-secondary);
```
To:
```css
  background: var(--color-bg-app);
```

---

## File: `frontend/src/App.css`

**Purpose**: App component styles  
**Change Type**: Update text colors on exposed surfaces for contrast compliance

### Change 1 — Update `.app-login h1` color

Change:
```css
  color: var(--color-text);
```
To:
```css
  color: #ffffff;
```

### Change 2 — Update `.app-login p` color

Change:
```css
  color: var(--color-text-secondary);
```
To:
```css
  color: #E9D5FF;
```
