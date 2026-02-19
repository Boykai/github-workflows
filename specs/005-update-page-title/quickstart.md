# Quickstart Guide: Update Page Title to "Objects"

**Feature**: 005-update-page-title | **Branch**: `005-update-page-title`  
**Estimated Time**: 10–15 minutes  
**Prerequisites**: Git access, text editor

## Overview

This guide walks through implementing the app title change from "Agent Projects" to "Objects". The implementation involves string replacements across ~15 files spanning frontend, backend, configuration, documentation, and test assertions.

**Complexity**: ⭐ Trivial (1/5)  
**Risk Level**: Minimal  
**Rollback**: Instant (single git revert)

---

## Step 1: Verify Current State

**Purpose**: Confirm you're working with the expected baseline

### 1.1 Check Current Title Occurrences

```bash
cd /home/runner/work/github-workflows/github-workflows
grep -rn "Agent Projects" --include="*.html" --include="*.tsx" --include="*.ts" --include="*.py" --include="*.toml" --include="*.json" --include="*.md" --include="*.sh" --include="*.env*" . | grep -v node_modules | grep -v ".git/" | grep -v "specs/"
```

**Expected**: ~22 occurrences across ~15 files

---

## Step 2: Update Frontend User-Facing Files

**Purpose**: Change browser tab title and application headers (FR-001, FR-002)

### 2.1 Edit `frontend/index.html`

Replace line 7:
```diff
-    <title>Agent Projects</title>
+    <title>Objects</title>
```

### 2.2 Edit `frontend/src/App.tsx`

Replace line 72 (login header):
```diff
-        <h1>Agent Projects</h1>
+        <h1>Objects</h1>
```

Replace line 89 (authenticated header):
```diff
-          <h1>Agent Projects</h1>
+          <h1>Objects</h1>
```

### 2.3 Verify

```bash
grep -n "Objects" frontend/index.html frontend/src/App.tsx
```

**Expected**: 3 matches (1 in index.html, 2 in App.tsx)

---

## Step 3: Update Backend

**Purpose**: Change API metadata and log messages (FR-007)

### 3.1 Edit `backend/src/main.py`

Replace all 4 occurrences of "Agent Projects" with "Objects":
- Line 75: `"Starting Objects API"`
- Line 77: `"Shutting down Objects API"`
- Line 85: `title="Objects API"`
- Line 86: `description="REST API for Objects"`

### 3.2 Edit `backend/pyproject.toml`

```diff
-description = "FastAPI backend for Agent Projects"
+description = "FastAPI backend for Objects"
```

### 3.3 Edit `backend/README.md`

Replace "Agent Projects" with "Objects" in heading and description.

### 3.4 Edit `backend/tests/test_api_e2e.py`

Update docstring reference.

---

## Step 4: Update E2E Tests

**Purpose**: Fix test assertions to expect new title (FR-006)

### 4.1 Edit `frontend/e2e/auth.spec.ts`

Replace all 5 occurrences:
```diff
-'Agent Projects'
+'Objects'
```

### 4.2 Edit `frontend/e2e/ui.spec.ts`

Replace all 2 occurrences.

### 4.3 Edit `frontend/e2e/integration.spec.ts`

Replace 1 occurrence.

---

## Step 5: Update Configuration and Documentation

**Purpose**: Ensure consistency across all references (FR-003)

### 5.1 Files to Update

| File | Change |
|------|--------|
| `README.md` | Heading: "Agent Projects" → "Objects" |
| `.devcontainer/devcontainer.json` | Name: "Agent Projects" → "Objects" |
| `.devcontainer/post-create.sh` | Message: "Agent Projects" → "Objects" |
| `.env.example` | Comment: "Agent Projects" → "Objects" |
| `frontend/src/services/api.ts` | Comment: "Agent Projects" → "Objects" |
| `frontend/src/types/index.ts` | Comment: "Agent Projects" → "Objects" |

---

## Step 6: Verify No Old References Remain

**Purpose**: Confirm complete replacement

```bash
grep -rn "Agent Projects" . --include="*.html" --include="*.tsx" --include="*.ts" --include="*.py" --include="*.toml" --include="*.json" --include="*.md" --include="*.sh" --include="*.env*" | grep -v node_modules | grep -v ".git/" | grep -v "specs/"
```

**Expected**: No matches (only matches should be in `specs/` directories as historical references)

---

## Step 7: Manual Verification

**Purpose**: Confirm changes work in running application

### 7.1 Start Development Server

```bash
cd frontend && npm run dev
```

### 7.2 Verify in Browser

- [ ] Browser tab displays "Objects"
- [ ] Login page header shows "Objects"
- [ ] Authenticated header shows "Objects"

### 7.3 Check API Docs

```bash
cd backend && uvicorn src.main:app --reload --port 8000
```

Navigate to http://localhost:8000/docs — title should show "Objects API"

---

## Troubleshooting

### Issue: Old Title Still Visible in Browser

**Solution**: Hard refresh (`Ctrl+Shift+R`) or clear browser cache.

### Issue: E2E Tests Still Fail

**Solution**: Verify all 8 assertions are updated. Search: `grep -n "Agent Projects" frontend/e2e/*.spec.ts`

### Issue: Backend Fails to Start

**Solution**: Check `main.py` syntax — ensure quotes are balanced in string replacements.

---

## Validation Checklist

- [ ] **FR-001**: Browser tab displays "Objects"
- [ ] **FR-002**: Application headers show "Objects" (login + authenticated)
- [ ] **FR-003**: Navigation elements display "Objects"
- [ ] **FR-004**: No other titles/labels affected
- [ ] **FR-006**: All E2E tests pass
- [ ] **FR-007**: Backend API metadata shows "Objects API"
- [ ] **SC-001**: 100% of UI title locations show "Objects"
- [ ] **SC-002**: Zero "Agent Projects" references in rendered UI
- [ ] **SC-003**: All automated tests pass

---

## Phase 1 Quickstart Completion Checklist

- [x] Step-by-step instructions provided (7 steps)
- [x] Prerequisites documented
- [x] Time estimate included (10–15 minutes)
- [x] Commands are copy-pasteable
- [x] Expected outputs documented
- [x] Troubleshooting section included
- [x] Validation checklist aligned with spec

**Status**: ✅ **QUICKSTART COMPLETE** — Ready for implementation by speckit.tasks
