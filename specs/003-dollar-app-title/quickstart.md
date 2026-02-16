# Quickstart Guide: Add Dollar Sign to Application Title

**Feature**: 003-dollar-app-title  
**Branch**: `copilot/add-dollar-sign-to-header`  
**Date**: 2026-02-16  
**Estimated Time**: 30 minutes  

## Overview

This guide provides step-by-step instructions for adding a dollar sign ($) prefix to the application title. The implementation involves simple string replacements in 3 locations across 2 files.

**Difficulty**: Beginner  
**Prerequisites**: Text editor, Node.js environment, basic Git knowledge  
**Risk Level**: Low (static text changes only)

---

## Prerequisites

Before starting, ensure you have:

1. **Development environment**: Node.js 18+ and npm installed
2. **Repository access**: Cloned repository with write permissions
3. **Branch**: Working on `copilot/add-dollar-sign-to-header` branch
4. **Dependencies installed**: Run `npm install` in `frontend/` directory (if not already done)
5. **Editor**: Any text editor or IDE (VS Code, Vim, nano, etc.)

---

## Step 0: Preparation

### 0.1 Navigate to Repository Root

```bash
cd /path/to/github-workflows
```

### 0.2 Verify Branch

Confirm you're on the correct feature branch:

```bash
git branch --show-current
# Should show: copilot/add-dollar-sign-to-header
```

If not on the correct branch:

```bash
git fetch origin
git checkout copilot/add-dollar-sign-to-header
```

### 0.3 Verify Current State

Check that titles currently show the old text:

```bash
# Check HTML title
grep -n "Welcome to Tech Connect 2026!" frontend/index.html
# Expected output: line 7

# Check React component headers
grep -n "Welcome to Tech Connect 2026!" frontend/src/App.tsx
# Expected output: lines 69 and 85
```

**Expected**: 3 matches total across 2 files

---

## Step 1: Update HTML Browser Tab Title

**Purpose**: Add dollar sign to browser tab title  
**File**: `frontend/index.html`  
**Time**: 2 minutes

### 1.1 Open HTML File

```bash
# Open with your preferred editor
nano frontend/index.html
# OR
code frontend/index.html
# OR
vim frontend/index.html
```

### 1.2 Locate Title Element

Navigate to line 7 (inside `<head>` section):

```html
<title>Welcome to Tech Connect 2026!</title>
```

**Context**: This is between `<meta name="viewport" ...>` and closing `</head>` tag

### 1.3 Add Dollar Sign Prefix

Replace the title content:

```html
<!-- Before -->
<title>Welcome to Tech Connect 2026!</title>

<!-- After -->
<title>$Welcome to Tech Connect 2026!</title>
```

**What changed**: Added `$` character at the beginning of the title text

### 1.4 Save File

- **nano**: Press `Ctrl+O` (save), `Enter`, then `Ctrl+X` (exit)
- **vim**: Press `Esc`, type `:wq`, press `Enter`
- **VS Code**: Press `Ctrl+S` (or `Cmd+S` on Mac)

### 1.5 Verify Change

```bash
grep -n '$Welcome to Tech Connect 2026!' frontend/index.html
# Expected output: line 7 with new title
```

---

## Step 2: Update Login Page Header

**Purpose**: Add dollar sign to header shown on login page  
**File**: `frontend/src/App.tsx`  
**Time**: 3 minutes

### 2.1 Open React Component File

```bash
# Open with your preferred editor
nano frontend/src/App.tsx
# OR
code frontend/src/App.tsx
# OR
vim frontend/src/App.tsx
```

### 2.2 Locate Login Header

Search for line ~69 (inside `if (!isAuthenticated)` block):

**Visual context**:
- Above: `if (!isAuthenticated) {`
- Above: `return (`
- Above: `<div className="app-login">`
- Target: `<h1>Welcome to Tech Connect 2026!</h1>`
- Below: `<p>Manage your GitHub Projects with natural language</p>`

```tsx
if (!isAuthenticated) {
  return (
    <div className="app-login">
      <h1>Welcome to Tech Connect 2026!</h1>
      <p>Manage your GitHub Projects with natural language</p>
      <LoginButton />
    </div>
  );
}
```

### 2.3 Add Dollar Sign Prefix

Replace the header text:

```tsx
<!-- Before -->
<h1>Welcome to Tech Connect 2026!</h1>

<!-- After -->
<h1>$Welcome to Tech Connect 2026!</h1>
```

**What changed**: Added `$` character at the beginning inside the `<h1>` tags

### 2.4 Save Progress

- **Don't close the file yet** - we have one more change in this file
- Save the current change (Ctrl+S / Cmd+S)

---

## Step 3: Update Authenticated App Header

