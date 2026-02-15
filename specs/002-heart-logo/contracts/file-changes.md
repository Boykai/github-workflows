# File Changes Contract: Heart Logo on Homepage

**Feature**: 002-heart-logo | **Date**: 2026-02-15 | **Spec**: [spec.md](../spec.md)

## Purpose

This contract documents all file changes required to implement the heart logo feature. Each change is specified with before/after context and validation criteria.

---

## File 1: Create `frontend/public/heart-logo.svg`

**Action**: Create new file  
**Status**: New file (does not currently exist)  

### Requirements

- **Format**: SVG (Scalable Vector Graphics)
- **File size**: < 10KB (optimized)
- **Viewbox**: Must use viewBox attribute (not fixed width/height)
- **Content**: Heart shape with brand colors
- **Accessibility**: Include `<title>` element inside SVG

### Example SVG Structure

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
  <title>Heart Logo</title>
  <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
</svg>
```

### Validation

- [ ] File exists at `frontend/public/heart-logo.svg`
- [ ] Valid SVG XML syntax
- [ ] Uses `viewBox` (scalable)
- [ ] File size < 10KB
- [ ] Contains `<title>` element
- [ ] Accessible via `/heart-logo.svg` URL path

---

## File 2: Modify `frontend/src/App.tsx`

**Action**: Add logo img element to login section  
**Status**: Modify existing file  
**Lines affected**: ~68-71 (inside login section)

### Current Code (Before)

```tsx
<div className="app-login">
  <h1>Welcome to Tech Connect 2026!</h1>
  <LoginButton />
</div>
```

### New Code (After)

```tsx
<div className="app-login">
  <img 
    src="/heart-logo.svg" 
    alt="Heart logo - Tech Connect 2026" 
    className="logo"
  />
  <h1>Welcome to Tech Connect 2026!</h1>
  <LoginButton />
</div>
```

### Change Details

- **Location**: Inside `.app-login` div (lines 68-71)
- **Position**: Add as first child (before h1)
- **Attributes**:
  - `src="/heart-logo.svg"` - References logo file in public/
  - `alt="Heart logo - Tech Connect 2026"` - Descriptive alt text (FR-005)
  - `className="logo"` - References CSS styling

### Validation

- [ ] img element added inside `.app-login` div
- [ ] img is first child (before h1)
- [ ] src attribute points to `/heart-logo.svg`
- [ ] alt attribute is descriptive and non-empty
- [ ] className is `logo`
- [ ] No onClick or event handlers (FR-007: non-interactive)
- [ ] Component still compiles without errors

---

## File 3: Modify `frontend/src/App.css`

**Action**: Add CSS styling for logo  
**Status**: Modify existing file  
**Lines affected**: Add new `.logo` class (position TBD, suggest after `.app-login` rules)

### Current Code (Before)

```css
/* Existing .app-login styles */
.app-login {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  text-align: center;
}
```

### New Code (After)

```css
/* Existing .app-login styles */
.app-login {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  text-align: center;
}

/* Heart logo styling */
.logo {
  width: clamp(60px, 10vw, 120px);
  height: auto;
  display: block;
  margin: 0 auto 1.5rem auto;
}

/* Responsive adjustments for mobile */
@media (max-width: 768px) {
  .logo {
    width: clamp(50px, 15vw, 80px);
    margin-bottom: 1rem;
  }
}

/* High contrast mode support */
@media (prefers-contrast: high) {
  .logo {
    filter: contrast(1.2);
  }
}
```

### Change Details

- **New class**: `.logo`
- **Sizing**: 
  - Desktop: 60px-120px (10vw fluid)
  - Mobile: 50px-80px (15vw fluid)
  - `height: auto` maintains aspect ratio (FR-004)
- **Spacing**: `margin-bottom: 1.5rem` (desktop) / `1rem` (mobile)
- **Centering**: `margin: 0 auto` (horizontal center)
- **Accessibility**: High contrast mode support (edge case)

### Validation

- [ ] `.logo` class added to App.css
- [ ] Width uses clamp() for responsive sizing (FR-003)
- [ ] Height is `auto` (maintains aspect ratio)
- [ ] Margin centers logo horizontally
- [ ] Mobile media query includes logo adjustments
- [ ] High contrast mode handled (accessibility edge case)
- [ ] No `cursor: pointer` (FR-007: non-interactive)

---

## File Changes Summary

| File | Action | Lines | Risk | Dependencies |
|------|--------|-------|------|--------------|
| `frontend/public/heart-logo.svg` | Create | N/A | Low | None |
| `frontend/src/App.tsx` | Modify | ~4 | Low | heart-logo.svg must exist |
| `frontend/src/App.css` | Modify | ~20 | Low | None |

**Total Files Changed**: 3  
**New Files**: 1  
**Modified Files**: 2  
**Deleted Files**: 0  

---

## Testing Contract

### Manual Testing Checklist

#### User Story 1: Brand Recognition (P1)
- [ ] Load login page → Logo visible at top center
- [ ] Logo uses brand colors (or falls back gracefully)
- [ ] Logo displayed consistently on page reload

#### User Story 2: Responsive Display (P2)
- [ ] Mobile (320px-767px) → Logo scales appropriately
- [ ] Tablet (768px-1023px) → Logo scales appropriately
- [ ] Desktop (1024px+) → Logo scales appropriately
- [ ] Window resize → Logo adapts smoothly
- [ ] No distortion or pixelation at any size

#### User Story 3: Accessibility (P3)
- [ ] Screen reader announces alt text
- [ ] Remove logo file temporarily → Alt text displays
- [ ] High contrast mode → Logo remains visible
- [ ] 200% page zoom → Logo scales proportionally

#### Edge Cases
- [ ] Extremely small screen (<320px) → Logo still visible
- [ ] Logo file missing → Alt text displays gracefully
- [ ] Slow network → Logo loads within 1 second on broadband

### Cross-Browser Testing

- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)

---

## Rollback Plan

If issues arise, changes can be safely rolled back:

1. **Remove logo from App.tsx**: Delete the `<img>` element
2. **Remove CSS from App.css**: Delete the `.logo` class and media queries
3. **Delete logo file** (optional): Remove `frontend/public/heart-logo.svg`

**Risk**: Extremely low - feature is additive, doesn't modify existing functionality

---

## Notes

- No database migrations required
- No API changes required
- No configuration changes required
- No dependency updates required
- No environment variables required
- Changes are isolated to frontend presentation layer
- Feature can be toggled by commenting out img element
