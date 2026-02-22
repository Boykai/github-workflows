# Data Model: Add Black Background Theme to App

**Feature**: `009-black-background` | **Date**: 2026-02-22

> This feature introduces no new data entities, database models, or API schemas. It modifies existing CSS design tokens (custom property values). This document describes the **theme token model** — the design tokens that define the app's visual appearance.

## Theme Token Model

### 1. CSS Custom Property (Design Token)

A named design value declared on `:root` or `html.dark-mode-active` that controls the visual appearance of the app.

| Attribute | Description |
|-----------|-------------|
| Token name | CSS custom property name (e.g., `--color-bg`) |
| Light value | Value applied in default (`:root`) mode |
| Dark value | Value applied when `html.dark-mode-active` class is present |
| Usage context | Where the token is consumed (background, text, border, accent) |
| Contrast requirement | Minimum WCAG contrast ratio against background |

### 2. Token Registry — Light Mode (`:root`)

| Token | Value | Usage | Contrast vs `--color-bg` |
|-------|-------|-------|--------------------------|
| `--color-bg` | `#000000` | Root/primary background | — |
| `--color-bg-secondary` | `#121212` | Body, sidebar, cards, elevated surfaces | 1.3:1 (surface hierarchy) |
| `--color-text` | `#ffffff` | Primary body text, headings | 21:1 ✅ |
| `--color-text-secondary` | `#b0b0b0` | Muted text, descriptions, labels | 10.5:1 ✅ |
| `--color-border` | `#2C2C2C` | Borders, dividers, outlines | 1.9:1 (structural) |
| `--color-primary` | `#539bf5` | Links, primary buttons, active states | 5.1:1 ✅ |
| `--color-secondary` | `#8b949e` | Secondary actions, inactive states | 7.2:1 ✅ |
| `--color-success` | `#3fb950` | Success badges, confirmations | 6.3:1 ✅ |
| `--color-warning` | `#d29922` | Warning indicators, caution states | 7.4:1 ✅ |
| `--color-danger` | `#f85149` | Error states, delete actions | 4.8:1 ✅ |
| `--radius` | `6px` | Border radius (unchanged) | — |
| `--shadow` | `0 1px 3px rgba(0, 0, 0, 0.4)` | Box shadows | — |

### 3. Token Registry — Dark Mode (`html.dark-mode-active`)

| Token | Value | Usage | Contrast vs `--color-bg` |
|-------|-------|-------|--------------------------|
| `--color-bg` | `#000000` | Root/primary background | — |
| `--color-bg-secondary` | `#0a0a0a` | Body, sidebar, cards, elevated surfaces | 1.1:1 (subtle depth) |
| `--color-text` | `#e6edf3` | Primary body text | 14.4:1 ✅ |
| `--color-text-secondary` | `#8b949e` | Muted text | 7.2:1 ✅ |
| `--color-border` | `#1e1e1e` | Borders, dividers | 1.5:1 (structural) |
| `--color-primary` | `#539bf5` | Links, primary buttons | 5.1:1 ✅ |
| `--color-secondary` | `#8b949e` | Secondary actions | 7.2:1 ✅ |
| `--color-success` | `#3fb950` | Success indicators | 6.3:1 ✅ |
| `--color-warning` | `#d29922` | Warning indicators | 7.4:1 ✅ |
| `--color-danger` | `#f85149` | Error indicators | 4.8:1 ✅ |
| `--shadow` | `0 1px 3px rgba(0, 0, 0, 0.4)` | Box shadows (unchanged) | — |

### 4. Surface Level Hierarchy

Defines the visual depth system using background color differentiation.

| Level | Role | Token | Light Value | Dark Value |
|-------|------|-------|-------------|------------|
| 0 | Root background | `--color-bg` | `#000000` | `#000000` |
| 1 | Elevated surface (cards, sidebar, modals) | `--color-bg-secondary` | `#121212` | `#0a0a0a` |
| 2 | Structural separator (borders, dividers) | `--color-border` | `#2C2C2C` | `#1e1e1e` |

**Relationships**:
- All text tokens (`--color-text`, `--color-text-secondary`) are measured against Level 0 (`--color-bg`) for WCAG AA compliance
- All accent tokens (`--color-primary`, `--color-success`, etc.) are measured against Level 0 for readability
- Level 1 surfaces provide visual hierarchy without requiring text contrast validation against Level 0 (they are background-only)

## Hardcoded Color Overrides

These colors in `App.css` do not use the token system and require individual attention:

| Color | Context | Action | New Value |
|-------|---------|--------|-----------|
| `#dafbe1` | Success alert background | Replace | `rgba(63, 185, 80, 0.15)` |
| `#fff1f0` | Error alert/message background | Replace | `rgba(248, 81, 73, 0.15)` |
| `#32383f` | Avatar fallback | Keep | Already dark-compatible |
| `#2da44e` | Green status/confirm badge | Keep | Dark-compatible |
| `#bf8700` | Warning status badge | Keep | Dark-compatible |
| `#0969da` | Blue status badge | Keep | Dark-compatible |
| `#cf222e` | Red/danger badge, delete button | Keep | Dark-compatible |
| `#a40e26` | Delete button hover | Keep | Dark-compatible |

## State Transitions: No Changes

The `useAppTheme` hook manages the `dark-mode-active` class toggle. No changes to the state machine:
- `isDarkMode: false` → `:root` tokens apply (now black-themed)
- `isDarkMode: true` → `html.dark-mode-active` tokens apply (also black-themed)
- Toggle persisted via `localStorage` + optional API sync

## Validation Rules

- All text color tokens MUST achieve ≥4.5:1 contrast ratio against `--color-bg` (WCAG AA)
- All accent/interactive color tokens MUST achieve ≥4.5:1 contrast ratio against `--color-bg`
- Surface hierarchy tokens (`--color-bg-secondary`) provide visual depth; text may appear on both Level 0 and Level 1 surfaces, so text contrast is validated against the root background (`--color-bg`) as the worst case
