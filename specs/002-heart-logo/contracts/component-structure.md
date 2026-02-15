# Component Contracts: Heart Logo

**Feature**: 002-heart-logo | **Date**: 2026-02-15  
**Purpose**: Define interfaces and contracts for logo implementation

## Overview

This document defines the structural and styling contracts for the heart logo component. Since this is a static visual element with no API interactions, contracts focus on:
1. SVG element structure and attributes
2. CSS class and style contracts
3. Accessibility attribute requirements
4. Integration points with existing components

## SVG Element Contract

### Required Structure

```typescript
/**
 * Heart logo SVG element structure
 * Location: frontend/src/App.tsx (login and authenticated views)
 */
interface HeartLogoSVG {
  // DOM Element Type
  element: 'svg';
  
  // Required Accessibility Attributes
  role: 'img';
  ariaLabel: string; // Must be descriptive, e.g., "Heart logo"
  
  // SVG Viewbox (defines coordinate system)
  viewBox: '0 0 24 24'; // Standard 24x24 icon space
  
  // Styling (applied via className)
  className: 'heart-logo';
  
  // Child Elements
  children: SVGPathElement[];
}

interface SVGPathElement {
  element: 'path';
  d: string; // SVG path data defining heart shape
  // fill inherited from parent SVG
}
```

### Example Implementation

```jsx
<svg 
  className="heart-logo"
  role="img"
  aria-label="Heart logo"
  viewBox="0 0 24 24"
  xmlns="http://www.w3.org/2000/svg"
>
  <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
</svg>
```

### Contract Validation

**MUST Requirements**:
- ✅ Element type is `<svg>`
- ✅ Has `role="img"` attribute
- ✅ Has non-empty `aria-label` attribute
- ✅ Has `viewBox="0 0 24 24"` attribute
- ✅ Has `className="heart-logo"` for styling
- ✅ Contains at least one `<path>` child element
- ✅ No interactive attributes (`onClick`, `onKeyDown`, etc.)

**MUST NOT**:
- ❌ No `href` or `<a>` wrapper (must be non-interactive per FR-007)
- ❌ No inline `style` attribute (use CSS classes)
- ❌ No `<script>` tags within SVG
- ❌ No external references (`<use xlink:href>`)

---

## CSS Style Contract

### Required Class: `.heart-logo`

```css
/**
 * Heart logo styles
 * Location: frontend/src/App.css
 */
.heart-logo {
  /* Responsive sizing with constraints */
  width: clamp(40px, 8vw, 120px);
  height: auto;
  
  /* Centering */
  display: block;
  margin: 0 auto 16px auto; /* horizontal center + bottom spacing */
  
  /* Brand color integration */
  fill: var(--color-primary);
  
  /* Smooth theme transitions */
  transition: fill 0.2s ease;
}

/* High contrast mode support */
@media (forced-colors: active) {
  .heart-logo {
    fill: CanvasText;
  }
}
```

### Style Contract Requirements

**Size Constraints**:
- `width`: Must use `clamp(40px, 8vw, 120px)` for responsive behavior
  - Minimum: 40px (ensures visibility on 320px screens)
  - Scaling: 8vw (8% of viewport width)
  - Maximum: 120px (prevents oversizing on large displays)
- `height`: Must be `auto` to maintain aspect ratio

**Positioning**:
- `display`: Must be `block` to enable margin centering
- `margin`: Must use `0 auto` for horizontal centering
- Bottom margin recommended: `16px` for spacing from title

**Color**:
- `fill`: Must use `var(--color-primary)` for theme compatibility
- Fallback: Should include `currentColor` fallback if CSS variable fails

**Accessibility**:
- High contrast mode: Must override fill with `CanvasText` in `forced-colors` media query

**MUST NOT**:
- ❌ No `cursor: pointer` (must be non-interactive)
- ❌ No `:hover` color changes (logo is static)
- ❌ No `animation` properties (spec excludes animations)

---

## Integration Contracts

### Login Page Integration

**Location**: `frontend/src/App.tsx`, `.app-login` section

**Contract**:
```jsx
<div className="app-login">
  {/* INSERT LOGO HERE - before h1 */}
  <svg className="heart-logo" role="img" aria-label="Heart logo" viewBox="0 0 24 24">
    <path d="..." />
  </svg>
  
  <h1>Welcome to Tech Connect 2026!</h1>
  <p>Manage your GitHub Projects with natural language</p>
  <LoginButton />
</div>
```

**Requirements**:
- Logo must appear as first child of `.app-login` div
- Logo must be positioned before the `<h1>` title
- No wrapper element needed (logo is self-contained)

---

### Authenticated Header Integration

**Location**: `frontend/src/App.tsx`, `.app-header` section

**Contract**:
```jsx
<header className="app-header">
  <div className="app-header-top">
    {/* INSERT LOGO HERE */}
    <svg className="heart-logo" role="img" aria-label="Heart logo" viewBox="0 0 24 24">
      <path d="..." />
    </svg>
  </div>
  
  <div className="app-header-content">
    <h1>Welcome to Tech Connect 2026!</h1>
    <div className="header-actions">
      <button className="theme-toggle-btn" ...>...</button>
      <LoginButton />
    </div>
  </div>
</header>
```

**Requirements**:
- Logo appears in separate top section for clean layout
- Title and actions remain in existing layout structure
- Minimal changes to existing header CSS

---

## Theme System Contract

### CSS Custom Properties Dependency

**Contract**: Logo relies on existing theme variables from `frontend/src/index.css`

```css
:root {
  --color-primary: #0969da; /* Light mode */
  /* ... */
}

html.dark-mode-active {
  --color-primary: #539bf5; /* Dark mode */
  /* ... */
}
```

