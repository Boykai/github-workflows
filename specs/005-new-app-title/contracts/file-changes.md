# File Modification Contract: Update App Title to "New App"

**Feature**: 005-new-app-title | **Date**: 2026-02-19  
**Purpose**: Define exact file changes required for title update

## Contract Overview

This contract specifies the precise modifications needed to change the application title from "Agent Projects" to "New App" across all relevant files. Two replacement patterns are used:
- `"Agent Projects API"` → `"New App API"` (backend API-specific references)
- `"Agent Projects"` → `"New App"` (all other locations)

---

## File: `frontend/index.html`

**Purpose**: HTML page title for browser tab display  
**Change Type**: String replacement in `<title>` element

### Required Change

**Line 7**: Replace title text

```diff
-    <title>Agent Projects</title>
+    <title>New App</title>
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

**Change 1 - Line 72**: Replace login page header text

```diff
-        <h1>Agent Projects</h1>
+        <h1>New App</h1>
```

**Change 2 - Line 89**: Replace authenticated header text

```diff
-          <h1>Agent Projects</h1>
+          <h1>New App</h1>
```

**Validation**:
- ✅ JSX element structure unchanged (`<h1>` tags preserved)
- ✅ Only text content modified
- ✅ TypeScript/React syntax valid

---

## File: `backend/src/main.py`

**Purpose**: FastAPI application configuration and lifecycle logging  
**Change Type**: String replacements in 4 locations

### Required Changes

**Change 1 - Line 75**: Replace startup log message

```diff
-    logger.info("Starting Agent Projects API")
+    logger.info("Starting New App API")
```

**Change 2 - Line 77**: Replace shutdown log message

```diff
-    logger.info("Shutting down Agent Projects API")
+    logger.info("Shutting down New App API")
```

**Change 3 - Line 85**: Replace FastAPI title

```diff
-        title="Agent Projects API",
+        title="New App API",
```

**Change 4 - Line 86**: Replace FastAPI description

```diff
-        description="REST API for Agent Projects",
+        description="REST API for New App",
```

**Validation**:
- ✅ Python syntax valid
- ✅ FastAPI configuration structure unchanged
- ✅ Logger calls unchanged except message text

---

## File: `backend/pyproject.toml`

**Purpose**: Python package metadata  
**Change Type**: String replacement in description field

### Required Change

**Line 4**: Replace package description

```diff
-description = "FastAPI backend for Agent Projects"
+description = "FastAPI backend for New App"
```

**Validation**:
- ✅ TOML syntax valid
- ✅ Package name (`agent-projects-backend`) intentionally unchanged (internal identifier)

---

## File: `backend/README.md`

**Purpose**: Backend documentation  
**Change Type**: String replacements in header and body text

### Required Changes

**Line 1**: Replace header

```diff
-# Agent Projects — Backend
+# New App — Backend
```

**Line 3**: Replace body reference

```diff
-FastAPI backend that powers Agent Projects and the **Spec Kit agent pipeline**.
+FastAPI backend that powers New App and the **Spec Kit agent pipeline**.
```

---

## File: `backend/tests/test_api_e2e.py`

**Purpose**: Backend E2E test file  
**Change Type**: String replacement in file header comment

### Required Change

**Line 2**: Replace comment

```diff
-End-to-end API tests for the Agent Projects Backend.
+End-to-end API tests for the New App Backend.
```

---

## File: `.devcontainer/devcontainer.json`

**Purpose**: VS Code dev container configuration  
**Change Type**: String replacement in name field

### Required Change

**Line 2**: Replace container name

```diff
-  "name": "Agent Projects",
+  "name": "New App",
```

---

## File: `.devcontainer/post-create.sh`

**Purpose**: Dev container post-create setup script  
**Change Type**: String replacement in echo message

### Required Change

**Line 7**: Replace setup message

```diff
-echo "🚀 Setting up Agent Projects development environment..."
+echo "🚀 Setting up New App development environment..."
```

---

## File: `frontend/e2e/auth.spec.ts`

**Purpose**: Authentication E2E tests  
**Change Type**: String replacements in 5 test assertions

### Required Changes

**Lines 12, 24, 38, 99**: Replace heading assertions

```diff
-    await expect(page.locator('h1')).toContainText('Agent Projects');
+    await expect(page.locator('h1')).toContainText('New App');
```

**Line 62**: Replace title assertion

```diff
-    await expect(page).toHaveTitle(/Agent Projects/i);
+    await expect(page).toHaveTitle(/New App/i);
```

---

## File: `frontend/e2e/ui.spec.ts`

**Purpose**: UI E2E tests  
**Change Type**: String replacements in 2 test assertions

### Required Changes

**Lines 43, 67**: Replace heading assertions

```diff
-    await expect(page.locator('h1')).toContainText('Agent Projects');
+    await expect(page.locator('h1')).toContainText('New App');
```

---

## File: `frontend/e2e/integration.spec.ts`

**Purpose**: Integration E2E tests  
**Change Type**: String replacement in 1 test assertion

### Required Change

**Line 69**: Replace heading assertion

```diff
-    await expect(page.locator('h1')).toContainText('Agent Projects');
+    await expect(page.locator('h1')).toContainText('New App');
```

---

## File: `frontend/src/types/index.ts`

**Purpose**: TypeScript type definitions  
**Change Type**: String replacement in file header comment

### Required Change

**Line 2**: Replace comment

```diff
- * TypeScript types for Agent Projects API.
+ * TypeScript types for New App API.
```

---

## File: `frontend/src/services/api.ts`

**Purpose**: API client service  
**Change Type**: String replacement in file header comment

### Required Change

**Line 2**: Replace comment

```diff
- * API client service for Agent Projects.
+ * API client service for New App.
```

---

## File: `README.md`

**Purpose**: Root project documentation  
**Change Type**: String replacement in header

### Required Change

**Line 1**: Replace header

```diff
-# Agent Projects
+# New App
```

---

## Files NOT Modified

The following files are explicitly **NOT** included in this change:

### Package Identifiers (Internal, Not User-Facing)
- `frontend/package.json` - `"name": "agent-projects-frontend"` (npm internal identifier)
- `backend/pyproject.toml` - `name = "agent-projects-backend"` (Python internal identifier)

---

## Verification Contract

After implementing changes, verify the following:

### Browser Tab Title (FR-001)
- [ ] Open application in browser
- [ ] Observe browser tab displays "New App"

### Application Headers (FR-002)
- [ ] Load application (unauthenticated) - login page header displays "New App"
- [ ] Authenticate (login) - main application header displays "New App"

### Backend API (FR-006)
- [ ] Start backend server
- [ ] Navigate to API docs - title displays "New App API"

### Consistency (FR-005)
- [ ] Search codebase for `"Agent Projects"` excluding package names and specs/
- [ ] Verify 0 matches remain

### E2E Tests
- [ ] Run Playwright E2E tests
- [ ] All title/heading assertions pass with "New App"

---

## Contract Compliance Checklist

- [x] All file paths are absolute and verified to exist
- [x] Line numbers documented for reference (note: may shift during implementation)
- [x] Exact string replacements specified
- [x] Before/after states documented
- [x] Validation criteria defined
- [x] Out-of-scope files explicitly listed
- [x] Rollback procedure defined (standard git revert)

**Status**: ✅ **CONTRACT COMPLETE** - Ready for implementation
