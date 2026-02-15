# Quickstart: Heart Logo on Homepage

**Feature**: 002-heart-logo | **Date**: 2026-02-15 | **Spec**: [spec.md](./spec.md)

## Purpose

This quickstart guide provides step-by-step instructions to implement and validate the heart logo feature. Follow these steps in order for successful implementation.

---

## Prerequisites

- [ ] spec.md is finalized and approved
- [ ] plan.md is complete with technical decisions
- [ ] Development environment is set up (Node.js, npm, React)
- [ ] Repository is cloned and dependencies are installed
- [ ] Frontend server can run successfully (`npm run dev` in frontend/)

---

## Implementation Steps

### Step 1: Create Logo Asset

**Time estimate**: 10-15 minutes (if creating) or 2 minutes (if using existing)

```bash
# Navigate to frontend directory
cd frontend

# Create public directory if it doesn't exist
mkdir -p public

# Option A: Create a simple heart SVG
cat > public/heart-logo.svg << 'EOF'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
  <title>Heart Logo</title>
  <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
</svg>
EOF

# Option B: If you have a custom heart logo, copy it
# cp /path/to/your/heart-logo.svg public/heart-logo.svg
```

**Validation**:
- [ ] File exists at `frontend/public/heart-logo.svg`
- [ ] File size < 10KB
- [ ] SVG is valid (can open in browser or editor)

---

### Step 2: Add Logo to App Component

**Time estimate**: 5 minutes

```bash
# Open App.tsx in your editor
# Location: frontend/src/App.tsx
# Find the login section (around lines 68-71)
```

**Find this code** (in the `app-login` div):

```tsx
<div className="app-login">
  <h1>Welcome to Tech Connect 2026!</h1>
  <LoginButton />
</div>
```

**Replace with**:

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

**Validation**:
- [ ] Code compiles without errors
- [ ] TypeScript shows no type errors
- [ ] img element is first child in `.app-login` div

---

### Step 3: Add Logo Styling

**Time estimate**: 5 minutes

```bash
# Open App.css in your editor
# Location: frontend/src/App.css
# Add these styles (suggested location: after .app-login rules)
```

**Add this CSS**:

```css
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

**Validation**:
- [ ] No CSS syntax errors
- [ ] Styles are saved

---

### Step 4: Start Development Server

**Time estimate**: 2 minutes

```bash
# From frontend directory
npm run dev

# Expected output:
# ➜  Local:   http://localhost:5173/
# ➜  press h to show help
```

**Validation**:
- [ ] Server starts without errors
- [ ] No compilation warnings related to logo

---

### Step 5: Visual Verification (User Story 1 - P1)

**Time estimate**: 3 minutes

**Open browser**: http://localhost:5173/

**Check**:
- [ ] Heart logo is visible at top center of login page
- [ ] Logo appears above "Welcome to Tech Connect 2026!" heading
- [ ] Logo is centered horizontally
- [ ] Logo has appropriate size (not too large or too small)

**If logo not visible**:
- Check browser console for 404 errors on `/heart-logo.svg`
- Verify SVG file is in `frontend/public/` (not `frontend/src/`)
- Check that dev server was restarted after adding SVG file

---

### Step 6: Responsive Testing (User Story 2 - P2)

**Time estimate**: 5 minutes

**Desktop testing**:
1. Open browser DevTools (F12)
2. Resize browser window from large to small
3. Verify logo scales smoothly

**Mobile testing**:
1. Open DevTools → Toggle device toolbar (Ctrl+Shift+M)
2. Test iPhone SE (375px width)
   - [ ] Logo visible and appropriately sized
3. Test iPad (768px width)
   - [ ] Logo visible and appropriately sized
4. Test Desktop (1920px width)
   - [ ] Logo visible and not overly large

**Check for issues**:
- [ ] No distortion or pixelation at any size
- [ ] Logo doesn't overflow or break layout
- [ ] Logo maintains aspect ratio

---

### Step 7: Accessibility Testing (User Story 3 - P3)

**Time estimate**: 5 minutes

**Screen reader test** (if available):
1. Enable screen reader (macOS: VoiceOver, Windows: Narrator)
2. Navigate to login page
3. Listen for alt text announcement
   - [ ] Screen reader says "Heart logo - Tech Connect 2026"

**Alt text fallback test**:
1. Temporarily rename `heart-logo.svg` to `heart-logo-temp.svg`
2. Reload page
3. Verify alt text displays in place of image
   - [ ] "Heart logo - Tech Connect 2026" visible as text
4. Rename file back to `heart-logo.svg`

**High contrast test**:
1. Enable high contrast mode (Windows: Alt+Shift+PrintScreen, macOS: System Preferences)
2. Reload page
3. Verify logo is still visible
   - [ ] Logo has sufficient contrast

---

### Step 8: Cross-Browser Testing

**Time estimate**: 10 minutes

Test in each browser:
- [ ] **Chrome**: Logo displays correctly
- [ ] **Firefox**: Logo displays correctly
- [ ] **Safari**: Logo displays correctly (if on macOS)
- [ ] **Edge**: Logo displays correctly (if on Windows)

**Common issues**:
- SVG rendering differences: Usually not an issue with simple paths
- CSS clamp() support: Supported in all modern browsers (2020+)

---

### Step 9: Edge Case Testing

**Time estimate**: 5 minutes

**Extremely small screen** (<320px):
```bash
# In DevTools, manually set viewport to 300px width
```
- [ ] Logo still visible (at minimum size)
- [ ] Layout not broken

**Page zoom test**:
1. Zoom browser to 200% (Ctrl + +)
2. Verify logo scales proportionally
   - [ ] No pixelation (SVG scales infinitely)

**Slow network simulation**:
1. DevTools → Network tab → Throttle to "Slow 3G"
2. Reload page
3. Logo should appear within 1 second (SVG is small)
   - [ ] Logo loads quickly even on slow connection

---

### Step 10: Interactivity Verification (FR-007)

**Time estimate**: 1 minute

- [ ] Click on logo → Nothing happens (correct behavior)
- [ ] Hover over logo → No pointer cursor (no cursor: pointer in CSS)
- [ ] Logo is not a link or button (just an img element)

---

### Step 11: Code Quality Check

**Time estimate**: 3 minutes

```bash
# Run linter (if available)
cd frontend
npm run lint

