# Contracts: Update App Title to "Happy Place"

**Feature**: 007-app-title-happy-place
**Date**: 2026-02-20

## Overview

This feature involves no API contract changes, no new endpoints, no schema modifications, and no interface changes. The only "contract" is the string replacement specification: every occurrence of "Agent Projects" in the codebase (outside `specs/`) must be replaced with "Happy Place".

## File Change Contract

The following files must be modified. Each change is a direct string replacement with no structural or logical modifications.

### Frontend Changes

**`frontend/index.html`** — 1 change
```diff
-    <title>Agent Projects</title>
+    <title>Happy Place</title>
```

**`frontend/src/App.tsx`** — 2 changes
```diff
-        <h1>Agent Projects</h1>
+        <h1>Happy Place</h1>
```
```diff
-          <h1>Agent Projects</h1>
+          <h1>Happy Place</h1>
```

**`frontend/src/services/api.ts`** — 1 change
```diff
- * API client service for Agent Projects.
+ * API client service for Happy Place.
```

**`frontend/src/types/index.ts`** — 1 change
```diff
- * TypeScript types for Agent Projects API.
+ * TypeScript types for Happy Place API.
```

### Frontend E2E Test Changes

**`frontend/e2e/auth.spec.ts`** — 5 changes
```diff
- await expect(page.locator('h1')).toContainText('Agent Projects');
+ await expect(page.locator('h1')).toContainText('Happy Place');
```
*(applied at lines 12, 24, 38, 99)*

```diff
- await expect(page).toHaveTitle(/Agent Projects/i);
+ await expect(page).toHaveTitle(/Happy Place/i);
```
*(applied at line 62)*

**`frontend/e2e/ui.spec.ts`** — 2 changes
```diff
- await expect(page.locator('h1')).toContainText('Agent Projects');
+ await expect(page.locator('h1')).toContainText('Happy Place');
```
*(applied at lines 43, 67)*

**`frontend/e2e/integration.spec.ts`** — 1 change
```diff
- await expect(page.locator('h1')).toContainText('Agent Projects');
+ await expect(page.locator('h1')).toContainText('Happy Place');
```
*(applied at line 69)*

### Backend Changes

**`backend/src/main.py`** — 4 changes
```diff
-    logger.info("Starting Agent Projects API")
+    logger.info("Starting Happy Place API")
```
```diff
-    logger.info("Shutting down Agent Projects API")
+    logger.info("Shutting down Happy Place API")
```
```diff
-        title="Agent Projects API",
+        title="Happy Place API",
```
```diff
-        description="REST API for Agent Projects",
+        description="REST API for Happy Place",
```

**`backend/pyproject.toml`** — 1 change
```diff
- description = "FastAPI backend for Agent Projects"
+ description = "FastAPI backend for Happy Place"
```

**`backend/tests/test_api_e2e.py`** — 1 change
```diff
- End-to-end API tests for the Agent Projects Backend.
+ End-to-end API tests for the Happy Place Backend.
```

**`backend/README.md`** — 2 changes
```diff
- # Agent Projects — Backend
+ # Happy Place — Backend
```
```diff
- ...powers Agent Projects and the...
+ ...powers Happy Place and the...
```

### Configuration & Documentation Changes

**`.devcontainer/devcontainer.json`** — 1 change
```diff
- "name": "Agent Projects",
+ "name": "Happy Place",
```

**`.devcontainer/post-create.sh`** — 1 change
```diff
- echo "🚀 Setting up Agent Projects development environment..."
+ echo "🚀 Setting up Happy Place development environment..."
```

**`.env.example`** — 1 change
```diff
- # Agent Projects - Environment Configuration
+ # Happy Place - Environment Configuration
```

**`README.md`** — 1 change
```diff
- # Agent Projects
+ # Happy Place
```

## Summary

| Category | Files | Changes |
|----------|-------|---------|
| User-visible (HTML/React) | 2 | 3 |
| API metadata (FastAPI) | 1 | 4 |
| Developer config | 3 | 3 |
| Documentation | 2 | 3 |
| Code comments | 3 | 3 |
| E2E test assertions | 3 | 8 |
| Build config | 1 | 1 |
| **Total** | **15** | **25** |