**Logo Usage**:
```css
.heart-logo {
  fill: var(--color-primary);
}
```

**Requirements**:
- Logo must use `var(--color-primary)` for fill color
- Logo automatically updates when theme toggles (CSS variable changes)
- No JavaScript theme handling needed (CSS variables handle reactivity)

**Fallback Behavior**:
```css
.heart-logo {
  fill: var(--color-primary, currentColor);
}
```
If `--color-primary` is undefined, falls back to `currentColor` (inherits text color).

---

## Accessibility Contract

### Screen Reader Requirements

**Contract**: Logo must be announced as an image with descriptive label

**Required Attributes**:
```jsx
<svg 
  role="img"                  // Announces as image
  aria-label="Heart logo"     // Descriptive text alternative
  aria-hidden="false"         // Ensure it's announced (default)
>
```

**Screen Reader Output** (expected):
- NVDA: "Heart logo, image"
- JAWS: "Heart logo graphic"
- VoiceOver: "Heart logo, image"

**Testing Verification**:
1. Navigate to page with screen reader active
2. Logo should be announced with its label
3. Logo should not be skipped (not decorative)

**MUST NOT**:
- ❌ No `aria-hidden="true"` (would hide from screen readers)
- ❌ No empty `aria-label=""` (violates FR-005)

---

### Keyboard Navigation Contract

**Contract**: Logo is not keyboard focusable (non-interactive)

**Requirements**:
- No `tabindex` attribute (logo not in tab order)
- No event handlers (`onClick`, `onKeyDown`, etc.)
- No `<a>` wrapper (prevents accidental navigation)

**Verification**:
1. Tab through page with keyboard
2. Logo should not receive focus
3. Enter/Space on nearby elements should not trigger logo interaction

---

## Responsive Behavior Contract

### Viewport Size Handling

**Contract**: Logo scales smoothly across all viewport sizes

| Viewport Width | Logo Width | Calculation |
|----------------|------------|-------------|
| 320px (min) | 40px | clamp lower bound |
| 500px | 40px | 8vw = 40px |
| 1000px | 80px | 8vw = 80px |
| 1500px | 120px | clamp upper bound |
| 2560px (max) | 120px | clamp upper bound |

**Scaling Function**: `width = clamp(40px, 8vw, 120px)`
- Below 500px viewport: Fixed 40px (minimum)
- 500px-1500px viewport: Scales with 8vw
- Above 1500px viewport: Fixed 120px (maximum)

**Aspect Ratio**: Always 1:1 (square)
- `height: auto` maintains SVG viewBox aspect ratio

---

### Browser Zoom Contract

**Contract**: Logo scales proportionally with browser zoom

| Zoom Level | Behavior |
|------------|----------|
| 100% | Base size (40px-120px range) |
| 150% | 1.5x size (60px-180px range) |
| 200% | 2x size (80px-240px range) |

**SVG Quality**: Vector format ensures crisp rendering at all zoom levels

**Verification**:
1. Set browser zoom to 200%
2. Logo should scale proportionally
3. No pixelation or blurriness (SVG advantage)

---

## Failure Mode Contract

### Graceful Degradation

**Contract**: Logo handles edge cases without breaking layout

**Scenario 1: CSS Variables Undefined**
```css
fill: var(--color-primary, currentColor);
```
- Fallback to `currentColor` (text color)
- Logo remains visible with inherited color

**Scenario 2: Browser Doesn't Support `clamp()`**
```css
width: 80px; /* Fallback for old browsers */
width: clamp(40px, 8vw, 120px);
```
- Older browsers use fixed 80px width
- Modern browsers use responsive clamp()

**Scenario 3: SVG Rendering Fails**
- `aria-label` still provides text alternative
- Screen readers announce "Heart logo" even if visual fails

**MUST NOT Break**:
- Logo failure must not prevent page load
- Logo failure must not break header layout
- Logo failure must not hide title or actions

---

## Testing Contract

### Manual Verification Checklist

- [ ] Logo visible at top center of login page
- [ ] Logo visible at top center of authenticated page
- [ ] Logo scales correctly on mobile (320px width)
- [ ] Logo scales correctly on tablet (768px width)
- [ ] Logo scales correctly on desktop (1920px width)
- [ ] Logo uses brand blue color in light mode
- [ ] Logo updates to dark mode color when theme toggled
- [ ] Logo has no hover cursor (non-interactive)
- [ ] Logo announced by screen reader as "Heart logo"
- [ ] Logo visible in Windows High Contrast mode
- [ ] Logo scales correctly at 200% browser zoom
- [ ] Logo does not break header layout

### E2E Test Updates (Optional)

If existing tests assert header content, update assertions:

```typescript
// frontend/e2e/auth.spec.ts or similar
test('homepage displays heart logo', async ({ page }) => {
  await page.goto('/');
  
  const logo = page.locator('svg.heart-logo');
  await expect(logo).toBeVisible();
  await expect(logo).toHaveAttribute('role', 'img');
  await expect(logo).toHaveAttribute('aria-label', 'Heart logo');
});
```

---

## Contract Validation Summary

**Compliance Checklist**:

- [x] SVG element structure defined
- [x] Required attributes specified (role, aria-label, viewBox)
- [x] CSS class and styles documented
- [x] Responsive sizing formula provided (clamp)
- [x] Theme integration specified (CSS variables)
- [x] Accessibility requirements detailed (screen reader, keyboard)
- [x] Integration points identified (login, authenticated headers)
- [x] Non-interactive constraint enforced (no click handlers)
- [x] High contrast mode support included
- [x] Failure modes addressed (fallbacks)

**Status**: ✅ **CONTRACTS COMPLETE** - Implementation ready
