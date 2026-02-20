# Quickstart Guide: Add Purple Background Color to App

**Feature**: 005-purple-background | **Date**: 2026-02-20  
**Estimated Time**: 5–10 minutes  
**Prerequisites**: Git access, text editor

## Overview

This guide walks through implementing the purple background (#7C3AED) for the Agent Projects app. The implementation involves adding a CSS custom property and updating 3 CSS rules across 2 files.

**Complexity**: ⭐ Trivial (1/5)  
**Risk Level**: Minimal  
**Rollback**: Instant (single git revert)

---

## Step 1: Verify Current State

**Purpose**: Confirm you're working with expected baseline

### 1.1 Check Current Branch

```bash
cd /home/runner/work/github-workflows/github-workflows
git status
```

**Expected**: On branch `005-purple-background` or similar feature branch

### 1.2 Verify Current Background

```bash
# Check body background in index.css
grep "background:" frontend/src/index.css
```

**Expected Output**:
```
  background: var(--color-bg-secondary);
```

### 1.3 Verify Login Text Colors

```bash
grep -A1 "app-login h1" frontend/src/App.css
grep -A1 "app-login p" frontend/src/App.css
```

**Expected Output**:
```
.app-login h1 {
  font-size: 32px;
  color: var(--color-text);
.app-login p {
  color: var(--color-text-secondary);
```

If the above matches, proceed to Step 2.

---

## Step 2: Add Purple CSS Variable (Light Mode)

**Purpose**: Define the purple background color in the global theme

### 2.1 Edit `frontend/src/index.css`

Open the file and locate the `:root` block (lines 2–15).

### 2.2 Add Variable After `--color-bg-secondary`

Find:
```css
  --color-bg-secondary: #f6f8fa;
  --color-border: #d0d7de;
```

Add `--color-bg-app` between them:
```css
  --color-bg-secondary: #f6f8fa;
  --color-bg-app: #7C3AED;
  --color-border: #d0d7de;
```

### 2.3 Save and Verify

```bash
grep "color-bg-app" frontend/src/index.css
```

**Expected**: At least 1 match showing `--color-bg-app: #7C3AED`

---

## Step 3: Add Purple CSS Variable (Dark Mode)

**Purpose**: Maintain purple in dark mode for brand consistency

### 3.1 Locate Dark Theme Block

Find the `html.dark-mode-active` block (lines 18–30).

### 3.2 Add Variable After `--color-bg-secondary`

Find:
```css
  --color-bg-secondary: #161b22;
  --color-border: #30363d;
```

Add `--color-bg-app` between them:
```css
  --color-bg-secondary: #161b22;
  --color-bg-app: #7C3AED;
  --color-border: #30363d;
```

### 3.3 Verify Both Declarations

```bash
grep -c "color-bg-app" frontend/src/index.css
```

**Expected**: `2` (one in `:root`, one in `html.dark-mode-active`)

---

## Step 4: Update Body Background

**Purpose**: Apply the purple background to the body element

### 4.1 Locate Body Selector

Find the `body` block in `index.css` (line ~38–44).

### 4.2 Update Background Property

Find:
```css
  background: var(--color-bg-secondary);
```

Change to:
```css
  background: var(--color-bg-app);
```

### 4.3 Verify Change

```bash
grep "background:" frontend/src/index.css
```

**Expected**: `background: var(--color-bg-app);`

---

## Step 5: Update Login Page Text Colors

**Purpose**: Ensure text is readable on purple background (WCAG AA compliance)

### 5.1 Edit `frontend/src/App.css`

Open the file and locate the `.app-login h1` and `.app-login p` selectors.

### 5.2 Update Heading Color

Find:
```css
.app-login h1 {
  font-size: 32px;
  color: var(--color-text);
}
```

Change to:
```css
.app-login h1 {
  font-size: 32px;
  color: #ffffff;
}
```

### 5.3 Update Subtitle Color

Find:
```css
.app-login p {
  color: var(--color-text-secondary);
  margin-bottom: 16px;
}
```

Change to:
```css
.app-login p {
  color: rgba(255, 255, 255, 0.85);
  margin-bottom: 16px;
}
```

### 5.4 Verify Changes

```bash
grep -A2 "app-login h1" frontend/src/App.css | grep "color:"
grep -A1 "app-login p {" frontend/src/App.css | grep "color:"
```

**Expected**:
```
  color: #ffffff;
  color: rgba(255, 255, 255, 0.85);
```

---

## Step 6: Manual Verification

**Purpose**: Confirm changes work in running application

### 6.1 Start Development Server

```bash
cd frontend
npm run dev
```

**Expected**: Server starts on http://localhost:5173 (or similar)

### 6.2 Verify Login Page

1. Open http://localhost:5173 in browser
2. **Check**: Purple (#7C3AED) background visible
3. **Check**: "Agent Projects" heading is white and readable
4. **Check**: Subtitle text is light/readable
5. **Check**: Login button is visible and clickable

### 6.3 Verify Dark Mode Toggle

1. If accessible, toggle dark mode
2. **Check**: Purple background persists in dark mode

### 6.4 Verify Authenticated Views (if possible)

1. Log in using test credentials
2. **Check**: Header, sidebar, chat section render with their own backgrounds
3. **Check**: Purple body not visible behind authenticated components

### 6.5 Cross-Browser Check

1. Open in Chrome and Firefox (at minimum)
2. **Check**: Purple renders identically

### 6.6 FOUC Check

1. Hard-refresh page (Ctrl+Shift+R)
2. **Check**: No flash of white/unstyled background

### 6.7 Stop Server

Press `Ctrl+C` to stop the dev server

---

## Step 7: Commit Changes

**Purpose**: Persist changes to git

### 7.1 Stage Changed Files

```bash
cd /home/runner/work/github-workflows/github-workflows

git add frontend/src/index.css
git add frontend/src/App.css
```

### 7.2 Commit with Clear Message

```bash
git commit -m "Apply purple background (#7C3AED) to app body

- Add --color-bg-app CSS variable in light and dark themes
- Update body background to use --color-bg-app
- Adjust login page text colors for WCAG AA contrast

Addresses FR-001, FR-002, FR-003, FR-005, FR-006"
```

### 7.3 Verify Commit

```bash
git log -1 --stat
```

**Expected**: Shows commit with 2 files changed (index.css, App.css)

---

## Step 8: Push and Create PR (If Applicable)

**Purpose**: Share changes for review

### 8.1 Push to Remote

```bash
git push origin 005-purple-background
```

### 8.2 Create Pull Request

Follow your team's PR process (GitHub UI, `gh` CLI, etc.)

**PR Title**: "Apply purple background (#7C3AED) to app"  
**PR Description**: Reference spec at `specs/005-purple-background/spec.md`

---

## Troubleshooting

### Issue: Purple Background Not Showing

**Symptom**: Body still shows old background color  
**Solution**: 
1. Check `--color-bg-app` is defined in `:root` block
2. Check body uses `var(--color-bg-app)` not `var(--color-bg-secondary)`
3. Hard-refresh browser (Ctrl+Shift+R)

### Issue: Text Not Readable on Login Page

**Symptom**: Dark text on purple background  
**Solution**: Verify `.app-login h1 { color: #ffffff; }` and `.app-login p { color: rgba(255, 255, 255, 0.85); }` are applied

### Issue: Components Show Purple Background

**Symptom**: Board columns, sidebar, or modals have purple background  
**Solution**: If you accidentally changed `--color-bg-secondary` instead of adding `--color-bg-app`, revert and follow steps 2–4 exactly

### Issue: CSS Syntax Error

**Symptom**: Vite build fails or styles don't load  
**Solution**: Check for missing semicolons, unclosed brackets, or typos in hex value

### Issue: Dark Mode Shows Different Color

**Symptom**: Dark mode doesn't show purple  
**Solution**: Verify `--color-bg-app: #7C3AED` is defined in `html.dark-mode-active` block (Step 3)

---

## Rollback Procedure

If you need to undo changes:

### Quick Rollback (Before Push)

```bash
git checkout -- frontend/src/index.css frontend/src/App.css
```

### Rollback After Push

```bash
git revert <commit-hash>
git push origin 005-purple-background
```

---

## Validation Checklist

Before marking feature complete, verify:

- [ ] **FR-001**: Purple background visible on login page ✅
- [ ] **FR-002**: DevTools shows `rgb(124, 58, 237)` (#7C3AED) ✅
- [ ] **FR-003**: White text on purple meets WCAG AA (6.65:1) ✅
- [ ] **FR-004**: Purple renders same in Chrome, Firefox, Safari, Edge ✅
- [ ] **FR-005**: No FOUC on hard-refresh ✅
- [ ] **FR-006**: Background defined via `--color-bg-app` CSS variable ✅
- [ ] **FR-007**: Authenticated components render correctly ✅

---

## Success Criteria

✅ **Feature Complete** when:
1. Body background is purple (#7C3AED) in both light and dark modes
2. Login page text is white and readable (WCAG AA)
3. Authenticated views are unaffected (components have own backgrounds)
4. No FOUC on page load
5. Changes committed to git

**Total Time**: ~5–10 minutes for experienced developer

---

## Phase 1 Quickstart Completion Checklist

- [x] Step-by-step instructions provided (8 steps)
- [x] Prerequisites documented
- [x] Time estimate included (5–10 minutes)
- [x] Commands are copy-pasteable
- [x] Expected outputs documented
- [x] Troubleshooting section included
- [x] Rollback procedure defined
- [x] Validation checklist aligned with spec
- [x] Success criteria clearly stated

**Status**: ✅ **QUICKSTART COMPLETE** — Ready for implementation by speckit.tasks
