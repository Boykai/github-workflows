# Quickstart Guide: Update App Name to "Robot"

**Feature**: 007-update-app-name | **Date**: 2026-02-19  
**Estimated Time**: 10–15 minutes  
**Prerequisites**: Git access, text editor

## Overview

This guide walks through renaming the application display name from "Agent Projects" to "Robot" across all user-facing surfaces. The implementation involves string replacements in ~12 files spanning frontend, backend, configuration, documentation, and tests.

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

### 1.2 Verify Current Name

```bash
# Search for all occurrences of old name
grep -rn "Agent Projects" \
  frontend/index.html \
  frontend/src/App.tsx \
  backend/src/main.py \
  backend/pyproject.toml \
  backend/README.md \
  .devcontainer/devcontainer.json \
  .devcontainer/post-create.sh \
  .env.example \
  README.md \
  frontend/e2e/
```

**Expected**: ~15+ matches across these files. If you see matches, proceed to Step 2.

---

## Step 2: Update Frontend — Browser Tab Title

**Purpose**: Change browser tab title (FR-001)

### 2.1 Edit `frontend/index.html`

**Line 7**: Replace title text

```diff
-    <title>Agent Projects</title>
+    <title>Robot</title>
```

### 2.2 Verify

```bash
grep "<title>" frontend/index.html
```

**Expected**: `<title>Robot</title>`

---

## Step 3: Update Frontend — Application Headers

**Purpose**: Change application UI headers (FR-002)

### 3.1 Edit `frontend/src/App.tsx`

**Line 72** (login page header):
```diff
-        <h1>Agent Projects</h1>
+        <h1>Robot</h1>
```

**Line 89** (authenticated app header):
```diff
-          <h1>Agent Projects</h1>
+          <h1>Robot</h1>
```

### 3.2 Verify

```bash
grep -n "Robot" frontend/src/App.tsx
```

**Expected**: 2 matches showing `<h1>Robot</h1>`

---

## Step 4: Update Backend — FastAPI Metadata and Logs

**Purpose**: Change API title, description, and startup/shutdown logs (FR-003, FR-004)

### 4.1 Edit `backend/src/main.py`

**Line 75** (startup log):
```diff
-    logger.info("Starting Agent Projects API")
+    logger.info("Starting Robot API")
```

**Line 77** (shutdown log):
```diff
-    logger.info("Shutting down Agent Projects API")
+    logger.info("Shutting down Robot API")
```

**Line 85** (FastAPI title):
```diff
-        title="Agent Projects API",
+        title="Robot API",
```

**Line 86** (FastAPI description):
```diff
-        description="REST API for Agent Projects",
+        description="REST API for Robot",
```

### 4.2 Verify

```bash
grep -n "Robot" backend/src/main.py
```

**Expected**: 4 matches

---

## Step 5: Update Configuration Files

**Purpose**: Update project metadata and dev environment (FR-005, FR-006)

### 5.1 Edit `.devcontainer/devcontainer.json`

**Line 2**:
```diff
-  "name": "Agent Projects",
+  "name": "Robot",
```

### 5.2 Edit `.devcontainer/post-create.sh`

**Line 7**:
```diff
-echo "🚀 Setting up Agent Projects development environment..."
+echo "🚀 Setting up Robot development environment..."
```

### 5.3 Edit `.env.example`

**Line 2**:
```diff
-# Agent Projects - Environment Configuration
+# Robot - Environment Configuration
```

### 5.4 Edit `backend/pyproject.toml`

**Line 4** (description only — do NOT change `name` field):
```diff
-description = "FastAPI backend for Agent Projects"
+description = "FastAPI backend for Robot"
```

---

## Step 6: Update Documentation

**Purpose**: Update README files (FR-007)

### 6.1 Edit `README.md`

**Line 1**:
```diff
-# Agent Projects
+# Robot
```

### 6.2 Edit `backend/README.md`

**Line 1**:
```diff
-# Agent Projects — Backend
+# Robot — Backend
```

