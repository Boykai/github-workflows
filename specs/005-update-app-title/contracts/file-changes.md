# File Change Contracts: Update App Title to "Happy Place"

**Feature**: 005-update-app-title | **Date**: 2026-02-20

---

This feature has no API contract changes (no new endpoints, no changed request/response shapes). The contracts below define the exact file modifications required, serving as the implementation specification.

## Contract 1: Frontend Title Tag

**File**: `frontend/index.html`
**Type**: String replacement

```diff
-    <title>Agent Projects</title>
+    <title>Happy Place</title>
```

**Verification**: Open browser → tab title shows "Happy Place"

---

## Contract 2: Frontend App Headers

**File**: `frontend/src/App.tsx`
**Type**: String replacement (2 locations)

```diff
-        <h1>Agent Projects</h1>
+        <h1>Happy Place</h1>
```

```diff
-          <h1>Agent Projects</h1>
+          <h1>Happy Place</h1>
```

**Verification**: Load app (logged out) → h1 shows "Happy Place"; load app (logged in) → header h1 shows "Happy Place"

---

## Contract 3: Backend FastAPI Metadata

**File**: `backend/src/main.py`
**Type**: String replacement (4 locations)

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
-        description="REST API for Agent Projects",
+        title="Happy Place API",
+        description="REST API for Happy Place",
```

**Verification**: `GET /api/docs` → OpenAPI title shows "Happy Place API"

---

## Contract 4: E2E Test Assertions

**File**: `frontend/e2e/auth.spec.ts`
**Type**: String replacement (5 locations)

```diff
-    await expect(page.locator('h1')).toContainText('Agent Projects');
+    await expect(page.locator('h1')).toContainText('Happy Place');
```

(Lines 12, 24, 38, 99)

```diff
-    await expect(page).toHaveTitle(/Agent Projects/i);
+    await expect(page).toHaveTitle(/Happy Place/i);
```

(Line 62)

**File**: `frontend/e2e/ui.spec.ts`
**Type**: String replacement (2 locations)

```diff
-    await expect(page.locator('h1')).toContainText('Agent Projects');
+    await expect(page.locator('h1')).toContainText('Happy Place');
```

(Lines 43, 67)

**File**: `frontend/e2e/integration.spec.ts`
**Type**: String replacement (1 location)

```diff
-    await expect(page.locator('h1')).toContainText('Agent Projects');
+    await expect(page.locator('h1')).toContainText('Happy Place');
```

(Line 69)

**Verification**: `npx playwright test` → all tests pass

---

## Contract 5: Configuration Files

**File**: `.devcontainer/devcontainer.json`

```diff
-  "name": "Agent Projects",
+  "name": "Happy Place",
```

**File**: `.devcontainer/post-create.sh`

```diff
-echo "🚀 Setting up Agent Projects development environment..."
+echo "🚀 Setting up Happy Place development environment..."
```

**File**: `.env.example`

```diff
-# Agent Projects - Environment Configuration
+# Happy Place - Environment Configuration
```

**File**: `backend/pyproject.toml`

```diff
-description = "FastAPI backend for Agent Projects"
+description = "FastAPI backend for Happy Place"
```

---

## Contract 6: Documentation

**File**: `README.md`

```diff
-# Agent Projects
+# Happy Place
```

**File**: `backend/README.md`

```diff
-# Agent Projects — Backend
+# Happy Place — Backend
```

```diff
-...powers Agent Projects and the **Spec Kit agent pipeline**...
+...powers Happy Place and the **Spec Kit agent pipeline**...
```

---

## Contract 7: Code Comments

**File**: `frontend/src/types/index.ts`

```diff
- * TypeScript types for Agent Projects API.
+ * TypeScript types for Happy Place API.
```

**File**: `frontend/src/services/api.ts`

```diff
- * API client service for Agent Projects.
+ * API client service for Happy Place.
```

**File**: `backend/tests/test_api_e2e.py`

```diff
-End-to-end API tests for the Agent Projects Backend.
+End-to-end API tests for the Happy Place Backend.
```

---

## Post-Implementation Verification

```bash
# Must return zero results (excluding specs/ directory)
grep -rn "Agent Projects" . \
  --include="*.html" --include="*.tsx" --include="*.ts" \
  --include="*.py" --include="*.json" --include="*.md" \
  --include="*.toml" --include="*.sh" \
  | grep -v "specs/" | grep -v "node_modules/"
```

Expected output: no matches.
