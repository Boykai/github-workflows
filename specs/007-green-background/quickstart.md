# Quickstart: Add Green Background Color to App

**Feature**: 007-green-background | **Branch**: `007-green-background`

---

## Prerequisites

- Node.js ≥ 18 (for frontend development)
- Git access
- Text editor

## Setup

### 1. Switch to feature branch

```bash
cd /home/runner/work/github-workflows/github-workflows
git status
```

**Expected**: On branch `007-green-background` or a related feature branch

### 2. No new dependencies required

This feature requires no new packages — it is a CSS-only change.

### 3. Start development server (optional, for visual verification)

```bash
cd frontend
npm run dev
```

- Frontend: http://localhost:5173

---

## Implementation Steps

### Step 1: Add CSS Custom Property to `:root`

**File**: `frontend/src/index.css`

Locate the `:root` block and add `--color-bg-primary` after `--color-bg-secondary`:

```css
:root {
  /* ... existing variables ... */
  --color-bg: #ffffff;
  --color-bg-secondary: #f6f8fa;
  --color-bg-primary: #2D6A4F;    /* ← ADD THIS LINE */
  --color-border: #d0d7de;
  /* ... rest of variables ... */
}
```

### Step 2: Add CSS Custom Property to Dark Mode Block

Locate the `html.dark-mode-active` block and add the same variable:

```css
html.dark-mode-active {
  /* ... existing variables ... */
  --color-bg: #0d1117;
  --color-bg-secondary: #161b22;
  --color-bg-primary: #2D6A4F;    /* ← ADD THIS LINE */
  --color-border: #30363d;
  /* ... rest of variables ... */
}
```

### Step 3: Update Body Background

Locate the `body` rule and replace the background declaration:

**Before**:
```css
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif;
  font-size: 14px;
  line-height: 1.5;
  color: var(--color-text);
  background: var(--color-bg-secondary);
}
```

**After**:
```css
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif;
  font-size: 14px;
  line-height: 1.5;
  color: var(--color-text);
  background: #2D6A4F;
  background: var(--color-bg-primary);
}
```

**Note**: The first `background: #2D6A4F;` is a fallback for browsers that don't support CSS custom properties. The second `background: var(--color-bg-primary);` overrides it in modern browsers.

### Step 4: Verify Changes

```bash
# Confirm only index.css was modified
git diff --name-only

# Verify the CSS variable is defined
grep "color-bg-primary" frontend/src/index.css
```

**Expected**: 3 matches — one in `:root`, one in `html.dark-mode-active`, and body references via `var()`

---

## Visual Verification

### Open Application

If the dev server is running:

1. Navigate to http://localhost:5173
2. Observe green background visible at the page edges and behind components
3. Toggle dark mode (🌙 button) — green should persist
4. Resize browser window — green should fill viewport without gaps

### Check Existing UI

1. Verify header, sidebar, and cards remain readable
2. Verify buttons and inputs are visually legible
3. Verify no layout changes or spacing issues

---

## Running Tests

```bash
# Frontend unit tests (should pass — no logic changes)
cd frontend
npm run test

# TypeScript type checking (should pass — no TS changes)
npm run type-check

# Lint (should pass — no JS/TS changes)
npm run lint
```

---

## Troubleshooting

### Issue: Green Not Visible

**Symptom**: No green background after changes
**Solution**: Check that the `body` rule uses `var(--color-bg-primary)`, not `var(--color-bg-secondary)`. Verify the variable is defined in `:root`.

### Issue: Components Unreadable

**Symptom**: Text on components is hard to read
**Solution**: Components should have their own background colors (`var(--color-bg)` or `var(--color-bg-secondary)`). If a component lacks a background, add `background: var(--color-bg);` to its CSS rule.

### Issue: Green Looks Wrong in Dark Mode

**Symptom**: Green clashes with dark mode
**Solution**: Verify `--color-bg-primary: #2D6A4F;` is defined in both `:root` and `html.dark-mode-active` blocks.

---

## Validation Checklist

Before marking feature complete, verify:

- [ ] **FR-001**: Green background visible across all pages ✅
- [ ] **FR-002**: `--color-bg-primary` defined as reusable CSS variable ✅
- [ ] **FR-004**: Green consistent across all views, modals, overlays ✅
- [ ] **FR-005**: Green fills full viewport on mobile, tablet, desktop ✅
- [ ] **FR-006**: Existing UI components remain legible ✅
- [ ] **FR-007**: Hardcoded fallback present before `var()` declaration ✅
- [ ] **FR-008**: No visual regressions to layout or spacing ✅
- [ ] **SC-006**: Green color defined in single reusable location ✅

---

## Success Criteria

✅ **Feature Complete** when:
1. Green background (#2D6A4F) visible as base layer across all pages
2. `--color-bg-primary` CSS variable defined in `:root` and dark mode blocks
3. Hardcoded fallback ensures green even without CSS variable support
4. All existing UI components remain readable and functional
5. Changes committed to git

**Total Time**: ~5-10 minutes for implementation

---

## Next Steps

After completing this guide:

1. **Review**: Self-review CSS changes in git diff
2. **Test**: Run existing test suite to confirm no regressions
3. **Visual Check**: Open app in browser and verify green background
4. **Deploy**: Follow standard deployment process

**Status**: ✅ **QUICKSTART COMPLETE** — Ready for implementation by speckit.tasks
