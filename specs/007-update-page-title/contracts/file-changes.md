# File Modification Contract: Update Page Title to "Front"

**Feature**: 007-update-page-title | **Date**: 2026-02-19  
**Purpose**: Define exact file changes required for title update

## Contract Overview

This contract specifies the precise modifications to frontend files to change the application title from "Agent Projects" to "Front". All changes are string literal replacements in presentation layer files and E2E test assertions.

---

## File: `frontend/index.html`

**Purpose**: HTML page title for browser tab display  
**Change Type**: String replacement in `<title>` element

### Required Change

**Line 7**: Replace title text

```diff
-    <title>Agent Projects</title>
+    <title>Front</title>
```

**Validation**:
- ✅ `<title>` element structure unchanged
- ✅ Only text content modified
- ✅ HTML validity maintained

---

## File: `frontend/src/App.tsx`

**Purpose**: React component with application headers  
**Change Type**: String replacement in 2 JSX `<h1>` elements

### Required Changes

**Change 1 — Line 72**: Replace login page header text

```diff
-        <h1>Agent Projects</h1>
+        <h1>Front</h1>
```

**Context**: Inside the `!isAuthenticated` condition (login view)

**Change 2 — Line 89**: Replace authenticated header text

```diff
-          <h1>Agent Projects</h1>
+          <h1>Front</h1>
```

**Context**: Inside the main app header (authenticated view)

**Validation**:
- ✅ JSX element structure unchanged (`<h1>` tags preserved)
- ✅ Only text content modified
- ✅ Subtitle text ("Manage your GitHub Projects with natural language") unchanged
- ✅ TypeScript/React syntax valid

---

## File: `frontend/e2e/auth.spec.ts`

**Purpose**: E2E tests for authentication flow  
**Change Type**: String replacement in 5 test assertions

### Required Changes

**Change 1 — Line 12**:
```diff
-    await expect(page.locator('h1')).toContainText('Agent Projects');
+    await expect(page.locator('h1')).toContainText('Front');
```

**Change 2 — Line 24**:
```diff
-    await expect(page.locator('h1')).toContainText('Agent Projects', { timeout: 5000 });
+    await expect(page.locator('h1')).toContainText('Front', { timeout: 5000 });
```

**Change 3 — Line 38**:
```diff
-    await expect(page.locator('h1')).toContainText('Agent Projects');
+    await expect(page.locator('h1')).toContainText('Front');
```

**Change 4 — Line 62**:
```diff
-    await expect(page).toHaveTitle(/Agent Projects/i);
+    await expect(page).toHaveTitle(/Front/i);
```

**Change 5 — Line 99**:
```diff
-    await expect(page.locator('h1')).toContainText('Agent Projects');
+    await expect(page.locator('h1')).toContainText('Front');
```

---

## File: `frontend/e2e/ui.spec.ts`

**Purpose**: E2E tests for UI components and layout  
**Change Type**: String replacement in 2 test assertions

### Required Changes

**Change 1 — Line 43**:
```diff
-    await expect(page.locator('h1')).toContainText('Agent Projects');
+    await expect(page.locator('h1')).toContainText('Front');
```

**Change 2 — Line 67**:
```diff
-    await expect(page.locator('h1')).toContainText('Agent Projects');
+    await expect(page.locator('h1')).toContainText('Front');
```

---

## File: `frontend/e2e/integration.spec.ts`

**Purpose**: E2E tests for application integration  
**Change Type**: String replacement in 1 test assertion

### Required Change

**Change 1 — Line 69**:
```diff
-    await expect(page.locator('h1')).toContainText('Agent Projects');
+    await expect(page.locator('h1')).toContainText('Front');
```

---

## Files NOT Modified

The following files are explicitly **NOT** included in this change per spec scope:

### Frontend Files (No Changes)
- `frontend/package.json` — Internal package name unchanged
- `frontend/src/**/*.css` — No style changes
- `frontend/src/**/*.tsx` (other than App.tsx) — No other components affected
- `frontend/src/services/api.ts` — JSDoc comment only, not user-facing
- `frontend/src/types/index.ts` — JSDoc comment only, not user-facing

### Backend Files (No Changes)
- `backend/src/main.py` — API title/description (developer-facing)
- `backend/pyproject.toml` — Package description (developer-facing)
- `backend/tests/test_api_e2e.py` — Test docstring (developer-facing)
- `backend/README.md` — Documentation (developer-facing)

### Documentation (No Changes)
- `README.md` — Out of scope per spec assumptions
- `.devcontainer/devcontainer.json` — Development environment
- `.devcontainer/post-create.sh` — Development setup script
- `.env.example` — Configuration template
- `docker-compose.yml` — Service names unchanged

---

## Verification Contract

After implementing changes, verify the following:

### Browser Tab Title (FR-001)
- [ ] Open application in browser
- [ ] Observe browser tab displays "Front"

### Application Headers (FR-002)
- [ ] Load application (unauthenticated) — header displays "Front"
- [ ] Authenticate (login) — main header displays "Front"

### Consistency (FR-003, FR-005)
- [ ] Search codebase for `"Agent Projects"` in user-facing frontend code
- [ ] Verify 0 matches in `frontend/index.html`, `frontend/src/App.tsx`, `frontend/e2e/`

### No Regressions (FR-004)
- [ ] Page layout unchanged
- [ ] E2E test assertions pass with new title

---

## Contract Compliance Checklist

- [x] All file paths are verified to exist
- [x] Line numbers documented for reference
- [x] Exact string replacements specified
- [x] Before/after states documented
- [x] Validation criteria defined
- [x] Out-of-scope files explicitly listed
- [x] Verification procedure defined

**Status**: ✅ **CONTRACT COMPLETE** — Ready for implementation
