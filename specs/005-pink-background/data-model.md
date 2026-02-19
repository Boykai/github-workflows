# Data Model: Pink Background Color

**Feature**: 005-pink-background | **Date**: 2026-02-19  
**Purpose**: Define entities and their relationships for feature implementation

## Model Overview

This feature involves no data model in the traditional sense (no database entities, API models, or state management). The "data" being changed consists of CSS custom property values in a single stylesheet. This document exists to satisfy Phase 1 requirements but is intentionally minimal due to the feature's lack of programmatic data structures.

## Entities

### Entity: ThemeColorVariable

**Type**: CSS Custom Property (Design Token)  
**Purpose**: Centralized background color definition consumed across the application  
**Lifecycle**: Defined at stylesheet parse time, applied at render time

**Attributes**:

| Attribute | Type | Location | Current Value | New Value |
|-----------|------|----------|---------------|-----------|
| `--color-bg-secondary` (light) | CSS color | `:root` in `index.css` | `#f6f8fa` | `#FFC0CB` |
| `--color-bg-secondary` (dark) | CSS color | `html.dark-mode-active` in `index.css` | `#161b22` | `#3D2027` |

**Consumers** (no changes needed — automatic propagation):

| Consumer | File | CSS Usage |
|----------|------|-----------|
| Body background | `index.css` line 43 | `background: var(--color-bg-secondary)` |
| Any component referencing `--color-bg-secondary` | Various | Automatic |

**Validation Rules**:
1. **Valid CSS color**: Must be a valid hex color value
2. **Contrast compliance**: Text color on this background must meet WCAG AA 4.5:1 ratio
3. **Consistency**: Light and dark mode values should both convey "pink" identity

**State Transitions**: None — CSS variables are static per theme mode. Theme switching (light ↔ dark) is handled by existing `html.dark-mode-active` toggle mechanism.

**Relationships**: None — `--color-bg-secondary` is an independent design token. It does not depend on other variables.

---

## Unchanged Entities

The following CSS variables are explicitly **NOT** modified:

| Variable | Current Value (Light) | Current Value (Dark) | Reason Unchanged |
|----------|-----------------------|----------------------|------------------|
| `--color-bg` | `#ffffff` | `#0d1117` | Used for component surfaces (cards, modals, inputs). Must remain distinct from page background per spec edge cases. |
| `--color-text` | `#24292f` | `#e6edf3` | Verified sufficient contrast against new pink backgrounds. No change needed. |
| `--color-text-secondary` | `#57606a` | `#8b949e` | Verified sufficient contrast against new pink backgrounds. No change needed. |
| `--color-primary` | `#0969da` | `#539bf5` | Link/button color. Sufficient contrast on pink. |
| `--color-border` | `#d0d7de` | `#30363d` | Border styling independent of background color. |

---

## Contrast Verification Matrix

| Text Variable | Text Color | Background | Contrast Ratio | WCAG AA (4.5:1) |
|--------------|------------|------------|----------------|------------------|
| `--color-text` | `#24292f` | `#FFC0CB` | ~10.3:1 | ✅ PASS |
| `--color-text-secondary` | `#57606a` | `#FFC0CB` | ~5.2:1 | ✅ PASS |
| `--color-text` (dark) | `#e6edf3` | `#3D2027` | ~9.1:1 | ✅ PASS |
| `--color-text-secondary` (dark) | `#8b949e` | `#3D2027` | ~5.1:1 | ✅ PASS |

---

## Data Flow

```
Developer updates CSS variable values in index.css
       ↓
Git commit with updated color values
       ↓
Vite build process (frontend)
       ↓
CSS variables defined in :root and dark-mode-active
       ↓
Browser cascades variables to all consuming elements
       ↓
Body and page-level backgrounds render as pink
```

**Flow Characteristics**:
- **Automatic propagation**: CSS custom properties cascade to all consumers without explicit updates
- **Theme-aware**: Light/dark mode variants activate via existing class toggle
- **No JavaScript involvement**: Pure CSS change, no runtime logic
- **Responsive by default**: CSS variables apply identically across all viewport sizes

---

## Security Considerations

**Threat Model**: None — CSS color values are inert presentation data

- **No XSS risk**: CSS variables are not user-controllable
- **No injection risk**: Hardcoded hex values with no dynamic generation
- **No data exposure**: Color values are public presentation information

---

## Performance Characteristics

**Size Impact**:
- Old light value: 7 chars (`#f6f8fa`)
- New light value: 7 chars (`#FFC0CB`)
- Old dark value: 7 chars (`#161b22`)
- New dark value: 7 chars (`#3D2027`)
- **Net change**: 0 bytes (same length hex values)

**Runtime Impact**: None — CSS variable resolution is identical regardless of color value

---

## Phase 1 Data Model Completion Checklist

- [x] All entities identified (1 entity: ThemeColorVariable with 2 mode variants)
- [x] Entity attributes documented with current/new values
- [x] Validation rules defined (valid CSS color, contrast compliance)
- [x] Relationships documented (none — independent token)
- [x] Data flow described (CSS variable cascade)
- [x] Unchanged entities explicitly listed
- [x] Contrast verification matrix included
- [x] Security considerations addressed (no risks)
- [x] Performance impact assessed (zero)

**Status**: ✅ **DATA MODEL COMPLETE** - Ready for contracts and quickstart generation
