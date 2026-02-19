# Quickstart Guide: Replace App Title with 'agentic'

**Feature**: 001-agentic-app-title | **Date**: 2026-02-19
**Estimated Time**: 10-15 minutes
**Prerequisites**: Git access, text editor

## Overview

This guide walks through implementing the app title change from "Agent Projects" to "agentic" (all lowercase). The implementation involves string replacements across ~10 files spanning frontend, backend, E2E tests, devcontainer configuration, and documentation.

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
# Check all instances of current title
grep -rn "Agent Projects" frontend/index.html frontend/src/App.tsx backend/src/main.py .devcontainer/ README.md backend/README.md backend/pyproject.toml
```

**Expected Output**: Multiple matches across listed files showing "Agent Projects" as the current title

---

## Step 2: Update Frontend HTML Title

**Purpose**: Change browser tab title (FR-001)

### 2.1 Edit `frontend/index.html`

**Line 7**: Replace title text

```diff
-    <title>Agent Projects</title>
+    <title>agentic</title>
```

### 2.2 Verify

```bash
grep "<title>" frontend/index.html
```

**Expected**: `<title>agentic</title>`

---

## Step 3: Update React Component Headers

**Purpose**: Change login and authenticated headers (FR-002, FR-003)

### 3.1 Edit `frontend/src/App.tsx`

**Line 72** (login page header):

```diff
-        <h1>Agent Projects</h1>
+        <h1>agentic</h1>
```

**Line 89** (authenticated header):

```diff
-          <h1>Agent Projects</h1>
+          <h1>agentic</h1>
```

### 3.2 Verify

```bash
grep -n "agentic" frontend/src/App.tsx
```

**Expected**: 2 matches showing `<h1>agentic</h1>`

---

## Step 4: Update E2E Test Assertions

**Purpose**: Update test expectations to match new title (FR-004)

### 4.1 Edit `frontend/e2e/auth.spec.ts`

Replace all instances of `'Agent Projects'` with `'agentic'` and `/Agent Projects/i` with `/agentic/i` on lines 12, 24, 38, 62, 99.

### 4.2 Edit `frontend/e2e/ui.spec.ts`

Replace `'Agent Projects'` with `'agentic'` on lines 43, 67.

### 4.3 Edit `frontend/e2e/integration.spec.ts`

Replace `'Agent Projects'` with `'agentic'` on line 69.

### 4.4 Verify

```bash
grep -rn "Agent Projects" frontend/e2e/
```

**Expected**: No matches (all replaced with "agentic")

---

## Step 5: Update Backend Metadata

**Purpose**: Update FastAPI service metadata and log messages (FR-006)

### 5.1 Edit `backend/src/main.py`

**Line 75** (startup log):

```diff
-    logger.info("Starting Agent Projects API")
+    logger.info("Starting agentic API")
```

**Line 77** (shutdown log):

```diff
-    logger.info("Shutting down Agent Projects API")
+    logger.info("Shutting down agentic API")
```

**Line 85** (FastAPI title):

```diff
-        title="Agent Projects API",
+        title="agentic API",
```

**Line 86** (FastAPI description):

```diff
-        description="REST API for Agent Projects",
+        description="REST API for agentic",
```

### 5.2 Verify

```bash
grep -n "agentic" backend/src/main.py
```

**Expected**: 4 matches

---

## Step 6: Update Developer Configuration

**Purpose**: Update devcontainer name and setup message (FR-005)

### 6.1 Edit `.devcontainer/devcontainer.json`

**Line 2**:

```diff
-  "name": "Agent Projects",
+  "name": "agentic",
```

### 6.2 Edit `.devcontainer/post-create.sh`

**Line 7**:

```diff
-echo "🚀 Setting up Agent Projects development environment..."
+echo "🚀 Setting up agentic development environment..."
```

---

## Step 7: Update Backend Package Metadata

**Purpose**: Update pyproject.toml name and description

### 7.1 Edit `backend/pyproject.toml`

**Line 2**:

```diff
-name = "agent-projects-backend"
+name = "agentic-backend"
```

**Line 4**:

```diff
-description = "FastAPI backend for Agent Projects"
+description = "FastAPI backend for agentic"
```

---

## Step 8: Update Documentation

**Purpose**: Update README files (FR-007)

### 8.1 Edit `README.md`

**Line 1**:

```diff
-# Agent Projects
+# agentic
```

### 8.2 Edit `backend/README.md`

**Line 1**:

```diff
-# Agent Projects — Backend
+# agentic — Backend
```

---

## Step 9: Final Verification

**Purpose**: Confirm complete replacement

### 9.1 Search for Old Title

```bash
grep -rn "Agent Projects" frontend/ backend/ .devcontainer/ README.md
```

**Expected**: No matches in source files (may still appear in spec artifacts under `specs/`)

### 9.2 Verify New Title

```bash
grep -rn "agentic" frontend/index.html frontend/src/App.tsx backend/src/main.py .devcontainer/ README.md backend/README.md backend/pyproject.toml
```

**Expected**: All locations show "agentic"

---

## Troubleshooting

### Issue: Can't Find Old Title Text

**Symptom**: `grep` returns no matches for "Agent Projects"
**Solution**: Title may already be updated. Check git log to see if changes exist.

### Issue: TypeScript Compilation Fails

**Symptom**: `tsc` fails after changes
**Solution**: Ensure only text inside `<h1>` tags was changed, not JSX structure.

### Issue: E2E Tests Still Fail

**Symptom**: Playwright tests fail on title assertion
**Solution**: Verify all assertion strings were updated (check lines 12, 24, 38, 62, 99 in auth.spec.ts).

### Issue: Backend Won't Start

**Symptom**: FastAPI fails to start after main.py changes
**Solution**: Verify Python string syntax — ensure quotes are balanced and no extra characters were introduced.

---

## Rollback Procedure

If issues arise, revert changes via:

```bash
git revert <commit-hash>
```

**Expected Rollback State**: All files return to "Agent Projects" title

---

## Validation Checklist

Before marking feature complete, verify:

- [ ] **FR-001**: Browser tab displays "agentic"
- [ ] **FR-002**: Login page heading displays "agentic"
- [ ] **FR-003**: App header heading displays "agentic"
- [ ] **FR-004**: All E2E test assertions updated to "agentic"
- [ ] **FR-005**: Devcontainer name and setup message reference "agentic"
- [ ] **FR-006**: Backend FastAPI title and description reference "agentic"
- [ ] **FR-007**: README files reference "agentic"
- [ ] **FR-008**: No styling changes — text-only replacement
- [ ] **SC-001**: All visible title instances show "agentic"
- [ ] **SC-002**: Existing test suites pass with updated assertions
- [ ] **SC-003**: No lingering "Agent Projects" references in source files

---

## Success Criteria

✅ **Feature Complete** when:
1. Browser tab shows "agentic"
2. Login page header shows "agentic"
3. Authenticated header shows "agentic"
4. All E2E test assertions use "agentic"
5. Backend metadata shows "agentic API"
6. Devcontainer and setup script reference "agentic"
7. READMEs reference "agentic"
8. No old title references remain in source files

**Total Time**: ~10-15 minutes for experienced developer

---

## Phase 1 Quickstart Completion Checklist

- [x] Step-by-step instructions provided (9 steps)
- [x] Prerequisites documented
- [x] Time estimate included (10-15 minutes)
- [x] Commands are copy-pasteable
- [x] Expected outputs documented
- [x] Troubleshooting section included
- [x] Rollback procedure defined
- [x] Validation checklist aligned with spec
- [x] Success criteria clearly stated

**Status**: ✅ **QUICKSTART COMPLETE** — Ready for implementation by speckit.tasks
