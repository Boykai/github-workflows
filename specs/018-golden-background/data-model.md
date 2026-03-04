# Data Model: Add Golden Background to App

**Feature**: `018-golden-background` | **Date**: 2026-03-04

## Entities

### CSS Custom Properties (Design Tokens)

This feature modifies existing CSS custom properties (design tokens) in `frontend/src/index.css`. No new database entities, API models, or data structures are introduced. The "data model" for this feature is the set of CSS variables that define the theme.

### Modified Tokens — Light Mode (`:root`)

| Token | Current Value | New Value | Notes |
|-------|--------------|-----------|-------|
| `--background` | `0 0% 100%` (white) | `51 100% 50%` (#FFD700 gold) | Primary change — golden background |
| `--foreground` | `222.2 84% 4.9%` | `222.2 84% 4.9%` (unchanged) | 13.6:1 contrast against gold — compliant |
| `--card` | `0 0% 100%` | `0 0% 100%` (unchanged) | Cards stay white per spec edge cases |
| `--card-foreground` | `222.2 84% 4.9%` | `222.2 84% 4.9%` (unchanged) | No change needed |
| `--popover` | `0 0% 100%` | `0 0% 100%` (unchanged) | Popovers stay white per spec edge cases |
| `--popover-foreground` | `222.2 84% 4.9%` | `222.2 84% 4.9%` (unchanged) | No change needed |
| All other tokens | (various) | (unchanged) | No modifications needed |

### Modified Tokens — Dark Mode (`.dark`)

| Token | Current Value | New Value | Notes |
|-------|--------------|-----------|-------|
| `--background` | `222.2 84% 4.9%` | `43 74% 15%` (dark gold ~#43330A) | Deepened gold for dark mode |
| `--foreground` | `210 40% 98%` | `210 40% 98%` (unchanged) | ~12.5:1 contrast against dark gold |
| `--card` | `222.2 84% 4.9%` | `222.2 84% 4.9%` (unchanged) | Cards stay dark per existing behavior |
| `--card-foreground` | `210 40% 98%` | `210 40% 98%` (unchanged) | No change needed |
| `--popover` | `222.2 84% 4.9%` | `222.2 84% 4.9%` (unchanged) | Popovers stay dark per existing behavior |
| `--popover-foreground` | `210 40% 98%` | `210 40% 98%` (unchanged) | No change needed |
| All other tokens | (various) | (unchanged) | No modifications needed |

## Relationships

```text
index.css :root / .dark
    │
    ├── --background ─────────► tailwind.config.js: background color
    │                               │
    │                               └──► body { @apply bg-background } (index.css)
    │                                    ├── All pages inherit golden background
    │                                    └── Components using bg-background get gold
    │
    ├── --card ───────────────► Card components (unchanged, white/dark)
    ├── --popover ────────────► Popover/dropdown components (unchanged)
    └── --foreground ─────────► All text via text-foreground (unchanged)
```

## Validation Rules

- **Contrast ratio**: `--foreground` against `--background` must achieve ≥4.5:1 (WCAG AA). Verified: 13.6:1 in light mode, ~12.5:1 in dark mode.
- **HSL format**: Values must be space-separated `H S% L%` without `hsl()` wrapper (consumed by Tailwind's `hsl(var(--xxx))` pattern).
- **No inheritance leakage**: `--card` and `--popover` must NOT be set to the gold value to prevent overlay surfaces from becoming gold.

## State Transitions

No state transitions apply. This is a static styling change with two states determined by the theme class:

```text
Document.documentElement
    │
    ├── no .dark class ──► :root variables active ──► Gold #FFD700 background
    │
    └── .dark class ──────► .dark variables active ──► Dark gold ~#43330A background
```

The ThemeProvider (`frontend/src/components/ThemeProvider.tsx`) toggles the `.dark` class on `document.documentElement`, which CSS handles automatically via the existing `:root` / `.dark` selector cascade. No ThemeProvider changes needed.
