# Implementation Quickstart: Green Theme Option

**Feature**: Green Theme Option  
**Branch**: `002-green-theme`  
**Date**: 2026-02-14  
**Phase**: 1 - Design

## Overview

This quickstart guide provides a step-by-step implementation plan for adding the green theme option to the application. Follow these steps in order for a smooth implementation.

---

## Prerequisites

- Node.js and npm installed
- Frontend development environment set up
- Familiarity with React and TypeScript
- Access to `frontend/src/` directory

---

## Implementation Steps

### Step 1: Update Type Definitions

**File**: `frontend/src/types/theme.ts` (create if doesn't exist)

**Action**: Add or update theme type definitions

```typescript
// Copy from specs/002-green-theme/contracts/types.ts
export type ThemeMode = 'light' | 'dark' | 'green' | 'green-dark';

export const VALID_THEMES: readonly ThemeMode[] = ['light', 'dark', 'green', 'green-dark'] as const;

export const THEME_STORAGE_KEY = 'tech-connect-theme-mode';

export const THEME_CLASS_MAP: Record<ThemeMode, string> = {
  light: '',
  dark: 'dark-mode-active',
  green: 'green-mode-active',
  'green-dark': 'green-dark-mode-active',
};

// Include other type definitions from contracts/types.ts
```

**Verification**:
```bash
# Check TypeScript compilation
npm run type-check
# or
tsc --noEmit
```

---

### Step 2: Add Green Theme CSS

**File**: `frontend/src/index.css`

**Action**: Add green theme CSS classes after existing dark theme

```css
/* Existing :root and html.dark-mode-active stay unchanged */

/* Green Light Theme */
html.green-mode-active {
  --color-primary: #2da44e;
  --color-secondary: #6e7781;
  --color-success: #1a7f37;
  --color-warning: #9a6700;
  --color-danger: #cf222e;
  --color-bg: #ffffff;
  --color-bg-secondary: #f6fff8;
  --color-border: #d0d7de;
  --color-text: #24292f;
  --color-text-secondary: #57606a;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* Green Dark Theme */
html.green-dark-mode-active {
  --color-primary: #3fb950;
  --color-secondary: #8b949e;
  --color-success: #56d364;
  --color-warning: #d29922;
  --color-danger: #f85149;
  --color-bg: #0d1117;
  --color-bg-secondary: #0d1a12;
  --color-border: #30363d;
  --color-text: #e6edf3;
  --color-text-secondary: #8b949e;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
}
```

**Verification**:
1. Start dev server: `npm run dev`
2. Open browser DevTools console
3. Execute: `document.documentElement.classList.add('green-mode-active')`
4. Verify UI turns green
5. Execute: `document.documentElement.classList.remove('green-mode-active')`

---

### Step 3: Refactor useAppTheme Hook

**File**: `frontend/src/hooks/useAppTheme.ts`

**Current Implementation**:
```typescript
// Boolean-based theme (isDarkMode)
const [isDarkMode, setIsDarkMode] = useState(...)
```

**New Implementation**:
```typescript
import { useState, useEffect } from 'react';
import { ThemeMode, THEME_STORAGE_KEY, THEME_CLASS_MAP, VALID_THEMES } from '@/types/theme';

export function useAppTheme() {
  // Initialize theme from localStorage
  const [theme, setThemeState] = useState<ThemeMode>(() => {
    try {
      const stored = localStorage.getItem(THEME_STORAGE_KEY);
      if (stored) {
        // Try parsing as JSON (new format)
        try {
          const parsed = JSON.parse(stored);
          if (parsed.mode && VALID_THEMES.includes(parsed.mode)) {
            return parsed.mode;
          }
        } catch {
          // Legacy string format
          if (stored === 'dark' || stored === 'light') {
            return stored;
          }
        }
      }
    } catch (error) {
      console.warn('Failed to load theme preference:', error);
    }
    return 'light'; // Default
  });

  // Apply theme class to DOM
  useEffect(() => {
    const root = document.documentElement;
    
    // Remove all theme classes
    root.classList.remove('dark-mode-active', 'green-mode-active', 'green-dark-mode-active');
    
    // Apply new theme class
    const className = THEME_CLASS_MAP[theme];
    if (className) {
      root.classList.add(className);
    }
  }, [theme]);

  // Set theme function
  const setTheme = (mode: ThemeMode) => {
    setThemeState(mode);
    
    // Persist to localStorage
    try {
      const preference = {
        mode,
        updatedAt: new Date().toISOString(),
      };
      localStorage.setItem(THEME_STORAGE_KEY, JSON.stringify(preference));
    } catch (error) {
      console.warn('Failed to save theme preference:', error);
    }
  };

  // Helper function
  const isThemeActive = (mode: ThemeMode) => theme === mode;

  // Legacy support
  const isDarkMode = theme === 'dark' || theme === 'green-dark';
  const toggleTheme = () => {
    setTheme(isDarkMode ? 'light' : 'dark');
  };

  return {
    theme,
    setTheme,
    isThemeActive,
    // Legacy properties for backward compatibility
    isDarkMode,
    toggleTheme,
  };
}
```

**Migration Notes**:
- Existing code using `isDarkMode` and `toggleTheme` continues to work
- New code should use `theme` and `setTheme` for full theme support

**Verification**:
```typescript
// In a test component
const { theme, setTheme } = useAppTheme();
console.log('Current theme:', theme);
setTheme('green'); // Should apply green theme instantly
```

---

### Step 4: Create Theme Selector Component

**File**: `frontend/src/components/ThemeSelector.tsx` (create new)

**Implementation**:
```typescript
import { useAppTheme } from '@/hooks/useAppTheme';
import { VALID_THEMES } from '@/types/theme';
import type { ThemeMode } from '@/types/theme';

const THEME_OPTIONS: Array<{ mode: ThemeMode; label: string; icon: string }> = [
  { mode: 'light', label: 'Light', icon: '☀️' },
  { mode: 'dark', label: 'Dark', icon: '🌙' },
  { mode: 'green', label: 'Green', icon: '🌱' },
  { mode: 'green-dark', label: 'Green Dark', icon: '🌿' },
];

export function ThemeSelector() {
  const { theme, setTheme } = useAppTheme();

  return (
    <div className="theme-selector">
      <h3>Theme</h3>
      <div role="radiogroup" aria-label="Theme selection">
        {THEME_OPTIONS.map(({ mode, label, icon }) => (
          <label key={mode} className="theme-option">
            <input
              type="radio"
              name="theme"
              value={mode}
              checked={theme === mode}
              onChange={() => setTheme(mode)}
              aria-label={label}
            />
            <span className="theme-label">
              <span className="theme-icon" aria-hidden="true">{icon}</span>
              {label}
            </span>
          </label>
        ))}
      </div>
    </div>
  );
}
```

**Styling** (add to component CSS or index.css):
```css
.theme-selector {
  padding: 1rem;
}

.theme-option {
  display: flex;
  align-items: center;
  padding: 0.5rem;
  margin: 0.25rem 0;
  cursor: pointer;
  border-radius: var(--radius);
  transition: background 0.15s;
}

.theme-option:hover {
  background: var(--color-bg-secondary);
}

.theme-option input[type="radio"] {
  margin-right: 0.5rem;
}

.theme-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.theme-icon {
  font-size: 1.25rem;
}
```

**Verification**:
1. Import `ThemeSelector` into a settings page or header
2. Click each theme option
3. Verify instant theme change
4. Refresh page and verify theme persists

---

### Step 5: Add Theme Selector to Settings Page

**File**: `frontend/src/pages/Settings.tsx` (or equivalent)

**Action**: Import and render ThemeSelector component

```typescript
import { ThemeSelector } from '@/components/ThemeSelector';

export function Settings() {
  return (
    <div className="settings-page">
      <h1>Settings</h1>
      
      {/* Add theme selector */}
      <section className="settings-section">
        <ThemeSelector />
      </section>
      
      {/* Other settings... */}
    </div>
  );
}
```

**Alternative**: Add to app header for quick access
```typescript
import { ThemeSelector } from '@/components/ThemeSelector';

export function AppHeader() {
  return (
    <header className="app-header">
      {/* ... other header content ... */}
      <ThemeSelector />
    </header>
  );
}
```

---

### Step 6: Validate Accessibility

**Manual Testing**:

1. **Keyboard Navigation**:
   ```
   Tab → Focus on theme selector
   Arrow keys → Move between options
   Space/Enter → Select theme
   ```

2. **Screen Reader Testing**:
   - Enable VoiceOver (Mac) or NVDA (Windows)
   - Navigate to theme selector
   - Verify proper announcements

3. **Contrast Validation**:
   - Use WebAIM Contrast Checker: https://webaim.org/resources/contrastchecker/
   - Test all text/background combinations
   - Ensure minimum 4.5:1 ratio for normal text

**Automated Testing**:
```bash
# Install Lighthouse CI (if not already)
npm install --save-dev @lhci/cli

# Run accessibility audit
npm run lighthouse -- --only-categories=accessibility
```

**Expected Results**:
- All text meets WCAG 2.1 Level AA contrast requirements
- Theme selector is keyboard accessible
- Screen readers announce current selection

---

### Step 7: Test Edge Cases

**Test Scenarios**:

1. **Corrupted localStorage**:
   ```javascript
   localStorage.setItem('tech-connect-theme-mode', 'invalid-theme');
   // Reload app → Should fall back to 'light'
   ```

2. **localStorage Unavailable**:
   ```javascript
   // In browser's privacy/incognito mode
   // Reload app → Should use 'light', log warning
   ```

3. **Rapid Theme Switching**:
   ```javascript
   // Click multiple theme options quickly
   // Should not cause visual glitches or errors
   ```

4. **Legacy Data Migration**:
   ```javascript
   localStorage.setItem('tech-connect-theme-mode', 'dark');
   // Reload app → Should migrate to new format, preserve 'dark' theme
   ```

5. **Cross-Session Persistence**:
   ```javascript
   // Select green theme
   // Close browser completely
   // Reopen app → Should still be green theme
   ```

---

## Testing Checklist

### Functional Testing

- [ ] Theme selector displays all four options (Light, Dark, Green, Green Dark)
- [ ] Clicking a theme option applies the theme instantly (<1 second)
- [ ] Selected theme is visually indicated (radio button checked)
- [ ] Theme persists after page reload
- [ ] Theme persists after browser close/reopen
- [ ] Legacy `isDarkMode` and `toggleTheme` still work for existing code

### Visual Testing

- [ ] All text is readable in all four themes
- [ ] Buttons have sufficient contrast in all themes
- [ ] Links are distinguishable from regular text
- [ ] Hover states are visible in all themes
- [ ] Focus indicators are visible in all themes

### Accessibility Testing

- [ ] Theme selector is keyboard accessible (Tab, Arrow keys, Enter)
- [ ] Screen reader announces theme options and current selection
- [ ] All color combinations meet WCAG 2.1 AA standards (4.5:1 normal text, 3:1 large text)
- [ ] Radio buttons have proper labels and ARIA attributes

### Edge Case Testing

- [ ] Invalid theme data in localStorage falls back to default
- [ ] localStorage unavailable doesn't break app
- [ ] Rapid theme switching works without glitches
- [ ] Legacy string values in localStorage migrate correctly

### Cross-Browser Testing

- [ ] Chrome/Edge (Chromium)
- [ ] Firefox
- [ ] Safari (macOS/iOS)
- [ ] Mobile browsers (iOS Safari, Chrome Mobile)

---

## Troubleshooting

### Issue: Theme doesn't apply on first load

**Cause**: localStorage not being read correctly  
**Solution**: Check browser console for errors, verify THEME_STORAGE_KEY constant

### Issue: Theme flashes default before applying saved theme

**Cause**: Delay between mount and localStorage read  
**Solution**: This is expected for client-side storage; consider SSR if critical

### Issue: TypeScript errors about ThemeMode

**Cause**: Type definitions not imported correctly  
**Solution**: Ensure `@/types/theme` exports are correct and path alias is configured

### Issue: CSS not applying in production build

**Cause**: CSS classes may be tree-shaken or purged  
**Solution**: Add theme class names to safelist in CSS optimization config

### Issue: Contrast ratio fails validation

**Cause**: Colors don't meet WCAG AA requirements  
**Solution**: Adjust color values darker/lighter, revalidate with WebAIM checker

---

## Performance Considerations

**Expected Performance**:
- Theme initialization: <5ms (localStorage read)
- Theme switching: <50ms (state update + DOM class change)
- CSS updates: Instant (browser hardware acceleration)
- Storage write: <1ms (localStorage write)

**No performance optimization needed** for this feature - CSS custom properties are highly efficient.

---

## Rollback Plan

If issues arise in production:

1. **Quick Rollback**: Revert the PR
   ```bash
   git revert <commit-hash>
   git push
   ```

2. **Partial Disable**: Comment out theme selector in UI, keep hook and CSS
   ```typescript
   // Temporarily hide theme selector
   // import { ThemeSelector } from '@/components/ThemeSelector';
   ```

3. **Force Default Theme**: Override localStorage on app load
   ```typescript
   localStorage.setItem('tech-connect-theme-mode', JSON.stringify({ mode: 'light' }));
   ```

---

## Next Steps

After successful implementation:

1. **Gather User Feedback**: Monitor user adoption and feedback
2. **Analytics** (optional): Track theme selection preferences
3. **Documentation**: Update user-facing help docs with theme instructions
4. **Future Enhancements**:
   - Theme preview before selection
   - Animated transitions between themes
   - Sync theme preference across devices (requires backend)
   - Additional theme colors (blue, red, etc.)

---

## Support & Resources

- **Feature Spec**: `specs/002-green-theme/spec.md`
- **Data Model**: `specs/002-green-theme/data-model.md`
- **Contracts**: `specs/002-green-theme/contracts/`
- **WCAG Guidelines**: https://www.w3.org/WAI/WCAG21/quickref/
- **WebAIM Contrast Checker**: https://webaim.org/resources/contrastchecker/

---

## Summary

This quickstart provides a complete implementation guide for the green theme feature:

1. ✅ Update TypeScript type definitions
2. ✅ Add green theme CSS to index.css
3. ✅ Refactor useAppTheme hook to support multiple themes
4. ✅ Create ThemeSelector component
5. ✅ Add theme selector to UI (settings or header)
6. ✅ Validate accessibility compliance
7. ✅ Test edge cases and cross-browser compatibility

Follow the steps in order, verify each step before proceeding, and use the testing checklist to ensure complete coverage.

**Estimated Implementation Time**: 2-3 hours for experienced developer
