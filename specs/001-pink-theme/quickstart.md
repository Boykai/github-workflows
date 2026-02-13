# Quickstart Guide: Pink Theme Implementation

**Feature**: 001-pink-theme  
**Date**: 2026-02-13  
**Target Audience**: Developers implementing the pink theme feature

## Overview

This quickstart guide provides a streamlined path to understanding and implementing the pink color theme feature. It covers the key concepts, implementation steps, and testing strategies.

---

## What You're Building

A pink color theme option that extends the existing default/dark theme system. Users will be able to:

1. ✅ Select "Pink" or "Pink Dark" theme from a theme selector UI
2. ✅ See all UI components immediately switch to pink color palette
3. ✅ Have their theme preference persist across sessions
4. ✅ Experience WCAG 2.1 AA compliant colors (accessible to users with visual impairments)

**Existing System**: The app currently has a binary dark/light theme toggle using CSS custom properties.

**What's New**: Expanding to four themes (default, dark, pink, pink-dark) with a proper theme selector.

---

## Key Concepts

### 1. CSS Custom Properties (CSS Variables)

The theme system uses CSS variables defined in `frontend/src/index.css`:

```css
:root {
  --color-primary: #0969da;
  --color-bg: #ffffff;
  --color-text: #24292f;
  /* ... more variables */
}

html.dark-mode-active {
  --color-primary: #539bf5;
  --color-bg: #0d1117;
  --color-text: #e6edf3;
  /* ... overrides */
}
```

**Why this pattern?**
- Changes apply instantly (no page reload)
- Works across all components automatically
- Excellent browser support
- Simple to extend with new themes

### 2. Theme State Management

The `useAppTheme` hook manages theme state:

```typescript
// Current (binary):
const { isDarkMode, toggleTheme } = useAppTheme();

// New (multi-theme):
const { currentTheme, setTheme } = useAppTheme();
setTheme('pink'); // or 'pink-dark'
```

Theme state is:
- Initialized from `localStorage` on mount
- Stored in React state for reactivity
- Persisted to `localStorage` on change
- Applied to DOM via CSS classes

### 3. Theme Persistence

Theme preference is stored in `localStorage`:

```json
{
  "mode": "pink",
  "lastUpdated": "2026-02-13T10:30:00Z",
  "version": 1
}
```

**Key**: `tech-connect-theme-mode`

**Fallback**: If localStorage is unavailable (e.g., private browsing), theme selection works in-session only.

---

## Architecture Overview

```
┌─────────────────────┐
│ User clicks theme   │
│ in selector         │
└──────────┬──────────┘
           │
           v
┌─────────────────────┐
│ ThemeSelector calls │
│ setTheme('pink')    │
└──────────┬──────────┘
           │
           v
┌─────────────────────────┐
│ useAppTheme hook:       │
│ 1. Updates React state  │
│ 2. Applies CSS classes  │
│ 3. Saves to localStorage│
└──────────┬──────────────┘
           │
           v
┌─────────────────────────┐
│ CSS variables change    │
│ based on applied classes│
└──────────┬──────────────┘
           │
           v
┌─────────────────────────┐
│ All components re-render│
│ with new colors         │
└─────────────────────────┘
```

---

## Implementation Steps

### Step 1: Extend Type Definitions (10 min)

**File**: `frontend/src/types/theme.ts` (new file)

```typescript
export type ThemeMode = 'default' | 'dark' | 'pink' | 'pink-dark';

export interface ThemePreference {
  mode: ThemeMode;
  lastUpdated: string;
  version: number;
}

export interface ThemeOption {
  value: ThemeMode;
  label: string;
  previewColor: string;
  ariaLabel: string;
}
```

**Why**: Provides type safety and prevents typos in theme names.

---

### Step 2: Add Pink Theme CSS (20 min)

**File**: `frontend/src/index.css`

Add new CSS sections:

