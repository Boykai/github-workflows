# Quickstart Guide: App Title Update to 'GitHub Workflows'

**Feature**: 001-app-title-update | **Date**: 2026-02-14  
**Estimated Time**: 5-10 minutes  
**Prerequisites**: Git access, text editor

## Overview

This guide walks through implementing the app title change from "Welcome to Tech Connect 2026!" to "GitHub Workflows". The implementation involves 3 simple string replacements in 2 frontend files.

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

**Expected**: On branch `001-app-title-update` or similar feature branch

### 1.2 Verify Current Title

```bash
# Check HTML title
grep -n "<title>" frontend/index.html

# Check App.tsx headers
grep -n "Welcome to Tech Connect 2026!" frontend/src/App.tsx
```

**Expected Output**:
```
frontend/index.html:7:    <title>Welcome to Tech Connect 2026!</title>
frontend/src/App.tsx:69:    <h1>Welcome to Tech Connect 2026!</h1>
frontend/src/App.tsx:85:  <h1>Welcome to Tech Connect 2026!</h1>
```

If you see 3 matches (1 in index.html, 2 in App.tsx), proceed to Step 2.

---

## Step 2: Update HTML Page Title

**Purpose**: Change browser tab title

### 2.1 Edit `frontend/index.html`

Open the file:
```bash
nano frontend/index.html
# or use your preferred editor
```

### 2.2 Locate Line 7

Find the `<title>` element:
```html
<title>Welcome to Tech Connect 2026!</title>
```

### 2.3 Replace Title Text

Change to:
```html
<title>GitHub Workflows</title>
```

### 2.4 Save and Verify

Save the file and verify:
```bash
grep "<title>" frontend/index.html
```

**Expected**: `<title>GitHub Workflows</title>`

---

## Step 3: Update React Component Headers

**Purpose**: Change application header in login and authenticated views

### 3.1 Edit `frontend/src/App.tsx`

Open the file:
```bash
nano frontend/src/App.tsx
# or use your preferred editor
```

### 3.2 Find First Header (Login Page)

Search for line ~69 (in the `!isAuthenticated` condition):
```tsx
<h1>Welcome to Tech Connect 2026!</h1>
```

**Context**: This is inside the login form section

### 3.3 Replace First Header

Change to:
```tsx
<h1>GitHub Workflows</h1>
```

### 3.4 Find Second Header (Authenticated View)

Search for line ~85 (in the chat container):
```tsx
<h1>Welcome to Tech Connect 2026!</h1>
```

**Context**: This is at the top of the main chat interface

### 3.5 Replace Second Header

Change to:
```tsx
<h1>GitHub Workflows</h1>
```

### 3.6 Save and Verify

Save the file and verify both changes:
```bash
grep -n "GitHub Workflows" frontend/src/App.tsx
```

**Expected**: 2 matches showing lines with `<h1>GitHub Workflows</h1>`

---

## Step 4: Verify No Old References Remain

**Purpose**: Confirm complete replacement (FR-005)

### 4.1 Search for Old Title

```bash
grep -r "Welcome to Tech Connect 2026!" frontend/
```

**Expected**: No matches (or only matches in test files if tests hardcoded title)

If you see matches in `frontend/e2e/auth.spec.ts`, proceed to Step 5 (optional).

---

## Step 5: Update E2E Tests (Optional)

**Purpose**: Fix test failures if tests assert old title

### 5.1 Run E2E Tests

```bash
cd frontend
npm run test:e2e
```

### 5.2 If Tests Fail on Title

If you see title assertion failure, edit `frontend/e2e/auth.spec.ts`:

Find:
```typescript
await expect(page).toHaveTitle(/GitHub Projects|Chat/i);
```

Change to:
```typescript
await expect(page).toHaveTitle(/GitHub Workflows/i);
```

### 5.3 Re-run Tests

```bash
npm run test:e2e
```

**Note**: If tests passed in Step 5.1, skip this update. Only change if tests explicitly fail.

---

## Step 6: Manual Verification

**Purpose**: Confirm changes work in running application

### 6.1 Start Development Server

```bash
cd frontend
npm run dev
```

**Expected**: Server starts on http://localhost:5173 (or similar)

### 6.2 Open in Browser

Navigate to http://localhost:5173

### 6.3 Verify Browser Tab

**Check**: Browser tab displays "GitHub Workflows"

### 6.4 Verify Login Page Header

**Check**: Page shows `<h1>GitHub Workflows</h1>` header

### 6.5 Authenticate

Log in using test credentials (if available) or bypass auth

### 6.6 Verify Authenticated Header

**Check**: Main application header shows "GitHub Workflows"

### 6.7 Stop Server

