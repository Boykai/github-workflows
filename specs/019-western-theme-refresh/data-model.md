# Data Model: Western/Cowboy UI Theme Refresh

**Phase**: 1 — Design & Contracts  
**Branch**: `019-western-theme-refresh`

## Overview

This feature has no traditional data model (no database entities, API models, or persistent state). The "data model" is the **Design Token System** — the set of CSS custom properties that define the visual language of the application. These tokens are the single source of truth for colors, typography, spacing, and shadows.

---

## Entity: Design Token Set (Light Mode)

**Source**: `frontend/src/index.css` → `:root` block  
**Format**: HSL triplets consumed by Tailwind via `hsl(var(--token))`

### Color Tokens

| Token | Type | Value (HSL) | Hex Equiv | Validation Rule |
|-------|------|-------------|-----------|-----------------|
| `--background` | Background | `39 50% 96%` | #F5EFE0 | Must provide ≥4.5:1 contrast with `--foreground` |
| `--foreground` | Text | `24 30% 15%` | #3B2D1F | Primary readable text color |
| `--card` | Surface | `39 40% 97%` | #F7F2E8 | Must be distinguishable from `--background` |
| `--card-foreground` | Text | `24 30% 15%` | #3B2D1F | Same as `--foreground` |
| `--popover` | Surface | `39 40% 97%` | #F7F2E8 | Same as `--card` |
| `--popover-foreground` | Text | `24 30% 15%` | #3B2D1F | Same as `--foreground` |
| `--primary` | Interactive | `24 50% 22%` | #55351A | Saddle brown for CTAs |
| `--primary-foreground` | Text | `40 60% 95%` | #F8F0DC | Text on primary surfaces |
| `--secondary` | Surface | `33 30% 88%` | #E8DCC8 | Light tan for secondary areas |
| `--secondary-foreground` | Text | `24 30% 20%` | #42321F | Dark brown on tan |
| `--muted` | Surface | `35 25% 90%` | #EBE4D6 | Pale wheat for muted areas |
| `--muted-foreground` | Text | `24 15% 45%` | #6B5D50 | Dusty brown secondary text |
| `--accent` | Interactive | `36 80% 55%` | #D4A017 | Sunset gold for accents |
| `--accent-foreground` | Text | `24 50% 15%` | #3A2410 | Dark brown on gold |
| `--destructive` | Semantic | `0 60% 45%` | #B84233 | Terra-cotta red |
| `--destructive-foreground` | Text | `40 60% 95%` | #F8F0DC | Cream on red |
| `--border` | Border | `30 20% 80%` | #D4C8B8 | Warm tan border |
| `--input` | Border | `30 20% 82%` | #D9CEC0 | Input border |
| `--ring` | Focus | `36 80% 55%` | #D4A017 | Gold focus ring |

### Layout Token

| Token | Type | Value | Notes |
|-------|------|-------|-------|
| `--radius` | Spacing | `0.375rem` | Slightly less rounded (was 0.5rem) |

---

## Entity: Design Token Set (Dark Mode)

**Source**: `frontend/src/index.css` → `.dark` block  
**Format**: Same HSL triplet format

