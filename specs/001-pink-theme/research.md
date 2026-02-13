# Research Document: Pink Color Theme

**Feature**: 001-pink-theme  
**Date**: 2026-02-13  
**Phase**: 0 (Research & Analysis)

## Overview

This document consolidates research findings for implementing a pink color theme in the application. Research covers color selection, accessibility compliance, theme architecture patterns, and best practices for multi-theme systems.

---

## 1. Pink Color Palette Selection

### Decision: GitHub-Inspired Pink Palette

We will use a pink color palette inspired by GitHub's color system, adapted for a cohesive pink theme that maintains consistency with the existing default and dark themes.

**Primary Pink Colors**:
- **Primary Pink**: `#e85aad` (vibrant pink for main actions and emphasis)
- **Secondary Pink**: `#bf3a8f` (darker pink for hover states and secondary actions)
- **Light Pink**: `#ffebf6` (very light pink for backgrounds)
- **Pink Border**: `#f0b5d6` (soft pink for borders)
- **Pink Text**: `#8f1d5f` (dark pink for readable text on light backgrounds)

**Dark Mode Pink Colors** (adjusted for dark backgrounds):
- **Primary Pink**: `#ff94d1` (brighter pink that stands out on dark backgrounds)
- **Secondary Pink**: `#e85aad` (standard pink for secondary elements)
- **Dark Pink BG**: `#2b1420` (very dark pink-tinted background)
- **Dark Pink Border**: `#4a2438` (darker pink border)
- **Pink Text Dark**: `#ffcce8` (light pink for text on dark backgrounds)

**Rationale**:
- These colors provide sufficient vibrancy to create a distinct "pink" theme
- They maintain semantic meaning (primary/secondary/success/danger) through saturation and lightness adjustments
- The palette has been tested for contrast ratios against both light and dark backgrounds

**Alternatives Considered**:
- **Material Design Pink**: Too saturated and potentially overwhelming for long-term use
- **Pastel Pink Only**: Insufficient contrast ratios, failed accessibility requirements
- **Hot Pink/Magenta**: Too harsh, poor readability for extended sessions

---

## 2. WCAG 2.1 Accessibility Compliance

### Decision: Contrast Ratio Validation Required

All pink theme colors must meet WCAG 2.1 Level AA standards:
- **Normal text (< 18pt)**: Minimum 4.5:1 contrast ratio
- **Large text (≥ 18pt or ≥ 14pt bold)**: Minimum 3:1 contrast ratio
- **UI components and graphical objects**: Minimum 3:1 contrast ratio

**Implementation Approach**:
- Use WebAIM Contrast Checker or similar tools during development
- Include automated contrast testing in E2E tests using Playwright with axe-core
- Document contrast ratios for each color combination in data-model.md

**Rationale**:
- WCAG 2.1 Level AA is the industry standard for web accessibility
- Meeting these standards ensures the theme is usable by users with visual impairments
- Automated testing prevents regression and ensures ongoing compliance

**Alternatives Considered**:
- **WCAG AAA (7:1 ratio)**: Too restrictive for a vibrant pink theme, would require very dark pinks that lose the "pink" aesthetic
- **Manual testing only**: Error-prone and not sustainable for ongoing development

---

## 3. Theme Architecture Pattern

### Decision: Extend Existing CSS Custom Properties System

The current theme system uses CSS custom properties (CSS variables) with theme-specific classes applied to `document.documentElement`. We will extend this pattern for the pink theme.

**Current Pattern** (from `index.css`):
```css
:root {
  --color-primary: #0969da;
  --color-bg: #ffffff;
  /* ... other variables */
}

html.dark-mode-active {
  --color-primary: #539bf5;
  --color-bg: #0d1117;
  /* ... overrides */
}
```

**Extended Pattern for Pink Theme**:
```css
html.pink-theme-active {
  --color-primary: #e85aad;
  --color-bg: #ffebf6;
  /* ... pink overrides */
}

html.pink-theme-active.dark-mode-active {
  --color-primary: #ff94d1;
  --color-bg: #2b1420;
  /* ... dark pink overrides */
}
```

**Hook Extension** (from `useAppTheme.ts`):
- Change from boolean `isDarkMode` to string-based `theme` state: `'default' | 'dark' | 'pink' | 'pink-dark'`
- Store theme preference in localStorage
- Apply appropriate CSS classes based on theme selection

**Rationale**:
- Consistent with existing implementation pattern
- CSS custom properties provide excellent performance and browser support
- Allows dynamic theme switching without page reload
- Supports compound themes (light pink, dark pink)

**Alternatives Considered**:
- **CSS-in-JS (styled-components/emotion)**: Would require major refactoring of existing codebase, increases bundle size
- **Separate CSS files per theme**: More complex build process, slower theme switching, cache invalidation issues
- **SCSS/SASS variables**: Not runtime-dynamic, would require build-time theme generation

---

## 4. Theme Persistence Strategy

### Decision: localStorage with Fallback

Continue using `localStorage` for theme preference persistence, with graceful fallback to default theme if storage is unavailable.

**Storage Format**:
```typescript
// Current: localStorage.setItem('tech-connect-theme-mode', 'dark' | 'light')
// New: localStorage.setItem('tech-connect-theme-mode', 'default' | 'dark' | 'pink' | 'pink-dark')
```

**Fallback Behavior**:
- If localStorage is unavailable (private browsing, storage quota exceeded), theme selection works in-session only
- Default theme is applied on next session if persistence fails
- User is informed via console warning (non-intrusive)

