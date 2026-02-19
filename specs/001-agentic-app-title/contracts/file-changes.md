# File Modification Contract: Replace App Title with 'agentic'

**Feature**: 001-agentic-app-title | **Date**: 2026-02-19
**Purpose**: Define exact file changes required for title update

## Contract Overview

This contract specifies the precise modifications to replace the application title from "Agent Projects" to "agentic" (all lowercase) across all relevant files. All changes are string literal replacements with no structural modifications.

---

## File: `frontend/index.html`

**Purpose**: HTML page title for browser tab display
**Change Type**: String replacement in `<title>` element

### Required Change

**Line 7**: Replace title text

```diff
-    <title>Agent Projects</title>
+    <title>agentic</title>
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
+        <h1>agentic</h1>
```

**Change 2 — Line 89**: Replace authenticated header text

```diff
-          <h1>Agent Projects</h1>
+          <h1>agentic</h1>
```

**Validation**:
- ✅ JSX element structure unchanged (`<h1>` tags preserved)
- ✅ Only text content modified
- ✅ TypeScript/React syntax valid

---

## File: `frontend/e2e/auth.spec.ts`

**Purpose**: E2E authentication tests with title assertions
**Change Type**: String replacement in test assertions

### Required Changes

**Lines 12, 24, 38, 99**: Replace heading text assertions

```diff
-    await expect(page.locator('h1')).toContainText('Agent Projects');
+    await expect(page.locator('h1')).toContainText('agentic');
```

**Line 62**: Replace title regex assertion

```diff
-    await expect(page).toHaveTitle(/Agent Projects/i);
+    await expect(page).toHaveTitle(/agentic/i);
```

---

## File: `frontend/e2e/ui.spec.ts`

**Purpose**: E2E UI tests with heading assertions
**Change Type**: String replacement in test assertions

### Required Changes

**Lines 43, 67**: Replace heading text assertions

```diff
-    await expect(page.locator('h1')).toContainText('Agent Projects');
+    await expect(page.locator('h1')).toContainText('agentic');
```

---

## File: `frontend/e2e/integration.spec.ts`

**Purpose**: E2E integration tests with heading assertions
**Change Type**: String replacement in test assertion

### Required Change

**Line 69**: Replace heading text assertion

```diff
-    await expect(page.locator('h1')).toContainText('Agent Projects');
+    await expect(page.locator('h1')).toContainText('agentic');
```

---

## File: `backend/src/main.py`

**Purpose**: FastAPI application metadata and log messages
**Change Type**: String replacement in 4 locations

### Required Changes

**Line 75**: Replace startup log message

```diff
-    logger.info("Starting Agent Projects API")
+    logger.info("Starting agentic API")
```

**Line 77**: Replace shutdown log message

```diff
-    logger.info("Shutting down Agent Projects API")
+    logger.info("Shutting down agentic API")
```

**Line 85**: Replace FastAPI title

```diff
-        title="Agent Projects API",
+        title="agentic API",
```

**Line 86**: Replace FastAPI description

```diff
-        description="REST API for Agent Projects",
+        description="REST API for agentic",
```

---

## File: `.devcontainer/devcontainer.json`

**Purpose**: Development container configuration
**Change Type**: String replacement in name field

### Required Change

**Line 2**: Replace container name

```diff
-  "name": "Agent Projects",
+  "name": "agentic",
```

---

## File: `.devcontainer/post-create.sh`

**Purpose**: Post-creation setup script
**Change Type**: String replacement in echo message

### Required Change

**Line 7**: Replace setup message

```diff
-echo "🚀 Setting up Agent Projects development environment..."
+echo "🚀 Setting up agentic development environment..."
```

---

## File: `backend/pyproject.toml`

**Purpose**: Python project metadata
**Change Type**: String replacement in name and description

### Required Changes

**Line 2**: Replace project name

```diff
-name = "agent-projects-backend"
+name = "agentic-backend"
```

**Line 4**: Replace project description

```diff
-description = "FastAPI backend for Agent Projects"
+description = "FastAPI backend for agentic"
```

---

## File: `README.md`

**Purpose**: Root project documentation
**Change Type**: String replacement in header

### Required Change

**Line 1**: Replace header

```diff
-# Agent Projects
+# agentic
```

---

## File: `backend/README.md`

**Purpose**: Backend project documentation
**Change Type**: String replacement in header

### Required Change

**Line 1**: Replace header

```diff
-# Agent Projects — Backend
+# agentic — Backend
```

---

## Files NOT Modified

The following files are explicitly **NOT** included in this change:

### Frontend Files (No Changes)
- `frontend/package.json` — Internal package name unchanged
- `frontend/src/**/*.css` — No style changes (FR-008)
- `frontend/src/**/*.tsx` (other than App.tsx) — No other components affected

### Spec Files (No Changes)
- `specs/` — Spec artifacts reference old title for historical context

---

## Verification Contract

After implementing changes, verify the following:

### Browser Tab Title (FR-001)
- [ ] Browser tab displays "agentic"

### Application Headers (FR-002, FR-003)
- [ ] Login page header displays "agentic"
- [ ] Authenticated header displays "agentic"

### E2E Tests (FR-004)
- [ ] All test assertions updated
- [ ] Tests pass with no regressions

### Developer Config (FR-005)
- [ ] Devcontainer name is "agentic"
- [ ] Setup script message references "agentic"

### Backend Metadata (FR-006)
- [ ] FastAPI title is "agentic API"
- [ ] Swagger UI shows "agentic API"

### Documentation (FR-007)
- [ ] Root README header is "# agentic"
- [ ] Backend README header is "# agentic — Backend"

### Consistency (FR-008)
- [ ] No styling changes — text-only replacement
- [ ] `grep -rn "Agent Projects"` in source files returns 0 matches

---

## Contract Compliance Checklist

- [x] All file paths are documented
- [x] Line numbers documented for reference
- [x] Exact string replacements specified with diffs
- [x] Validation criteria defined per file
- [x] Out-of-scope files explicitly listed
- [x] Verification aligned with spec FRs

**Status**: ✅ **CONTRACT COMPLETE** — Ready for implementation
