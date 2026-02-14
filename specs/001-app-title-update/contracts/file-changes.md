# File Modification Contract: App Title Update

**Feature**: 001-app-title-update | **Date**: 2026-02-14  
**Purpose**: Define exact file changes required for title update

## Contract Overview

This contract specifies the precise modifications to frontend files to change the application title from "Welcome to Tech Connect 2026!" to "GitHub Workflows". All changes are string literal replacements in presentation layer files.

---

## File: `frontend/index.html`

**Purpose**: HTML page title for browser tab display  
**Change Type**: String replacement in `<title>` element

### Current State

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Welcome to Tech Connect 2026!</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

### Required Change

**Line 7**: Replace title text

```diff
-    <title>Welcome to Tech Connect 2026!</title>
+    <title>GitHub Workflows</title>
```

### Expected New State

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>GitHub Workflows</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

**Validation**:
- ✅ `<title>` element structure unchanged
- ✅ Only text content modified
- ✅ HTML validity maintained

---

## File: `frontend/src/App.tsx`

**Purpose**: React component with application headers  
**Change Type**: String replacement in 2 JSX `<h1>` elements

### Current State (Relevant Sections)

**Login Page Header (Line 69)**:
```tsx
{!isAuthenticated ? (
  <div className="auth-section">
    <h1>Welcome to Tech Connect 2026!</h1>
    <p>Manage your GitHub Projects with natural language</p>
    {/* ... rest of login form ... */}
  </div>
) : (
  /* ... authenticated content ... */
)}
```

**Authenticated Header (Line 85)**:
```tsx
<div className="chat-container">
  <h1>Welcome to Tech Connect 2026!</h1>
  {/* ... rest of chat interface ... */}
</div>
```

### Required Changes

**Change 1 - Line 69**: Replace login page header text

```diff
-    <h1>Welcome to Tech Connect 2026!</h1>
+    <h1>GitHub Workflows</h1>
```

**Change 2 - Line 85**: Replace authenticated header text

```diff
-  <h1>Welcome to Tech Connect 2026!</h1>
+  <h1>GitHub Workflows</h1>
```

### Expected New State (Relevant Sections)

**Login Page Header**:
```tsx
{!isAuthenticated ? (
  <div className="auth-section">
    <h1>GitHub Workflows</h1>
    <p>Manage your GitHub Projects with natural language</p>
    {/* ... rest of login form ... */}
  </div>
) : (
  /* ... authenticated content ... */
)}
```

**Authenticated Header**:
```tsx
<div className="chat-container">
  <h1>GitHub Workflows</h1>
  {/* ... rest of chat interface ... */}
</div>
```

**Validation**:
- ✅ JSX element structure unchanged (`<h1>` tags preserved)
- ✅ Only text content modified
- ✅ Subtitle text ("Manage your GitHub Projects with natural language") unchanged
- ✅ TypeScript/React syntax valid

---

## Files NOT Modified

The following files are explicitly **NOT** included in this change per spec scope:

### Frontend Files (No Changes)
- `frontend/package.json` - Internal package name unchanged
- `frontend/src/**/*.css` - No style changes
- `frontend/src/**/*.tsx` (other than App.tsx) - No other components affected
- `frontend/e2e/**/*.spec.ts` - Test updates optional (see below)

### Backend Files (No Changes)
- All backend files unchanged (title is frontend-only concern)

### Documentation (No Changes)
- `README.md` - Out of scope per spec assumptions
- `docker-compose.yml` - Service names unchanged

---

## Optional Test Updates

### File: `frontend/e2e/auth.spec.ts` (Optional)

**Current Behavior**: Test may assert page title matches pattern `/GitHub Projects|Chat/i`

**If Test Fails**: Update title assertion to include "GitHub Workflows"

```diff
-  await expect(page).toHaveTitle(/GitHub Projects|Chat/i);
+  await expect(page).toHaveTitle(/GitHub Workflows/i);
```

**Decision Rule**: 
- If E2E tests pass without changes → No update needed
- If E2E tests fail on title assertion → Update to match new title

---

## Verification Contract

After implementing changes, verify the following:

### Browser Tab Title (FR-001)
- [ ] Open application in browser
- [ ] Observe browser tab displays "GitHub Workflows"
- [ ] Switch to another tab and back - title persists

### Application Headers (FR-002)
- [ ] Load application (unauthenticated)
- [ ] Observe login page header displays "GitHub Workflows"
- [ ] Authenticate (login)
- [ ] Observe main application header displays "GitHub Workflows"

### Consistency (FR-004, FR-005)
- [ ] Search codebase for `"Welcome to Tech Connect 2026!"`
- [ ] Verify 0 matches in frontend user-facing code
- [ ] Check README/docs only if time permits (out of primary scope)

### Accessibility (Edge Case)
- [ ] Use screen reader (optional) - should announce "GitHub Workflows"
- [ ] Verify page title in browser history

---

## Rollback Contract

If issues arise, revert changes via:

```bash
git revert <commit-hash>
```

**Expected Rollback State**: All files return to previous title "Welcome to Tech Connect 2026!"

---

## Contract Compliance Checklist

- [x] All file paths are absolute and verified to exist
- [x] Line numbers documented for reference (note: may shift during implementation)
- [x] Exact string replacements specified
- [x] Before/after states documented
- [x] Validation criteria defined
- [x] Optional changes clearly marked
- [x] Out-of-scope files explicitly listed
- [x] Rollback procedure defined

**Status**: ✅ **CONTRACT COMPLETE** - Ready for implementation