```css
/* Pink theme (light) */
html.pink-theme-active {
  --color-primary: #e85aad;
  --color-secondary: #c77ba3;
  --color-bg: #ffebf6;
  --color-bg-secondary: #ffe0f0;
  --color-border: #f0b5d6;
  --color-text: #2d1520;
  --color-text-secondary: #6b3a52;
  --shadow: 0 1px 3px rgba(232, 90, 173, 0.15);
}

/* Pink theme (dark) - combines both classes */
html.pink-theme-active.dark-mode-active {
  --color-primary: #ff94d1;
  --color-secondary: #e85aad;
  --color-bg: #1a0d14;
  --color-bg-secondary: #2b1420;
  --color-border: #4a2438;
  --color-text: #f8e7f1;
  --color-text-secondary: #d4a5c4;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
}
```

**Testing**: Manually add `pink-theme-active` class to `<html>` in browser DevTools to see colors change.

---

### Step 3: Update useAppTheme Hook (30 min)

**File**: `frontend/src/hooks/useAppTheme.ts`

**Changes**:
1. Replace `isDarkMode` state with `currentTheme: ThemeMode`
2. Replace `toggleTheme` with `setTheme(theme: ThemeMode)`
3. Update localStorage read/write to handle new format
4. Update CSS class application logic
5. Keep legacy methods for backward compatibility (deprecated)

**Key Logic**:

```typescript
const setTheme = (theme: ThemeMode) => {
  setCurrentTheme(theme);
  
  // Apply CSS classes
  document.documentElement.classList.remove('dark-mode-active', 'pink-theme-active');
  if (theme === 'dark') {
    document.documentElement.classList.add('dark-mode-active');
  } else if (theme === 'pink') {
    document.documentElement.classList.add('pink-theme-active');
  } else if (theme === 'pink-dark') {
    document.documentElement.classList.add('pink-theme-active', 'dark-mode-active');
  }
  
  // Persist
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      mode: theme,
      lastUpdated: new Date().toISOString(),
      version: 1,
    }));
  } catch (e) {
    console.warn('Failed to save theme preference:', e);
  }
};
```

**Testing**: Call `setTheme('pink')` in React DevTools and verify CSS classes are applied.

---

### Step 4: Create ThemeSelector Component (40 min)

**File**: `frontend/src/components/theme/ThemeSelector.tsx` (new file)

Create a dropdown/select component that:
- Displays all theme options (Default, Dark, Pink, Pink Dark)
- Shows color preview swatches
- Calls `setTheme()` on selection
- Is keyboard accessible (Space/Enter, Arrow keys)
- Has proper ARIA labels

**Component Structure**:

```typescript
import { useState } from 'react';
import { ThemeMode, ThemeOption } from '@/types/theme';

const THEME_OPTIONS: ThemeOption[] = [
  { value: 'default', label: 'Default', previewColor: '#0969da', ariaLabel: '...' },
  { value: 'dark', label: 'Dark', previewColor: '#539bf5', ariaLabel: '...' },
  { value: 'pink', label: 'Pink', previewColor: '#e85aad', ariaLabel: '...' },
  { value: 'pink-dark', label: 'Pink Dark', previewColor: '#ff94d1', ariaLabel: '...' },
];

export function ThemeSelector({ currentTheme, onThemeChange }) {
  const [isOpen, setIsOpen] = useState(false);
  
  // Render dropdown with options
  // Handle keyboard navigation
  // Call onThemeChange when user selects
}
```

**Testing**: Render component in isolation with different `currentTheme` values.

---

### Step 5: Integrate ThemeSelector in App (15 min)

**File**: `frontend/src/App.tsx`

Replace the current theme toggle button with ThemeSelector:

```typescript
// Before:
<button onClick={toggleTheme}>
  {isDarkMode ? '☀️' : '🌙'}
</button>

// After:
<ThemeSelector
  currentTheme={currentTheme}
  onThemeChange={setTheme}
/>
```

**Testing**: Click through all theme options and verify UI updates.

---

### Step 6: Add Unit Tests (30 min)

**File**: `frontend/src/hooks/useAppTheme.test.ts` (new file)