# Expected: No new errors related to App.tsx or App.css
```

- [ ] No linting errors
- [ ] No TypeScript errors
- [ ] No console warnings in browser

---

### Step 12: Git Commit

**Time estimate**: 2 minutes

```bash
# From repository root
git add frontend/public/heart-logo.svg
git add frontend/src/App.tsx
git add frontend/src/App.css

git commit -m "Add heart logo to homepage

- Create heart-logo.svg in public/ directory
- Add logo img element to login section in App.tsx
- Add responsive CSS styling for logo in App.css
- Implements User Stories 1-3 from spec.md (P1-P3)
"

git push origin <feature-branch>
```

- [ ] Changes committed
- [ ] Changes pushed to remote

---

### Step 13: Final Validation

**Time estimate**: 5 minutes

Run through all acceptance criteria from spec.md:

**User Story 1 (P1) - Brand Recognition**:
- [x] Logo visible at top center on page load
- [x] Logo uses recognizable colors
- [x] Logo displayed consistently on reload

**User Story 2 (P2) - Responsive Display**:
- [x] Mobile: Logo visible and appropriately sized
- [x] Tablet: Logo visible and appropriately sized
- [x] Desktop: Logo adapts on window resize

**User Story 3 (P3) - Accessibility**:
- [x] Screen reader announces alt text
- [x] Alt text displays if image fails to load

**Edge Cases**:
- [x] Missing image handled gracefully
- [x] Small screens (<320px) handled
- [x] High contrast mode supported
- [x] 200% zoom scales proportionally

---

## Troubleshooting

### Logo not displaying

**Symptom**: Blank space where logo should be  
**Causes & Solutions**:
- SVG file not in `public/` → Move to `frontend/public/`
- Wrong src path → Ensure `src="/heart-logo.svg"` (starts with `/`)
- Dev server not restarted → Restart with `npm run dev`
- Browser cache → Hard refresh (Ctrl+Shift+R)

### Logo too large or too small

**Symptom**: Logo size incorrect  
**Causes & Solutions**:
- CSS clamp values wrong → Adjust min/max in `clamp(60px, 10vw, 120px)`
- Missing CSS class → Verify `className="logo"` in JSX
- CSS not applied → Check for typos in class name

### Logo distorted or pixelated

**Symptom**: Logo appears stretched or blurry  
**Causes & Solutions**:
- Using PNG instead of SVG → Convert to SVG
- Fixed width/height in SVG → Use viewBox instead
- CSS height not `auto` → Set `height: auto`

### Screen reader not announcing

**Symptom**: Alt text not read by screen reader  
**Causes & Solutions**:
- Empty alt attribute → Add descriptive text
- Img element missing alt → Verify `alt="..."` attribute exists
- Screen reader not enabled → Check system settings

---

## Success Criteria Checklist

✅ **All User Stories Implemented**:
- User Story 1 (P1): Brand Recognition ✓
- User Story 2 (P2): Responsive Display ✓
- User Story 3 (P3): Accessibility ✓

✅ **All Functional Requirements Met**:
- FR-001: Logo at top center ✓
- FR-002: Above main content ✓
- FR-003: Responsive scaling ✓
- FR-004: Visual quality maintained ✓
- FR-005: Alt text present ✓
- FR-006: Brand colors (optional) ✓
- FR-007: Non-interactive ✓
- FR-008: Error handling ✓

✅ **All Success Criteria Met**:
- SC-001: Loads within 1 second ✓
- SC-002: Quality on 320px-2560px ✓
- SC-003: All major browsers ✓
- SC-004: Screen reader support ✓
- SC-005: All test devices ✓

---

## Next Steps

1. **Code Review**: Request review from team member
2. **QA Testing**: Have QA test on physical devices if available
3. **Staging Deployment**: Deploy to staging environment
4. **Stakeholder Demo**: Show to product owner for approval
5. **Production Deployment**: Merge to main and deploy

---

## Time Summary

| Step | Time | Cumulative |
|------|------|------------|
| 1. Create logo asset | 10m | 10m |
| 2. Add to component | 5m | 15m |
| 3. Add styling | 5m | 20m |
| 4. Start server | 2m | 22m |
| 5. Visual verification | 3m | 25m |
| 6. Responsive testing | 5m | 30m |
| 7. Accessibility testing | 5m | 35m |
| 8. Cross-browser testing | 10m | 45m |
| 9. Edge case testing | 5m | 50m |
| 10. Interactivity check | 1m | 51m |
| 11. Code quality | 3m | 54m |
| 12. Git commit | 2m | 56m |
| 13. Final validation | 5m | 61m |

**Total Time**: ~1 hour (matches 2.0h estimate from issue metadata, accounting for breaks and potential issues)
