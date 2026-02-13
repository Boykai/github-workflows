# Theme System Type Contracts

**Feature**: 001-pink-theme  
**Date**: 2026-02-13  
**Type**: TypeScript Interface Contracts

This file defines the TypeScript interfaces and types that serve as contracts between components in the pink theme feature.

---

## Core Types

### ThemeMode

```typescript
/**
 * Available theme modes for the application.
 * 
 * @example
 * const theme: ThemeMode = 'pink';
 */
export type ThemeMode = 'default' | 'dark' | 'pink' | 'pink-dark';
```

**Contract Guarantees**:
- Only these four values are valid
- Type system enforces exhaustive checking
- Cannot be null or undefined

---

## Theme Preference

### ThemePreference

```typescript
/**
 * User's theme preference with metadata.
 * Stored in localStorage and synchronized with application state.
 * 
 * @example
 * const preference: ThemePreference = {
 *   mode: 'pink',
 *   lastUpdated: '2026-02-13T10:30:00Z',
 *   version: 1
 * };
 */
export interface ThemePreference {
  /**
   * The selected theme mode.
   * @see ThemeMode
   */
  mode: ThemeMode;
  
  /**
   * ISO 8601 timestamp of when the theme was last changed.
   * Used for debugging and potential future analytics.
   */
  lastUpdated: string;
  
  /**
   * Version of the theme preference schema.
   * Allows for future migrations if the structure changes.
   * Current version: 1
   */
  version: number;
}
```

**Contract Guarantees**:
- `mode` is always a valid ThemeMode
- `lastUpdated` is always a valid ISO 8601 string
- `version` is always a positive integer

**Storage Contract**:
- Key: `tech-connect-theme-mode`
- Format: JSON-serialized ThemePreference object
- Location: `localStorage`

---

## Color Palette

### ColorPalette

```typescript
/**
 * Complete color palette definition for a theme.
 * All colors must meet WCAG 2.1 Level AA accessibility standards.
 * 
 * @example
 * const palette: ColorPalette = {
 *   primary: '#e85aad',
 *   background: '#ffebf6',
 *   text: '#2d1520',
 *   // ... other colors
 * };
 */
export interface ColorPalette {
  /** Primary action color (buttons, links) - must have 3:1 contrast on backgrounds */
  primary: string;
  
  /** Secondary accent color */
  secondary: string;
  
  /** Success state color (typically green) */
  success: string;
  
  /** Warning state color (typically amber/yellow) */
  warning: string;
  
  /** Danger/error state color (typically red) */
  danger: string;
  
  /** Main background color */
  background: string;
  
  /** Secondary background (cards, panels, sidebars) */
  backgroundSecondary: string;
  
  /** Border color */
  border: string;
  
  /** Primary text color - must have 4.5:1 contrast on backgrounds */
  text: string;
  
  /** Secondary text color (labels, muted text) - must have 4.5:1 contrast on backgrounds */
  textSecondary: string;
  
  /** Box shadow CSS value */
  shadow: string;
  
  /** Border radius CSS value */
  radius: string;
}
```

**Contract Guarantees**:
- All color values are valid CSS color strings
- Text/background combinations meet WCAG AA standards (4.5:1 for normal text)
- UI components meet WCAG AA standards (3:1 for large text/components)

**Accessibility Contract**:
```typescript
/**
 * Validates that a color palette meets accessibility standards.
 * @throws Error if contrast ratios are insufficient
 */
export function validateColorPalette(palette: ColorPalette): void;
```

---

## Hook Interface

### UseAppThemeReturn

```typescript
/**
 * Return type of the useAppTheme hook.
 * Provides theme state and methods for theme management.
 * 
 * @example
 * const { currentTheme, setTheme } = useAppTheme();
 * setTheme('pink');
 */
export interface UseAppThemeReturn {
  /**
   * Currently active theme mode.
   */
  currentTheme: ThemeMode;
  
  /**
   * Set the active theme.
   * Synchronously updates DOM classes and persists to localStorage.
   * 
   * @param theme - The theme mode to activate
   * 
   * @example
   * setTheme('pink-dark');
   */
  setTheme: (theme: ThemeMode) => void;
  
  /**
   * Indicates whether theme preference was successfully saved to localStorage.
   * False if storage is unavailable (e.g., private browsing mode).
   */
  isPersisted: boolean;
  
  /**
   * @deprecated Use currentTheme instead. Kept for backward compatibility.
   * Returns true if currentTheme is 'dark' or 'pink-dark'.
   */
  isDarkMode: boolean;
  
  /**
   * @deprecated Use setTheme('dark' | 'default') instead. Kept for backward compatibility.
   * Toggles between 'default' and 'dark' themes only.
   */
  toggleTheme: () => void;
}
```

