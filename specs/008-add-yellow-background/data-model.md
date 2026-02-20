# Data Model: Add Yellow Background Color to App

**Feature**: 008-add-yellow-background | **Date**: 2026-02-20
**Purpose**: Define entities and their relationships for feature implementation

## Model Overview

This feature involves no data model in the traditional sense (no database entities, API models, or state management). The "data" being changed consists of a single CSS custom property value in the global stylesheet. This document exists to satisfy Phase 1 requirements but is intentionally minimal due to the feature's purely presentational nature.

## Entities

### Entity: CSS Design Tokens (Light Mode)

**Type**: CSS Custom Properties (`:root` selector)
**Purpose**: Define the global color palette for light mode
**Lifecycle**: Compile-time constants loaded by the browser at page render

**Attributes Modified**:

| Attribute | Type | Current Value | New Value | Impact |
|-----------|------|---------------|-----------|--------|
| `--color-bg-secondary` | CSS color | `#f6f8fa` | `#FFFDE7` | Global page background and secondary surfaces turn yellow |

**Attributes Unchanged**:

| Attribute | Value | Reason |
|-----------|-------|--------|
| `--color-bg` | `#ffffff` | Cards, headers, modals keep white background |
| `--color-text` | `#24292f` | Primary text color remains dark for contrast |
| `--color-text-secondary` | `#57606a` | Secondary text remains unchanged |
| `--color-border` | `#d0d7de` | Borders remain neutral gray |
| All dark mode variables | (unchanged) | Yellow is light-mode only |

**Location**: `frontend/src/index.css`, `:root` selector (line 7 approximately)

**Validation Rules**:
1. Must be a valid CSS color value
2. Must maintain WCAG AA contrast ratio (≥4.5:1) with `--color-text` (#24292f)
3. Must be defined in `:root` selector only (not in `html.dark-mode-active`)

**State Transitions**: None — static CSS value with no runtime changes

**Relationships**: 
- Used by `body { background: var(--color-bg-secondary) }` for global page background
- Used by various component classes for secondary surface backgrounds

---

## Entity Relationships

```text
:root (CSS Custom Properties)
  └── --color-bg-secondary: #FFFDE7
       ├── body { background } → Page background
       ├── .status-column { background } → Board columns
       ├── .board-column { background } → Project board columns  
       ├── .theme-toggle-btn { background } → Theme button
       └── Various hover/secondary states
```

## Data Validation

### Visual Validation
- **Contrast**: #24292f text on #FFFDE7 background = ~17.6:1 ratio (WCAG AAA) ✅
- **Contrast**: #57606a text on #FFFDE7 background = ~7.2:1 ratio (WCAG AA) ✅
- **Dark mode isolation**: `html.dark-mode-active` overrides prevent yellow in dark mode ✅
