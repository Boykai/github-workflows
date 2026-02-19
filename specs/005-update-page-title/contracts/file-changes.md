# File Modification Contract: Update Page Title to "Objects"

**Feature**: 005-update-page-title | **Date**: 2026-02-19  
**Purpose**: Define exact file changes required for title update from "Agent Projects" to "Objects"

## Contract Overview

This contract specifies the precise modifications across all files to change the application title from "Agent Projects" to "Objects". All changes are string literal replacements. Changes span frontend (HTML, React, E2E tests), backend (Python, TOML), configuration (.devcontainer, .env), and documentation (README).

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

**Line 72**: Replace login page header text

```diff
-        <h1>Agent Projects</h1>
+        <h1>Objects</h1>
```

**Line 89**: Replace authenticated header text

```diff
-          <h1>Agent Projects</h1>
+          <h1>Objects</h1>
```

---

## File: `backend/src/main.py`

**Purpose**: FastAPI application configuration and logging  
**Change Type**: String replacement in 4 locations

### Required Changes

**Line 75**: Startup log message

```diff
-    logger.info("Starting Agent Projects API")
+    logger.info("Starting Objects API")
```

**Line 77**: Shutdown log message

```diff
-    logger.info("Shutting down Agent Projects API")
+    logger.info("Shutting down Objects API")
```

**Line 85**: FastAPI title parameter

```diff
-        title="Agent Projects API",
+        title="Objects API",
```

**Line 86**: FastAPI description parameter

```diff
-        description="REST API for Agent Projects",
+        description="REST API for Objects",
```

---

## File: `frontend/e2e/auth.spec.ts`

**Purpose**: Playwright E2E authentication tests  
**Change Type**: Update 5 test assertion strings

### Required Changes

**Line 12**:
```diff
-    await expect(page.locator('h1')).toContainText('Agent Projects');
+    await expect(page.locator('h1')).toContainText('Objects');
```

**Line 24**:
```diff
-    await expect(page.locator('h1')).toContainText('Agent Projects', { timeout: 5000 });
+    await expect(page.locator('h1')).toContainText('Objects', { timeout: 5000 });
```

**Line 38**:
```diff
-    await expect(page.locator('h1')).toContainText('Agent Projects');
+    await expect(page.locator('h1')).toContainText('Objects');
```

**Line 62**:
```diff
-    await expect(page).toHaveTitle(/Agent Projects/i);
+    await expect(page).toHaveTitle(/Objects/i);
```

**Line 99**:
```diff
-    await expect(page.locator('h1')).toContainText('Agent Projects');
+    await expect(page.locator('h1')).toContainText('Objects');
```

---

## File: `frontend/e2e/ui.spec.ts`

**Purpose**: Playwright E2E UI tests  
**Change Type**: Update 2 test assertion strings

### Required Changes

**Line 43**:
```diff
-    await expect(page.locator('h1')).toContainText('Agent Projects');
+    await expect(page.locator('h1')).toContainText('Objects');
```

**Line 67**:
```diff
-    await expect(page.locator('h1')).toContainText('Agent Projects');
+    await expect(page.locator('h1')).toContainText('Objects');
```

---

## File: `frontend/e2e/integration.spec.ts`

**Purpose**: Playwright E2E integration tests  
**Change Type**: Update 1 test assertion string

### Required Change

**Line 69**:
```diff
-    await expect(page.locator('h1')).toContainText('Agent Projects');
+    await expect(page.locator('h1')).toContainText('Objects');
```

---

## File: `.devcontainer/devcontainer.json`

**Purpose**: VS Code dev container configuration  
**Change Type**: String replacement in name field

### Required Change

**Line 2**:
```diff
-  "name": "Agent Projects",
+  "name": "Objects",
```

---

## File: `.devcontainer/post-create.sh`

**Purpose**: Dev container post-create setup script  
**Change Type**: String replacement in echo message

### Required Change

**Line 7**:
```diff
-echo "🚀 Setting up Agent Projects development environment..."
+echo "🚀 Setting up Objects development environment..."
```

---

## File: `.env.example`

**Purpose**: Environment configuration example  
**Change Type**: String replacement in comment header

### Required Change

**Line 2**:
```diff
-# Agent Projects - Environment Configuration
+# Objects - Environment Configuration
```

---

## File: `README.md`

**Purpose**: Main project documentation  
**Change Type**: String replacement in heading

### Required Change

**Line 1**:
```diff
-# Agent Projects
+# Objects
```

---

## File: `backend/README.md`

**Purpose**: Backend project documentation  
**Change Type**: String replacement in heading and description

### Required Changes

**Line 1**:
```diff
-# Agent Projects — Backend
+# Objects — Backend
```

**Line 3**:
```diff
-FastAPI backend that powers Agent Projects and the **Spec Kit agent pipeline**.
+FastAPI backend that powers Objects and the **Spec Kit agent pipeline**.
```

---

## File: `backend/pyproject.toml`

**Purpose**: Python project metadata  
**Change Type**: String replacement in description

### Required Change

**Line 4**:
```diff
-description = "FastAPI backend for Agent Projects"
+description = "FastAPI backend for Objects"
```

---

## File: `frontend/src/services/api.ts`

**Purpose**: API client service JSDoc  
**Change Type**: String replacement in comment

### Required Change

**Line 2**:
```diff
- * API client service for Agent Projects.
+ * API client service for Objects.
```

---

## File: `frontend/src/types/index.ts`

**Purpose**: TypeScript type definitions JSDoc  
**Change Type**: String replacement in comment

### Required Change

**Line 2**:
```diff
- * TypeScript types for Agent Projects API.
+ * TypeScript types for Objects API.
```

---

## File: `backend/tests/test_api_e2e.py`

**Purpose**: Backend E2E test module  
**Change Type**: String replacement in docstring

### Required Change

**Line 2**:
```diff
-End-to-end API tests for the Agent Projects Backend.
+End-to-end API tests for the Objects Backend.
```

---

## File: `frontend/package.json`

**Purpose**: npm package metadata  
**Change Type**: Update package name

### Required Change

**Line 2** (approximate):
```diff
-  "name": "agent-projects-frontend",
+  "name": "objects-frontend",
```

---

## Verification Contract

After implementing changes, verify the following:

### Browser Tab Title (FR-001)
- [ ] Open application in browser
- [ ] Observe browser tab displays "Objects"

### Application Headers (FR-002)
- [ ] Load application (unauthenticated) — login page header displays "Objects"
- [ ] Authenticate (login) — main application header displays "Objects"

### Navigation Elements (FR-003)
- [ ] All navigation elements referencing the title display "Objects"

### No Unintended Changes (FR-004)
- [ ] No other titles or labels are affected

### Test Assertions (FR-006)
- [ ] All E2E test assertions updated to expect "Objects"
- [ ] Existing test suite passes

### Backend Configuration (FR-007)
- [ ] FastAPI title reflects "Objects API" in OpenAPI docs
- [ ] Log messages reference "Objects API"

### Codebase Search
- [ ] `grep -rn "Agent Projects"` returns 0 matches outside of specs/ directory

---

## Contract Compliance Checklist

- [x] All file paths are verified to exist
- [x] Line numbers documented for reference (may shift during implementation)
- [x] Exact string replacements specified
- [x] Before/after states documented
- [x] Validation criteria defined
- [x] Out-of-scope files explicitly excluded (specs/ directory contents)

**Status**: ✅ **CONTRACT COMPLETE** - Ready for implementation
