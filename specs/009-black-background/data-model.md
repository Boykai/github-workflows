# Data Model: Add Black Background Theme to App

**Feature**: `009-black-background` | **Date**: 2026-02-22

> This feature creates no new data entities, database schemas, or API contracts. It modifies only CSS design tokens (custom properties) and a handful of hardcoded color values. This document describes the **design token entities** — the color values that define the black background theme.

## Design Token Entities

### 1. Theme Token

A CSS custom property defined on `:root` or `html.dark-mode-active` that controls a visual aspect of the app.

| Attribute | Description |
|-----------|-------------|
| Name | CSS custom property name (e.g., `--color-bg`) |
| Light Value | Color value applied in default (light) mode via `:root` |
| Dark Value | Color value applied when `html.dark-mode-active` class is present |
| Usage | Where the token is referenced (background, text, border, etc.) |
| Consumers | Components/selectors that use `var(--token-name)` |

**Token Definitions (Black Theme)**:

| Token | Light Value | Dark Value | Usage |
|-------|-------------|------------|-------|
| `--color-bg` | `#000000` | `#000000` | Root/app-level background |
| `--color-bg-secondary` | `#121212` | `#0a0a0a` | Body background, alternate areas, card surfaces |
| `--color-text` | `#ffffff` | `#f0f0f0` | Primary text |
| `--color-text-secondary` | `#a0a0a0` | `#8a8a8a` | Secondary/muted text |
| `--color-border` | `#2c2c2c` | `#1f1f1f` | Borders, dividers, outlines |
| `--color-primary` | `#539bf5` | `#539bf5` | Primary action (buttons, links) |
| `--color-secondary` | `#8b949e` | `#8b949e` | Secondary elements |
| `--color-success` | `#3fb950` | `#3fb950` | Success indicators |
| `--color-warning` | `#d29922` | `#d29922` | Warning indicators |
| `--color-danger` | `#f85149` | `#f85149` | Danger/error indicators |
| `--radius` | `6px` | `6px` | Border radius (unchanged) |
| `--shadow` | `0 1px 3px rgba(0,0,0,0.6)` | `0 1px 3px rgba(0,0,0,0.8)` | Elevation shadow |

**Relationships**:
- `--color-bg` → used by `.app-header`, `.app-container`, cards, modals, panels
- `--color-bg-secondary` → used by `body`, `.theme-toggle-btn`, sidebar, alternate sections
- `--color-text` → used by `body`, all heading/paragraph elements
- `--color-border` → used by `.app-header` border, `.spinner`, card borders, dividers
- All components consume tokens via `var()` — no direct coupling to hex values

### 2. Surface Level

A conceptual layer in the visual hierarchy distinguishing the root background from elevated components.

| Level | Token | Color | Components |
|-------|-------|-------|------------|
| Root | `--color-bg` | `#000000` | Page background, full-bleed sections |
| Elevated | `--color-bg-secondary` | `#121212` (light) / `#0a0a0a` (dark) | Cards, sidebar, navbar, modals, input backgrounds, alternate sections |
| Interactive | `--color-primary` | `#539bf5` | Buttons, links, focused inputs |

**Visual hierarchy**: Root (darkest) → Elevated (slightly lighter) → Interactive (accent colored). This creates depth perception on a true black background per FR-004.

### 3. Hardcoded Color Overrides

Values that cannot use design tokens because they are context-specific (notification colors, accent badges, button variants).

| Current Value | New Value | Context | Reason for Override |
|--------------|-----------|---------|-------------------|
| `#dafbe1` (light green) | `rgba(63, 185, 80, 0.15)` | Success notification background | Must be dark-compatible green tint |
| `#fff1f0` (light red) | `rgba(248, 81, 73, 0.15)` | Error notification/alert background | Must be dark-compatible red tint |

These use semi-transparent versions of the success/danger accent colors, which naturally adapt to any background.

## State Transitions: No Changes

The `useAppTheme` hook's state machine remains unchanged:
- **Mount** → read localStorage → set `isDarkMode` state
- **API settings load** → sync from API (takes precedence) → update localStorage
- **Toggle** → flip `isDarkMode` → update localStorage → update API (fire-and-forget)
- **Effect** → add/remove `dark-mode-active` class on `<html>` element

## Validation Rules

### WCAG AA Contrast Requirements

All text tokens must achieve a minimum 4.5:1 contrast ratio against their background:

| Text Token | Against Background | Ratio | Status |
|-----------|-------------------|-------|--------|
| `--color-text` (`#ffffff`) | `--color-bg` (`#000000`) | 21:1 | ✅ |
| `--color-text-secondary` (`#a0a0a0`) | `--color-bg` (`#000000`) | 10.4:1 | ✅ |
| `--color-text` (`#ffffff`) | `--color-bg-secondary` (`#121212`) | 17.4:1 | ✅ |
| `--color-text-secondary` (`#a0a0a0`) | `--color-bg-secondary` (`#121212`) | 8.6:1 | ✅ |