**Purpose**: Add dollar sign to header shown after login  
**File**: `frontend/src/App.tsx` (same file, continue editing)  
**Time**: 3 minutes

### 3.1 Locate Authenticated Header

Search for line ~85 (inside main `return` statement):

**Visual context**:
- Above: `return (`
- Above: `<div className="app-container">`
- Above: `<header className="app-header">`
- Target: `<h1>Welcome to Tech Connect 2026!</h1>`
- Below: `<div className="header-actions">`

```tsx
return (
  <div className="app-container">
    <header className="app-header">
      <h1>Welcome to Tech Connect 2026!</h1>
      <div className="header-actions">
        <button 
          className="theme-toggle-btn"
          onClick={toggleTheme}
```

### 3.2 Add Dollar Sign Prefix

Replace the header text:

```tsx
<!-- Before -->
<h1>Welcome to Tech Connect 2026!</h1>

<!-- After -->
<h1>$Welcome to Tech Connect 2026!</h1>
```

**What changed**: Added `$` character at the beginning inside the `<h1>` tags

### 3.3 Save and Close File

- **nano**: Press `Ctrl+O` (save), `Enter`, then `Ctrl+X` (exit)
- **vim**: Press `Esc`, type `:wq`, press `Enter`
- **VS Code**: Press `Ctrl+S` (or `Cmd+S` on Mac), then close tab

### 3.4 Verify Both Changes

```bash
grep -n '$Welcome to Tech Connect 2026!' frontend/src/App.tsx
# Expected output: 2 lines (69 and 85) with new title
```

---

## Step 4: Verify All Changes

**Purpose**: Confirm all 3 instances were updated correctly  
**Time**: 2 minutes

### 4.1 Search for Old Title

Verify no old title remains in user-facing code:

```bash
grep -r "Welcome to Tech Connect 2026!" frontend/ --exclude-dir=node_modules --exclude-dir=dist
# Expected: Should only find matches in test files (if any), NOT in index.html or App.tsx
```

### 4.2 Search for New Title

Confirm new title is present in all locations:

```bash
grep -rn '\$Welcome to Tech Connect 2026!' frontend/ --exclude-dir=node_modules --exclude-dir=dist
# Expected output:
# frontend/index.html:7:    <title>$Welcome to Tech Connect 2026!</title>
# frontend/src/App.tsx:69:      <h1>$Welcome to Tech Connect 2026!</h1>
# frontend/src/App.tsx:85:      <h1>$Welcome to Tech Connect 2026!</h1>
```

### 4.3 Check Git Diff

Review your changes:

```bash
git diff frontend/index.html frontend/src/App.tsx
```

**Expected output**:
- 3 lines with `-` (old title removed)
- 3 lines with `+` (new title added with $)
- All other lines unchanged

---

## Step 5: Build and Type Check

**Purpose**: Ensure changes don't break TypeScript compilation or build  
**Time**: 5 minutes

### 5.1 Navigate to Frontend Directory

```bash
cd frontend
```

### 5.2 Run TypeScript Type Check (Optional)

If TypeScript compilation is configured:

```bash
npx tsc --noEmit
# Expected: No type errors (string literals don't affect types)
```

**Note**: If this command fails with "command not found", skip it - the build process will verify TypeScript anyway.

### 5.3 Run Build

Build the frontend application:

```bash
npm run build
```

**Expected output**:
- "vite build" executes successfully
- "✓ built in [time]" message appears
- `dist/` directory is created/updated
- No errors or warnings related to title changes

**If build fails**:
1. Check for syntax errors in index.html or App.tsx
2. Verify no extra or missing characters (e.g., unclosed tags)
3. Review git diff to ensure only title strings changed

### 5.4 Verify Built Files

Check that built files contain new title:

```bash
grep '\$Welcome to Tech Connect 2026!' dist/index.html
# Expected: Match found in built HTML
```

---

## Step 6: Test in Browser

**Purpose**: Visual verification of dollar sign in all locations  
**Time**: 5 minutes

### 6.1 Start Development Server

From the `frontend/` directory:

```bash
npm run dev
```

**Expected output**:
- "VITE ready" message
- "Local: http://localhost:5173/" (or similar port)
- Development server running

### 6.2 Open Application in Browser

Open the URL shown in terminal (typically `http://localhost:5173/`)

### 6.3 Test Browser Tab Title (FR-001, SC-001)

**Check**:
- [ ] Browser tab displays "$Welcome to Tech Connect 2026!"
- [ ] Dollar sign is visible and clear
- [ ] Title is not truncated

### 6.4 Test Login Page Header (FR-001, FR-003, FR-004)

On the login/unauthenticated page:

**Check**:
- [ ] Page header shows "$Welcome to Tech Connect 2026!"
- [ ] Dollar sign styling matches rest of title (font, color, size)
- [ ] Header is readable and not cut off

### 6.5 Test Authenticated Header (FR-001, FR-003, FR-004)

Log in to the application:

**Check**:
- [ ] Main application header shows "$Welcome to Tech Connect 2026!"
- [ ] Dollar sign styling is consistent
- [ ] Header layout is unchanged (theme toggle button, login button still visible)

### 6.6 Test Responsive Layouts (FR-004, SC-002)

Resize browser window or use DevTools responsive mode:

**Mobile (320px width)**:
- [ ] Header text wraps gracefully or stays on one line
- [ ] Dollar sign remains visible
- [ ] No horizontal scrolling

**Tablet (768px width)**:
- [ ] Header displays properly
- [ ] Dollar sign visible

**Desktop (1920px+ width)**:
- [ ] Header displays properly
- [ ] Dollar sign visible

### 6.7 Test Multiple Browsers (SC-001, SC-004)

If possible, test in:
- [ ] Chrome/Chromium
- [ ] Firefox
- [ ] Safari (if on Mac)
- [ ] Edge (if on Windows)

**Check**: Dollar sign renders identically across browsers

### 6.8 Stop Development Server

Return to terminal and press `Ctrl+C` to stop the dev server

---

## Step 7: Test Accessibility (Optional)

**Purpose**: Verify screen reader announces dollar sign  
**Time**: 5 minutes (optional, recommended)

### 7.1 Enable Screen Reader

**Windows**: Windows Narrator (Windows + Ctrl + Enter)  
**Mac**: VoiceOver (Cmd + F5)  
**Linux**: Orca screen reader

### 7.2 Navigate to Application

With screen reader active, navigate to the application URL

### 7.3 Listen to Page Title Announcement

**Check**:
- [ ] Screen reader announces page title on load
- [ ] Dollar sign is announced as "dollar sign" or "dollar"
- [ ] Full title is read: "dollar [Welcome to Tech Connect 2026!]"

### 7.4 Navigate to Headers

Use screen reader heading navigation (H key in most screen readers):

**Check**:
- [ ] Login header is announced with dollar sign
- [ ] Authenticated header (after login) is announced with dollar sign

### 7.5 Disable Screen Reader

**Windows**: Windows + Ctrl + Enter  
**Mac**: Cmd + F5  
**Linux**: Alt + Super + S

---

## Step 8: Update Tests (If Applicable)

**Purpose**: Update E2E tests to expect new title  
**Time**: 5-10 minutes

### 8.1 Check for Existing Tests

```bash
cd /path/to/github-workflows/frontend
grep -rn "Welcome to Tech Connect 2026!" e2e/
```

**If no matches found**: Skip to Step 9 (no tests to update)

**If matches found**: Continue with test updates

### 8.2 Open Test File

Likely location: `frontend/e2e/ui.spec.ts`

```bash
nano e2e/ui.spec.ts
# OR
code e2e/ui.spec.ts
```

### 8.3 Update Test Expectations

Find assertions like:

```typescript
// Before
await expect(page).toHaveTitle('Welcome to Tech Connect 2026!');
await expect(page.locator('h1')).toContainText('Welcome to Tech Connect 2026!');
```

Update to:

```typescript
// After
await expect(page).toHaveTitle('$Welcome to Tech Connect 2026!');
await expect(page.locator('h1')).toContainText('$Welcome to Tech Connect 2026!');
```

### 8.4 Save Test File

Save and close the file

### 8.5 Run E2E Tests

```bash
npm run test:e2e
```

**Expected**: All tests pass with new title expectations

**If tests fail**:
1. Review error messages for title mismatches
2. Ensure all test assertions were updated
3. Verify application is running correctly (repeat Step 6)

---

## Step 9: Commit Changes

**Purpose**: Save changes to Git with descriptive commit message  
**Time**: 2 minutes

### 9.1 Navigate to Repository Root

```bash
cd /path/to/github-workflows
```

### 9.2 Stage Changes

```bash
git add frontend/index.html frontend/src/App.tsx
```

**If tests were updated**:

```bash
git add frontend/e2e/ui.spec.ts
```

### 9.3 Review Staged Changes

```bash
git diff --staged
```

**Verify**:
- Only intended files are staged
- Only title strings changed (3 instances)
- No unintended modifications

### 9.4 Commit with Descriptive Message

```bash
git commit -m "Add dollar sign ($) prefix to application title

- Update HTML page title in index.html
- Update login page header in App.tsx
- Update authenticated header in App.tsx
- All titles now show: \$Welcome to Tech Connect 2026!

Addresses: FR-001 through FR-006
Completes user stories: US1 (P1), US2 (P1)"
```

