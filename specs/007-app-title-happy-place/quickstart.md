# Quickstart Guide: Update App Title to "Happy Place"

**Feature**: 007-app-title-happy-place | **Date**: 2026-02-20  
**Estimated Time**: 10-15 minutes  
**Prerequisites**: Git access, text editor

## Overview

This guide walks through implementing the app title change from "Agent Projects" to "Happy Place" across all locations in the codebase: frontend, backend, configuration, documentation, and tests.

**Complexity**: ⭐ Trivial (1/5)  
**Risk Level**: Minimal  
**Rollback**: Instant (single git revert)

---

## Step 1: Verify Current State

**Purpose**: Confirm you're working with expected baseline

```bash
cd /home/runner/work/github-workflows/github-workflows

# Verify current title across all files
grep -rn "Agent Projects" frontend/index.html frontend/src/App.tsx backend/src/main.py README.md
```

**Expected**: Multiple matches showing "Agent Projects" in each file.

---

## Step 2: Update Frontend Files

### 2.1 HTML Page Title (`frontend/index.html`)

Replace line 7:
```diff
-    <title>Agent Projects</title>
+    <title>Happy Place</title>
```

### 2.2 React Headers (`frontend/src/App.tsx`)

Replace line 72 (login header):
```diff
-        <h1>Agent Projects</h1>
+        <h1>Happy Place</h1>
```

Replace line 89 (authenticated header):
```diff
-          <h1>Agent Projects</h1>
+          <h1>Happy Place</h1>
```

### 2.3 JSDoc Comments

In `frontend/src/services/api.ts`:
```diff
- * API client service for Agent Projects.
+ * API client service for Happy Place.
```

In `frontend/src/types/index.ts`:
```diff
- * TypeScript types for Agent Projects API.
+ * TypeScript types for Happy Place API.
```

---

## Step 3: Update Backend Files

### 3.1 FastAPI Configuration (`backend/src/main.py`)

Replace 4 occurrences of "Agent Projects":
- `"Starting Agent Projects API"` → `"Starting Happy Place API"`
- `"Shutting down Agent Projects API"` → `"Shutting down Happy Place API"`
- `title="Agent Projects API"` → `title="Happy Place API"`
- `description="REST API for Agent Projects"` → `description="REST API for Happy Place"`

### 3.2 Backend Documentation

In `backend/README.md`:
- `# Agent Projects — Backend` → `# Happy Place — Backend`
- `powers Agent Projects` → `powers Happy Place`

In `backend/pyproject.toml`:
- `"FastAPI backend for Agent Projects"` → `"FastAPI backend for Happy Place"`

In `backend/tests/test_api_e2e.py`:
- `"Agent Projects Backend"` → `"Happy Place Backend"`

---

## Step 4: Update Configuration Files

### 4.1 Dev Container (`.devcontainer/devcontainer.json`)
```diff
-  "name": "Agent Projects",
+  "name": "Happy Place",
```

### 4.2 Post-Create Script (`.devcontainer/post-create.sh`)
```diff
-echo "🚀 Setting up Agent Projects development environment..."
+echo "🚀 Setting up Happy Place development environment..."
```

### 4.3 Environment Example (`.env.example`)
```diff
-# Agent Projects - Environment Configuration
+# Happy Place - Environment Configuration
```

---

## Step 5: Update Root Documentation

### 5.1 README (`README.md`)
```diff
-# Agent Projects
+# Happy Place
```

---

## Step 6: Update E2E Test Assertions

### 6.1 Auth Tests (`frontend/e2e/auth.spec.ts`)
Replace all `'Agent Projects'` with `'Happy Place'` in `toContainText()` and `toHaveTitle()` calls.

### 6.2 UI Tests (`frontend/e2e/ui.spec.ts`)
Replace all `'Agent Projects'` with `'Happy Place'` in `toContainText()` calls.

### 6.3 Integration Tests (`frontend/e2e/integration.spec.ts`)
Replace `'Agent Projects'` with `'Happy Place'` in `toContainText()` call.

---

## Step 7: Verify No Old References Remain

```bash
grep -rn "Agent Projects" --include="*.ts" --include="*.tsx" --include="*.py" --include="*.html" --include="*.json" --include="*.toml" --include="*.sh" --include="*.md" . | grep -v specs/ | grep -v node_modules/ | grep -v .git/
```

**Expected**: Zero matches.

---

## Step 8: Manual Verification

### 8.1 Start Development Server

```bash
cd frontend && npm run dev
```

### 8.2 Verify in Browser

- Browser tab displays "Happy Place"
- Login page header shows "Happy Place"

### 8.3 Check Backend API Docs

```bash
cd backend && python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```

Navigate to http://localhost:8000/docs — title should show "Happy Place API"

---

## Troubleshooting

### Issue: Old Title Still Visible
**Solution**: Hard refresh (`Ctrl+Shift+R`), clear browser cache, or restart dev server.

### Issue: E2E Tests Fail
**Solution**: Verify all `toContainText('Agent Projects')` assertions updated to `'Happy Place'`.

### Issue: Backend Fails to Start
**Solution**: Verify Python string syntax is correct in `main.py` — check for unclosed quotes.

---

## Validation Checklist

- [ ] **FR-001**: Browser tab displays "Happy Place"
- [ ] **FR-002**: Application headers show "Happy Place" (login + authenticated)
- [ ] **FR-003**: Backend API metadata shows "Happy Place API"
- [ ] **FR-004**: Dev config and docs use "Happy Place"
- [ ] **FR-005**: Casing is exactly "Happy Place" everywhere
- [ ] **FR-006**: Zero old title references remain
- [ ] **FR-007**: All E2E test assertions updated

---

## Phase 1 Quickstart Completion Checklist

- [x] Step-by-step instructions provided (8 steps)
- [x] Prerequisites documented
- [x] Time estimate included (10-15 minutes)
- [x] Commands are copy-pasteable
- [x] Expected outputs documented
- [x] Troubleshooting section included
- [x] Validation checklist aligned with spec

**Status**: ✅ **QUICKSTART COMPLETE** - Ready for implementation by speckit.tasks