**Contract Guarantees**:
- `currentTheme` always reflects the actual applied theme
- `setTheme` updates DOM within same tick (synchronous)
- `isPersisted` accurately reflects localStorage write status
- Deprecated methods maintain backward compatibility

**Side Effects Contract**:
```typescript
/**
 * Side effects of useAppTheme hook:
 * 1. Reads from localStorage on mount
 * 2. Applies CSS classes to document.documentElement on theme change
 * 3. Writes to localStorage on theme change (if available)
 * 4. Logs warning to console if localStorage is unavailable
 */
```

---

## Theme Selector

### ThemeOption

```typescript
/**
 * Represents a selectable theme option in the UI.
 * 
 * @example
 * const option: ThemeOption = {
 *   value: 'pink',
 *   label: 'Pink',
 *   previewColor: '#e85aad',
 *   ariaLabel: 'Pink theme with light backgrounds'
 * };
 */
export interface ThemeOption {
  /**
   * Theme mode value - must match a valid ThemeMode.
   */
  value: ThemeMode;
  
  /**
   * Human-readable label for display in UI.
   */
  label: string;
  
  /**
   * Color to display as a preview swatch.
   * Typically the theme's primary color.
   */
  previewColor: string;
  
  /**
   * Accessible label for screen readers.
   * Should describe the theme's appearance and characteristics.
   */
  ariaLabel: string;
}
```

**Contract Guarantees**:
- `value` is always a valid ThemeMode
- `label` is never empty
- `previewColor` is a valid CSS color
- `ariaLabel` provides meaningful context for screen readers

### ThemeSelectorProps

```typescript
/**
 * Props for the ThemeSelector component.
 * 
 * @example
 * <ThemeSelector
 *   currentTheme="pink"
 *   onThemeChange={(theme) => setTheme(theme)}
 *   options={THEME_OPTIONS}
 * />
 */
export interface ThemeSelectorProps {
  /**
   * Currently active theme.
   */
  currentTheme: ThemeMode;
  
  /**
   * Callback invoked when user selects a theme.
   * Should call the useAppTheme setTheme method.
   */
  onThemeChange: (theme: ThemeMode) => void;
  
  /**
   * Available theme options to display.
   */
  options: ThemeOption[];
  
  /**
   * Optional CSS class name for styling.
   */
  className?: string;
  
  /**
   * Optional accessible label for the selector button.
   * Defaults to "Choose theme".
   */
  ariaLabel?: string;
}
```

**Contract Guarantees**:
- `onThemeChange` is called exactly once per user selection
- Component is keyboard-accessible (Space/Enter to open, Arrow keys to navigate)
- Component respects `prefers-reduced-motion` for animations
- Component maintains focus management for accessibility

---

## CSS Class Mapping

### ThemeCSSClassMap

```typescript
/**
 * Maps theme modes to CSS classes that should be applied to document.documentElement.
 * 
 * @example
 * const classes = THEME_CSS_CLASSES['pink-dark'];
 * // ['pink-theme-active', 'dark-mode-active']
 */
export type ThemeCSSClassMap = Record<ThemeMode, string[]>;

/**
 * Standard CSS class mapping for theme modes.
 */
export const THEME_CSS_CLASSES: ThemeCSSClassMap = {
  'default': [],
  'dark': ['dark-mode-active'],
  'pink': ['pink-theme-active'],
  'pink-dark': ['pink-theme-active', 'dark-mode-active'],
};
```

**Contract Guarantees**:
- Map is exhaustive (covers all ThemeMode values)
- Each entry is an array (possibly empty)
- Class names are kebab-case
- Multiple classes can be applied simultaneously

**CSS Selector Contract**:
```css
/* Base styles */
:root { /* ... */ }

/* Dark mode */
html.dark-mode-active { /* ... */ }

/* Pink theme */
html.pink-theme-active { /* ... */ }

/* Pink dark (both classes) */
html.pink-theme-active.dark-mode-active { /* ... */ }
```

---

## Utility Functions

### ThemeUtils

