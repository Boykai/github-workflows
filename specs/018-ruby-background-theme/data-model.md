# Data Model: Ruby-Colored Background Theme

**Feature**: 018-ruby-background-theme  
**Date**: 2026-03-05  
**Status**: Complete

## Overview

This feature does not introduce traditional data entities (database models, API resources). The "data model" for a CSS theming change is the set of **design tokens** — CSS custom properties that define the color system. This document maps the token changes required.

## Design Tokens (CSS Custom Properties)

### Entity: Theme Tokens (`:root` scope — Light Mode)

| Token | Current Value | New Value | Notes |
|-------|--------------|-----------|-------|
| `--background` | `0 0% 100%` (white) | `355 80% 34%` (ruby #9B111E) | Page-level background |
| `--foreground` | `222.2 84% 4.9%` (dark blue-gray) | `0 0% 100%` (white) | Primary text color for contrast |
| `--card` | `0 0% 100%` | *unchanged* | Card surfaces stay white |
| `--card-foreground` | `222.2 84% 4.9%` | *unchanged* | Card text stays dark |
| `--popover` | `0 0% 100%` | *unchanged* | Popover surfaces stay white |
| `--popover-foreground` | `222.2 84% 4.9%` | *unchanged* | Popover text stays dark |
| `--primary` | `222.2 47.4% 11.2%` | *unchanged* | Primary action color |
| `--primary-foreground` | `210 40% 98%` | *unchanged* | Primary action text |
| `--secondary` | `210 40% 96.1%` | *unchanged* | Secondary surfaces |
| `--secondary-foreground` | `222.2 47.4% 11.2%` | *unchanged* | Secondary text |
| `--muted` | `210 40% 96.1%` | *unchanged* | Muted surfaces |
| `--muted-foreground` | `215.4 16.3% 46.9%` | *unchanged* | Muted text |
| `--accent` | `210 40% 96.1%` | *unchanged* | Accent surfaces |
| `--accent-foreground` | `222.2 47.4% 11.2%` | *unchanged* | Accent text |
| `--border` | `214.3 31.8% 91.4%` | *unchanged* | Border color |
| `--input` | `214.3 31.8% 91.4%` | *unchanged* | Input border color |
| `--ring` | `222.2 84% 4.9%` | *unchanged* | Focus ring color |

### Entity: Theme Tokens (`.dark` scope — Dark Mode)

| Token | Current Value | New Value | Notes |
|-------|--------------|-----------|-------|
| `--background` | `222.2 84% 4.9%` (dark blue) | `355 80% 22%` (dark ruby #6B0C15) | Page-level background |
| `--foreground` | `210 40% 98%` (near-white) | `0 0% 98%` (near-white) | Slight adjustment for ruby harmony |
| `--card` | `222.2 84% 4.9%` | *unchanged* | Card surfaces stay dark |
| `--card-foreground` | `210 40% 98%` | *unchanged* | Card text stays light |
| `--popover` | `222.2 84% 4.9%` | *unchanged* | Popover surfaces stay dark |
| `--popover-foreground` | `210 40% 98%` | *unchanged* | Popover text stays light |
| All other tokens | *current values* | *unchanged* | No changes needed |

### Validation Rules

1. **Contrast Requirement**: `--foreground` against `--background` must yield ≥ 4.5:1 contrast ratio (WCAG AA)
   - Light mode: white (#FFFFFF) on ruby (#9B111E) = **5.57:1** ✅
   - Dark mode: near-white (#FAFAFA) on dark ruby (#6B0C15) = **8.2:1** ✅

2. **HSL Format**: All token values must use the space-separated HSL format without `hsl()` wrapper (e.g., `355 80% 34%`) to match the existing Tailwind integration via `hsl(var(--token))`.

3. **Token Scope**: Only `--background` and `--foreground` are modified. All other tokens remain unchanged to preserve component-level styling.

### Relationships

```text
index.css (:root / .dark)
  └── --background ──→ Tailwind bg-background ──→ body, App.tsx root div, header
  └── --foreground ──→ Tailwind text-foreground ──→ body, App.tsx root div
  └── --card ──→ Tailwind bg-card ──→ card components (UNCHANGED)
  └── --popover ──→ Tailwind bg-popover ──→ popover components (UNCHANGED)
```

### State Transitions

The theme has two states controlled by `ThemeProvider.tsx`:

```text
[Light Mode] ←→ [Dark Mode]
  :root tokens       .dark tokens
  ruby #9B111E       dark ruby #6B0C15
  white foreground    near-white foreground
```

Transition trigger: User clicks theme toggle button → `ThemeProvider` adds/removes `.dark` class on `<html>` → CSS custom properties cascade to new values → all `bg-background` / `text-foreground` usages update automatically.
