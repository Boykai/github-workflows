# Research & Technology Decisions: Green Theme Option

**Feature**: Green Theme Option  
**Branch**: `002-green-theme`  
**Date**: 2026-02-14  
**Phase**: 0 - Research

## Overview

This document captures all technology decisions, research findings, and rationale for implementing the green theme option feature. Each decision addresses a specific technical unknown or design choice.

---

## Decision 1: Green Color Palette Selection

**Context**: The green theme needs a cohesive color palette for primary UI elements (backgrounds, buttons, links) while meeting WCAG 2.1 Level AA contrast requirements (4.5:1 for normal text, 3:1 for large text).

**Decision**: Use a nature-inspired green palette with the following values:
- Primary green (light mode): `#2da44e` (GitHub's success green)
- Primary green (dark mode): `#3fb950` (lighter, more visible on dark backgrounds)
- Secondary backgrounds: Subtle green tints for layering
- Success indicators: Deeper forest green
- Text colors: Maintain high contrast with backgrounds

**Rationale**: 
- GitHub's green palette is proven for accessibility and has been extensively tested
- The selected shades maintain 4.5:1+ contrast ratios when paired appropriately
- Nature-inspired greens are psychologically calming and widely preferred
- Using existing GitHub design system colors ensures professional appearance

**Alternatives Considered**:
1. **Material Design Green**: Would require custom contrast validation
2. **Custom vibrant green**: Risk of eye strain and accessibility issues
3. **Multiple green shades**: Added complexity without clear user value

**Verification**: Use WebAIM contrast checker to validate all text/background combinations meet WCAG AA standards.

---

## Decision 2: CSS Variable Pattern Extension

**Context**: The existing theme system uses CSS custom properties defined in `:root` and overridden in `html.dark-mode-active`. We need to extend this pattern to support green theme variants.

**Decision**: Extend the CSS class-based theming approach with:
- `html.green-mode-active` for light green theme
- `html.green-dark-mode-active` for dark green theme
- Reuse existing CSS variable names (`--color-primary`, `--color-bg`, etc.)
- Apply appropriate classes to `document.documentElement`

**Rationale**:
- Maintains consistency with existing theme architecture
- CSS specificity rules naturally override base values
- No need to modify HTML structure or component code
- Enables instant theme switching via class toggling
- Supports future theme additions without architectural changes

**Alternatives Considered**:
1. **Data attributes (`data-theme="green"`)**: Less browser support, same complexity
2. **Separate CSS files per theme**: Would require dynamic stylesheet loading
3. **CSS-in-JS**: Would require significant refactoring of existing styles

**Implementation Pattern**:
```css
/* Green light theme */
html.green-mode-active {
  --color-primary: #2da44e;
  --color-bg: #ffffff;
  /* ... other overrides */
}

/* Green dark theme */
html.green-dark-mode-active {
  --color-primary: #3fb950;
  --color-bg: #0d1117;
  /* ... other overrides */
}
```

---

## Decision 3: Theme State Management Approach

**Context**: The current `useAppTheme` hook manages a boolean `isDarkMode` state. We need to support multiple theme options (default, dark, green, green-dark).

**Decision**: Refactor `useAppTheme` to manage theme as an enumerated string value:
- Theme type: `'light' | 'dark' | 'green' | 'green-dark'`
- localStorage key: Keep existing `'tech-connect-theme-mode'` for backward compatibility
- State management: Use single state variable for current theme
- Class application: Apply corresponding CSS class to `document.documentElement`

**Rationale**:
- Enum string values are more maintainable than boolean flags
- Scales naturally to additional themes in the future
- Backward compatible with existing localStorage values
- Simplifies conditional logic in components
- Type-safe with TypeScript discriminated unions

**Alternatives Considered**:
1. **Multiple boolean flags**: `isGreen`, `isDark` - becomes combinatorial nightmare
2. **Separate hooks per theme**: Would duplicate logic and state
3. **Context API for theme**: Over-engineered for client-side-only state

**Migration Strategy**: Detect legacy boolean values in localStorage and convert to new format on first load.

---

## Decision 4: Theme Selector UI Component

**Context**: Need a UI control in settings to allow users to select between available themes.

**Decision**: Create a radio button group or dropdown selector with:
- Theme options: Default, Dark, Green, Green Dark
- Visual preview: Small color swatch next to each option
- Active indicator: Radio selection or checkmark
- Location: Settings page (or app header for quick access)

**Rationale**:
- Radio buttons provide clear single-selection semantics
- Visual previews help users make informed choices
- Familiar UI pattern requires no learning curve
- Accessible via keyboard and screen readers

**Alternatives Considered**:
1. **Toggle switches**: Only work for binary choices (dark/light)
2. **Color picker**: Too complex for predefined themes
3. **Automatic detection**: Would override user preference

**Accessibility Considerations**:
- Use semantic HTML (`<input type="radio">` or `<select>`)
- Provide labels with theme names, not just colors
- Ensure focus indicators are visible
- Include ARIA labels for screen readers

---

## Decision 5: Persistence Strategy

**Context**: Theme preference must persist across browser sessions and page reloads.

**Decision**: Use browser localStorage with key `'tech-connect-theme-mode'`:
- Store theme as string value (`'light'`, `'dark'`, `'green'`, `'green-dark'`)
- Read on application mount
- Update on theme change
- Scoped to origin (device-specific as per spec)

**Rationale**:
- localStorage is synchronous and immediately available on mount
- No network requests required (faster initial render)
- Works offline
- Sufficient for device-specific preferences
- Existing pattern in codebase

**Alternatives Considered**:
1. **Server-side user profile**: Requires authentication, network calls, added complexity
2. **Cookies**: More limited storage, unnecessary for client-only data
3. **sessionStorage**: Would not persist across browser sessions (violates FR-004)
4. **IndexedDB**: Over-engineered for simple key-value storage

**Edge Case Handling**: If localStorage is unavailable (privacy mode, storage full), fall back to default theme and display warning.

---

## Decision 6: Instant Theme Application

**Context**: FR-003 requires instant theme changes without page refresh. Current architecture uses React state and CSS classes.

**Decision**: Maintain existing instant application mechanism:
- Theme state update triggers React re-render
- `useEffect` hook applies CSS class to `document.documentElement`
- CSS custom properties update instantly via browser rendering
- No page reload or manual refresh needed

**Rationale**:
- Current architecture already supports this requirement
- CSS custom properties update immediately on class change
- React state changes propagate synchronously to DOM
- No additional work needed beyond existing pattern

**Performance Considerations**:
- CSS class changes are fast (single DOM operation)
- Custom property updates are hardware-accelerated by browsers
- No JavaScript-based style recalculation needed
- Meets the <1 second requirement from SC-001

---

## Decision 7: Accessibility Validation Approach

**Context**: FR-005 requires WCAG 2.1 Level AA contrast ratios (4.5:1 normal text, 3:1 large text).

**Decision**: Validate contrast ratios using automated tools during development:
- **Tool**: WebAIM Contrast Checker (https://webaim.org/resources/contrastchecker/)
- **Process**: Test all text/background combinations before committing CSS
- **Documentation**: Record contrast ratios in code comments
- **CI Integration**: Consider adding automated contrast checks (optional)

**Color Pairing Guidelines**:
- Light green backgrounds: Use dark text (#24292f or darker)
- Dark green backgrounds: Use light text (#e6edf3 or lighter)
- Green buttons: Ensure button text meets 4.5:1 minimum
- Links: Test against both background and surrounding text

**Rationale**:
- Manual testing with proven tools is sufficient for MVP
- Automated testing can be added later if needed
- Documenting ratios in comments aids future maintenance
- Prevention during development is more efficient than fixing post-implementation

**Alternatives Considered**:
1. **Automated CI checks**: Good long-term but adds setup complexity
2. **Design system tokens**: Over-engineered for single feature
3. **Manual visual inspection**: Insufficient for accessibility compliance

---

## Decision 8: Fallback Behavior for Invalid Theme Data

**Context**: FR-007 requires graceful fallback if theme preference data is corrupted or invalid.

**Decision**: Implement defensive validation in theme initialization:
```typescript
const VALID_THEMES = ['light', 'dark', 'green', 'green-dark'] as const;

function loadThemeFromStorage(): ThemeMode {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored && VALID_THEMES.includes(stored as ThemeMode)) {
      return stored as ThemeMode;
    }
  } catch (error) {
    console.warn('Failed to load theme preference:', error);
  }
  return 'light'; // Safe default
}
```

**Rationale**:
- Try-catch handles localStorage access errors (privacy mode, quota exceeded)
- Explicit validation prevents invalid values from breaking UI
- Silent fallback to default ensures app remains functional
- Logging aids debugging without interrupting user experience

**Error Scenarios Handled**:
- localStorage throws error (SecurityError, QuotaExceededError)
- Stored value is not a valid theme string
- Stored value is null or undefined
- localStorage is disabled by browser policy

---

## Summary

All technical decisions are now resolved. Key technologies:
- **Frontend**: React with TypeScript
- **Styling**: CSS custom properties with class-based theming
- **State**: React hooks (`useState`, `useEffect`)
- **Persistence**: Browser localStorage
- **Accessibility**: WebAIM Contrast Checker validation

No external dependencies required. Implementation extends existing theme system architecture.

**Next Phase**: Proceed to Phase 1 - Design (data-model.md, contracts/, quickstart.md)
