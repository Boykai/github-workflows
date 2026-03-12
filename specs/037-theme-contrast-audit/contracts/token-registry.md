# Token Registry: Celestial Design System — Light/Dark Theme Tokens

**Feature**: `037-theme-contrast-audit` | **Date**: 2026-03-12

## Purpose

Living reference of all Celestial design-system theme tokens. Updated during the theme audit to reflect current state, any corrections, and new tokens introduced.

---

## Core Surface Tokens

| Token | Light Value (HSL) | Dark Value (HSL) | Category | Usage |
|-------|-------------------|-------------------|----------|-------|
| `--background` | `41 82% 95%` | `236 28% 7%` | background | Page background |
| `--foreground` | `228 24% 16%` | `38 45% 89%` | text | Default body text |
| `--card` | `40 88% 97%` | `238 22% 11%` | background | Card surfaces |
| `--card-foreground` | `228 24% 16%` | `38 45% 89%` | text | Card body text |
| `--popover` | `39 82% 96%` | `238 23% 9%` | background | Popover/dropdown surfaces |
| `--popover-foreground` | `228 24% 16%` | `38 45% 89%` | text | Popover body text |
| `--panel` | `40 78% 95%` | `238 19% 11%` | background | Panel/sidebar surfaces |
| `--panel-foreground` | `228 24% 16%` | `38 45% 89%` | text | Panel body text |

## Interactive Tokens

| Token | Light Value (HSL) | Dark Value (HSL) | Category | Usage |
|-------|-------------------|-------------------|----------|-------|
| `--primary` | `42 90% 48%` | `45 90% 68%` | accent | Primary actions, links, highlights |
| `--primary-foreground` | `32 36% 12%` | `236 28% 9%` | text | Text on primary surfaces |
| `--secondary` | `38 52% 89%` | `237 14% 17%` | background | Secondary action backgrounds |
| `--secondary-foreground` | `228 16% 24%` | `38 45% 89%` | text | Text on secondary surfaces |
| `--accent` | `230 34% 40%` | `242 28% 25%` | accent | Accent highlights, active states |
| `--accent-foreground` | `40 90% 97%` | `38 45% 89%` | text | Text on accent surfaces |
| `--destructive` | `0 72% 51%` | `0 65% 53%` | status | Destructive/error actions |
| `--destructive-foreground` | `0 0% 100%` | `240 10% 92%` | text | Text on destructive surfaces |

## Utility Tokens

| Token | Light Value (HSL) | Dark Value (HSL) | Category | Usage |
|-------|-------------------|-------------------|----------|-------|
| `--muted` | `39 44% 90%` | `237 16% 13%` | background | Muted/subtle backgrounds |
| `--muted-foreground` | `228 10% 40%` | `35 24% 72%` | text | Muted/placeholder text |
| `--border` | `37 34% 78%` | `239 16% 24%` | border | Default borders |
| `--input` | `39 50% 93%` | `238 18% 15%` | background | Input field backgrounds |
| `--ring` | `42 90% 48%` | `45 90% 68%` | interactive | Focus ring indicator |

## Celestial Tokens

| Token | Light Value (HSL) | Dark Value (HSL) | Category | Usage |
|-------|-------------------|-------------------|----------|-------|
| `--glow` | `47 100% 79%` | `45 82% 72%` | accent | Golden glow effects |
| `--gold` | `42 92% 52%` | `45 92% 67%` | accent | Gold accent elements |
| `--night` | `226 28% 19%` | `235 34% 5%` | background | Deep background (dark surfaces) |
| `--star` | `38 72% 42%` | `43 76% 92%` | accent | Star/highlight accents |
| `--star-soft` | `43 84% 62%` | `44 86% 74%` | accent | Soft star accents |

## Status Tokens

| Token | Light Value (HSL) | Dark Value (HSL) | Category | Usage |
|-------|-------------------|-------------------|----------|-------|
| `--priority-p0` | `0 72% 51%` | `0 72% 51%` | status | Critical priority (red) |
| `--priority-p1` | `25 95% 53%` | `25 95% 53%` | status | High priority (orange) |
| `--priority-p2` | `217 91% 60%` | `217 91% 60%` | status | Medium priority (blue) |
| `--priority-p3` | `142 71% 45%` | `142 71% 45%` | status | Low priority (green) |
| `--sync-connected` | `160 84% 39%` | `160 84% 47%` | status | Connected (teal) |
| `--sync-polling` | `38 92% 50%` | `38 92% 56%` | status | Polling (golden) |
| `--sync-connecting` | `199 89% 48%` | `199 89% 56%` | status | Connecting (cyan) |
| `--sync-disconnected` | `0 84% 60%` | `0 84% 65%` | status | Disconnected (red) |

