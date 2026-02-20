# Quickstart Guide: Update App Title to "Happy Place"

**Feature**: 005-update-app-title | **Date**: 2026-02-20  
**Estimated Time**: 10-15 minutes  
**Prerequisites**: Git access, text editor

## Overview

This guide walks through implementing the app title change from "Agent Projects" to "Happy Place" across all locations in the codebase. The implementation involves ~25 string replacements in ~15 files.

**Complexity**: ⭐ Trivial (1/5)  
**Risk Level**: Minimal  
**Rollback**: Instant (single git revert)

---

## Step 1: Verify Current State

**Purpose**: Confirm you're working with expected baseline

### 1.1 Verify Current Title Locations

```bash
cd /home/runner/work/github-workflows/github-workflows
grep -rn "Agent Projects" --include="*.ts" --include="*.tsx" --include="*.html" \
  --include="*.py" --include="*.json" --include="*.md" --include="*.sh" \
  --include="*.toml" --include="*.cfg" . | grep -v node_modules | grep -v ".git/" | grep -v "specs/"
```

**Expected**: ~21-25 matches across 14 files. If you see this, proceed to Step 2.

---

## Step 2: Update Frontend User-Facing Files (P1)

**Purpose**: Change browser tab title and in-app headers

### 2.1 Edit `frontend/index.html` (line 7)

```html
<!-- Change from: -->
<title>Agent Projects</title>
<!-- Change to: -->
<title>Happy Place</title>
```

### 2.2 Edit `frontend/src/App.tsx` (lines 72 and 89)

```tsx
// Change both <h1> elements from:
<h1>Agent Projects</h1>
// Change to:
<h1>Happy Place</h1>
```

### 2.3 Verify

```bash
grep -n "Happy Place" frontend/index.html frontend/src/App.tsx
```

**Expected**: 3 matches (1 in index.html, 2 in App.tsx)

---

## Step 3: Update E2E Tests (P1)

**Purpose**: Fix test assertions to match new title (FR-006)

### 3.1 Edit `frontend/e2e/auth.spec.ts`

Replace all 5 occurrences:
```typescript
// Change all instances of:
await expect(page.locator('h1')).toContainText('Agent Projects');
// To:
await expect(page.locator('h1')).toContainText('Happy Place');

// Change the title assertion from:
await expect(page).toHaveTitle(/Agent Projects/i);
// To:
await expect(page).toHaveTitle(/Happy Place/i);
```

### 3.2 Edit `frontend/e2e/ui.spec.ts`

Replace 2 occurrences of `'Agent Projects'` with `'Happy Place'`.

### 3.3 Edit `frontend/e2e/integration.spec.ts`

Replace 1 occurrence of `'Agent Projects'` with `'Happy Place'`.

### 3.4 Verify

```bash
grep -c "Happy Place" frontend/e2e/auth.spec.ts frontend/e2e/ui.spec.ts frontend/e2e/integration.spec.ts
```

**Expected**: auth.spec.ts: 5, ui.spec.ts: 2, integration.spec.ts: 1

---

## Step 4: Update Backend API Metadata (P2)

**Purpose**: Update FastAPI OpenAPI docs and logger messages

### 4.1 Edit `backend/src/main.py`

```python
# Line 75 - Change:
logger.info("Starting Agent Projects API")
# To:
logger.info("Starting Happy Place API")

# Line 77 - Change:
logger.info("Shutting down Agent Projects API")
# To:
logger.info("Shutting down Happy Place API")

# Line 85 - Change:
title="Agent Projects API",
# To:
title="Happy Place API",

# Line 86 - Change:
description="REST API for Agent Projects",
# To:
description="REST API for Happy Place",
```

---

## Step 5: Update Configuration Files (P2)

**Purpose**: Update container name, setup script, and environment config

### 5.1 Edit `.devcontainer/devcontainer.json` (line 2)

```json
"name": "Happy Place",
```

### 5.2 Edit `.devcontainer/post-create.sh` (line 7)

```bash
echo "🚀 Setting up Happy Place development environment..."
```

### 5.3 Edit `.env.example` (line 2)

```bash
# Happy Place - Environment Configuration
```

### 5.4 Edit `backend/pyproject.toml` (line 4)

```toml
description = "FastAPI backend for Happy Place"
```

---

## Step 6: Update Documentation (P2)

### 6.1 Edit `README.md` (line 1)

```markdown
# Happy Place
```

### 6.2 Edit `backend/README.md` (lines 1 and 3)

```markdown
# Happy Place — Backend

FastAPI backend that powers Happy Place and the **Spec Kit agent pipeline**...
```

---

## Step 7: Update Code Comments (P2)

### 7.1 Edit `frontend/src/services/api.ts` (line 2)

```typescript
 * API client service for Happy Place.
```

### 7.2 Edit `frontend/src/types/index.ts` (line 2)

```typescript
 * TypeScript types for Happy Place API.
```

### 7.3 Edit `backend/tests/test_api_e2e.py` (line 2)

```python
End-to-end API tests for the Happy Place Backend.
```

---

## Step 8: Verify No Old References Remain

**Purpose**: Confirm complete replacement (FR-007)

```bash
grep -rn "Agent Projects" --include="*.ts" --include="*.tsx" --include="*.html" \
  --include="*.py" --include="*.json" --include="*.md" --include="*.sh" \
  --include="*.toml" --include="*.cfg" . | grep -v node_modules | grep -v ".git/" | grep -v "specs/"
```

**Expected**: Zero matches outside of spec files.

---

## Step 9: Manual Verification

### 9.1 Start Frontend Dev Server

```bash
cd frontend && npm run dev
```

### 9.2 Verify in Browser

- **Browser tab**: Displays "Happy Place"
- **Login page header**: Shows "Happy Place"
- **Authenticated header**: Shows "Happy Place" (after login)

### 9.3 Check Backend API Docs

```bash
cd backend && python -m uvicorn src.main:app
```

Navigate to `http://localhost:8000/docs` — title should show "Happy Place API"

---

## Troubleshooting

### Issue: Missed a Reference

**Symptom**: `grep` still finds "Agent Projects"  
**Solution**: Update the file shown in grep output. Use `sed -i 's/Agent Projects/Happy Place/g' <file>` for quick replacement.

### Issue: E2E Tests Fail

**Symptom**: Playwright tests fail on title assertion  
**Solution**: Verify all 8 assertions across 3 test files were updated. Check exact casing.

### Issue: TypeScript/Python Syntax Error

**Symptom**: Compilation or runtime error after edits  
**Solution**: Ensure only the string content was changed, not surrounding quotes or syntax.

---

## Rollback Procedure

```bash
# Before push:
git checkout -- .

# After push:
git revert <commit-hash>
git push
```

---

## Validation Checklist

- [ ] **FR-001**: Browser tab displays "Happy Place"
- [ ] **FR-002**: Header/navbar shows "Happy Place"
- [ ] **FR-003**: HTML `<title>` contains "Happy Place"
- [ ] **FR-006**: All E2E tests pass with updated assertions
- [ ] **FR-007**: No "Agent Projects" references remain (outside specs/)
- [ ] **FR-008**: Consistent "Happy Place" casing everywhere

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

**Status**: ✅ **QUICKSTART COMPLETE** - Ready for implementation by speckit.tasks
