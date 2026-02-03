/**
 * Theme selector component for switching between light and pink themes.
 */

import { useTheme, Theme } from '@/hooks/useTheme';
import './ThemeSelector.css';

export function ThemeSelector() {
  const { theme, setTheme } = useTheme();

  const handleThemeChange = (newTheme: Theme) => {
    setTheme(newTheme);
  };

  return (
    <div className="theme-selector">
      <button
        className={`theme-button ${theme === 'light' ? 'active' : ''}`}
        onClick={() => handleThemeChange('light')}
        aria-label="Light theme"
        title="Light theme"
      >
        <span className="theme-preview theme-preview-light" />
      </button>
      <button
        className={`theme-button ${theme === 'pink' ? 'active' : ''}`}
        onClick={() => handleThemeChange('pink')}
        aria-label="Pink theme"
        title="Pink theme"
      >
        <span className="theme-preview theme-preview-pink" />
      </button>
    </div>
  );
}