Test cases:
- ✅ Hook initializes with default theme
- ✅ Hook loads theme from localStorage on mount
- ✅ `setTheme()` updates state and applies CSS classes
- ✅ `setTheme()` persists to localStorage
- ✅ Hook handles corrupted localStorage data gracefully
- ✅ Legacy methods (`isDarkMode`, `toggleTheme`) still work

**File**: `frontend/src/components/theme/ThemeSelector.test.tsx` (new file)

Test cases:
- ✅ Component renders all theme options
- ✅ Component calls `onThemeChange` when option selected
- ✅ Component is keyboard accessible
- ✅ Component shows current theme as selected

---

### Step 7: Add E2E Tests (40 min)

**File**: `frontend/e2e/theme.spec.ts` (new file)

Test scenarios:
- ✅ User can select pink theme from selector
- ✅ UI colors change to pink when theme selected
- ✅ Theme persists after page reload
- ✅ Pink theme meets accessibility contrast standards (via axe-core)

**Example**:

```typescript
test('user can select pink theme', async ({ page }) => {
  await page.goto('/');
  await page.click('[aria-label="Choose theme"]');
  await page.click('text=Pink');
  
  // Verify CSS class applied
  const htmlClass = await page.locator('html').getAttribute('class');
  expect(htmlClass).toContain('pink-theme-active');
  
  // Verify color changed
  const primaryColor = await page.evaluate(() => {
    return getComputedStyle(document.documentElement)
      .getPropertyValue('--color-primary');
  });
  expect(primaryColor).toBe('#e85aad');
});
```

---

## Testing Strategy

### Manual Testing Checklist

Before marking the feature complete:

- [ ] All four themes can be selected
- [ ] Theme changes apply instantly (no flicker)
- [ ] Theme persists after browser refresh
- [ ] Theme persists after closing/reopening browser
- [ ] All text is readable in all themes (no contrast issues)
- [ ] Theme selector is keyboard accessible (Tab, Space, Arrow keys, Enter)
- [ ] Theme selector has proper ARIA labels for screen readers
- [ ] Works in Chrome, Firefox, Safari, Edge
- [ ] Works in private/incognito mode (localStorage fallback)

### Automated Testing

**Run Unit Tests**:
```bash
cd frontend
npm run test
```

**Run E2E Tests**:
```bash
cd frontend
npm run test:e2e
```

**Run Accessibility Tests**:
```bash
cd frontend
npm run test:e2e -- --grep "accessibility"
```

---

## Accessibility Verification

### Contrast Ratio Checking

Use WebAIM Contrast Checker: https://webaim.org/resources/contrastchecker/

**Required Ratios** (WCAG 2.1 Level AA):
- Normal text: 4.5:1
- Large text (18pt+ or 14pt+ bold): 3:1
- UI components: 3:1