**Rationale**:
- localStorage is well-supported across modern browsers
- Simple, synchronous API suitable for theme preferences
- Minimal implementation changes required

**Alternatives Considered**:
- **IndexedDB**: Overkill for a single key-value preference, adds complexity
- **Cookies**: Limited size, sent with every request (unnecessary overhead), GDPR concerns
- **Server-side storage**: Requires backend changes and authentication, offline access issues

---

## 5. Theme Selector UI Pattern

### Decision: Dropdown/Segmented Control with Theme Preview

Implement a theme selector UI that allows users to choose between default, dark, pink, and pink-dark themes.

**UI Approach**:
- Replace binary toggle button with dropdown or segmented control
- Options: "Default", "Dark", "Pink", "Pink Dark"
- Visual preview indicators (color swatches) for each option
- Accessible via keyboard navigation (Space/Enter to open, Arrow keys to select)

**Location**:
- Keep in header next to current theme toggle button
- Maintain existing accessibility attributes (aria-label)

**Rationale**:
- Clear, discoverable UI for theme selection
- Scales to support additional themes in the future
- Maintains accessibility through proper ARIA attributes and keyboard support

**Alternatives Considered**:
- **Separate settings page**: Adds friction, less discoverable
- **Multiple toggle buttons**: Clutters UI, doesn't scale well
- **Context menu (right-click)**: Poor discoverability, not mobile-friendly

---

## 6. Testing Strategy

### Decision: Multi-Layer Testing Approach

**Unit Tests** (Vitest):
- Theme state management logic in `useAppTheme` hook
- localStorage read/write operations
- CSS class application logic

**E2E Tests** (Playwright):
- Theme selection flow (click dropdown, select pink, verify UI changes)
- Theme persistence across page reloads
- Accessibility compliance (contrast ratios via axe-core integration)
- Cross-browser compatibility (Chrome, Firefox, Safari)

**Manual QA Checklist**:
- Visual inspection of all major components (header, sidebar, buttons, cards, inputs)
- Color blindness simulation (Chrome DevTools)
- High contrast mode compatibility (Windows/macOS)

**Rationale**:
- Comprehensive coverage at multiple levels ensures quality
- Automated accessibility testing prevents regressions
- Manual QA catches visual issues that automated tests may miss

**Alternatives Considered**:
- **Visual regression testing (Percy/Chromatic)**: Adds cost and complexity, overkill for this feature
- **Manual testing only**: Not sustainable, prone to human error

---

## 7. Performance Considerations

### Decision: Optimize for Instant Theme Switching

Ensure theme switching completes within the 500ms performance goal specified in the feature spec.

**Optimization Techniques**:
- CSS custom properties update synchronously (no async operations)
- Minimize repaints by updating only root-level CSS variables
- Avoid layout thrashing by batching DOM reads/writes
- Use `requestAnimationFrame` if visual transitions are added

**Monitoring**:
- Add performance marks in theme switching code
- Measure time from user click to visual update completion
- Target: < 100ms for theme application (well under 500ms requirement)

**Rationale**:
- Instant feedback improves perceived performance and user satisfaction
- CSS custom properties are designed for efficient runtime updates
- Modern browsers optimize CSS variable changes

**Alternatives Considered**:
- **Delayed theme application with loading spinner**: Poor UX, unnecessary for such a fast operation
- **Gradual color transitions**: May exceed 500ms budget, potential for visual artifacts

---

## 8. Browser Compatibility

### Decision: Target Modern Browsers with CSS Custom Properties Support

**Supported Browsers**:
- Chrome/Edge 88+ (released 2021)
- Firefox 85+ (released 2021)
- Safari 14+ (released 2020)

All of these browsers have full CSS custom properties support.

**Rationale**:
- CSS custom properties are well-supported in modern browsers (98%+ global usage)
- Existing application already uses CSS custom properties for dark mode
- No need for additional polyfills or fallbacks

**Alternatives Considered**:
- **Legacy browser support (IE11, older Safari)**: Not required based on current browser statistics and existing codebase decisions
- **Progressive enhancement with fallbacks**: Unnecessary complexity given target audience uses modern browsers

---

## Summary of Key Decisions

| Area | Decision | Rationale |
|------|----------|-----------|
| **Color Palette** | GitHub-inspired pink with WCAG-compliant contrast | Balances aesthetics with accessibility |
| **Architecture** | Extend CSS custom properties pattern | Consistent with existing implementation |
| **Persistence** | localStorage with fallback | Simple, reliable, already in use |
| **UI Pattern** | Dropdown/segmented control | Scalable, discoverable, accessible |
| **Testing** | Multi-layer (unit + E2E + manual) | Comprehensive coverage without over-engineering |
| **Performance** | Synchronous CSS variable updates | Meets <500ms requirement |
| **Browser Support** | Modern browsers (2020+) | Aligns with existing app requirements |

---

## Open Questions & Future Considerations

**Resolved Questions**:
- ✅ Should pink theme have light and dark variants? → YES (pink-light and pink-dark)
- ✅ How to handle existing dark mode toggle? → Replace with theme selector dropdown
- ✅ Should theme preference sync across devices? → NO (localStorage only, no backend changes)

**Future Considerations** (out of scope for this feature):
- Additional theme options (blue, purple, custom themes)
- Theme customization (user-defined colors)
- Theme scheduling (auto-switch based on time of day)
- Server-side theme preference storage for cross-device sync

---

**Research Completed**: 2026-02-13  
**Next Phase**: Phase 1 - Design & Contracts
