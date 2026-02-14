# CSS Variable Contracts

**Feature**: Silver Background Color  
**Phase**: 1 - Design & Contracts  
**Date**: 2026-02-14

## Overview

This document defines the contracts (interfaces) for CSS custom properties used in the silver background feature. These contracts specify the expected types, values, and constraints for CSS variables.

---

## Contract 1: CSS Custom Property Definition

```css
/**
 * Contract: Root-level CSS Custom Properties
 * Scope: :root (light mode)
 * File: frontend/src/index.css
 */

:root {
  /* Primary Colors */
  --color-primary: <hex-color>;      /* Must meet 3.0:1 contrast with --color-bg-secondary */
  --color-secondary: <hex-color>;    /* Secondary UI color */
  --color-success: <hex-color>;      /* Success state color */
  --color-warning: <hex-color>;      /* Warning state color */
  --color-danger: <hex-color>;       /* Error state color */
  
  /* Background Colors */
  --color-bg: <hex-color>;           /* Surface background (cards, modals) */
  --color-bg-secondary: #C0C0C0;     /* NEW VALUE: Page background (silver) */
  
  /* Text Colors */
  --color-text: <hex-color>;         /* Must meet 4.5:1 contrast with --color-bg-secondary */
  --color-text-secondary: <hex-color>; /* Must meet 4.5:1 contrast with --color-bg-secondary */
  
  /* Borders and Decorative */
  --color-border: <hex-color>;       /* Border and divider color */
  
  /* Layout */
  --radius: <css-length>;            /* Border radius */
  --shadow: <css-shadow>;            /* Box shadow definition */
}
```

**Type Definitions**:
- `<hex-color>`: 6-digit hexadecimal color code (e.g., `#C0C0C0`)
- `<css-length>`: Valid CSS length unit (e.g., `6px`, `1rem`)
- `<css-shadow>`: Valid CSS box-shadow value (e.g., `0 1px 3px rgba(0, 0, 0, 0.1)`)

---

## Contract 2: Dark Mode CSS Custom Properties

```css
/**
 * Contract: Dark Mode CSS Custom Properties Override
 * Scope: html.dark-mode-active
 * File: frontend/src/index.css
 */

html.dark-mode-active {
  /* Primary Colors - Dark Mode Variants */
  --color-primary: <hex-color>;      /* Lighter variant of light mode primary */
  --color-secondary: <hex-color>;    /* Adjusted for dark backgrounds */
  --color-success: <hex-color>;      /* Brighter success color */
  --color-warning: <hex-color>;      /* Brighter warning color */
  --color-danger: <hex-color>;       /* Brighter danger color */
  
  /* Background Colors - Dark Mode */
  --color-bg: <hex-color>;           /* Dark surface background */
  --color-bg-secondary: #2d2d2d;     /* NEW VALUE: Dark page background */
  
  /* Text Colors - Dark Mode */
  --color-text: <hex-color>;         /* Light text for dark backgrounds */
  --color-text-secondary: <hex-color>; /* Muted light text */
  
  /* Borders and Decorative - Dark Mode */
  --color-border: <hex-color>;       /* Subtle borders for dark mode */
  --shadow: <css-shadow>;            /* Stronger shadow for dark mode */
}
```

**Dark Mode Constraints**:
- All text colors must maintain 4.5:1 contrast ratio with `--color-bg-secondary: #2d2d2d`
- All UI component colors must maintain 3.0:1 contrast ratio
- `--color-bg-secondary` luminance must be < 0.2 (dark)
- `--color-bg` luminance must be < 0.1 (darker, for layering)

---

## Contract 3: File Modification Contract

```typescript
/**
 * Contract: Required File Changes for Silver Background Feature
 */

interface FileChange {
  filePath: string;
  lineNumbers: number[];
  changeType: 'modify' | 'verify';
  description: string;
  beforeValue?: string;
  afterValue?: string;
}

const REQUIRED_CHANGES: FileChange[] = [
  {
    filePath: 'frontend/src/index.css',
    lineNumbers: [9],
    changeType: 'modify',
    description: 'Update light mode background to silver',
    beforeValue: '--color-bg-secondary: #f6f8fa;',
    afterValue: '--color-bg-secondary: #C0C0C0;'
  },
  {
    filePath: 'frontend/src/index.css',
    lineNumbers: [25],
    changeType: 'modify',
    description: 'Update dark mode background to dark gray',
    beforeValue: '--color-bg-secondary: #161b22;',
    afterValue: '--color-bg-secondary: #2d2d2d;'
  }
];
```

## Summary

All contracts maintain backward compatibility with existing theme system architecture. Only 2 lines need modification in 1 file.
