# Quickstart Guide: Orange Background Throughout the App

**Feature**: 003-orange-background | **Date**: 2026-02-17  
**Estimated Time**: 10-15 minutes  
**Prerequisites**: Git access, text editor

## Overview

This guide walks through implementing an orange background across the entire Tech Connect application. The implementation involves updating CSS custom property values in 1 file (index.css) and fixing the login button background in 1 file (App.css).

**Complexity**: ⭐⭐ Simple (2/5)  
**Risk Level**: Low  
**Rollback**: Instant (git checkout of 2 CSS files)

---

## Step 1: Verify Current State

**Purpose**: Confirm you're working with expected baseline

### 1.1 Check Current Branch

```bash
cd /home/runner/work/github-workflows/github-workflows
git status
```

### 1.2 Verify Current Theme Variables

```bash
grep -A 13 "^:root" frontend/src/index.css
grep -A 12 "dark-mode-active" frontend/src/index.css
```

**Expected**: `--color-bg: #ffffff` (light) and `--color-bg: #0d1117` (dark)

### 1.3 Verify Login Button

```bash
grep "background" frontend/src/App.css | grep -i "login"
```

**Expected**: Line referencing `var(--color-text)`

---

## Step 2: Update Light Mode CSS Variables

**Purpose**: Apply orange background for light mode (FR-001, FR-002)

### 2.1 Edit `frontend/src/index.css`

Open the file and locate the `:root` selector (lines 2-15).

### 2.2 Update Variable Values

Change the following variables in `:root`:

| Variable | Old Value | New Value |
|----------|-----------|-----------|
| `--color-bg` | `#ffffff` | `#FF8C00` |
| `--color-bg-secondary` | `#f6f8fa` | `#E07800` |
| `--color-border` | `#d0d7de` | `#C06800` |
| `--color-text` | `#24292f` | `#000000` |
| `--color-text-secondary` | `#57606a` | `#3D2400` |
| `--shadow` | `rgba(0, 0, 0, 0.1)` | `rgba(0, 0, 0, 0.2)` |

### 2.3 Save and Verify

```bash
grep "color-bg:" frontend/src/index.css
```

**Expected**: `--color-bg: #FF8C00` in `:root` section

---

## Step 3: Update Dark Mode CSS Variables

**Purpose**: Apply dark orange variant for dark mode (FR-005)

### 3.1 Update Dark Mode Variables

In the same file, locate `html.dark-mode-active` (lines 18-30) and update:

| Variable | Old Value | New Value |
|----------|-----------|-----------|
| `--color-bg` | `#0d1117` | `#CC7000` |
| `--color-bg-secondary` | `#161b22` | `#A05500` |
| `--color-border` | `#30363d` | `#8A4500` |
| `--color-text` | `#e6edf3` | `#FFFFFF` |
| `--color-text-secondary` | `#8b949e` | `#FFD9A0` |
| `--shadow` | `rgba(0, 0, 0, 0.4)` | `rgba(0, 0, 0, 0.5)` |

### 3.2 Save and Verify

```bash
grep -A 12 "dark-mode-active" frontend/src/index.css
```

---

## Step 4: Fix Login Button Background

**Purpose**: Prevent login button from becoming invisible in dark mode (Assumption 4)

### 4.1 Edit `frontend/src/App.css`

Locate the `.login-button` class (around line 92).

### 4.2 Replace Variable with Explicit Color

```diff
 .login-button {
   display: flex;
   align-items: center;
   gap: 8px;
-  background: var(--color-text);
+  background: #000000;
   color: white;
 }
```

### 4.3 Save and Verify

```bash
grep -A 5 "login-button {" frontend/src/App.css | head -7
```

**Expected**: `background: #000000;`

---

## Step 5: Manual Verification

**Purpose**: Confirm changes work in running application

### 5.1 Start Development Server

```bash
cd frontend
npm run dev
```

### 5.2 Verify Light Mode

1. Open http://localhost:5173
2. **Check**: Orange background visible everywhere
3. **Check**: Text is black and readable
4. **Check**: Cards, sidebar, and header have orange backgrounds
5. **Check**: Login button is black with white text

