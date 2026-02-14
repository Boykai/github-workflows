/**
 * React Hook Contract: useAppTheme
 * 
 * @module useAppTheme
 * @description Hook interface for managing application theme preferences
 */

import type { ThemeMode } from './types';

// ============================================================================
// Hook Return Type
// ============================================================================

/**
 * Return type for useAppTheme hook
 * 
 * @interface UseAppThemeReturn
 * @description Provides theme state and controls to consuming components
 */
export interface UseAppThemeReturn {
  /**
   * Current active theme mode
   * @type {ThemeMode}
   */
  theme: ThemeMode;

  /**
   * Set theme to a specific mode
   * 
   * @param {ThemeMode} mode - The theme mode to activate
   * @returns {void}
   * 
   * @example
   * setTheme('green'); // Switches to green theme
   */
  setTheme: (mode: ThemeMode) => void;

  /**
   * Check if a specific theme is currently active
   * 
   * @param {ThemeMode} mode - The theme mode to check
   * @returns {boolean} True if the specified theme is active
   * 
   * @example
   * if (isThemeActive('green')) {
   *   console.log('Green theme is active');
   * }
   */
  isThemeActive: (mode: ThemeMode) => boolean;

  /**
   * Legacy property for backward compatibility
   * @deprecated Use theme === 'dark' || theme === 'green-dark' instead
   * @type {boolean}
   */
  isDarkMode: boolean;

  /**
   * Legacy method for backward compatibility
   * @deprecated Use setTheme() instead
   * @returns {void}
   */
  toggleTheme: () => void;
}

// ============================================================================
// Hook Signature
// ============================================================================

/**
 * Custom hook for managing application theme
 * 
 * @function useAppTheme
 * @returns {UseAppThemeReturn} Theme state and control functions
 * 
 * @example
 * function SettingsPage() {
 *   const { theme, setTheme, isThemeActive } = useAppTheme();
 *   
 *   return (
 *     <div>
 *       <button onClick={() => setTheme('green')}>
 *         Green Theme {isThemeActive('green') && '✓'}
 *       </button>
 *     </div>
 *   );
 * }
 */
export type UseAppThemeHook = () => UseAppThemeReturn;

// ============================================================================
// Implementation Requirements
// ============================================================================

/**
 * Hook Implementation Requirements:
 * 
 * 1. **State Management**:
 *    - Maintain single state variable for current theme (ThemeMode)
 *    - Initialize from localStorage on first render
 *    - Update localStorage on every theme change
 * 
 * 2. **DOM Manipulation**:
 *    - Apply corresponding CSS class to document.documentElement
 *    - Remove previous theme class before applying new one
 *    - Use THEME_CLASS_MAP for class name lookup
 * 
 * 3. **Persistence**:
 *    - Store ThemePreference object in localStorage
 *    - Use THEME_STORAGE_KEY constant for key
 *    - Handle localStorage errors gracefully (fall back to default)
 * 
 * 4. **Backward Compatibility**:
 *    - Support legacy string values ('dark', 'light') in localStorage
 *    - Migrate to new ThemePreference format on load
 *    - Preserve existing isDarkMode and toggleTheme for existing code
 * 
 * 5. **Error Handling**:
 *    - Validate theme mode before applying
 *    - Fall back to 'light' for invalid values
 *    - Log warnings for invalid data (don't throw errors)
 * 
 * 6. **Performance**:
 *    - Use useEffect for side effects (DOM manipulation, storage)
 *    - Minimize re-renders (only when theme actually changes)
 *    - No debouncing required (CSS updates are instant)
 */

// ============================================================================
// Usage Examples
// ============================================================================

/**
 * Example 1: Theme Selector Component
 * 
 * ```tsx
 * import { useAppTheme } from '@/hooks/useAppTheme';
 * import { VALID_THEMES } from '@/types/theme';
 * 
 * export function ThemeSelector() {
 *   const { theme, setTheme } = useAppTheme();
 *   
 *   return (
 *     <div className="theme-selector">
 *       {VALID_THEMES.map((mode) => (
 *         <button
 *           key={mode}
 *           onClick={() => setTheme(mode)}
 *           className={theme === mode ? 'active' : ''}
 *         >
 *           {mode.charAt(0).toUpperCase() + mode.slice(1)}
 *         </button>
 *       ))}
 *     </div>
 *   );
 * }
 * ```
 */

/**
 * Example 2: Conditional Rendering Based on Theme
 * 
 * ```tsx
 * import { useAppTheme } from '@/hooks/useAppTheme';
 * 
 * export function Header() {
 *   const { isThemeActive } = useAppTheme();
 *   
 *   return (
 *     <header className="app-header">
 *       {isThemeActive('green') && <span>🌱 Green Mode</span>}
 *       {isThemeActive('green-dark') && <span>🌿 Green Dark Mode</span>}
 *     </header>
 *   );
 * }
 * ```
 */

/**
 * Example 3: Settings Page with Theme Preview
 * 
 * ```tsx
 * import { useAppTheme } from '@/hooks/useAppTheme';
 * 
 * export function Settings() {
 *   const { theme, setTheme } = useAppTheme();
 *   
 *   const themeOptions = [
 *     { mode: 'light', label: 'Light', icon: '☀️' },
 *     { mode: 'dark', label: 'Dark', icon: '🌙' },
 *     { mode: 'green', label: 'Green', icon: '🌱' },
 *     { mode: 'green-dark', label: 'Green Dark', icon: '🌿' },
 *   ] as const;
 *   
 *   return (
 *     <section>
 *       <h2>Theme Settings</h2>
 *       <div role="radiogroup" aria-label="Theme selection">
 *         {themeOptions.map(({ mode, label, icon }) => (
 *           <label key={mode}>
 *             <input
 *               type="radio"
 *               name="theme"
 *               value={mode}
 *               checked={theme === mode}
 *               onChange={() => setTheme(mode)}
 *             />
 *             {icon} {label}
 *           </label>
 *         ))}
 *       </div>
 *     </section>
 *   );
 * }
 * ```
 */

/**
 * Example 4: Backward Compatibility Usage
 * 
 * ```tsx
 * import { useAppTheme } from '@/hooks/useAppTheme';
 * 
 * // Existing code using legacy API still works
 * export function LegacyComponent() {
 *   const { isDarkMode, toggleTheme } = useAppTheme();
 *   
 *   return (
 *     <button onClick={toggleTheme}>
 *       {isDarkMode ? 'Switch to Light' : 'Switch to Dark'}
 *     </button>
 *   );
 * }
 * ```
 */
