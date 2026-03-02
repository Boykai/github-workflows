# Data Model: Add Green Background Color to App

**Feature**: 016-green-background  
**Date**: 2026-03-02  
**Depends on**: research.md (R1, R2, R3, R4)

## Entities

### Design Tokens (CSS Custom Properties)

This feature modifies existing design tokens rather than introducing new database entities. The "data model" for this feature is the set of CSS custom properties that define the application's color scheme.

#### Modified Token: `--background`

| Property | Current Value (Light) | New Value (Light) | Description |
|----------|-----------------------|-------------------|-------------|
| `--background` | `0 0% 100%` (white, #FFFFFF) | `122 39% 49%` (green, #4CAF50) | Global page background color |

#### Unchanged Tokens (Verified Isolated)

These tokens are **not modified** but are documented here to confirm they are isolated from the `--background` change per FR-004:

| Token | Light Mode Value | Purpose | Affected by Change? |
|-------|-----------------|---------|---------------------|
| `--foreground` | `222.2 84% 4.9%` | Global text color | No — contrast ratio ~8.6:1 against new green ✅ |
| `--card` | `0 0% 100%` | Card component background | No — independently defined |
| `--card-foreground` | `222.2 84% 4.9%` | Card text color | No |
| `--popover` | `0 0% 100%` | Popover/dropdown background | No — independently defined |
| `--popover-foreground` | `222.2 84% 4.9%` | Popover text color | No |
| `--primary` | `222.2 47.4% 11.2%` | Primary button/action color | No |
| `--secondary` | `210 40% 96.1%` | Secondary element background | No |
| `--muted` | `210 40% 96.1%` | Muted element background | No |
| `--accent` | `210 40% 96.1%` | Accent element background | No |
| `--destructive` | `0 84.2% 60.2%` | Destructive action color | No |
| `--border` | `214.3 31.8% 91.4%` | Border color | No |

#### Dark Mode Tokens (Unchanged)

| Token | Dark Mode Value | Notes |
|-------|----------------|-------|
| `--background` | `222.2 84% 4.9%` | Remains dark navy; green applies to light mode only (see research.md R3) |
| `--foreground` | `210 40% 98%` | Remains light text for dark mode |

## Validation Rules

- The `--background` value MUST be a valid HSL triplet (hue 0-360, saturation 0-100%, lightness 0-100%)
- The contrast ratio between `--background` and `--foreground` MUST be ≥ 4.5:1 (WCAG AA normal text)
- The contrast ratio between `--background` and `--foreground` MUST be ≥ 3:1 (WCAG AA large text)

## State Transitions

N/A — This is a static CSS configuration change with no runtime state transitions.

## Relationships

```
--background (modified)
├── consumed by: body { @apply bg-background }     (index.css base layer)
├── consumed by: <div className="bg-background">    (App.tsx root container)
├── consumed by: <header className="bg-background"> (App.tsx header)
└── NOT consumed by: --card, --popover, --primary, etc. (independent tokens)
```

## Migration

No database migration required. The change is a CSS-only modification to `frontend/src/index.css`.