### 5.3 Verify Dark Mode

1. Click theme toggle button (🌙/☀️)
2. **Check**: Background shifts to darker orange
3. **Check**: Text is white and readable
4. **Check**: Login button remains visible

### 5.4 Verify Responsive

1. Resize browser window to mobile width (~375px)
2. **Check**: Orange background fills viewport without gaps
3. **Check**: No layout shifts during resize

### 5.5 Stop Server

Press `Ctrl+C`

---

## Step 6: Verify No Regressions

**Purpose**: Ensure existing functionality still works

### 6.1 Search for Hardcoded Old Colors

```bash
grep -rn "#ffffff\|#f6f8fa\|#d0d7de\|#24292f\|#57606a" frontend/src/index.css
```

**Expected**: No matches (all replaced with orange values)

### 6.2 Run Build Check

```bash
cd frontend
npm run build
```

**Expected**: Build succeeds with no errors

---

## Troubleshooting

### Issue: Text Not Readable

**Symptom**: Text is hard to see on orange background  
**Solution**: Verify `--color-text` is set to `#000000` (not the old `#24292f`). Check that `--color-text-secondary` is dark enough.

### Issue: Login Button Invisible in Dark Mode

**Symptom**: Login button disappears when switching to dark mode  
**Solution**: Ensure `.login-button` background is `#000000` (not `var(--color-text)`)

### Issue: White Flashes During Navigation

**Symptom**: Brief white background appears between page transitions  
**Solution**: Verify `body` background uses `var(--color-bg-secondary)` and that it resolves to the orange shade

### Issue: Cards Blend Into Background

**Symptom**: Task cards not distinguishable from orange background  
**Solution**: Cards use `var(--color-bg)` while body uses `var(--color-bg-secondary)`. Verify both are different shades (#FF8C00 vs #E07800)

### Issue: Borders Not Visible

**Symptom**: Element borders disappear on orange background  
**Solution**: Verify `--color-border` is set to #C06800 (light) or #8A4500 (dark). These are darker than the background.

---

## Rollback Procedure

If you need to undo changes:

```bash
git checkout HEAD~1 -- frontend/src/index.css frontend/src/App.css
```

Or manually revert the CSS variables to their original values.

---

## Validation Checklist

Before marking feature complete, verify:

- [ ] **FR-001**: Orange background on all screens (login, dashboard, settings)
- [ ] **FR-002**: Consistent #FF8C00 shade in light mode
- [ ] **FR-003**: Text contrast ≥4.5:1 (black on orange)
- [ ] **FR-004**: Buttons, cards, forms have contrasting backgrounds/borders
- [ ] **FR-005**: Dark mode variant (#CC7000) present and readable
- [ ] **FR-006**: No layout issues on mobile, tablet, desktop
- [ ] **FR-007**: Orange is the base color (no overriding backgrounds)
- [ ] **FR-008**: Third-party content (if any) doesn't break layout
- [ ] **SC-001**: 100% of screens show orange
- [ ] **SC-002**: All text passes WCAG 2.1 AA contrast
- [ ] **SC-004**: No visual defects 320px-2560px
- [ ] **SC-005**: Dark mode passes contrast checks

---

## Next Steps

After completing this guide:

1. **Review**: Self-review CSS changes in git diff
2. **Test**: Run frontend build to ensure no CSS errors
3. **Screenshot**: Capture before/after for PR description
4. **Deploy**: Follow deployment process

---

## Phase 1 Quickstart Completion Checklist

- [x] Step-by-step instructions provided (6 steps)
- [x] Prerequisites documented
- [x] Time estimate included (10-15 minutes)
- [x] Commands are copy-pasteable
- [x] Expected outputs documented
- [x] Troubleshooting section included
- [x] Rollback procedure defined
- [x] Validation checklist aligned with spec FRs and SCs

**Status**: ✅ **QUICKSTART COMPLETE** - Ready for implementation by speckit.tasks
