# Quickstart: Fix Playwright Auth Setup, Mutation-Testing CI Noise, and Deprecated Chores Hook Usage

**Feature Branch**: `001-fix-ci-auth-chores`  
**Date**: 2026-03-28

## Prerequisites

- Node.js 22+
- Python 3.12+ (for workflow YAML validation only)
- Working clone of the repository

## Verification Commands

### 1. Playwright Auth Isolation

```bash
cd solune/frontend

# Confirm save-auth-state.ts is NOT in default test listing
npx playwright test --list 2>&1 | grep -c "save-auth-state"
# Expected: 0

# Confirm all 64 E2E tests still pass (requires dev server or E2E_BASE_URL)
npx playwright test
# Expected: 64 passed

# Confirm auth-setup project is available when AUTH_SETUP=1
AUTH_SETUP=1 npx playwright test --project=auth-setup --list 2>&1 | grep "save-auth-state"
# Expected: shows save-auth-state.ts
```

### 2. Stryker Config Validation

```bash
cd solune/frontend

# Dry run to validate config (does not run full mutation suite)
npx stryker run --dryRun
# Expected: completes without errors, shows "concurrency: 4"
```

### 3. Mutation Workflow Validation

```bash
# Confirm only one mutation workflow exists
ls .github/workflows/mutation*.yml
# Expected: mutation-testing.yml only (no mutation.yml)

# Validate YAML syntax
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/mutation-testing.yml')); print('Valid')"
# Expected: Valid
```

### 4. Hook Migration Validation

```bash
cd solune/frontend

# Confirm zero references to deprecated useChoresList
grep -r "useChoresList" src/ --include="*.ts" --include="*.tsx" | grep -v "Paginated"
# Expected: no output (zero matches)

# Type check (catches any dangling imports)
npm run type-check
# Expected: clean

# Run affected tests
npm run test -- --run src/pages/ChoresPage.test.tsx src/hooks/useCommandPalette.test.tsx src/hooks/useChores.test.tsx
# Expected: all pass
```

### 5. Full Validation Suite

```bash
cd solune/frontend

# Lint
npm run lint
# Expected: clean

# Type check
npm run type-check
# Expected: clean

# All frontend tests
npm run test:coverage
# Expected: 1,364+ tests pass, coverage thresholds met

# Build
npm run build
# Expected: success
```

### 6. Vitest Deprecation Comment

```bash
# Visual check
head -20 solune/frontend/vitest.config.ts
# Expected: comment block referencing @fast-check/vitest@0.3.0
```

## Common Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| `save-auth-state.ts` still in test list | `testIgnore` not applied | Check `playwright.config.ts` has `testIgnore: ['**/save-auth-state.ts']` at top level |
| `useChoresList is not exported` | Import not updated | Change import to `useChoresListPaginated` |
| Mock returns `undefined` for chores | Mock shape mismatch | Mock should return `{ allItems: ... }` not `{ data: ... }` |
| Two mutation workflows exist | `mutation.yml` not deleted | `git rm .github/workflows/mutation.yml` |