**Line 3**:
```diff
-FastAPI backend that powers Agent Projects and the **Spec Kit agent pipeline**.
+FastAPI backend that powers Robot and the **Spec Kit agent pipeline**.
```

---

## Step 7: Update E2E Test Assertions

**Purpose**: Ensure all test assertions expect "Robot" (FR-008)

### 7.1 Edit `frontend/e2e/auth.spec.ts`

Replace all `'Agent Projects'` with `'Robot'` in h1 assertions (lines 12, 24, 38, 99):
```diff
-    await expect(page.locator('h1')).toContainText('Agent Projects');
+    await expect(page.locator('h1')).toContainText('Robot');
```

Replace page title assertion (line 62):
```diff
-    await expect(page).toHaveTitle(/Agent Projects/i);
+    await expect(page).toHaveTitle(/Robot/i);
```

### 7.2 Edit `frontend/e2e/ui.spec.ts`

Replace h1 assertions (lines 43, 67):
```diff
-    await expect(page.locator('h1')).toContainText('Agent Projects');
+    await expect(page.locator('h1')).toContainText('Robot');
```

### 7.3 Edit `frontend/e2e/integration.spec.ts`

Replace h1 assertion (line 69):
```diff
-    await expect(page.locator('h1')).toContainText('Agent Projects');
+    await expect(page.locator('h1')).toContainText('Robot');
```

---

## Step 8: Final Verification

**Purpose**: Confirm no old references remain (FR-009)

### 8.1 Search for Old Name

```bash
cd /home/runner/work/github-workflows/github-workflows
grep -rn "Agent Projects" \
  --include="*.html" --include="*.tsx" --include="*.ts" \
  --include="*.py" --include="*.json" --include="*.toml" \
  --include="*.sh" --include="*.md" \
  . | grep -v "specs/" | grep -v "node_modules/" | grep -v ".git/"
```

**Expected**: Zero matches outside of spec documentation files.

### 8.2 Confirm New Name Present

```bash
grep -rn "Robot" \
  frontend/index.html frontend/src/App.tsx \
  backend/src/main.py .devcontainer/devcontainer.json \
  README.md backend/README.md
```

**Expected**: Multiple matches showing "Robot" in all key locations.

---

## Troubleshooting

### Issue: Old Name Still Appears in Grep

**Solution**: Check that all files in the contract were updated. Common misses: `.devcontainer/post-create.sh`, `.env.example`, `backend/pyproject.toml`.

### Issue: E2E Tests Still Fail

**Solution**: Verify all 8 assertion lines across the 3 test files were updated. The page title assertion in `auth.spec.ts` uses a regex, not a string.

### Issue: Backend Won't Start

**Solution**: Ensure only string literals were changed in `main.py`. Verify Python syntax with `python -c "import ast; ast.parse(open('backend/src/main.py').read())"`.

---

## Validation Checklist

- [ ] **FR-001**: Browser tab displays "Robot"
- [ ] **FR-002**: Login + authenticated headers display "Robot"
- [ ] **FR-003**: Backend startup log says "Starting Robot API"
- [ ] **FR-004**: API docs title displays "Robot API"
- [ ] **FR-005**: pyproject.toml description and .env.example updated
- [ ] **FR-006**: Devcontainer name and post-create.sh updated
- [ ] **FR-007**: README.md and backend/README.md updated
- [ ] **FR-008**: All 8 E2E test assertions updated
- [ ] **FR-009**: Zero "Agent Projects" matches in codebase (excluding specs/)

---

## Phase 1 Quickstart Completion Checklist

- [x] Step-by-step instructions provided (8 steps)
- [x] Prerequisites documented
- [x] Time estimate included (10–15 minutes)
- [x] Commands are copy-pasteable
- [x] Expected outputs documented
- [x] Troubleshooting section included
- [x] Validation checklist aligned with spec

**Status**: ✅ **QUICKSTART COMPLETE** — Ready for implementation by speckit.tasks