```typescript
/**
 * Utility functions for theme operations.
 */
export interface ThemeUtils {
  /**
   * Validates whether a string is a valid ThemeMode.
   * 
   * @param value - Value to validate
   * @returns True if value is a valid ThemeMode
   * 
   * @example
   * isValidThemeMode('pink'); // true
   * isValidThemeMode('invalid'); // false
   */
  isValidThemeMode(value: unknown): value is ThemeMode;
  
  /**
   * Migrates legacy theme value to new ThemeMode.
   * Handles transition from old 'light'/'dark' system.
   * 
   * @param legacyValue - Old theme value from localStorage
   * @returns Migrated ThemeMode
   * 
   * @example
   * migrateLegacyTheme('light'); // 'default'
   * migrateLegacyTheme('dark'); // 'dark'
   */
  migrateLegacyTheme(legacyValue: string | null): ThemeMode;
  
  /**
   * Gets the ColorPalette for a given ThemeMode.
   * 
   * @param mode - Theme mode
   * @returns Color palette for the theme
   * 
   * @example
   * const palette = getPaletteForTheme('pink');
   * console.log(palette.primary); // '#e85aad'
   */
  getPaletteForTheme(mode: ThemeMode): ColorPalette;
  
  /**
   * Applies theme CSS classes to the document element.
   * Removes old theme classes before applying new ones.
   * 
   * @param mode - Theme mode to apply
   * 
   * @example
   * applyThemeClasses('pink-dark');
   * // document.documentElement.classList contains: 'pink-theme-active', 'dark-mode-active'
   */
  applyThemeClasses(mode: ThemeMode): void;
  
  /**
   * Saves theme preference to localStorage.
   * 
   * @param preference - Theme preference to save
   * @returns True if successfully saved, false if storage unavailable
   * 
   * @example
   * const saved = saveThemePreference({
   *   mode: 'pink',
   *   lastUpdated: new Date().toISOString(),
   *   version: 1
   * });
   */
  saveThemePreference(preference: ThemePreference): boolean;
  
  /**
   * Loads theme preference from localStorage.
   * 
   * @returns Stored preference, or default if not found/invalid
   * 
   * @example
   * const preference = loadThemePreference();
   * console.log(preference.mode); // 'pink' or 'default'
   */
  loadThemePreference(): ThemePreference;
}
```

**Contract Guarantees**:
- All functions handle edge cases gracefully (null, undefined, invalid values)
- No function throws exceptions (returns safe defaults instead)
- Side effects are documented and predictable
- Functions are pure where possible (no hidden state)

---

## Constants

### Theme Constants

```typescript
/**
 * Storage key for theme preference in localStorage.
 */
export const THEME_STORAGE_KEY = 'tech-connect-theme-mode';

/**
 * Current version of the theme system.
 * Increment when making breaking changes to ThemePreference structure.
 */
export const THEME_VERSION = 1;

/**
 * Default theme mode when no preference is set.
 */
export const DEFAULT_THEME_MODE: ThemeMode = 'default';

/**
 * All available theme options with metadata.
 */
export const THEME_OPTIONS: readonly ThemeOption[] = [
  {
    value: 'default',
    label: 'Default',
    previewColor: '#0969da',
    ariaLabel: 'Default light theme with blue accents',
  },
  {
    value: 'dark',
    label: 'Dark',
    previewColor: '#539bf5',
    ariaLabel: 'Dark theme with muted colors',
  },
  {
    value: 'pink',
    label: 'Pink',
    previewColor: '#e85aad',
    ariaLabel: 'Pink theme with light backgrounds',
  },
  {
    value: 'pink-dark',
    label: 'Pink Dark',
    previewColor: '#ff94d1',
    ariaLabel: 'Pink theme with dark backgrounds',
  },
] as const;
```

**Contract Guarantees**:
- Constants are readonly/immutable
- Values are validated at compile time
- Constants are exported for reuse across application

---

## Type Guards

### Type Guard Functions

```typescript
/**
 * Type guard to check if a value is a valid ThemeMode.
 * 
 * @param value - Value to check
 * @returns True if value is ThemeMode
 */
export function isThemeMode(value: unknown): value is ThemeMode {
  return (
    typeof value === 'string' &&
    ['default', 'dark', 'pink', 'pink-dark'].includes(value)
  );
}

/**
 * Type guard to check if a value is a valid ThemePreference.
 * 
 * @param value - Value to check
 * @returns True if value is ThemePreference
 */
export function isThemePreference(value: unknown): value is ThemePreference {
  return (
    typeof value === 'object' &&
    value !== null &&
    'mode' in value &&
    isThemeMode(value.mode) &&
    'lastUpdated' in value &&
    typeof value.lastUpdated === 'string' &&
    'version' in value &&
    typeof value.version === 'number'
  );
}
```

---

## Summary

This contract defines:

1. **Core Types**: ThemeMode, ThemePreference, ColorPalette
2. **Hook Interface**: useAppTheme return type and contracts
3. **Component Props**: ThemeSelector props with accessibility requirements
4. **CSS Mapping**: Theme-to-class-name mappings
5. **Utilities**: Helper functions for theme operations
6. **Constants**: Shared configuration values
7. **Type Guards**: Runtime validation functions

All contracts include:
- JSDoc documentation with examples
- Type safety guarantees
- Accessibility requirements
- Side effect documentation

**Versioning**: These contracts are version 1.0 and follow semantic versioning. Breaking changes require a major version bump.
