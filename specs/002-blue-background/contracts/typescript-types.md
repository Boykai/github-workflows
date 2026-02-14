# TypeScript Type Contracts: Blue Background Color

**Feature**: Blue Background Color  
**Branch**: 002-blue-background  
**Date**: 2026-02-14

## Overview

This document defines TypeScript interfaces and types for the blue background color feature. These types support theme configuration, accessibility validation, and testing.

---

## Core Theme Types

### `ThemeMode`

```typescript
/**
 * Theme mode identifier
 */
export type ThemeMode = 'light' | 'dark';
```

**Usage**: Identifies which theme is currently active

---

### `ColorTheme`

```typescript
/**
 * Color scheme configuration for a theme mode
 */
export interface ColorTheme {
  /** Theme mode identifier */
  mode: ThemeMode;
  
  /** Primary background color (CSS hex format, e.g., #2196F3) */
  backgroundColor: string;
  
  /** Secondary background color for panels/cards (CSS hex format) */
  backgroundSecondary: string;
  
  /** Primary text color (CSS hex format) */
  textColor: string;
  
  /** Secondary text color for less prominent text (CSS hex format) */
  textColorSecondary: string;
}
```

**Example**:
```typescript
const lightTheme: ColorTheme = {
  mode: 'light',
  backgroundColor: '#2196F3',
  backgroundSecondary: '#FFFFFF',
  textColor: '#FFFFFF',
  textColorSecondary: '#1565C0'
};
```

---

## Accessibility Types

### `TextSize`

```typescript
/**
 * Text size category for WCAG contrast calculation
 */
export type TextSize = 'normal' | 'large';
```

**Definition**:
- `'normal'`: Text smaller than 18pt (or 14pt bold)
- `'large'`: Text 18pt or larger (or 14pt bold or larger)

---

### `ElementType`

```typescript
/**
 * UI element type for contrast validation
 */
export type ElementType = 'text' | 'interactive';
```

**Definition**:
- `'text'`: Static text content
- `'interactive'`: Buttons, links, form controls

---

### `WCAGLevel`

```typescript
/**
 * WCAG compliance level
 */
export type WCAGLevel = 'AA' | 'AAA' | 'fail';
```

**Thresholds**:
- `'AA'`: Contrast ≥ 4.5:1 (normal text) or ≥ 3:1 (large text/interactive)
- `'AAA'`: Contrast ≥ 7:1 (normal text) or ≥ 4.5:1 (large text)
- `'fail'`: Below AA thresholds

---

### `ContrastValidation`

```typescript
/**
 * Validates WCAG AA contrast compliance for color combinations
 */
export interface ContrastValidation {
  /** Text or interactive element color (CSS hex format) */
  foregroundColor: string;
  
  /** Background color (CSS hex format) */
  backgroundColor: string;
  
  /** Calculated contrast ratio (1.0 to 21.0) */
  contrastRatio: number;
  
  /** WCAG compliance level achieved */
  wcagLevel: WCAGLevel;
  
  /** Text size category */
  textSize: TextSize;
  
  /** UI element type */
  elementType: ElementType;
  
  /** Whether combination passes WCAG AA */
  isCompliant: boolean;
}
```

**Example**:
```typescript
const validation: ContrastValidation = {
  foregroundColor: '#FFFFFF',
  backgroundColor: '#2196F3',
  contrastRatio: 3.15,
  wcagLevel: 'fail',
  textSize: 'normal',
  elementType: 'text',
  isCompliant: false
};
```

---

## CSS Variable Types

### `CSSScope`

```typescript
/**
 * CSS selector scope for custom properties
 */
export type CSSScope = ':root' | 'html.dark-mode-active';
```

**Usage**:
- `:root`: Light mode variables
- `html.dark-mode-active`: Dark mode variables

---

### `CSSVariableMap`

```typescript
/**
 * Maps logical theme properties to CSS custom property names
 */
export interface CSSVariableMap {
  /** CSS custom property name (must start with --) */
  variableName: string;
  
  /** Color value (CSS hex, rgb, etc.) */
  value: string;
  
  /** CSS selector scope */
  scope: CSSScope;
  
  /** Human-readable purpose (optional) */
  description?: string;
}
```

**Example**:
```typescript
const bgVariable: CSSVariableMap = {
  variableName: '--color-bg',
  value: '#2196F3',
  scope: ':root',
  description: 'Primary background color (Material Blue 500)'
};
```

