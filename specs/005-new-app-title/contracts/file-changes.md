# File Modification Contract: Update App Title to "New App"

**Feature**: 005-new-app-title | **Date**: 2026-02-19  
**Purpose**: Define exact file changes required for title update from "Agent Projects" to "New App"

## Contract Overview

This contract specifies the precise modifications to update the application title from "Agent Projects" to "New App" across all locations in the codebase. All changes are string literal replacements.

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

**Validation**: ✅ `<title>` element structure unchanged; only text content modified

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

**Validation**: ✅ JSX element structure unchanged; only text content modified

---

## File: `backend/src/main.py`

**Purpose**: FastAPI application metadata  
**Change Type**: String replacement in FastAPI constructor

### Required Changes

**Line 85**: Replace API title

```diff
-        title="Agent Projects API",
+        title="New App API",
```

**Line 86**: Replace API description

```diff
-        description="REST API for Agent Projects",
+        description="REST API for New App",
```

**Validation**: ✅ FastAPI constructor structure unchanged; only string values modified

---

## File: `backend/pyproject.toml`

**Purpose**: Python project metadata  
**Change Type**: String replacement in project name and description

### Required Changes

**Line 2**: Replace package name

```diff
-name = "agent-projects-backend"
+name = "new-app-backend"
```

**Line 4**: Replace description

```diff
-description = "FastAPI backend for Agent Projects"
+description = "FastAPI backend for New App"
```

**Validation**: ✅ TOML structure unchanged; only string values modified

---

## File: `frontend/package.json`

**Purpose**: Frontend npm package metadata  
**Change Type**: String replacement in package name

### Required Change

**Line 2**: Replace package name

```diff
-  "name": "agent-projects-frontend",
+  "name": "new-app-frontend",
```

**Validation**: ✅ JSON structure unchanged; only string value modified

---

## File: `README.md`

**Purpose**: Root repository documentation  
**Change Type**: String replacement in heading and body text

### Required Change

**Line 1**: Replace heading

```diff
-# Agent Projects
+# New App
```

Additionally, replace all other occurrences of "Agent Projects" in the file body with "New App".

---

## File: `backend/README.md`

**Purpose**: Backend documentation  
**Change Type**: String replacement in heading and body text

### Required Change

**Line 1**: Replace heading

```diff
-# Agent Projects — Backend
+# New App — Backend
```

Additionally, replace all other occurrences of "Agent Projects" in the file body with "New App".

---

## File: `.devcontainer/devcontainer.json`

**Purpose**: VS Code dev container configuration  
**Change Type**: String replacement in container name

### Required Change

**Line 2**: Replace container name

```diff
-  "name": "Agent Projects",
+  "name": "New App",
```

**Validation**: ✅ JSON structure unchanged; only string value modified

---

## File: `.devcontainer/post-create.sh`

**Purpose**: Dev container setup script  
**Change Type**: String replacement in echo message

### Required Change

**Line 7**: Replace echo message

```diff
-echo "🚀 Setting up Agent Projects development environment..."
+echo "🚀 Setting up New App development environment..."
```

**Validation**: ✅ Script structure unchanged; only string value modified

---

## File: `.env.example`

**Purpose**: Environment configuration template  
**Change Type**: String replacement in header comment

### Required Change

**Line 2**: Replace header comment

```diff
-# Agent Projects - Environment Configuration
+# New App - Environment Configuration
```

**Validation**: ✅ Comment only; no functional impact

---

## File: `frontend/e2e/auth.spec.ts`

**Purpose**: E2E authentication test assertions  
**Change Type**: String replacement in test assertions

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

**Purpose**: E2E UI test assertions  
**Change Type**: String replacement in test assertions

### Required Changes

**Lines 43, 67**: Replace heading assertions

```diff
-    await expect(page.locator('h1')).toContainText('Agent Projects');
+    await expect(page.locator('h1')).toContainText('New App');
```

---

## File: `frontend/e2e/integration.spec.ts`

**Purpose**: E2E integration test assertions  
**Change Type**: String replacement in test assertions

### Required Change

**Line 69**: Replace heading assertion

```diff
-    await expect(page.locator('h1')).toContainText('Agent Projects');
+    await expect(page.locator('h1')).toContainText('New App');
```

---

## Verification Contract

After implementing all changes, verify:

### Browser Tab Title (FR-001)
- [ ] Browser tab displays "New App"

### Application Headers (FR-002)
- [ ] Login page header displays "New App"
- [ ] Authenticated header displays "New App"

### Configuration Files (FR-006)
- [ ] `backend/pyproject.toml` references "new-app-backend"
- [ ] `frontend/package.json` references "new-app-frontend"
- [ ] `.devcontainer/devcontainer.json` references "New App"
- [ ] `backend/src/main.py` references "New App API"

### Documentation (FR-007)
- [ ] `README.md` heading is "# New App"
- [ ] `backend/README.md` heading is "# New App — Backend"

### Consistency (FR-005)
- [ ] `grep -r "Agent Projects"` returns zero matches in codebase

### E2E Tests
- [ ] All E2E test assertions updated to match "New App"
- [ ] E2E tests pass (if run)

---

## Contract Compliance Checklist

- [x] All file paths verified to exist
- [x] Line numbers documented for reference
- [x] Exact string replacements specified
- [x] Before/after states documented
- [x] Validation criteria defined
- [x] All affected files enumerated
- [x] Rollback procedure: standard git revert

**Status**: ✅ **CONTRACT COMPLETE** - Ready for implementation
