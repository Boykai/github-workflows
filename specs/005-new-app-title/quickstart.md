# Quickstart Guide: Update App Title to "New App"

**Feature**: 005-new-app-title | **Date**: 2026-02-19  
**Estimated Time**: 10-15 minutes  
**Prerequisites**: Git access, text editor

## Overview

This guide walks through implementing the app title change from "Agent Projects" to "New App" across all locations in the codebase. The implementation involves string replacements in ~15 files spanning frontend, backend, configuration, tests, and documentation.

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
# Count all occurrences (excluding specs/ and .git/)
grep -rn "Agent Projects" --include="*.ts" --include="*.tsx" --include="*.py" --include="*.json" --include="*.html" --include="*.md" --include="*.sh" --include="*.toml" | grep -v ".git/" | grep -v "node_modules/" | grep -v "specs/"
```

**Expected Output**: ~20 matches across frontend, backend, config, tests, and docs

---

## Step 2: Update Frontend Files

**Purpose**: Change browser tab title and application headers

### 2.1 Edit `frontend/index.html`

Replace line 7:
```diff
-    <title>Agent Projects</title>
+    <title>New App</title>
```

### 2.2 Edit `frontend/src/App.tsx`

Replace line 72 (login header):
```diff
-        <h1>Agent Projects</h1>
+        <h1>New App</h1>
```

Replace line 89 (authenticated header):
```diff
-          <h1>Agent Projects</h1>
+          <h1>New App</h1>
```

### 2.3 Edit `frontend/src/types/index.ts`

Replace line 2 (file comment):
```diff
- * TypeScript types for Agent Projects API.
+ * TypeScript types for New App API.
```

### 2.4 Edit `frontend/src/services/api.ts`

Replace line 2 (file comment):
```diff
- * API client service for Agent Projects.
+ * API client service for New App.
```

---

## Step 3: Update Backend Files

**Purpose**: Change API metadata and log messages

### 3.1 Edit `backend/src/main.py`

Replace 4 occurrences:
```diff
-    logger.info("Starting Agent Projects API")
+    logger.info("Starting New App API")

-    logger.info("Shutting down Agent Projects API")
+    logger.info("Shutting down New App API")

-        title="Agent Projects API",
+        title="New App API",

-        description="REST API for Agent Projects",
+        description="REST API for New App",
```

### 3.2 Edit `backend/pyproject.toml`

Replace line 4 (description only; keep package name):
```diff
-description = "FastAPI backend for Agent Projects"
+description = "FastAPI backend for New App"
```

### 3.3 Edit `backend/README.md`

Replace header and body reference:
```diff
-# Agent Projects — Backend
+# New App — Backend
```

### 3.4 Edit `backend/tests/test_api_e2e.py`

Replace line 2:
```diff
-End-to-end API tests for the Agent Projects Backend.
+End-to-end API tests for the New App Backend.
```

---

## Step 4: Update Configuration Files

### 4.1 Edit `.devcontainer/devcontainer.json`

Replace line 2:
```diff
-  "name": "Agent Projects",
+  "name": "New App",
```

### 4.2 Edit `.devcontainer/post-create.sh`

Replace line 7:
```diff
-echo "🚀 Setting up Agent Projects development environment..."
+echo "🚀 Setting up New App development environment..."
```

---

## Step 5: Update E2E Tests

**Purpose**: Fix test assertions to match new title

### 5.1 Edit `frontend/e2e/auth.spec.ts`

Replace all 5 occurrences of `'Agent Projects'` with `'New App'`:
- Lines 12, 24, 38, 99: `toContainText('New App')`
- Line 62: `toHaveTitle(/New App/i)`

### 5.2 Edit `frontend/e2e/ui.spec.ts`

Replace 2 occurrences on lines 43, 67:
```diff
-    await expect(page.locator('h1')).toContainText('Agent Projects');
+    await expect(page.locator('h1')).toContainText('New App');
```

### 5.3 Edit `frontend/e2e/integration.spec.ts`

Replace 1 occurrence on line 69:
```diff
-    await expect(page.locator('h1')).toContainText('Agent Projects');
+    await expect(page.locator('h1')).toContainText('New App');
```

---

## Step 6: Update Documentation

### 6.1 Edit `README.md`

Replace line 1:
```diff
-# Agent Projects
+# New App
```

---

## Step 7: Verify No Old References Remain

**Purpose**: Confirm complete replacement (FR-005)

```bash
grep -rn "Agent Projects" --include="*.ts" --include="*.tsx" --include="*.py" --include="*.json" --include="*.html" --include="*.md" --include="*.sh" --include="*.toml" | grep -v ".git/" | grep -v "node_modules/" | grep -v "specs/"
```

**Expected**: No matches (or only internal package names like `agent-projects-frontend` and `agent-projects-backend`)

---

## Step 8: Manual Verification

### 8.1 Start Frontend Dev Server

```bash
cd frontend
npm run dev
```

### 8.2 Verify in Browser

1. **Browser tab**: Displays "New App"
2. **Login page header**: Shows "New App"
3. **After login header**: Shows "New App"

### 8.3 Start Backend Server

```bash
cd backend
python -m uvicorn src.main:app --reload
```

### 8.4 Verify API Docs

Navigate to `http://localhost:8000/api/docs` - title shows "New App API"

---

## Troubleshooting

### Issue: Old Title Still Visible in Browser
**Solution**: Hard refresh with `Ctrl+Shift+R` or clear browser cache

### Issue: E2E Tests Still Fail
**Solution**: Verify all 8 assertion strings were updated. Run `grep -rn "Agent Projects" frontend/e2e/`

### Issue: Backend Won't Start After Changes
**Solution**: Verify Python string syntax in `main.py` - ensure quotes are properly matched

---

## Rollback Procedure

```bash
git revert <commit-hash>
```

All files return to previous title "Agent Projects".

---

## Validation Checklist

- [ ] **FR-001**: Browser tab displays "New App"
- [ ] **FR-002**: Application headers show "New App" (login + authenticated)
- [ ] **FR-003**: Title visible across supported browsers
- [ ] **FR-004**: Title consistent across all pages
- [ ] **FR-005**: No old title references in codebase search
- [ ] **FR-006**: Configuration files updated
- [ ] **FR-007**: Documentation files updated
- [ ] **SC-001**: Browser tab title confirmed
- [ ] **SC-002**: Header consistency confirmed
- [ ] **SC-003**: Zero old title matches in search

---

## Phase 1 Quickstart Completion Checklist

- [x] Step-by-step instructions provided (8 steps)
- [x] Prerequisites documented
- [x] Time estimate included (10-15 minutes)
- [x] Commands are copy-pasteable
- [x] Expected outputs documented
- [x] Troubleshooting section included
- [x] Rollback procedure defined
- [x] Validation checklist aligned with spec

**Status**: ✅ **QUICKSTART COMPLETE** - Ready for implementation by speckit.tasks