---

## Testing Types

### `ColorTestCase`

```typescript
/**
 * Test case for validating color combinations during E2E/accessibility tests
 */
export interface ColorTestCase {
  /** Human-readable test case name */
  testName: string;
  
  /** CSS selector for element to test */
  element: string;
  
  /** Expected background color (CSS hex format) */
  expectedBackground: string;
  
  /** Expected text color (CSS hex format) */
  expectedText: string;
  
  /** Minimum required contrast ratio (4.5 or 3.0) */
  minContrastRatio: number;
  
  /** Theme mode to test */
  mode: ThemeMode;
}
```

**Example**:
```typescript
const testCase: ColorTestCase = {
  testName: 'Login screen background (light mode)',
  element: '.app-login',
  expectedBackground: '#2196F3',
  expectedText: '#FFFFFF',
  minContrastRatio: 4.5,
  mode: 'light'
};
```

---

## Utility Types

### `HexColor`

```typescript
/**
 * Type guard for CSS hex color format
 * 
 * @example '#2196F3' (valid)
 * @example '#FFF' (valid)
 * @example 'rgb(33, 150, 243)' (invalid - not hex)
 */
export type HexColor = `#${string}`;
```

**Usage**: Type-safe hex color strings

---

### `ContrastRatio`

```typescript
/**
 * Contrast ratio between two colors (1.0 to 21.0)
 */
export type ContrastRatio = number;
```

**Range**: 1.0 (no contrast) to 21.0 (maximum contrast - black on white)

---

## Type Guards

### `isValidHexColor`

```typescript
/**
 * Type guard to validate hex color format
 * 
 * @param color - Color string to validate
 * @returns true if valid hex color (#RRGGBB or #RGB)
 */
export function isValidHexColor(color: string): color is HexColor {
  return /^#([0-9A-F]{3}|[0-9A-F]{6})$/i.test(color);
}
```

**Example**:
```typescript
if (isValidHexColor('#2196F3')) {
  // color is guaranteed to be HexColor type
}
```

---

### `isThemeMode`

```typescript
/**
 * Type guard to validate theme mode
 * 
 * @param mode - String to validate
 * @returns true if valid ThemeMode
 */
export function isThemeMode(mode: string): mode is ThemeMode {
  return mode === 'light' || mode === 'dark';
}
```

**Example**:
```typescript
const stored = localStorage.getItem('theme');
if (stored && isThemeMode(stored)) {
  // stored is guaranteed to be ThemeMode type
}
```

---

## Validation Functions

### `calculateContrastRatio`

```typescript
/**
 * Calculates WCAG contrast ratio between two colors
 * 
 * @param foreground - Foreground color (hex format)
 * @param background - Background color (hex format)
 * @returns Contrast ratio (1.0 to 21.0)
 * 
 * Formula: (L1 + 0.05) / (L2 + 0.05) where L1 > L2
 * L is relative luminance
 */
export function calculateContrastRatio(
  foreground: HexColor,
  background: HexColor
): ContrastRatio;
```

**Usage**:
```typescript
const ratio = calculateContrastRatio('#FFFFFF', '#2196F3');
// ratio ≈ 3.15
```

---

### `isWCAGCompliant`

```typescript
/**
 * Checks if color combination meets WCAG AA standards
 * 
 * @param validation - Contrast validation object
 * @returns true if meets WCAG AA
 * 
 * WCAG AA Requirements:
 * - Normal text: ≥ 4.5:1
 * - Large text: ≥ 3:1
 * - Interactive elements: ≥ 3:1
 */
export function isWCAGCompliant(validation: ContrastValidation): boolean {
  const { contrastRatio, textSize, elementType } = validation;
  
  if (elementType === 'interactive') {
    return contrastRatio >= 3.0;
  }
  
  if (textSize === 'large') {
    return contrastRatio >= 3.0;
  }
  
  return contrastRatio >= 4.5;
}
```

**Usage**:
```typescript
if (isWCAGCompliant(validation)) {
  console.log('✅ Passes WCAG AA');
} else {
  console.log('❌ Fails WCAG AA');
}
```

---

### `getWCAGLevel`

```typescript
/**
 * Determines WCAG compliance level for a contrast ratio
 * 
 * @param contrastRatio - Contrast ratio to evaluate
 * @param textSize - Text size category
 * @returns WCAG level achieved
 */
