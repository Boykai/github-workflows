# Data Model: Add Purple Background Color to Application

**Date**: 2026-02-27 | **Branch**: `012-purple-background` | **Plan**: [plan.md](plan.md)

## Overview

This feature is a frontend-only CSS theming change. No backend schema, API, or data model changes are required. No new component state is introduced. The change is limited to CSS custom property values in `frontend/src/index.css`.

## CSS Design Token Model

### Modified Tokens — Light Mode (`:root`)

| Token | Current Value | New Value | Description |
|-------|--------------|-----------|-------------|
| `--background` | `0 0% 100%` (white) | `270 50% 40%` (purple) | Primary background surface color |
| `--foreground` | `222.2 84% 4.9%` (near-black) | `210 40% 98%` (near-white) | Primary text color |
| `--card` | `0 0% 100%` (white) | `270 50% 45%` (lighter purple) | Card surface background |
| `--card-foreground` | `222.2 84% 4.9%` | `210 40% 98%` | Card text color |
| `--popover` | `0 0% 100%` (white) | `270 50% 45%` (lighter purple) | Popover surface background |
| `--popover-foreground` | `222.2 84% 4.9%` | `210 40% 98%` | Popover text color |
| `--primary` | `222.2 47.4% 11.2%` | `210 40% 98%` | Primary action color |
| `--primary-foreground` | `210 40% 98%` | `270 50% 40%` | Primary action text |
| `--secondary` | `210 40% 96.1%` | `270 40% 50%` | Secondary surface color |
| `--secondary-foreground` | `222.2 47.4% 11.2%` | `210 40% 98%` | Secondary surface text |
| `--muted` | `210 40% 96.1%` | `270 30% 50%` | Muted surface color |
| `--muted-foreground` | `215.4 16.3% 46.9%` | `270 20% 80%` | Muted text color |
| `--accent` | `210 40% 96.1%` | `270 40% 50%` | Accent surface color |
| `--accent-foreground` | `222.2 47.4% 11.2%` | `210 40% 98%` | Accent text color |
| `--destructive` | `0 84.2% 60.2%` | `0 84.2% 60.2%` (unchanged) | Destructive action color |
| `--destructive-foreground` | `210 40% 98%` | `210 40% 98%` (unchanged) | Destructive action text |
| `--border` | `214.3 31.8% 91.4%` | `270 30% 55%` | Border color |
| `--input` | `214.3 31.8% 91.4%` | `270 30% 55%` | Input border color |
| `--ring` | `222.2 84% 4.9%` | `210 40% 98%` | Focus ring color |

### Modified Tokens — Dark Mode (`.dark`)

| Token | Current Value | New Value | Description |
|-------|--------------|-----------|-------------|
| `--background` | `222.2 84% 4.9%` (dark blue) | `270 50% 20%` (deep purple) | Primary background surface |
| `--foreground` | `210 40% 98%` | `210 40% 98%` (unchanged) | Primary text color |
| `--card` | `222.2 84% 4.9%` | `270 50% 25%` (slightly lighter purple) | Card surface background |
| `--card-foreground` | `210 40% 98%` | `210 40% 98%` (unchanged) | Card text color |
| `--popover` | `222.2 84% 4.9%` | `270 50% 25%` | Popover surface background |
| `--popover-foreground` | `210 40% 98%` | `210 40% 98%` (unchanged) | Popover text color |
| `--primary` | `210 40% 98%` | `210 40% 98%` (unchanged) | Primary action color |
| `--primary-foreground` | `222.2 47.4% 11.2%` | `270 50% 20%` | Primary action text |
| `--secondary` | `217.2 32.6% 17.5%` | `270 40% 30%` | Secondary surface color |
| `--secondary-foreground` | `210 40% 98%` | `210 40% 98%` (unchanged) | Secondary surface text |
| `--muted` | `217.2 32.6% 17.5%` | `270 30% 30%` | Muted surface color |
| `--muted-foreground` | `215 20.2% 65.1%` | `270 20% 70%` | Muted text color |
| `--accent` | `217.2 32.6% 17.5%` | `270 40% 30%` | Accent surface color |
| `--accent-foreground` | `210 40% 98%` | `210 40% 98%` (unchanged) | Accent text color |
| `--destructive` | `0 62.8% 30.6%` | `0 62.8% 30.6%` (unchanged) | Destructive action color |
| `--destructive-foreground` | `210 40% 98%` | `210 40% 98%` (unchanged) | Destructive text color |
| `--border` | `217.2 32.6% 17.5%` | `270 30% 35%` | Border color |
| `--input` | `217.2 32.6% 17.5%` | `270 30% 35%` | Input border color |
| `--ring` | `212.7 26.8% 83.9%` | `270 30% 70%` | Focus ring color |

### Unchanged Token

| Token | Value | Scope |
|-------|-------|-------|
| `--radius` | `0.5rem` | Both modes |

## Relationships

```
index.css (:root / .dark)
├── --background → Tailwind bg-background → body, App.tsx container, header, select options
├── --foreground → Tailwind text-foreground → body, all text elements
├── --card → Tailwind bg-card → Card components
├── --popover → Tailwind bg-popover → Popover, dropdown components
├── --primary → Tailwind bg-primary → Button (default variant)
├── --secondary → Tailwind bg-secondary → Button (secondary variant), badges
├── --muted → Tailwind bg-muted → Muted surfaces, disabled states
├── --accent → Tailwind bg-accent → Hover/focus highlights
├── --destructive → Tailwind bg-destructive → Destructive buttons/alerts
├── --border → Tailwind border-border → All borders (via * { @apply border-border })
├── --input → Tailwind border-input → Input field borders
└── --ring → Tailwind ring-ring → Focus ring outlines
```

## Validation Rules

- All `--*-foreground` tokens must achieve ≥ 4.5:1 contrast ratio against their corresponding surface token (WCAG AA).
- HSL values must use the space-separated format without the `hsl()` wrapper (e.g., `270 50% 40%`, not `hsl(270, 50%, 40%)`), as required by the Tailwind `hsl(var(--token))` consumption pattern.
- Hue values must remain in the purple family (260°–280°) across all purple-based tokens.

## Schema Changes

**None.** No database migrations, no API contract changes, no new backend endpoints.
