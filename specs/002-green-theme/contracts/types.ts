/**
 * Type Definitions for Green Theme Feature
 * 
 * @module theme-types
 * @description Core TypeScript types for theme management system
 */

// ============================================================================
// Theme Mode Types
// ============================================================================

/**
 * Available theme modes in the application
 * 
 * @typedef {('light' | 'dark' | 'green' | 'green-dark')} ThemeMode
 */
export type ThemeMode = 'light' | 'dark' | 'green' | 'green-dark';

/**
 * Readonly array of valid theme modes for validation
 */
export const VALID_THEMES: readonly ThemeMode[] = ['light', 'dark', 'green', 'green-dark'] as const;

// ============================================================================
// Theme Preference
// ============================================================================

/**
 * User's theme preference with metadata
 * 
 * @interface ThemePreference
 * @description Represents a stored user preference for theme selection
 */
export interface ThemePreference {
  /**
   * Selected theme mode
   * @type {ThemeMode}
   */
  mode: ThemeMode;

  /**
   * Timestamp when preference was last updated (ISO 8601 format)
   * @type {string}
   * @example "2026-02-14T12:00:00.000Z"
   */
  updatedAt: string;

  /**
   * Optional device identifier for cross-device differentiation
   * @type {string}
   * @optional
   */
  deviceId?: string;
}

// ============================================================================
// Theme Definition
// ============================================================================

/**
 * Color palette for a theme
 * 
 * @interface ThemeColors
 * @description Defines all color values used in a theme
 */
export interface ThemeColors {
  /** Primary accent color (CSS hex or rgb) */
  primary: string;

  /** Secondary accent color */
  secondary: string;

  /** Success state color */
  success: string;

  /** Warning state color */
  warning: string;

  /** Error/danger color */
  danger: string;

  /** Main background color */
  background: string;

  /** Secondary background (cards, panels, sidebars) */
  backgroundSecondary: string;

  /** Border color */
  border: string;

  /** Primary text color */
  text: string;

  /** Secondary text color (hints, descriptions) */
  textSecondary: string;
}

/**
 * Accessibility metadata for a theme
 * 
 * @interface ThemeAccessibility
 * @description Documents WCAG compliance and contrast ratios
 */
export interface ThemeAccessibility {
  /**
   * Minimum contrast ratio for normal text (WCAG AA: 4.5:1)
   * @type {number}
   */
  normalTextContrast: number;

  /**
   * Minimum contrast ratio for large text (WCAG AA: 3:1)
   * @type {number}
   */
  largeTextContrast: number;

  /**
   * WCAG compliance level
   * @type {('AA' | 'AAA')}
   */
  wcagLevel: 'AA' | 'AAA';

  /**
   * Whether theme is color-blind safe
   * @type {boolean}
   */
  colorBlindSafe: boolean;
}

/**
 * Complete theme definition with metadata
 * 
 * @interface ThemeDefinition
 * @description Defines all properties of a theme including colors and accessibility
 */
export interface ThemeDefinition {
  /**
   * Unique theme identifier matching ThemeMode
   * @type {ThemeMode}
   */
  id: ThemeMode;

  /**
   * Human-readable theme name for UI display
   * @type {string}
   * @example "Green" or "Green Dark"
   */
  name: string;

  /**
   * CSS class name applied to document root
   * @type {string}
   * @example "green-mode-active"
   */
  className: string;

  /**
   * Color palette for this theme
   * @type {ThemeColors}
   */
  colors: ThemeColors;

  /**
   * Accessibility metadata
   * @type {ThemeAccessibility}
   */
  accessibility: ThemeAccessibility;
}

// ============================================================================
// Type Guards
// ============================================================================

/**
 * Type guard to check if a value is a valid ThemeMode
 * 
 * @param {unknown} value - Value to check
 * @returns {boolean} True if value is a valid ThemeMode
 * 
 * @example
 * if (isValidThemeMode(userInput)) {
 *   setTheme(userInput);
 * }
 */
export function isValidThemeMode(value: unknown): value is ThemeMode {
  return typeof value === 'string' && VALID_THEMES.includes(value as ThemeMode);
}

/**
 * Type guard to check if a value is a valid ThemePreference object
 * 
 * @param {unknown} value - Value to check
 * @returns {boolean} True if value is a valid ThemePreference
 * 
 * @example
 * const stored = JSON.parse(localStorage.getItem(KEY));
 * if (isThemePreference(stored)) {
 *   applyTheme(stored.mode);
 * }
 */
export function isThemePreference(value: unknown): value is ThemePreference {
  return (
    typeof value === 'object' &&
    value !== null &&
    'mode' in value &&
    isValidThemeMode((value as ThemePreference).mode) &&
    'updatedAt' in value &&
    typeof (value as ThemePreference).updatedAt === 'string'
  );
}

// ============================================================================
// Constants
// ============================================================================

/**
 * localStorage key for theme preference
 */
export const THEME_STORAGE_KEY = 'tech-connect-theme-mode';

/**
 * Default theme preference
 */
export const DEFAULT_THEME_PREFERENCE: ThemePreference = {
  mode: 'light',
  updatedAt: new Date().toISOString(),
};

/**
 * Mapping of theme modes to CSS class names
 */
export const THEME_CLASS_MAP: Record<ThemeMode, string> = {
  light: '', // No class for default light theme
  dark: 'dark-mode-active',
  green: 'green-mode-active',
  'green-dark': 'green-dark-mode-active',
};
