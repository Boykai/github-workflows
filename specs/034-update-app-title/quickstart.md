# Quickstart: Update App Title to "Hello World"

**Feature**: 034-update-app-title
**Date**: 2026-03-11

## What to Change

Replace the string `"Solune"` with `"Hello World"` in 5 locations across 4 files:

### 1. Browser Tab Title

**File**: `frontend/index.html` (line 7)

```html
<!-- Before -->
<title>Solune</title>

<!-- After -->
<title>Hello World</title>
```

### 2. Sidebar Branding

**File**: `frontend/src/layout/Sidebar.tsx` (line 63)

```tsx
// Before
Solune

// After
Hello World
```

### 3. Login Page Description

**File**: `frontend/src/pages/LoginPage.tsx` (line 45)

```tsx
// Before
Solune reframes GitHub operations with a brighter solar shell by day, a lunar shell by

// After
Hello World reframes GitHub operations with a brighter solar shell by day, a lunar shell by
```

### 4. Login Page Heading

**File**: `frontend/src/pages/LoginPage.tsx` (line 112)

```tsx
// Before
Solune

// After
Hello World
```

### 5. Settings Page Subtitle

**File**: `frontend/src/pages/SettingsPage.tsx` (line 85)

```tsx
// Before
<p className="text-muted-foreground">Configure your preferences for Solune.</p>

// After
<p className="text-muted-foreground">Configure your preferences for Hello World.</p>
```

## What NOT to Change

- Taglines: "Sun & Moon", "Guided solar orbit", "Sun & Moon Workspace"
- Code comments referencing "Solune" (JSDoc, section markers)
- Backend code and comments
- Test fixture data using "Solune" as sample project names
- Functional descriptions like "Solune-generated branches"
- `api.ts` device name default parameter

## Verification

```bash
# Build frontend to verify no compile errors
cd frontend && npm run build

# Run existing tests to verify no regressions
cd frontend && npm run test

# Verify no user-facing "Solune" remains (should only show comments/tests/internal refs)
grep -rn "Solune" frontend/src/ frontend/index.html | grep -v "test\." | grep -v "//" | grep -v "Solune-" | grep -v "deviceName"
```

## Acceptance

- [ ] Browser tab shows "Hello World"
- [ ] Sidebar displays "Hello World" with taglines intact
- [ ] Login page heading reads "Hello World"
- [ ] Login page description starts with "Hello World reframes..."
- [ ] Settings page reads "Configure your preferences for Hello World."
- [ ] `npm run build` succeeds
- [ ] `npm run test` passes
- [ ] `npm run lint` passes
- [ ] `npm run type-check` passes
