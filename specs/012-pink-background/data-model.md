# Data Model: Add Pink Background Color to App

**Date**: 2026-02-27 | **Branch**: `012-pink-background` | **Plan**: [plan.md](plan.md)

## Overview

This feature is a CSS-only change. No backend schema, API, data model, or UI state changes are required. The only modification is to CSS custom property values in the existing theming system.

## CSS Token Changes

### Modified Tokens

| Token | Selector | Current Value | New Value | Visual Result |
|-------|----------|---------------|-----------|---------------|
| `--background` | `:root` (light mode) | `0 0% 100%` (white) | `350 100% 88%` (#FFC0CB, pink) | App body background changes from white to pink |
| `--background` | `.dark` (dark mode) | `222.2 84% 4.9%` (dark navy) | `350 30% 12%` (#281519, dark pink) | App dark mode background changes from dark navy to dark muted pink |

### Unchanged Tokens

All other CSS custom properties remain unchanged. The following tokens are independent of `--background` and are not affected:

| Token | Purpose | Why Unchanged |
|-------|---------|---------------|
| `--foreground` | Text color | Provides sufficient contrast against both pink values |
| `--card` / `--card-foreground` | Card surfaces | Component-level, independent of app background |
| `--popover` / `--popover-foreground` | Popover surfaces | Component-level, independent of app background |
| `--primary` / `--primary-foreground` | Primary action color | Semantic color, not a surface |
| `--secondary` / `--secondary-foreground` | Secondary surfaces | Component-level, independent of app background |
| `--muted` / `--muted-foreground` | Muted surfaces | Component-level, independent of app background |
| `--accent` / `--accent-foreground` | Accent surfaces | Component-level, independent of app background |
| `--destructive` / `--destructive-foreground` | Destructive action color | Semantic color, not a surface |
| `--border` | Border color | Decorative, independent of background |
| `--input` | Input border color | Form element, independent of background |
| `--ring` | Focus ring color | Accessibility indicator, independent of background |

## Contrast Verification

| Mode | Background | Foreground | Contrast Ratio | WCAG AA (4.5:1) |
|------|-----------|------------|----------------|-----------------|
| Light | `350 100% 88%` (#FFC0CB) | `222.2 84% 4.9%` (#020817) | ~12.5:1 | ✅ Pass |
| Dark | `350 30% 12%` (#281519) | `210 40% 98%` (#F8FAFC) | ~15:1 | ✅ Pass |

## Entities

No database entities, API models, or application state objects are affected by this change.

## Schema Changes

**None.** No database migrations, no API contract changes, no new backend endpoints, no new frontend state.
