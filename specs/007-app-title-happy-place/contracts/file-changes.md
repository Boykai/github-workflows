# File Modification Contract: Update App Title to "Happy Place"

**Feature**: 007-app-title-happy-place | **Date**: 2026-02-20  
**Purpose**: Define exact file changes required for title update from "Agent Projects" to "Happy Place"

## Contract Overview

This contract specifies the precise modifications across frontend, backend, configuration, documentation, and test files to change the application title from "Agent Projects" to "Happy Place". All changes are string literal replacements.

---

## Frontend Changes

### File: `frontend/index.html`

**Purpose**: HTML page title for browser tab display  
**Change Type**: String replacement in `<title>` element

```diff
-    <title>Agent Projects</title>
+    <title>Happy Place</title>
```

---

### File: `frontend/src/App.tsx`

**Purpose**: React component with application headers  
**Change Type**: String replacement in 2 JSX `<h1>` elements

**Change 1 — Login page header (line 72)**:
```diff
-        <h1>Agent Projects</h1>
+        <h1>Happy Place</h1>
```

**Change 2 — Authenticated header (line 89)**:
```diff
-          <h1>Agent Projects</h1>
+          <h1>Happy Place</h1>
```

---

### File: `frontend/src/services/api.ts`

**Purpose**: API client service JSDoc  
**Change Type**: String replacement in comment

```diff
- * API client service for Agent Projects.
+ * API client service for Happy Place.
```

---

### File: `frontend/src/types/index.ts`

**Purpose**: TypeScript types JSDoc  
**Change Type**: String replacement in comment

```diff
- * TypeScript types for Agent Projects API.
+ * TypeScript types for Happy Place API.
```

---

## Backend Changes

### File: `backend/src/main.py`

**Purpose**: FastAPI application configuration and logging  
**Change Type**: String replacements in 4 locations

**Change 1 — Startup log (line 75)**:
```diff
-    logger.info("Starting Agent Projects API")
+    logger.info("Starting Happy Place API")
```

**Change 2 — Shutdown log (line 77)**:
```diff
-    logger.info("Shutting down Agent Projects API")
+    logger.info("Shutting down Happy Place API")
```

**Change 3 — FastAPI title (line 85)**:
```diff
-        title="Agent Projects API",
+        title="Happy Place API",
```

**Change 4 — FastAPI description (line 86)**:
```diff
-        description="REST API for Agent Projects",
+        description="REST API for Happy Place",
```

---

### File: `backend/README.md`

**Purpose**: Backend documentation  
**Change Type**: String replacements in heading and body

```diff
-# Agent Projects — Backend
+# Happy Place — Backend

-FastAPI backend that powers Agent Projects and the **Spec Kit agent pipeline**.
+FastAPI backend that powers Happy Place and the **Spec Kit agent pipeline**.
```

---

### File: `backend/pyproject.toml`

**Purpose**: Python package metadata  
**Change Type**: String replacement in description

```diff
-description = "FastAPI backend for Agent Projects"
+description = "FastAPI backend for Happy Place"
```

---

### File: `backend/tests/test_api_e2e.py`

**Purpose**: Backend E2E test docstring  
**Change Type**: String replacement in docstring

```diff
-End-to-end API tests for the Agent Projects Backend.
+End-to-end API tests for the Happy Place Backend.
```

---

## Configuration Changes

### File: `.devcontainer/devcontainer.json`

**Purpose**: Dev container display name  
**Change Type**: String replacement in name field

```diff
-  "name": "Agent Projects",
+  "name": "Happy Place",
```

---

### File: `.devcontainer/post-create.sh`

**Purpose**: Dev container setup message  
**Change Type**: String replacement in echo

```diff
-echo "🚀 Setting up Agent Projects development environment..."
+echo "🚀 Setting up Happy Place development environment..."
```

---

### File: `.env.example`

**Purpose**: Environment configuration comment  
**Change Type**: String replacement in comment

```diff
-# Agent Projects - Environment Configuration
+# Happy Place - Environment Configuration
```

---

## Documentation Changes

### File: `README.md`

**Purpose**: Project root documentation  
**Change Type**: String replacement in heading

```diff
-# Agent Projects
+# Happy Place
```

---

## E2E Test Changes

### File: `frontend/e2e/auth.spec.ts`

**Purpose**: Authentication E2E test assertions  
**Change Type**: 5 assertion string replacements

```diff
-    await expect(page.locator('h1')).toContainText('Agent Projects');
+    await expect(page.locator('h1')).toContainText('Happy Place');
```
(repeated at lines 12, 24, 38, 99)

```diff
-    await expect(page).toHaveTitle(/Agent Projects/i);
+    await expect(page).toHaveTitle(/Happy Place/i);
```
(at line 62)

---

### File: `frontend/e2e/ui.spec.ts`

**Purpose**: UI E2E test assertions  
**Change Type**: 2 assertion string replacements

```diff
-    await expect(page.locator('h1')).toContainText('Agent Projects');
+    await expect(page.locator('h1')).toContainText('Happy Place');
```
(at lines 43, 67)

---

### File: `frontend/e2e/integration.spec.ts`

**Purpose**: Integration E2E test assertions  
**Change Type**: 1 assertion string replacement

```diff
-    await expect(page.locator('h1')).toContainText('Agent Projects');
+    await expect(page.locator('h1')).toContainText('Happy Place');
```
(at line 69)

---

## Files NOT Modified

The following files are explicitly **NOT** included:

- `frontend/package.json` — Internal package name, not user-facing title
- `frontend/src/**/*.css` — No style changes
- `docker-compose.yml` — Service names are infrastructure identifiers
- `scripts/` — Internal tooling scripts

---

## Verification Contract

After implementing changes, verify the following:

### Browser Tab Title (FR-001)
- [ ] Browser tab displays "Happy Place"

### Application Headers (FR-002)
- [ ] Login page header displays "Happy Place"
- [ ] Authenticated header displays "Happy Place"

### Metadata (FR-003)
- [ ] FastAPI docs show "Happy Place API" as title
- [ ] FastAPI docs show "REST API for Happy Place" as description

### Developer Config (FR-004)
- [ ] Dev container named "Happy Place"
- [ ] README heading reads "Happy Place"

### Consistency (FR-005, FR-006)
- [ ] `grep -r "Agent Projects"` returns zero matches in codebase (excluding specs/)

### Tests (FR-007)
- [ ] All E2E test assertions updated to expect "Happy Place"

---

## Contract Compliance Checklist

- [x] All file paths verified to exist
- [x] Exact string replacements specified with diffs
- [x] Before/after states documented
- [x] Out-of-scope files explicitly listed
- [x] Verification criteria defined

**Status**: ✅ **CONTRACT COMPLETE** - Ready for implementation