## Layout Token

| Token | Light Value | Dark Value | Category | Usage |
|-------|-------------|------------|----------|-------|
| `--radius` | `1rem` | `1rem` | layout | Default border radius |

## Shadow Tokens (defined in `@theme` block)

| Token | Value | Theme-Aware | Notes |
|-------|-------|-------------|-------|
| `--shadow-sm` | `0 10px 26px rgba(41, 29, 12, 0.08)` | ❌ No | Warm brown; needs dark-mode override |
| `--shadow-default` | `0 18px 44px rgba(41, 29, 12, 0.12)` | ❌ No | Warm brown; needs dark-mode override |
| `--shadow-md` | `0 26px 58px rgba(29, 21, 10, 0.16)` | ❌ No | Warm brown; needs dark-mode override |
| `--shadow-lg` | `0 34px 84px rgba(9, 8, 18, 0.24)` | ❌ No | Cool dark; less impacted but should verify |

## Tailwind @theme Mappings

| Tailwind Variable | CSS Custom Property | Type |
|-------------------|--------------------|----|
| `--color-background` | `hsl(var(--background))` | color |
| `--color-foreground` | `hsl(var(--foreground))` | color |
| `--color-primary` | `hsl(var(--primary))` | color |
| `--color-primary-foreground` | `hsl(var(--primary-foreground))` | color |
| `--color-secondary` | `hsl(var(--secondary))` | color |
| `--color-secondary-foreground` | `hsl(var(--secondary-foreground))` | color |
| `--color-destructive` | `hsl(var(--destructive))` | color |
| `--color-destructive-foreground` | `hsl(var(--destructive-foreground))` | color |
| `--color-muted` | `hsl(var(--muted))` | color |
| `--color-muted-foreground` | `hsl(var(--muted-foreground))` | color |
| `--color-accent` | `hsl(var(--accent))` | color |
| `--color-accent-foreground` | `hsl(var(--accent-foreground))` | color |
| `--color-popover` | `hsl(var(--popover))` | color |
| `--color-popover-foreground` | `hsl(var(--popover-foreground))` | color |
| `--color-card` | `hsl(var(--card))` | color |
| `--color-card-foreground` | `hsl(var(--card-foreground))` | color |
| `--color-border` | `hsl(var(--border))` | color |
| `--color-input` | `hsl(var(--input))` | color |
| `--color-ring` | `hsl(var(--ring))` | color |
| `--color-panel` | `hsl(var(--panel))` | color |
| `--color-panel-foreground` | `hsl(var(--panel-foreground))` | color |
| `--color-glow` | `hsl(var(--glow))` | color |
| `--color-gold` | `hsl(var(--gold))` | color |
| `--color-night` | `hsl(var(--night))` | color |

## Solar Utility Classes

| Class | Type | Light Appearance | Dark Override |
|-------|------|-----------------|--------------|
| `.solar-chip` | base chip | Primary border, gradient bg | Uses CSS vars (auto-adapts) |
| `.solar-chip-soft` | soft chip | Subtle border, light gradient | Uses CSS vars (auto-adapts) |
| `.solar-chip-neutral` | neutral chip | Border-color, mixed gradient | Uses CSS vars (auto-adapts) |
| `.solar-chip-success` | success chip | Green border, green bg, dark green text `rgb(4 120 87)` | Text → `rgb(110 231 183)` |
| `.solar-chip-warning` | warning chip | Amber border, amber bg, amber text `rgb(180 83 9)` | Text → `rgb(253 224 71)` |
| `.solar-chip-danger` | danger chip | Red border, red bg, dark red text `rgb(185 28 28)` | Text → `rgb(252 165 165)` |
| `.solar-chip-violet` | violet chip | Purple border, purple bg, dark purple text `rgb(109 40 217)` | Text → `rgb(196 181 253)` |
| `.solar-text-success` | text utility | Dark green text `rgb(4 120 87)` | Light green text `rgb(110 231 183)` |
| `.solar-action` | action button | Neutral border, gradient bg | Uses CSS vars (auto-adapts) |
| `.solar-action-danger` | danger action | Red border, red bg, dark red text `rgb(185 28 28)` | Text → `rgb(252 165 165)` |
| `.solar-halo` | halo effect | Glow radial gradient | Uses CSS vars (auto-adapts) |

## Change Log

| Date | Token | Change | Reason |
|------|-------|--------|--------|
| — | — | Initial audit baseline | Pre-audit documentation |
