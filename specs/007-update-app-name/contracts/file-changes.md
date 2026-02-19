# File Modification Contract: Update App Name to "Robot"

**Feature**: 007-update-app-name | **Date**: 2026-02-19  
**Purpose**: Define exact file changes required for the app name update

## Contract Overview

This contract specifies the precise modifications to rename the application display name from "Agent Projects" to "Robot" across all user-facing surfaces, configuration files, documentation, and test assertions. All changes are string literal replacements.

---

## File: `frontend/index.html`

**Purpose**: HTML page title for browser tab display (FR-001)  
**Change Type**: String replacement in `<title>` element

### Required Change

**Line 7**: Replace title text

```diff
-    <title>Agent Projects</title>
+    <title>Robot</title>
```

---

## File: `frontend/src/App.tsx`

**Purpose**: React component with application headers (FR-002)  
**Change Type**: String replacement in 2 JSX `<h1>` elements

### Required Changes

**Change 1 — Line 72** (login page header):

```diff
-        <h1>Agent Projects</h1>
+        <h1>Robot</h1>
```

**Change 2 — Line 89** (authenticated app header):

```diff
-          <h1>Agent Projects</h1>
+          <h1>Robot</h1>
```

---

## File: `backend/src/main.py`

**Purpose**: FastAPI app metadata and startup/shutdown logs (FR-003, FR-004)  
**Change Type**: String replacement in log messages and FastAPI config

### Required Changes

**Change 1 — Line 75** (startup log):

```diff
-    logger.info("Starting Agent Projects API")
+    logger.info("Starting Robot API")
```

**Change 2 — Line 77** (shutdown log):

```diff
-    logger.info("Shutting down Agent Projects API")
+    logger.info("Shutting down Robot API")
```

**Change 3 — Line 85** (FastAPI title):

```diff
-        title="Agent Projects API",
+        title="Robot API",
```

**Change 4 — Line 86** (FastAPI description):

```diff
-        description="REST API for Agent Projects",
+        description="REST API for Robot",
```

---

## File: `.devcontainer/devcontainer.json`

**Purpose**: Dev environment display name in VS Code/Codespaces (FR-006)  
**Change Type**: String replacement in `name` field

### Required Change

**Line 2**:

```diff
-  "name": "Agent Projects",
+  "name": "Robot",
```

---

## File: `.devcontainer/post-create.sh`

**Purpose**: Setup script log message (FR-006)  
**Change Type**: String replacement in echo statement

### Required Change

**Line 7**:

```diff
-echo "🚀 Setting up Agent Projects development environment..."
+echo "🚀 Setting up Robot development environment..."
```

---

## File: `.env.example`

**Purpose**: Environment configuration file header (FR-005)  
**Change Type**: String replacement in comment header

### Required Change

**Line 2**:

```diff
-# Agent Projects - Environment Configuration
+# Robot - Environment Configuration
```

---

## File: `backend/pyproject.toml`

**Purpose**: Project metadata description (FR-005)  
**Change Type**: String replacement in `description` field

### Required Change

**Line 4**:

```diff
-description = "FastAPI backend for Agent Projects"
+description = "FastAPI backend for Robot"
```

**Note**: The `name` field (`agent-projects-backend`) is an internal Python package identifier and is NOT renamed per spec assumptions.

---

## File: `README.md`

**Purpose**: Main project documentation (FR-007)  
**Change Type**: String replacement in heading and body text

### Required Change

**Line 1**:

```diff
-# Agent Projects
+# Robot
```

**Note**: Only the heading is changed. The body text describes functionality and uses "Agent Projects" as a proper noun reference to the old name — all user-facing occurrences should be updated to "Robot".

---

## File: `backend/README.md`

**Purpose**: Backend documentation (FR-007)  
**Change Type**: String replacement in heading and body text

### Required Changes

**Change 1 — Line 1**:

```diff
-# Agent Projects — Backend
+# Robot — Backend
```

**Change 2 — Line 3** (first sentence):

```diff
-FastAPI backend that powers Agent Projects and the **Spec Kit agent pipeline**.
+FastAPI backend that powers Robot and the **Spec Kit agent pipeline**.
```

---

## E2E Test Files (FR-008)

### File: `frontend/e2e/auth.spec.ts`

**Lines 12, 24, 38, 99**: Replace h1 text assertions

```diff
-    await expect(page.locator('h1')).toContainText('Agent Projects');
+    await expect(page.locator('h1')).toContainText('Robot');
```

**Line 62**: Replace page title assertion

```diff
-    await expect(page).toHaveTitle(/Agent Projects/i);
+    await expect(page).toHaveTitle(/Robot/i);
```

### File: `frontend/e2e/ui.spec.ts`

**Lines 43, 67**: Replace h1 text assertions

```diff
-    await expect(page.locator('h1')).toContainText('Agent Projects');
+    await expect(page.locator('h1')).toContainText('Robot');
```

### File: `frontend/e2e/integration.spec.ts`

**Line 69**: Replace h1 text assertion

```diff
-    await expect(page.locator('h1')).toContainText('Agent Projects');
+    await expect(page.locator('h1')).toContainText('Robot');
```

---

## Files NOT Modified

The following files are explicitly **NOT** included in this change per spec scope:

- `backend/pyproject.toml` `name` field — internal Python package identifier
- `frontend/package.json` — internal npm package name
- `docker-compose.yml` — service names are infrastructure identifiers
- All source code directories — no directory renames
- Repository name — not in scope

---

## Verification Contract

After implementing changes, verify the following:

### User-Facing Surfaces
- [ ] Browser tab displays "Robot" (FR-001)
- [ ] Login page header displays "Robot" (FR-002)
- [ ] Authenticated app header displays "Robot" (FR-002)
- [ ] FastAPI docs title displays "Robot API" (FR-004)

### Developer Surfaces
- [ ] Backend startup log says "Starting Robot API" (FR-003)
- [ ] Devcontainer name is "Robot" (FR-006)

### Completeness Check
- [ ] `grep -r "Agent Projects" . --include="*.html" --include="*.tsx" --include="*.py" --include="*.json" --include="*.toml" --include="*.sh" --include="*.md" --include="*.ts"` returns zero results in user-facing/config files (FR-009)
- [ ] All E2E test assertions updated (FR-008)

---

## Contract Compliance Checklist

- [x] All file paths verified to exist in codebase
- [x] Line numbers documented for reference
- [x] Exact string replacements specified with diff format
- [x] Out-of-scope files explicitly listed
- [x] Verification criteria defined per functional requirement
- [x] E2E test assertion updates documented

**Status**: ✅ **CONTRACT COMPLETE** — Ready for implementation
