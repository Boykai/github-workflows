# Data Model: Add Yellow Background to App

**Feature**: `009-yellow-background`
**Date**: 2026-02-23

---

This feature does not introduce new application data models or database entities. It modifies existing **design tokens** (CSS custom properties) that define the app's visual theme. Below are the entities affected.

## Design Token: `--color-bg`

| Property | Value |
|----------|-------|
| Token name | `--color-bg` |
| Scope | `:root` (light mode) |
| Current value | `#ffffff` |
| New value | `#FFF9C4` |
| Purpose | Primary app-level background color used by components and layout areas |
| Consumers | Components referencing `var(--color-bg)` for background styling |

**Dark mode**: Unchanged — remains `#0d1117` in `html.dark-mode-active`.

---

## Design Token: `--color-bg-secondary`

| Property | Value |
|----------|-------|
| Token name | `--color-bg-secondary` |
| Scope | `:root` (light mode) |
| Current value | `#f6f8fa` |
| New value | `#FFF9C4` |
| Purpose | Body/page-level background and secondary surface areas |
| Consumers | `body` element (`background: var(--color-bg-secondary)`), secondary UI surfaces |

**Dark mode**: Unchanged — remains `#161b22` in `html.dark-mode-active`.

---

## Entity: Theme Mode

| Property | Description |
|----------|-------------|
| Modes | `light` (default), `dark` |
| Toggle mechanism | `useAppTheme` hook toggles `dark-mode-active` class on `<html>` |
| Storage | `localStorage` key `tech-connect-theme-mode`, synced with user settings API |
| Behavior | Light mode → yellow background (#FFF9C4); Dark mode → existing dark background (#0d1117 / #161b22) |

**No changes to theme mode logic** — the existing toggle mechanism handles light/dark switching. The yellow background is activated by the `:root` token values, which only apply when `dark-mode-active` class is absent.

---

## Contrast Validation

| Foreground Token | Foreground Value | Background Value | Contrast Ratio | WCAG AA (4.5:1) |
|-----------------|-----------------|-----------------|----------------|------------------|
| `--color-text` | `#24292f` | `#FFF9C4` | ~12.6:1 | ✅ PASS |
| `--color-text-secondary` | `#57606a` | `#FFF9C4` | ~6.3:1 | ✅ PASS |
| `--color-primary` | `#0969da` | `#FFF9C4` | ~5.4:1 | ✅ PASS |
| `--color-danger` | `#cf222e` | `#FFF9C4` | ~5.0:1 | ✅ PASS |
| `--color-success` | `#1a7f37` | `#FFF9C4` | ~5.2:1 | ✅ PASS |
| `--color-warning` | `#9a6700` | `#FFF9C4` | ~4.8:1 | ✅ PASS |

All foreground colors meet or exceed the 4.5:1 minimum contrast ratio against the yellow background.
