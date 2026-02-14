# Quickstart Guide: Blue Background Color Implementation

**Feature**: Blue Background Color  
**Branch**: 002-blue-background  
**Date**: 2026-02-14  
**Estimated Time**: 2 hours

## Overview

This guide provides step-by-step instructions for implementing the blue background color feature. The implementation modifies CSS custom properties to apply #2196F3 (Material Blue 500) as the primary background in light mode and #1565C0 (Material Blue 800) in dark mode, while maintaining WCAG AA accessibility standards.

---

## Prerequisites

- Node.js 18+ installed
- Frontend development environment set up
- Access to `frontend/src/index.css` and `frontend/src/App.css`
- Basic understanding of CSS custom properties
- (Optional) Playwright and axe-core for accessibility testing

---

## Step 1: Update CSS Custom Properties (15 minutes)

### 1.1 Open `frontend/src/index.css`

Navigate to the frontend source directory:
```bash
cd frontend/src
```

Open `index.css` in your editor.

### 1.2 Modify Light Mode Background (`:root`)

Find the `:root` selector and update the `--color-bg` property:

**Before**:
```css
:root {
  --color-bg: #ffffff;              /* Old: white */
  --color-bg-secondary: #f6f8fa;
  /* ... rest */
}
```

**After**:
```css
:root {
  --color-bg: #2196F3;              /* New: Material Blue 500 */
  --color-bg-secondary: #f6f8fa;    /* Keep unchanged */
  /* ... rest */
}
```

### 1.3 Modify Dark Mode Background (`html.dark-mode-active`)

Find the `html.dark-mode-active` selector and update the `--color-bg` property:

**Before**:
```css
html.dark-mode-active {
  --color-bg: #0d1117;              /* Old: near-black */
  --color-bg-secondary: #161b22;
  /* ... rest */
}
```

**After**:
```css
html.dark-mode-active {
  --color-bg: #1565C0;              /* New: Material Blue 800 */
  --color-bg-secondary: #161b22;    /* Keep unchanged */
  /* ... rest */
}
```

### 1.4 Save and Verify

Save `index.css`. At this point, the blue background should be visible if you run the development server.

```bash
npm run dev
```

Open the app in your browser and verify the blue background appears.

---

## Step 2: Verify Text Contrast (20 minutes)

### 2.1 Review Current Text Colors

The current CSS should already have appropriate text colors:
- Light mode: `--color-text: #24292f` (dark text on light secondary backgrounds)
- Dark mode: `--color-text: #e6edf3` (light text on dark secondary backgrounds)

### 2.2 Check Login Screen

Open `frontend/src/App.css` and locate `.app-login` styles. Ensure text is readable:

```css
.app-login {
  background: var(--color-bg); /* Blue background */
  /* ... other styles ... */
}

.app-login h1 {
  color: #FFFFFF; /* White text on blue */
  font-size: 2rem; /* Large text: 32px ≈ 24pt */
}

.app-login p {
  color: #FFFFFF; /* White text on blue */
}
```

**Contrast Check**:
- `#FFFFFF` on `#2196F3` = 3.15:1 ratio
- Acceptable for large text (≥18pt) per WCAG AA
- May need darker text for paragraph text if not large enough

### 2.3 Adjust Paragraph Text (if needed)

If the paragraph text is not large enough (≥18pt), consider using a darker background for better contrast:

```css
.app-login p {
  color: #FFFFFF;
  font-size: 1.125rem; /* 18px - still below 18pt threshold */
  /* Option 1: Make text larger */
  font-size: 1.5rem; /* 24px ≈ 18pt */
  
  /* OR Option 2: Add semi-transparent background */
  background: rgba(0, 0, 0, 0.15);
  padding: 0.5rem 1rem;
  border-radius: var(--radius);
}
```

---

## Step 3: Validate Interactive Elements (25 minutes)

### 3.1 Test Button Contrast

Open the app and inspect buttons (Login button, theme toggle, etc.).

Use browser DevTools to check computed background color of buttons against the blue background.

### 3.2 Use WebAIM Contrast Checker

1. Go to https://webaim.org/resources/contrastchecker/
2. Enter foreground: `#0969da` (primary button color in light mode)
3. Enter background: `#2196F3` (blue background)
4. Check if contrast ratio ≥ 3:1 for interactive elements