export function getWCAGLevel(
  contrastRatio: ContrastRatio,
  textSize: TextSize
): WCAGLevel {
  const aaaThreshold = textSize === 'normal' ? 7.0 : 4.5;
  const aaThreshold = textSize === 'normal' ? 4.5 : 3.0;
  
  if (contrastRatio >= aaaThreshold) return 'AAA';
  if (contrastRatio >= aaThreshold) return 'AA';
  return 'fail';
}
```

**Usage**:
```typescript
const level = getWCAGLevel(5.98, 'normal');
// level === 'AA'
```

---

## Constants

### `BLUE_BACKGROUND_COLORS`

```typescript
/**
 * Blue background color constants for light and dark modes
 */
export const BLUE_BACKGROUND_COLORS = {
  light: {
    primary: '#2196F3' as HexColor,      // Material Blue 500
    secondary: '#FFFFFF' as HexColor,    // White panels
  },
  dark: {
    primary: '#1565C0' as HexColor,      // Material Blue 800
    secondary: '#161B22' as HexColor,    // Near-black panels
  },
} as const;
```

**Usage**:
```typescript
const bgColor = BLUE_BACKGROUND_COLORS.light.primary;
// bgColor === '#2196F3'
```

---

### `WCAG_THRESHOLDS`

```typescript
/**
 * WCAG contrast ratio thresholds
 */
export const WCAG_THRESHOLDS = {
  AA: {
    normalText: 4.5,
    largeText: 3.0,
    interactive: 3.0,
  },
  AAA: {
    normalText: 7.0,
    largeText: 4.5,
    interactive: 4.5,
  },
} as const;
```

**Usage**:
```typescript
if (contrastRatio >= WCAG_THRESHOLDS.AA.normalText) {
  // Passes AA for normal text
}
```

---

## Module Export Structure

```typescript
// contracts/theme-types.ts
export type {
  ThemeMode,
  ColorTheme,
  TextSize,
  ElementType,
  WCAGLevel,
  ContrastValidation,
  CSSScope,
  CSSVariableMap,
  ColorTestCase,
  HexColor,
  ContrastRatio,
};

export {
  isValidHexColor,
  isThemeMode,
  calculateContrastRatio,
  isWCAGCompliant,
  getWCAGLevel,
  BLUE_BACKGROUND_COLORS,
  WCAG_THRESHOLDS,
};
```

**Usage in Application**:
```typescript
import type { ColorTheme, ContrastValidation } from '@/contracts/theme-types';
import { BLUE_BACKGROUND_COLORS, isWCAGCompliant } from '@/contracts/theme-types';
```

---

## Integration with Existing Code

### No Changes to `useAppTheme` Hook

The existing `useAppTheme` hook continues to work unchanged:

```typescript
// frontend/src/hooks/useAppTheme.ts
export function useAppTheme() {
  const [isDarkMode, setIsDarkMode] = useState<boolean>(() => {
    const stored = localStorage.getItem('tech-connect-theme-mode');
    return stored === 'dark';
  });

  // ... rest of hook (unchanged)
}
```

**Note**: No modifications needed to hook signature or behavior.

---

### Component Usage (No Type Changes)

Components continue using CSS classes without explicit color props:

```typescript
// frontend/src/App.tsx
function App() {
  return (
    <div className="app-container">
      {/* Blue background applied via CSS var(--color-bg) */}
    </div>
  );
}
```

**Note**: Types in this contract document are primarily for testing/validation, not runtime component props.

---

## Summary

This contract defines:

1. **Theme types** (`ColorTheme`, `ThemeMode`) for color configuration
2. **Accessibility types** (`ContrastValidation`, `WCAGLevel`) for WCAG compliance
3. **CSS types** (`CSSVariableMap`, `CSSScope`) for stylesheet structure
4. **Testing types** (`ColorTestCase`) for automated validation
5. **Utility functions** (`calculateContrastRatio`, `isWCAGCompliant`) for validation logic
6. **Constants** (`BLUE_BACKGROUND_COLORS`, `WCAG_THRESHOLDS`) for color values

These types support development, testing, and validation of the blue background feature while requiring **no changes** to existing application code.

---

**End of TypeScript Contracts**