| Token | Type | Value (HSL) | Hex Equiv | Notes |
|-------|------|-------------|-----------|-------|
| `--background` | Background | `24 30% 10%` | #1E1610 | Deep espresso (not black) |
| `--foreground` | Text | `39 40% 90%` | #EDE4D1 | Warm off-white |
| `--card` | Surface | `24 25% 14%` | #2A2018 | Elevated dark brown |
| `--card-foreground` | Text | `39 40% 90%` | #EDE4D1 | Match foreground |
| `--popover` | Surface | `24 25% 14%` | #2A2018 | Match card |
| `--popover-foreground` | Text | `39 40% 90%` | #EDE4D1 | Match foreground |
| `--primary` | Interactive | `36 80% 55%` | #D4A017 | Gold primary on dark |
| `--primary-foreground` | Text | `24 30% 10%` | #1E1610 | Dark text on gold |
| `--secondary` | Surface | `24 20% 20%` | #3D3228 | Warm dark gray-brown |
| `--secondary-foreground` | Text | `39 40% 90%` | #EDE4D1 | Light text |
| `--muted` | Surface | `24 20% 18%` | #372D24 | Muted dark surface |
| `--muted-foreground` | Text | `24 15% 60%` | #A49585 | Dusty tan |
| `--accent` | Interactive | `36 80% 55%` | #D4A017 | Gold accent |
| `--accent-foreground` | Text | `24 30% 10%` | #1E1610 | Dark on gold |
| `--destructive` | Semantic | `0 50% 40%` | #993333 | Muted terra-cotta |
| `--destructive-foreground` | Text | `39 40% 90%` | #EDE4D1 | Cream on red |
| `--border` | Border | `24 20% 25%` | #4D3F33 | Warm dark border |
| `--input` | Border | `24 20% 25%` | #4D3F33 | Match border |
| `--ring` | Focus | `36 80% 55%` | #D4A017 | Gold |

---

## Entity: Typography Configuration

**Source**: `frontend/tailwind.config.js` → `theme.extend.fontFamily` + `frontend/index.html` → Google Fonts `<link>`

| Property | Value | Fallback Chain | Usage |
|----------|-------|----------------|-------|
| `fontFamily.display` | `'Rye'` | `'Georgia', serif` | h1, h2, h3, branding text |
| `fontFamily.sans` | `'Inter'` | `'system-ui', 'sans-serif'` | Body text, labels, UI elements |

**CSS Base Rule** (in `index.css`):
```css
h1, h2, h3 { font-family: theme('fontFamily.display'); }
```

---

## Entity: Warm Shadow System

**Source**: `frontend/tailwind.config.js` → `theme.extend.boxShadow`

| Token | Value | Usage |
|-------|-------|-------|
| `shadow-warm-sm` | `0 1px 2px 0 rgba(59,45,31,0.08)` | Default card shadow |
| `shadow-warm` | `0 1px 3px 0 rgba(59,45,31,0.12), 0 1px 2px -1px rgba(59,45,31,0.12)` | Standard elevation |
| `shadow-warm-md` | `0 4px 6px -1px rgba(59,45,31,0.12), 0 2px 4px -2px rgba(59,45,31,0.12)` | Hover/elevated state |
| `shadow-warm-lg` | `0 10px 15px -3px rgba(59,45,31,0.12), 0 4px 6px -4px rgba(59,45,31,0.12)` | Modals, popovers |

**Tint color**: `rgb(59,45,31)` — matches `--foreground` dark brown for cohesive warm shadows.

---

## Entity: Hardcoded Color Inventory

**Source**: Grep audit of all `frontend/src/components/**/*.tsx` files  
**See**: [research.md → RT-4](research.md) for full disposition decisions

| Disposition | Count | Action |
|-------------|-------|--------|
| KEEP | ~20 instances in 5 files | Retain standard semantic colors (system status) |
| REPLACE | ~70 instances in 13 files | Switch to theme tokens or adjusted shades |
| SOFTEN | ~30 instances in 5 files | Shift shade darker (-600) for cream contrast |

---

## State Transitions

N/A — This feature modifies visual presentation only. No state machines, workflows, or data transitions are involved. The existing ThemeProvider light/dark toggle works unchanged; only the CSS variable values it controls are redefined.

## Relationships

```
index.css (:root / .dark)
    │
    ├── tailwind.config.js (reads CSS vars via hsl(var(--token)))
    │       │
    │       ├── All shadcn/ui components (auto-inherit via Tailwind classes)
    │       │       ├── button.tsx (bg-primary, text-primary-foreground, etc.)
    │       │       ├── card.tsx (bg-card, border, shadow)
    │       │       └── input.tsx (border-input, bg-background, ring-ring)
    │       │
    │       └── All page/feature components using Tailwind classes
    │               ├── Components using ONLY theme classes → auto-update
    │               └── Components with hardcoded colors → manual update needed
    │
    └── ThemeProvider.tsx (toggles .dark class on <html>)
            └── Triggers CSS variable swap (no code change needed)
```