**If contrast fails** (< 3:1):
- Darken button color: try `#0550ae` or `#024a96`
- Update `--color-primary` in `:root`

### 3.3 Update Button Colors (if needed)

If button contrast is insufficient, update `index.css`:

```css
:root {
  --color-primary: #024a96; /* Darker blue for better contrast */
  /* ... rest ... */
}
```

### 3.4 Test Links and Form Controls

Inspect other interactive elements (links, input borders, etc.) and adjust colors as needed.

---

## Step 4: Test Dark Mode (15 minutes)

### 4.1 Toggle Dark Mode

Click the theme toggle button (moon/sun icon) in the app header.

### 4.2 Verify Dark Mode Blue Background

Check that:
- Background is darker blue (`#1565C0`)
- Text is readable (light colors on dark blue)
- Buttons and interactive elements have adequate contrast

### 4.3 Contrast Check for Dark Mode

Use WebAIM Contrast Checker:
- Foreground: `#e6edf3` (dark mode text)
- Background: `#1565C0` (dark mode blue)
- Should be ~6:1 ratio (passes WCAG AA)

### 4.4 Adjust Dark Mode Colors (if needed)

If contrast is insufficient in dark mode, adjust `html.dark-mode-active` in `index.css`:

```css
html.dark-mode-active {
  --color-bg: #0d47a1; /* Even darker blue if needed */
  --color-text: #ffffff; /* Pure white for maximum contrast */
  /* ... rest ... */
}
```

---

## Step 5: Cross-Browser Testing (20 minutes)

### 5.1 Test in Multiple Browsers

Open the app in:
- Chrome
- Firefox
- Safari (if on macOS)
- Edge

### 5.2 Verify Consistent Appearance

Check that:
- Blue background displays correctly in all browsers
- No color shifts or visual artifacts
- Theme toggle works in all browsers

### 5.3 Test Responsive Layouts

Resize browser window or use DevTools device emulation:
- Mobile (375px width)
- Tablet (768px width)
- Desktop (1920px width)

Verify blue background scales correctly across all viewport sizes.

---

## Step 6: Accessibility Validation (25 minutes)

### 6.1 Run Lighthouse Audit

1. Open Chrome DevTools (F12)
2. Go to Lighthouse tab
3. Select "Accessibility" category
4. Click "Generate report"
5. Review any contrast-related issues

### 6.2 Install axe DevTools Extension (Optional)

1. Install axe DevTools browser extension
2. Run accessibility scan
3. Filter for "Color contrast" issues
4. Fix any reported violations

### 6.3 Manual WCAG Validation

Check key screens:
- Login screen: All text readable?
- Dashboard: Buttons/links have 3:1 contrast?
- Chat interface: Messages readable on panels?

---

## Step 7: Write or Update Tests (Optional, 20 minutes)

### 7.1 E2E Visual Test (Playwright)

Create or update `frontend/e2e/ui.spec.ts`:

```typescript
import { test, expect } from '@playwright/test';

test.describe('Blue Background', () => {
  test('applies blue background in light mode', async ({ page }) => {
    await page.goto('/');
    
    // Wait for app to load
    await page.waitForSelector('.app-login, .app-container');
    
    // Get computed background color
    const bgColor = await page.evaluate(() => {
      const root = document.documentElement;
      return getComputedStyle(root).getPropertyValue('--color-bg').trim();
    });
    
    expect(bgColor).toBe('#2196F3');
  });

  test('applies darker blue in dark mode', async ({ page }) => {
    await page.goto('/');
    
    // Toggle dark mode
    await page.click('button[aria-label*="dark mode"]');
    
    // Get computed background color
    const bgColor = await page.evaluate(() => {
      const root = document.documentElement;
      return getComputedStyle(root).getPropertyValue('--color-bg').trim();
    });
    
    expect(bgColor).toBe('#1565C0');
  });
});
```

### 7.2 Run E2E Tests

```bash
cd frontend
npm run test:e2e
```

Verify tests pass.

### 7.3 Accessibility Test with axe-core (Optional)

Add accessibility test to Playwright:

```typescript
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('meets WCAG AA standards', async ({ page }) => {
  await page.goto('/');
  
  const results = await new AxeBuilder({ page })
    .analyze();
  
  expect(results.violations).toEqual([]);
});
```

---

## Step 8: Final Verification (10 minutes)

### 8.1 Checklist

- [ ] Light mode displays `#2196F3` background
- [ ] Dark mode displays `#1565C0` background
- [ ] All text meets 4.5:1 contrast (normal text) or 3:1 (large text)
- [ ] All buttons/links meet 3:1 contrast against blue background
- [ ] Theme toggle switches between light/dark correctly
- [ ] No visual artifacts across browsers
- [ ] No console errors or warnings
- [ ] Lighthouse accessibility score ≥ 90
- [ ] Manual review confirms visual appeal

### 8.2 Take Screenshots

Capture screenshots for documentation:
```bash
# Light mode
# Dark mode
# Login screen
# Dashboard
```

### 8.3 Git Commit

Commit your changes:
```bash
git add frontend/src/index.css frontend/src/App.css
git commit -m "feat: apply blue background color (#2196F3) with WCAG AA compliance"
git push origin [your-branch]
```

---

## Troubleshooting

### Issue: Blue background not appearing

**Solution**: Check that `body` or `.app-container` uses `var(--color-bg)`:
```css
body {
  background: var(--color-bg-secondary); /* Change to --color-bg if desired */
}

.app-container {
  background: var(--color-bg); /* Ensure this is set */
}
```

### Issue: Text is unreadable (poor contrast)

**Solution**: Use layered backgrounds:
- Blue background (`--color-bg`) for layout
- White/dark panels (`--color-bg-secondary`) for text content

### Issue: Dark mode blue is too bright

**Solution**: Adjust `--color-bg` in `html.dark-mode-active` to a darker shade:
```css
html.dark-mode-active {
  --color-bg: #0d47a1; /* Darker than #1565C0 */
}
```

### Issue: Buttons don't have enough contrast

**Solution**: Darken button color:
```css
:root {
  --color-primary: #024a96; /* Darker blue */
}
```

### Issue: Theme toggle not working

**Solution**: Verify `useAppTheme` hook is being called and CSS class is toggled:
```typescript
const { isDarkMode, toggleTheme } = useAppTheme();
```

Check that `html` element has `dark-mode-active` class when toggled.

---

## Next Steps

1. **User Testing**: Have users test the new blue background in real-world scenarios
2. **Analytics**: Monitor for any usability issues or feedback
3. **Iterate**: Adjust colors based on user feedback
4. **Document**: Update any design system documentation with new color values

---

## Key Files Modified

- ✅ `frontend/src/index.css` - Primary CSS custom properties
- ✅ `frontend/src/App.css` - Application layout styles (contrast verification)
- ⚠️  Component CSS files - Only if contrast adjustments needed

---

## Success Criteria

- All core screens display blue background (`#2196F3` light, `#1565C0` dark)
- 100% of text meets WCAG AA contrast (4.5:1 normal, 3:1 large)
- Dark mode adapts blue appropriately
- Cross-browser compatibility (Chrome, Firefox, Safari, Edge)
- Zero accessibility violations in automated tests

---

## Estimated Time Breakdown

| Step | Time | Cumulative |
|------|------|------------|
| 1. Update CSS properties | 15 min | 15 min |
| 2. Verify text contrast | 20 min | 35 min |
| 3. Validate interactive elements | 25 min | 60 min |
| 4. Test dark mode | 15 min | 75 min |
| 5. Cross-browser testing | 20 min | 95 min |
| 6. Accessibility validation | 25 min | 120 min (2 hours) |
| 7. Write tests (optional) | 20 min | 140 min |
| 8. Final verification | 10 min | 150 min |

**Total**: 2-2.5 hours (including optional testing)

---

## Resources

- [CSS Custom Properties (MDN)](https://developer.mozilla.org/en-US/docs/Web/CSS/--*)
- [WCAG Contrast Guidelines](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html)
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [Material Design Colors](https://m2.material.io/design/color/the-color-system.html)
- [Playwright Testing](https://playwright.dev/)
- [axe-core Accessibility](https://github.com/dequelabs/axe-core)

---

**End of Quickstart Guide**
