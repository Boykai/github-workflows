# Quickstart Guide: Update App Title to "New App"

**Feature**: 005-new-app-title | **Date**: 2026-02-19  
**Estimated Time**: 10-15 minutes  
**Prerequisites**: Git access, text editor

## Overview

This guide walks through implementing the app title change from "Agent Projects" to "New App". The implementation involves string replacements across ~12 files spanning frontend, backend, configuration, documentation, and E2E tests.

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

**Expected**: On a feature branch for this work

### 1.2 Verify Current Title

```bash
# Search for all occurrences of "Agent Projects"
grep -rn "Agent Projects" frontend/index.html frontend/src/App.tsx backend/src/main.py backend/pyproject.toml frontend/package.json README.md backend/README.md .devcontainer/ .env.example frontend/e2e/
```

**Expected Output**: Multiple matches across ~12 files showing "Agent Projects" references

---

## Step 2: Update Frontend Files

**Purpose**: Change browser tab title and application headers

### 2.1 Edit `frontend/index.html`

**Line 7**: Change `<title>` text

```diff
-    <title>Agent Projects</title>
+    <title>New App</title>
```

### 2.2 Edit `frontend/src/App.tsx`

**Line 72** (login header): Change `<h1>` text

```diff
-        <h1>Agent Projects</h1>
+        <h1>New App</h1>
```

**Line 89** (authenticated header): Change `<h1>` text

```diff
-          <h1>Agent Projects</h1>
+          <h1>New App</h1>
```

---

## Step 3: Update Backend Files

**Purpose**: Change API metadata and package info

### 3.1 Edit `backend/src/main.py`

**Lines 85-86**: Change FastAPI title and description

```diff
-        title="Agent Projects API",
-        description="REST API for Agent Projects",
+        title="New App API",
+        description="REST API for New App",
```

### 3.2 Edit `backend/pyproject.toml`

**Lines 2, 4**: Change package name and description

```diff
-name = "agent-projects-backend"
+name = "new-app-backend"
```

```diff
-description = "FastAPI backend for Agent Projects"
+description = "FastAPI backend for New App"
```

---

## Step 4: Update Configuration Files

**Purpose**: Change dev container and environment settings

### 4.1 Edit `.devcontainer/devcontainer.json`

**Line 2**: Change container name

```diff
-  "name": "Agent Projects",
+  "name": "New App",
```

### 4.2 Edit `.devcontainer/post-create.sh`

**Line 7**: Change echo message

```diff
-echo "🚀 Setting up Agent Projects development environment..."
+echo "🚀 Setting up New App development environment..."
```

### 4.3 Edit `.env.example`

**Line 2**: Change header comment

```diff
-# Agent Projects - Environment Configuration
+# New App - Environment Configuration
```

### 4.4 Edit `frontend/package.json`

**Line 2**: Change package name

```diff
-  "name": "agent-projects-frontend",
+  "name": "new-app-frontend",
```

---

## Step 5: Update Documentation

**Purpose**: Change README headings and body text

### 5.1 Edit `README.md`

Replace all occurrences of "Agent Projects" with "New App" in the file.

### 5.2 Edit `backend/README.md`

Replace all occurrences of "Agent Projects" with "New App" in the file.

---

## Step 6: Update E2E Test Assertions

**Purpose**: Update test expectations to match new title

### 6.1 Edit `frontend/e2e/auth.spec.ts`

Replace all occurrences of `'Agent Projects'` with `'New App'` in test assertions.

### 6.2 Edit `frontend/e2e/ui.spec.ts`

Replace all occurrences of `'Agent Projects'` with `'New App'` in test assertions.

### 6.3 Edit `frontend/e2e/integration.spec.ts`

Replace the occurrence of `'Agent Projects'` with `'New App'` in the test assertion.

---

## Step 7: Verify No Old References Remain

**Purpose**: Confirm complete replacement (FR-005)

```bash
grep -rn "Agent Projects" --include="*.ts" --include="*.tsx" --include="*.html" --include="*.py" --include="*.toml" --include="*.json" --include="*.md" --include="*.sh" --include="*.example" .
```

**Expected**: No matches (zero output)

---

## Step 8: Manual Verification

**Purpose**: Confirm changes work in running application

### 8.1 Start Development Server

```bash
cd frontend
npm run dev
```

### 8.2 Verify in Browser

1. Open http://localhost:5173
2. Check browser tab shows "New App"
3. Check login page header shows "New App"
4. Log in and check authenticated header shows "New App"

### 8.3 Stop Server

Press `Ctrl+C` to stop the dev server

---

## Troubleshooting

### Issue: Old Title Still Shows in Browser

**Solution**: Hard refresh with `Ctrl+Shift+R` or clear browser cache

### Issue: E2E Tests Fail

**Solution**: Verify all test assertion strings were updated from "Agent Projects" to "New App"

### Issue: TypeScript Compilation Error

**Solution**: Ensure you only changed text inside `<h1>` tags, not the JSX structure

---

## Rollback Procedure

```bash
# Before push
git checkout -- .

# After push
git revert <commit-hash>
git push
```

---

## Validation Checklist

- [ ] **FR-001**: Browser tab displays "New App"
- [ ] **FR-002**: Application headers show "New App" (login + authenticated)
- [ ] **FR-005**: No old title references in codebase search
- [ ] **FR-006**: Configuration files updated
- [ ] **FR-007**: Documentation updated
- [ ] **E2E**: Test assertions updated

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
