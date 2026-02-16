# CSS Changes Contract: White Background Interface

**Feature**: 002-white-background  
**Date**: 2026-02-16  
**Purpose**: Document exact CSS changes required to implement white background across application

## Overview

This contract specifies the minimal CSS modifications needed to achieve a consistent white (#FFFFFF) background throughout the application. Changes leverage existing CSS custom property infrastructure.

## File 1: frontend/src/index.css

### Change 1.1: Update Secondary Background Color

**Location**: Line 9 (`:root` selector)

**Before**:
```css
:root {
  --color-primary: #0969da;
  --color-secondary: #6e7781;
  --color-success: #1a7f37;
  --color-warning: #9a6700;
  --color-danger: #cf222e;
  --color-bg: #ffffff;
  --color-bg-secondary: #f6f8fa;  /* ← CHANGE THIS */
  --color-border: #d0d7de;
  --color-text: #24292f;
  --color-text-secondary: #57606a;
  --radius: 6px;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
```

**After**:
```css
:root {
  --color-primary: #0969da;
  --color-secondary: #6e7781;
  --color-success: #1a7f37;
  --color-warning: #9a6700;
  --color-danger: #cf222e;
  --color-bg: #FFFFFF;
  --color-bg-secondary: #FFFFFF;  /* ← CHANGED TO PURE WHITE */
  --color-border: #d0d7de;
  --color-text: #24292f;
  --color-text-secondary: #57606a;
  --radius: 6px;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
```

**Rationale**: Changes `--color-bg-secondary` from light gray (#f6f8fa) to pure white (#FFFFFF) to ensure all surfaces, cards, and secondary backgrounds are consistently white per specification.

**Impact**: Affects ~15 components that use `var(--color-bg-secondary)`:
- `body { background: var(--color-bg-secondary); }`
- `.theme-toggle-btn { background: var(--color-bg-secondary); }`
- `.logout-button { background: var(--color-bg-secondary); }`
- `.status-column { background: var(--color-bg-secondary); }`
- And others

### Change 1.2: Explicit Primary Background (Optional Clarification)

**Location**: Line 8 (`:root` selector)

**Current**: `--color-bg: #ffffff;` (lowercase)

**Recommended**: `--color-bg: #FFFFFF;` (uppercase for consistency)

**Rationale**: While functionally identical, uppercase hex codes match the specification's explicit "#FFFFFF" notation. This is a stylistic consistency improvement, not functionally required.

**Impact**: None (color value is identical)

## Summary

**Total Files Modified**: 1 (`frontend/src/index.css`)  
**Total Lines Changed**: 1 (line 9)  
**Optional Clarifications**: 1 (line 8 uppercase)  
**Risk Level**: Low (single CSS variable change)  
**Rollback Complexity**: Trivial (one-line revert)
