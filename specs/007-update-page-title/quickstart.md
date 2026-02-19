# Quickstart Guide: Update Page Title to "Front"

**Feature**: 007-update-page-title | **Date**: 2026-02-19  
**Estimated Time**: 5–10 minutes  
**Prerequisites**: Git access, text editor

## Overview

This guide walks through implementing the page title change from "Agent Projects" to "Front". The implementation involves 3 string replacements in 2 frontend source files and 8 assertion updates in 3 E2E test files.

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

**Expected**: On feature branch for this change

### 1.2 Verify Current Title

```bash
# Check HTML title
grep -n "<title>" frontend/index.html

# Check App.tsx headers
grep -n "Agent Projects" frontend/src/App.tsx
```

**Expected Output**:
```
frontend/index.html:7:    <title>Agent Projects</title>
frontend/src/App.tsx:72:        <h1>Agent Projects</h1>
frontend/src/App.tsx:89:          <h1>Agent Projects</h1>
```

If you see 3 matches (1 in index.html, 2 in App.tsx), proceed to Step 2.

---

## Step 2: Update HTML Page Title

**Purpose**: Change browser tab title

### 2.1 Edit `frontend/index.html`

**Line 7**: Replace title text

```diff
-    <title>Agent Projects</title>
+    <title>Front</title>
```

### 2.2 Verify

```bash
grep "<title>" frontend/index.html
```

**Expected**: `<title>Front</title>`

---

## Step 3: Update React Component Headers

**Purpose**: Change application header in login and authenticated views

### 3.1 Edit `frontend/src/App.tsx`

**Change 1 — Line 72** (login page header):
```diff
-        <h1>Agent Projects</h1>
+        <h1>Front</h1>
```

**Change 2 — Line 89** (authenticated header):
```diff
-          <h1>Agent Projects</h1>
+          <h1>Front</h1>
```

### 3.2 Verify

```bash
grep -n "Front" frontend/src/App.tsx
```

**Expected**: 2 matches showing lines with `<h1>Front</h1>`

---

## Step 4: Update E2E Test Assertions

**Purpose**: Prevent test failures from old title assertions

### 4.1 Edit `frontend/e2e/auth.spec.ts`

Replace all 5 occurrences of `'Agent Projects'` or `/Agent Projects/i`:

- **Line 12**: `toContainText('Agent Projects')` → `toContainText('Front')`
- **Line 24**: `toContainText('Agent Projects', { timeout: 5000 })` → `toContainText('Front', { timeout: 5000 })`
- **Line 38**: `toContainText('Agent Projects')` → `toContainText('Front')`
- **Line 62**: `toHaveTitle(/Agent Projects/i)` → `toHaveTitle(/Front/i)`
- **Line 99**: `toContainText('Agent Projects')` → `toContainText('Front')`

### 4.2 Edit `frontend/e2e/ui.spec.ts`

Replace both occurrences:

- **Line 43**: `toContainText('Agent Projects')` → `toContainText('Front')`
- **Line 67**: `toContainText('Agent Projects')` → `toContainText('Front')`

### 4.3 Edit `frontend/e2e/integration.spec.ts`

Replace the single occurrence:

- **Line 69**: `toContainText('Agent Projects')` → `toContainText('Front')`

---

## Step 5: Verify No Old References Remain

**Purpose**: Confirm complete replacement (FR-003)

```bash
grep -r "Agent Projects" frontend/index.html frontend/src/App.tsx frontend/e2e/
```

**Expected**: No matches

---

## Step 6: Manual Verification

**Purpose**: Confirm changes work in running application

### 6.1 Start Development Server

```bash
cd frontend
npm run dev
```

### 6.2 Verify in Browser

1. Navigate to http://localhost:5173
2. **Check**: Browser tab displays "Front"
3. **Check**: Login page shows `<h1>Front</h1>` header
4. Stop server with `Ctrl+C`

---

## Troubleshooting

### Issue: Can't Find Old Title Text

**Symptom**: `grep` returns no matches for "Agent Projects"  
**Solution**: Title may already be updated. Check git log to see if changes exist.

### Issue: E2E Tests Still Fail After Update

**Symptom**: Playwright tests fail on title assertion  
**Solution**: Verify all 8 assertion locations were updated. Run `grep -rn "Agent Projects" frontend/e2e/`.

### Issue: Changes Not Visible in Browser

**Symptom**: Browser still shows old title after dev server restart  
**Solution**: Hard refresh with `Ctrl+Shift+R` to bypass cache.

---

## Validation Checklist

Before marking feature complete, verify:

- [ ] **FR-001**: Browser tab displays "Front"
- [ ] **FR-002**: Main heading shows "Front" (login + authenticated)
- [ ] **FR-003**: No old title references in user-facing code
- [ ] **FR-004**: No visual regressions in page layout
- [ ] **FR-005**: Title consistent across all views

---

## Phase 1 Quickstart Completion Checklist

- [x] Step-by-step instructions provided (6 steps)
- [x] Prerequisites documented
- [x] Time estimate included (5–10 minutes)
- [x] Commands are copy-pasteable
- [x] Expected outputs documented
- [x] Troubleshooting section included
- [x] Validation checklist aligned with spec

**Status**: ✅ **QUICKSTART COMPLETE** — Ready for implementation by speckit.tasks