Press `Ctrl+C` to stop the dev server

---

## Step 7: Commit Changes

**Purpose**: Persist changes to git

### 7.1 Stage Changed Files

```bash
cd /home/runner/work/github-workflows/github-workflows

# Stage frontend files
git add frontend/index.html
git add frontend/src/App.tsx

# Optionally stage test file if updated
# git add frontend/e2e/auth.spec.ts
```

### 7.2 Commit with Clear Message

```bash
git commit -m "Update app title to 'GitHub Workflows'

- Change HTML page title in index.html
- Update login page header in App.tsx
- Update authenticated header in App.tsx

Addresses FR-001, FR-002, FR-004, FR-005"
```

### 7.3 Verify Commit

```bash
git log -1 --stat
```

**Expected**: Shows commit with 2-3 files changed (index.html, App.tsx, optionally auth.spec.ts)

---

## Step 8: Push and Create PR (If Applicable)

**Purpose**: Share changes for review

### 8.1 Push to Remote

```bash
git push origin 001-app-title-update
```

### 8.2 Create Pull Request

Follow your team's PR process (GitHub UI, `gh` CLI, etc.)

**PR Title**: "Update app title to 'GitHub Workflows'"  
**PR Description**: Reference spec at `specs/001-app-title-update/spec.md`

---

## Troubleshooting

### Issue: Can't Find Old Title Text

**Symptom**: `grep` returns no matches for old title  
**Solution**: Title may already be updated. Check git log to see if changes exist.

### Issue: Syntax Error in App.tsx

**Symptom**: TypeScript compilation fails  
**Solution**: Ensure you only changed text inside `<h1>` tags, not the JSX structure:
```tsx
<h1>GitHub Workflows</h1>  <!-- Correct -->
<h1>GitHub Workflows<h1>   <!-- Wrong: missing closing / -->
```

### Issue: Dev Server Won't Start

**Symptom**: `npm run dev` fails  
**Solution**: 
1. Check Node.js version: `node --version` (should be 18+)
2. Reinstall dependencies: `cd frontend && npm install`
3. Check for port conflicts: Kill process on port 5173

### Issue: E2E Tests Fail

**Symptom**: Playwright tests fail on title assertion  
**Solution**: Update title assertion in `frontend/e2e/auth.spec.ts` (see Step 5)

### Issue: Changes Not Visible in Browser

**Symptom**: Browser still shows old title after dev server restart  
**Solution**: 
1. Hard refresh: `Ctrl+Shift+R` (Chrome) or `Cmd+Shift+R` (Mac)
2. Clear browser cache
3. Check if you saved the files

---

## Rollback Procedure

If you need to undo changes:

### Quick Rollback (Before Push)

```bash
git reset --hard HEAD~1
```

### Rollback After Push

```bash
git revert <commit-hash>
git push origin 001-app-title-update
```

---

## Validation Checklist

Before marking feature complete, verify:

- [ ] **FR-001**: Browser tab displays "GitHub Workflows" ✅
- [ ] **FR-002**: Application headers show "GitHub Workflows" (login + authenticated) ✅
- [ ] **FR-003**: Title visible in Chrome, Firefox, Safari, Edge ✅
- [ ] **FR-004**: Title consistent across all pages ✅
- [ ] **FR-005**: No old title references in `grep` search ✅
- [ ] **SC-001**: Manual testing confirms browser tab title ✅
- [ ] **SC-002**: Manual testing confirms header consistency ✅
- [ ] **SC-003**: Codebase search shows zero old title matches ✅

---

## Success Criteria

✅ **Feature Complete** when:
1. Browser tab shows "GitHub Workflows"
2. Login page header shows "GitHub Workflows"
3. Authenticated header shows "GitHub Workflows"
4. No old title references remain in frontend code
5. Changes committed to git

**Total Time**: ~5-10 minutes for experienced developer

---

## Next Steps

After completing this guide:

1. **Review**: Self-review changes in git diff
2. **Test**: Run full E2E suite if your project requires it
3. **Document**: Update CHANGELOG or release notes (if applicable)
4. **Deploy**: Follow your deployment process
5. **Announce**: Notify team of branding update

---

## Phase 1 Quickstart Completion Checklist

- [x] Step-by-step instructions provided (8 steps)
- [x] Prerequisites documented
- [x] Time estimate included (5-10 minutes)
- [x] Commands are copy-pasteable
- [x] Expected outputs documented
- [x] Troubleshooting section included
- [x] Rollback procedure defined
- [x] Validation checklist aligned with spec
- [x] Success criteria clearly stated

**Status**: ✅ **QUICKSTART COMPLETE** - Ready for implementation by speckit.tasks
