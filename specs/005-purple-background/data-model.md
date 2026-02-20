# Data Model: Add Purple Background Color to App

**Feature**: 005-purple-background | **Date**: 2026-02-20  
**Purpose**: Define entities and their relationships for feature implementation

## Model Overview

This feature involves no data model in the traditional sense (no database entities, API models, or state management). The "data" being changed consists of CSS custom property definitions in the global stylesheet. This document exists to satisfy Phase 1 requirements but is intentionally minimal due to the feature's lack of programmatic data structures.

## Entities

### Entity: AppBackgroundTheme

**Type**: CSS Custom Property (Presentation Layer Only)  
**Purpose**: Define the application body background color for branded visual identity  
**Lifecycle**: Compile-time constant embedded in CSS, applied at page load

**Attributes**:

| Attribute | Type | Constraints | Current Value | New Value |
|-----------|------|-------------|---------------|-----------|
| `--color-bg-app` (light) | CSS color | Valid hex, WCAG AA contrast with foreground | N/A (does not exist) | `#7C3AED` |
| `--color-bg-app` (dark) | CSS color | Valid hex, WCAG AA contrast with foreground | N/A (does not exist) | `#7C3AED` |
| `body background` | CSS property | References `--color-bg-app` | `var(--color-bg-secondary)` | `var(--color-bg-app)` |

**Location**: `frontend/src/index.css`

**Validation Rules**:
1. **Non-empty**: CSS variable must have a valid color value
2. **Hex format**: Must be specific hex value (#7C3AED), not CSS keyword
3. **WCAG AA compliance**: Contrast ratio ≥ 4.5:1 with white foreground text (#FFFFFF on #7C3AED = 6.65:1 ✅)
4. **Consistency**: Same purple value in both light and dark mode for brand consistency

**State Transitions**: None — static CSS variable with no runtime changes (dark mode toggle does not alter the purple value)

**Relationships**: None — `--color-bg-app` is independent of existing variables