**Pink Theme Combinations to Check**:
- Text (#2d1520) on Background (#ffebf6): Should be 12.8:1 ✅
- Text (#2d1520) on Background Secondary (#ffe0f0): Should be 13.1:1 ✅
- Primary (#e85aad) on Background (#ffebf6): Should be 3.1:1 ✅

**Pink Dark Theme Combinations to Check**:
- Text (#f8e7f1) on Background (#1a0d14): Should be 13.5:1 ✅
- Text (#f8e7f1) on Background Secondary (#2b1420): Should be 11.2:1 ✅
- Primary (#ff94d1) on Background (#1a0d14): Should be 7.8:1 ✅

### Screen Reader Testing

Test with:
- **macOS**: VoiceOver (Cmd+F5)
- **Windows**: NVDA (free) or JAWS
- **Linux**: Orca

Verify:
- Theme selector announces current theme
- Theme options are clearly labeled
- Selection confirmation is announced

---

## Troubleshooting

### Theme doesn't persist

**Symptom**: Theme reverts to default on page reload.

**Likely Causes**:
1. localStorage is disabled (private browsing)
2. localStorage write failed silently
3. Storage key mismatch

**Debug**:
```javascript
// In browser console
localStorage.getItem('tech-connect-theme-mode');
// Should return JSON string with theme data
```

### Theme colors not applying

**Symptom**: CSS classes are added but colors don't change.

**Likely Causes**:
1. CSS specificity issue
2. CSS custom property name mismatch
3. Browser cache

**Debug**:
```javascript
// In browser console
getComputedStyle(document.documentElement).getPropertyValue('--color-primary');
// Should return pink color value
```

### Theme flickers on load

**Symptom**: Brief flash of default theme before pink theme applies.

**Solution**: Apply theme class synchronously before React renders (in index.html or early in main.tsx).

---

## Performance Considerations

### Current Performance Target

- **Theme Application**: < 500ms (spec requirement)
- **Actual Expected**: < 100ms (CSS custom properties update synchronously)

### Optimization Techniques

1. **Avoid Layout Thrashing**: Update all CSS variables at once
2. **Minimize Repaints**: Only change root-level variables
3. **No Async Operations**: Apply theme synchronously
4. **Batch State Updates**: Use React's automatic batching

### Performance Monitoring

Add performance marks:

```typescript
const setTheme = (theme: ThemeMode) => {
  performance.mark('theme-change-start');
  
  // ... theme change logic ...
  
  performance.mark('theme-change-end');
  performance.measure('theme-change', 'theme-change-start', 'theme-change-end');
};
```

View in Chrome DevTools Performance tab.

---

## Migration Notes

### Backward Compatibility

The updated `useAppTheme` hook maintains backward compatibility:

```typescript
// Old API (still works, deprecated)
const { isDarkMode, toggleTheme } = useAppTheme();

// New API (preferred)
const { currentTheme, setTheme } = useAppTheme();
```

**Migration Path**:
1. Deploy new theme system with backward-compatible hook
2. Update components to use new API in subsequent PRs
3. Remove deprecated methods in future version

### Data Migration

Old localStorage format:
```
Key: tech-connect-theme-mode
Value: "dark" or "light"
```

New format:
```json
{
  "mode": "dark",
  "lastUpdated": "2026-02-13T10:30:00Z",
  "version": 1
}
```

**Migration Logic** (handled in `useAppTheme`):
```typescript
const legacyValue = localStorage.getItem(STORAGE_KEY);
if (legacyValue === 'dark' || legacyValue === 'light') {
  // Old format detected, migrate
  const newMode = legacyValue === 'dark' ? 'dark' : 'default';
  // Save in new format
}
```

---

## Resources

### Design Assets
- **Color Palettes**: See `data-model.md` for exact color values
- **Contrast Ratios**: Validated in `data-model.md`

### Code References
- **Existing Theme Hook**: `frontend/src/hooks/useAppTheme.ts`
- **Existing CSS Variables**: `frontend/src/index.css`
- **Type Definitions**: `specs/001-pink-theme/contracts/types.md`

### Tools
- **WebAIM Contrast Checker**: https://webaim.org/resources/contrastchecker/
- **Chrome DevTools**: Color contrast in Accessibility panel
- **axe DevTools**: Browser extension for accessibility testing

---

## Timeline Estimate

| Task | Time | Dependencies |
|------|------|--------------|
| Type definitions | 10 min | None |
| CSS variables | 20 min | Types |
| Update hook | 30 min | Types |
| Create component | 40 min | Types, Hook |
| Integrate in App | 15 min | Component |
| Unit tests | 30 min | Hook, Component |
| E2E tests | 40 min | Full integration |
| Manual QA | 30 min | All above |
| **Total** | **~3.5 hours** | |

**Note**: Times are estimates for experienced developers familiar with the codebase.

---

## Next Steps

After completing implementation:

1. ✅ Run all tests and verify they pass
2. ✅ Perform manual accessibility testing
3. ✅ Test on all target browsers
4. ✅ Update user documentation (if exists)
5. ✅ Create PR with detailed description and screenshots
6. ✅ Request code review from team

**Ready to Start**: Begin with Step 1 (Type Definitions) and work through the steps sequentially.

---

**Document Version**: 1.0  
**Last Updated**: 2026-02-13  
**Next**: See `tasks.md` (generated by `/speckit.tasks` command) for granular task breakdown.