### 9.5 Verify Commit

```bash
git log -1 --stat
```

**Expected output**: Shows commit with changed files

---

## Step 10: Push and Verify

**Purpose**: Push changes to remote branch  
**Time**: 2 minutes

### 10.1 Push to Remote

```bash
git push origin copilot/add-dollar-sign-to-header
```

**Expected output**: 
- "Writing objects: 100%"
- "[remote branch] -> [remote branch]"

### 10.2 Verify on GitHub

1. Navigate to repository on GitHub
2. View pull request #243 (if it exists)
3. Check "Files changed" tab
4. Verify 2-3 files changed with title updates

---

## Troubleshooting

### Issue: Build fails with syntax error

**Symptom**: `npm run build` shows HTML/JSX syntax error

**Solution**:
1. Check for unclosed tags in index.html or App.tsx
2. Ensure dollar sign is inside quotes: `<h1>$Welcome...</h1>` not `<h1>$"Welcome..."`
3. Verify UTF-8 encoding: `file -i frontend/index.html frontend/src/App.tsx`

---

### Issue: Dollar sign not visible in browser

**Symptom**: Browser shows "Welcome to Tech Connect 2026!" without $

**Solution**:
1. Clear browser cache: Ctrl+Shift+Delete (or Cmd+Shift+Delete)
2. Hard refresh: Ctrl+Shift+R (or Cmd+Shift+R)
3. Check built files: `grep '\$' frontend/dist/index.html`
4. Restart dev server: Stop (Ctrl+C) and run `npm run dev` again

---

### Issue: Git diff shows unexpected changes

**Symptom**: `git diff` shows more than 3 line changes

**Solution**:
1. Review diff carefully: `git diff frontend/`
2. If auto-formatter ran: Check if only whitespace changed
3. Revert unintended changes: `git checkout -- [file]`
4. Reapply manual title changes

---

### Issue: Tests fail after update

**Symptom**: E2E tests show title mismatch errors

**Solution**:
1. Verify test expectations match new title exactly
2. Check for escaped characters in test strings
3. Run single test to isolate issue: `npm run test:e2e -- --grep "title"`
4. Ensure application is actually showing new title (Step 6)

---

### Issue: Screen reader doesn't announce dollar sign

**Symptom**: Screen reader skips over $ or announces incorrectly

**Solution**:
- **This is expected behavior variation** between screen readers
- NVDA: May say "dollar sign"
- JAWS: May say "dollar"
- VoiceOver: May say "dollar symbol"
- All variations satisfy accessibility requirement (FR-005)

---

## Success Criteria

By the end of this quickstart, you should have:

- [x] Updated 3 title instances across 2 files
- [x] Verified changes compile and build successfully
- [x] Tested dollar sign display in browser (tab + headers)
- [x] Tested responsive layouts (mobile, tablet, desktop)
- [x] Optionally tested screen reader accessibility
- [x] Updated E2E tests (if applicable)
- [x] Committed and pushed changes to feature branch

---

## Next Steps

After completing this quickstart:

1. **Code Review**: Request review from team members
2. **QA Testing**: Have QA verify changes in staging environment
3. **Merge**: Merge pull request after approval
4. **Deploy**: Deploy to production
5. **Monitor**: Check production logs for any issues
6. **Verify**: Confirm dollar sign appears on production site

---

## Time Breakdown

| Step | Estimated Time | Cumulative |
|------|----------------|------------|
| Step 0: Preparation | 2 min | 2 min |
| Step 1: Update HTML title | 2 min | 4 min |
| Step 2: Update login header | 3 min | 7 min |
| Step 3: Update auth header | 3 min | 10 min |
| Step 4: Verify changes | 2 min | 12 min |
| Step 5: Build and type check | 5 min | 17 min |
| Step 6: Test in browser | 5 min | 22 min |
| Step 7: Test accessibility (optional) | 5 min | 27 min |
| Step 8: Update tests (if needed) | 5-10 min | 32-37 min |
| Step 9: Commit changes | 2 min | 34-39 min |
| Step 10: Push and verify | 2 min | 36-41 min |

**Total Estimated Time**: 30-40 minutes (depending on optional steps)

---

## References

- **Feature Spec**: `specs/003-dollar-app-title/spec.md`
- **Implementation Plan**: `specs/003-dollar-app-title/plan.md`
- **Research**: `specs/003-dollar-app-title/research.md`
- **Data Model**: `specs/003-dollar-app-title/data-model.md`
- **File Contracts**: `specs/003-dollar-app-title/contracts/file-changes.md`
- **Pull Request**: PR #243 on `copilot/add-dollar-sign-to-header` branch
