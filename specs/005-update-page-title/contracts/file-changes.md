# File Modification Contract: Update Page Title to "Objects"

**Feature**: 005-update-page-title | **Date**: 2026-02-19  
**Purpose**: Define exact file changes required for title update

## Contract Overview

This contract specifies the precise modifications to update the application title from "Agent Projects" to "Objects". All changes are string literal replacements across frontend, backend, configuration, documentation, and test files.

---

## File: `frontend/index.html`

**Purpose**: HTML page title for browser tab display  
**Change Type**: String replacement in `<title>` element

### Required Change

**Line 7**: Replace title text

```diff
-    <title>Agent Projects</title>
+    <title>Objects</title>
```

---

## File: `frontend/src/App.tsx`

**Purpose**: React component with application headers  
**Change Type**: String replacement in 2 JSX `<h1>` elements

### Required Changes

**Change 1 — Line 72**: Replace login page header text

```diff
-        <h1>Agent Projects</h1>
+        <h1>Objects</h1>
```

**Change 2 — Line 89**: Replace authenticated header text

```diff
-          <h1>Agent Projects</h1>
+          <h1>Objects</h1>
```

---

## File: `backend/src/main.py`

**Purpose**: FastAPI application configuration and logging  
**Change Type**: String replacements in 4 locations

### Required Changes

**Change 1 — Line 75**: Startup log message

```diff
-    logger.info("Starting Agent Projects API")
+    logger.info("Starting Objects API")
```

**Change 2 — Line 77**: Shutdown log message

```diff
-    logger.info("Shutting down Agent Projects API")
+    logger.info("Shutting down Objects API")
```

**Change 3 — Line 85**: FastAPI app title

```diff
-        title="Agent Projects API",
+        title="Objects API",
```

**Change 4 — Line 86**: FastAPI app description

```diff
-        description="REST API for Agent Projects",
+        description="REST API for Objects",
```

---

## File: `frontend/e2e/auth.spec.ts`

**Purpose**: End-to-end authentication tests  
**Change Type**: Update 5 test assertions

### Required Changes

Replace all occurrences:

```diff
-    await expect(page.locator('h1')).toContainText('Agent Projects');
+    await expect(page.locator('h1')).toContainText('Objects');
```

```diff
-    await expect(page).toHaveTitle(/Agent Projects/i);
+    await expect(page).toHaveTitle(/Objects/i);
```

---

## File: `frontend/e2e/ui.spec.ts`

**Purpose**: End-to-end UI tests  
**Change Type**: Update 2 test assertions

### Required Changes

Replace all occurrences:

```diff
-    await expect(page.locator('h1')).toContainText('Agent Projects');
+    await expect(page.locator('h1')).toContainText('Objects');
```

---

## File: `frontend/e2e/integration.spec.ts`

**Purpose**: End-to-end integration tests  
**Change Type**: Update 1 test assertion

### Required Change

```diff
-    await expect(page.locator('h1')).toContainText('Agent Projects');
+    await expect(page.locator('h1')).toContainText('Objects');
```

---

## File: `frontend/src/services/api.ts`

**Purpose**: API client service  
**Change Type**: Comment update

```diff
- * API client service for Agent Projects.
+ * API client service for Objects.
```

---

## File: `frontend/src/types/index.ts`

**Purpose**: TypeScript type definitions  
**Change Type**: Comment update

```diff
- * TypeScript types for Agent Projects API.
+ * TypeScript types for Objects API.
```

---

## File: `backend/pyproject.toml`

**Purpose**: Python project configuration  
**Change Type**: String replacement

```diff
-description = "FastAPI backend for Agent Projects"
+description = "FastAPI backend for Objects"
```

---

## File: `backend/README.md`

**Purpose**: Backend documentation  
**Change Type**: String replacements in heading and description

```diff
-# Agent Projects — Backend
+# Objects — Backend
```

```diff
-FastAPI backend that powers Agent Projects and the **Spec Kit agent pipeline**.
+FastAPI backend that powers Objects and the **Spec Kit agent pipeline**.
```

---

## File: `backend/tests/test_api_e2e.py`

**Purpose**: Backend E2E test  
**Change Type**: Docstring update

```diff
-End-to-end API tests for the Agent Projects Backend.
+End-to-end API tests for the Objects Backend.
```

---

## File: `README.md`

**Purpose**: Repository documentation  
**Change Type**: String replacement in heading

```diff
-# Agent Projects
+# Objects
```

---

## File: `.devcontainer/devcontainer.json`

**Purpose**: Development container configuration  
**Change Type**: String replacement

```diff
-  "name": "Agent Projects",
+  "name": "Objects",
```

---

## File: `.devcontainer/post-create.sh`

**Purpose**: Post-create setup script  
**Change Type**: String replacement

```diff
-echo "🚀 Setting up Agent Projects development environment..."
+echo "🚀 Setting up Objects development environment..."
```

---

## File: `.env.example`

**Purpose**: Environment configuration example  
**Change Type**: Comment update

```diff
-# Agent Projects - Environment Configuration
+# Objects - Environment Configuration
```

---

## Files NOT Modified

The following files are explicitly **NOT** included in this change:

- `frontend/package.json` — internal package name unchanged
- `frontend/src/**/*.css` — no style changes
- `docker-compose.yml` — service names unchanged
- `specs/005-update-page-title/spec.md` — references "Agent Projects" as current title (historical context)

---

## Verification Contract

After implementing changes, verify:

### Browser Tab Title (FR-001)
- [ ] Browser tab displays "Objects"

### Application Headers (FR-002)
- [ ] Login page header displays "Objects"
- [ ] Authenticated header displays "Objects"

### Consistency (FR-003, FR-004)
- [ ] No other titles/labels unintentionally affected
- [ ] Navigation elements display "Objects" where applicable

### Backend (FR-007)
- [ ] FastAPI docs at `/docs` show title "Objects API"
- [ ] Startup logs show "Starting Objects API"

### Tests (FR-006)
- [ ] All E2E tests pass with updated assertions
- [ ] No remaining "Agent Projects" assertions

### Codebase Search
- [ ] `grep -r "Agent Projects" .` returns only spec files (historical references)

---

## Contract Compliance Checklist

- [x] All file paths verified to exist
- [x] Exact string replacements specified
- [x] Before/after states documented
- [x] Validation criteria defined
- [x] Out-of-scope files explicitly listed
- [x] Verification procedures defined

**Status**: ✅ **CONTRACT COMPLETE** — Ready for implementation
