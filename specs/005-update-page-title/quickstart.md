# Quickstart Guide: Update Page Title to "Objects"

**Feature**: 005-update-page-title | **Date**: 2026-02-19  
**Estimated Time**: 10-15 minutes  
**Prerequisites**: Git access, text editor

## Overview

This guide walks through implementing the app title change from "Agent Projects" to "Objects". The implementation involves string replacements across ~15 files spanning frontend, backend, tests, configuration, and documentation.

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

**Expected**: On a feature branch for this change

### 1.2 Verify Current Title

```bash
# Check all occurrences
grep -rn "Agent Projects" frontend/index.html frontend/src/App.tsx backend/src/main.py
```

**Expected Output**:
```
frontend/index.html:7:    <title>Agent Projects</title>
frontend/src/App.tsx:72:        <h1>Agent Projects</h1>
frontend/src/App.tsx:89:          <h1>Agent Projects</h1>
backend/src/main.py:75:    logger.info("Starting Agent Projects API")
backend/src/main.py:77:    logger.info("Shutting down Agent Projects API")
backend/src/main.py:85:        title="Agent Projects API",
backend/src/main.py:86:        description="REST API for Agent Projects",
```

If you see these matches, proceed to Step 2.

---

## Step 2: Update Frontend Files

**Purpose**: Change browser tab title and React component headers

### 2.1 Update `frontend/index.html`

Replace the `<title>` element content on line 7:
```diff
-    <title>Agent Projects</title>
+    <title>Objects</title>
```

### 2.2 Update `frontend/src/App.tsx`

Replace both `<h1>` headings:
- Line 72 (login page): `Agent Projects` → `Objects`
- Line 89 (authenticated view): `Agent Projects` → `Objects`

### 2.3 Verify Frontend Changes

```bash
grep -n "Objects" frontend/index.html frontend/src/App.tsx
```

**Expected**: 3 matches (1 in index.html, 2 in App.tsx)

---

## Step 3: Update Backend Files

**Purpose**: Change FastAPI configuration and log messages

### 3.1 Update `backend/src/main.py`

Replace 4 occurrences:
- Line 75: `"Starting Agent Projects API"` → `"Starting Objects API"`
- Line 77: `"Shutting down Agent Projects API"` → `"Shutting down Objects API"`
- Line 85: `title="Agent Projects API"` → `title="Objects API"`
- Line 86: `description="REST API for Agent Projects"` → `description="REST API for Objects"`

### 3.2 Update `backend/pyproject.toml`

Line 4:
```diff
-description = "FastAPI backend for Agent Projects"
+description = "FastAPI backend for Objects"
```

### 3.3 Update `backend/tests/test_api_e2e.py`

Line 2:
```diff
-End-to-end API tests for the Agent Projects Backend.
+End-to-end API tests for the Objects Backend.
```

### 3.4 Update `backend/README.md`

Line 1 and 3: Replace "Agent Projects" with "Objects"

---

## Step 4: Update E2E Test Assertions

**Purpose**: Ensure tests expect the new title (FR-006)

### 4.1 Update `frontend/e2e/auth.spec.ts`

Replace all 5 occurrences of `'Agent Projects'` with `'Objects'`:
- Lines 12, 24, 38, 99: `toContainText('Agent Projects')` → `toContainText('Objects')`
- Line 62: `toHaveTitle(/Agent Projects/i)` → `toHaveTitle(/Objects/i)`

### 4.2 Update `frontend/e2e/ui.spec.ts`

Replace 2 occurrences on lines 43 and 67.

### 4.3 Update `frontend/e2e/integration.spec.ts`

Replace 1 occurrence on line 69.

---

## Step 5: Update Configuration Files

**Purpose**: Maintain consistency across developer tooling

### 5.1 Update `.devcontainer/devcontainer.json`

Line 2:
```diff
-  "name": "Agent Projects",
+  "name": "Objects",
```

### 5.2 Update `.devcontainer/post-create.sh`

Line 7:
```diff
-echo "🚀 Setting up Agent Projects development environment..."
+echo "🚀 Setting up Objects development environment..."
```

### 5.3 Update `.env.example`

Line 2:
```diff
-# Agent Projects - Environment Configuration
+# Objects - Environment Configuration
```

### 5.4 Update `frontend/package.json`

```diff
-  "name": "agent-projects-frontend",
+  "name": "objects-frontend",
```

---

## Step 6: Update Documentation

### 6.1 Update `README.md`

Line 1:
```diff
-# Agent Projects
+# Objects
```

### 6.2 Update JSDoc Comments

- `frontend/src/services/api.ts` line 2: `Agent Projects` → `Objects`
- `frontend/src/types/index.ts` line 2: `Agent Projects` → `Objects`

---

## Step 7: Verify No Old References Remain

**Purpose**: Confirm complete replacement (FR-004)

```bash
grep -rn "Agent Projects" --include="*.ts" --include="*.tsx" --include="*.html" --include="*.py" --include="*.json" --include="*.toml" --include="*.md" --include="*.sh" --include="*.env*" . | grep -v "specs/" | grep -v "node_modules/"
```

**Expected**: No matches (only specs/ directory may still reference old title in historical context)

---

## Step 8: Manual Verification

**Purpose**: Confirm changes work in running application

### 8.1 Start Development Server

```bash
cd frontend
npm run dev
```

### 8.2 Verify in Browser

1. **Browser tab**: Displays "Objects"
2. **Login page**: Header shows "Objects"
3. **Authenticated view**: Header shows "Objects"

### 8.3 Stop Server

Press `Ctrl+C`

---

## Troubleshooting

### Issue: Old title still visible in browser
**Solution**: Hard refresh (`Ctrl+Shift+R`) or clear browser cache

### Issue: TypeScript compilation error
**Solution**: Ensure only text inside `<h1>` tags was changed, not JSX structure

### Issue: E2E tests fail
**Solution**: Verify all test assertion strings were updated from "Agent Projects" to "Objects"

---

## Rollback Procedure

```bash
git revert <commit-hash>
```

**Expected Rollback State**: All files return to "Agent Projects"

---

## Validation Checklist

- [ ] **FR-001**: Browser tab displays "Objects"
- [ ] **FR-002**: Application headers show "Objects" (login + authenticated)
- [ ] **FR-003**: All navigation elements display "Objects"
- [ ] **FR-004**: No other titles or labels affected
- [ ] **FR-005**: N/A (no i18n files exist)
- [ ] **FR-006**: All E2E test assertions updated
- [ ] **FR-007**: Backend FastAPI title reflects "Objects API"
- [ ] **SC-001**: Codebase search shows zero old title matches outside specs/

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
