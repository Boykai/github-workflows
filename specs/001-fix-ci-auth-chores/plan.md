# Implementation Plan: Fix Playwright Auth Setup, Mutation-Testing CI Noise, and Deprecated Chores Hook Usage

**Branch**: `001-fix-ci-auth-chores` | **Date**: 2026-03-28 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/001-fix-ci-auth-chores/spec.md`

## Summary

Isolate the Playwright `save-auth-state.ts` helper from default test discovery, silence misleading mutation-testing CI failures, consolidate duplicate mutation workflows, migrate two deprecated `useChoresList` consumers to `useChoresListPaginated`, and document an upstream Vitest deprecation warning. All changes are configuration edits or mechanical refactors — no new features, no data model changes, no API changes.

## Technical Context

**Language/Version**: TypeScript ~6.0.2 (frontend), Python 3.12 (backend, workflow only)  
**Primary Dependencies**: Playwright (E2E), Stryker/mutmut (mutation), React 19, TanStack React Query, Vitest  
**Storage**: N/A (no data model changes)  
**Testing**: Vitest (1,364 frontend), Pytest (3,582 backend), Playwright (64 E2E)  
**Target Platform**: GitHub Actions CI (ubuntu-latest), local dev (macOS/Linux)  
**Project Type**: Web application (monorepo: `solune/frontend` + `solune/backend`)  
**Performance Goals**: N/A (no new runtime code)  
**Constraints**: All existing tests must remain green; mutation jobs must appear green in CI  
**Scale/Scope**: 8 files modified, 1 file deleted, 0 new files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | spec.md exists with 4 prioritised user stories, GWT scenarios, and edge cases |
| **II. Template-Driven** | ✅ PASS | All artifacts follow canonical templates |
| **III. Agent-Orchestrated** | ✅ PASS | speckit.plan → speckit.tasks → speckit.implement pipeline |
| **IV. Test Optionality** | ✅ PASS | Existing tests are updated (mock shape changes), no new test infrastructure required. Tests for removed `useChoresList` function are deleted. |
| **V. Simplicity and DRY** | ✅ PASS | Configuration edits and mechanical refactors only; no new abstractions introduced |
| **Branch Naming** | ✅ PASS | `001-fix-ci-auth-chores` follows `###-short-name` convention |
| **Phase Ordering** | ✅ PASS | Specify → Plan → Tasks → Implement |

**Post-design re-check**: ✅ All gates still pass. No complexity violations.

## Project Structure

### Documentation (this feature)

```text
specs/001-fix-ci-auth-chores/
├── plan.md              # This file
├── research.md          # Phase 0 output — all decisions documented
├── data-model.md        # Phase 1 output — N/A for this feature
├── quickstart.md        # Phase 1 output — verification commands
├── contracts/           # Phase 1 output — N/A for this feature
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (files touched)

```text
solune/frontend/
├── playwright.config.ts              # FR-001, FR-002, FR-003 — auth isolation
├── stryker.config.mjs                # FR-005 — concurrency & timeout tuning
├── vitest.config.ts                  # FR-012 — deprecation warning comment
├── e2e/
│   └── save-auth-state.ts            # (unchanged, excluded via testIgnore)
├── src/
│   ├── hooks/
│   │   ├── useChores.ts              # FR-011 — remove useChoresList export
│   │   ├── useChores.test.tsx        # Update — remove useChoresList tests
│   │   ├── useCommandPalette.ts      # FR-010 — migrate to useChoresListPaginated
│   │   └── useCommandPalette.test.tsx # Update — mock shape change
│   └── pages/
│       ├── ChoresPage.tsx            # FR-009 — migrate to useChoresListPaginated
│       └── ChoresPage.test.tsx       # Update — mock shape change

.github/workflows/
├── mutation-testing.yml              # FR-006, FR-007 — consolidated workflow
└── mutation.yml                      # FR-008 — DELETED
```

**Structure Decision**: Existing web application monorepo (`solune/frontend` + `solune/backend`). All changes are in the frontend tree and `.github/workflows/`. No structural changes.

---

## Implementation Steps

### Step 1 — Playwright Auth Isolation (FR-001, FR-002, FR-003, FR-004)

**File**: `solune/frontend/playwright.config.ts`

**Changes**:

1. Add `testIgnore` to the top-level config to exclude `save-auth-state.ts` from default discovery:
   ```ts
   testIgnore: ['**/save-auth-state.ts'],
   ```

2. Add a conditional `auth-setup` project that only matches `save-auth-state.ts` when `AUTH_SETUP=1`:
   ```ts
   {
     name: 'auth-setup',
     testMatch: /save-auth-state\.ts/,
     use: {
       ...devices['Desktop Chrome'],
       headless: false,
     },
     // Only include tests when AUTH_SETUP=1 is set
     ...(process.env.AUTH_SETUP !== '1' && { testIgnore: ['**/*'] }),
   },
   ```

3. Add a `perf` project that depends on `auth-setup` and uses the saved storage state:
   ```ts
   {
     name: 'perf',
     testMatch: /project-load-performance/,
     dependencies: ['auth-setup'],
     use: { ...devices['Desktop Chrome'] },
   },
   ```

4. Add `testIgnore` to `chromium` and `firefox` projects to exclude the perf test from default runs (it requires auth state):
   ```ts
   // In each default project:
   testIgnore: ['**/project-load-performance*'],
   ```

**Verification**:
- `npx playwright test --list` → zero references to `save-auth-state.ts`
- `npx playwright test` → 64 tests pass
- `AUTH_SETUP=1 npx playwright test --project=auth-setup --list` → shows `save-auth-state.ts`

**Risk**: Low. Only config changes; no test code modified.

---

### Step 2 — Stryker Config Tuning (FR-005)

**File**: `solune/frontend/stryker.config.mjs`

**Changes**:
```diff
-  concurrency: 2,
+  concurrency: 4,
+  timeoutFactor: 2.5,
```

**Verification**: `npx stryker run --dryRun` completes without timeout errors (dry run validates config without running all mutants).

**Risk**: Low. Only affects mutation testing speed/timeouts, not production code.

---

### Step 3 — Mutation Workflow Consolidation (FR-006, FR-007, FR-008)

**Files**:
- Update: `.github/workflows/mutation-testing.yml`
- Delete: `.github/workflows/mutation.yml`

**Changes to `mutation-testing.yml`** (replace current content with consolidated version):

| Setting | Old (`mutation-testing.yml`) | New (consolidated) |
|---------|------------------------------|-------------------|
| Schedule | Sunday 2am | Monday 3am UTC |
| Backend continue-on-error | Step-level | **Job-level** |
| Frontend continue-on-error | Step-level | **Job-level** |
| Frontend Node version | 20 | **22** |
| Frontend command | `npx stryker run` | **`npm run test:mutate`** |
| Artifact retention | 14 days | **30 days** |
| Backend `--max-children 1` | Yes | Removed (use default) |
| Separate `mutmut results` step | Yes | Removed (output captured via tee) |
| Timeout | 60 minutes | Removed (use default) |
| Workflow name | "Mutation Testing" | "Mutation Testing (Weekly)" |

**Delete**: `.github/workflows/mutation.yml`

**Verification**:
- `ls .github/workflows/mutation*.yml` → only `mutation-testing.yml` exists
- YAML is valid: `python -c "import yaml; yaml.safe_load(open('.github/workflows/mutation-testing.yml'))"`

**Risk**: Low. Mutation testing is informational; any config error is caught on next weekly run.

---

### Step 4 — Migrate ChoresPage.tsx (FR-009)

**File**: `solune/frontend/src/pages/ChoresPage.tsx`

**Changes**:

1. Update import (line 10):
   ```diff
   -import { useChoresList, useEvaluateChoresTriggers, choreKeys } from '@/hooks/useChores';
   +import { useChoresListPaginated, useEvaluateChoresTriggers, choreKeys } from '@/hooks/useChores';
   ```

2. Update hook call (line 51):
   ```diff
   -const { data: chores, isLoading: choresLoading } = useChoresList(projectId);
   +const { allItems: chores, isLoading: choresLoading } = useChoresListPaginated(projectId);
   ```

All downstream usage (`chores ?? []`, `choresLoading`) remains unchanged.

**Test file** (`ChoresPage.test.tsx`): Update mock from `useChoresList` to `useChoresListPaginated`:
```diff
 vi.mock('@/hooks/useChores', () => ({
-  useChoresList: () => ({ data: undefined }),
+  useChoresListPaginated: () => ({ allItems: undefined }),
   useEvaluateChoresTriggers: vi.fn(),
   choreKeys: { list: () => ['chores'] },
 }));
```

**Verification**: `npm run test -- --run src/pages/ChoresPage.test.tsx` passes.

**Risk**: Low. Mechanical property rename (`data` → `allItems`).

---

### Step 5 — Migrate useCommandPalette.ts (FR-010)

**File**: `solune/frontend/src/hooks/useCommandPalette.ts`

**Changes**:

1. Update import (line 29):
   ```diff
   -import { useChoresList } from '@/hooks/useChores';
   +import { useChoresListPaginated } from '@/hooks/useChores';
   ```

2. Update hook call (line 124):
   ```diff
   -const choresQuery = useChoresList(isOpen ? projectId : null);
   +const choresQuery = useChoresListPaginated(isOpen ? projectId : null);
   ```

3. Update data access (line 186):
   ```diff
   -if (choresQuery.data) {
   -  for (const chore of choresQuery.data) {
   +if (choresQuery.allItems?.length) {
   +  for (const chore of choresQuery.allItems) {
   ```

4. Update `useMemo` dependency (line 249):
   ```diff
   -  choresQuery.data,
   +  choresQuery.allItems,
   ```

5. Update loading state (line 298):
   ```diff
   -  choresQuery.isLoading ||
   +  choresQuery.isLoading ||
   ```
   (No change needed — `isLoading` is available on both hook return types.)

**Test file** (`useCommandPalette.test.tsx`): Update mock:
```diff
 vi.mock('@/hooks/useChores', () => ({
-  useChoresList: vi.fn(),
+  useChoresListPaginated: vi.fn(),
 }));
```
And update all mock return values from `{ data: choresData, isLoading }` to `{ allItems: choresData, isLoading }`.

**Verification**: `npm run test -- --run src/hooks/useCommandPalette.test.tsx` passes.

**Risk**: Low. The paginated hook's `allItems` is semantically equivalent to the old `data` for list iteration.

---

### Step 6 — Remove Deprecated useChoresList (FR-011)

**File**: `solune/frontend/src/hooks/useChores.ts`

**Changes**: Delete lines 39–52 (the `@deprecated` comment and `useChoresList` function):
```diff
-// ── List Hook ──
-
-/**
- * @deprecated Use `useChoresListPaginated` instead for paginated, server-side
- * filtered/sorted results. Retained for legacy callers (e.g. useCommandPalette).
- */
-export function useChoresList(projectId: string | null | undefined) {
-  return useQuery<Chore[]>({
-    queryKey: choreKeys.list(projectId ?? ''),
-    queryFn: () => choresApi.list(projectId!),
-    staleTime: STALE_TIME_LONG,
-    enabled: !!projectId,
-  });
-}
```

Also remove the `useQuery` import if it becomes unused (check: other hooks in this file use `useQuery` — `useChoreTemplates` and `useAllChoreNames` — so the import stays).

**Test file** (`useChores.test.tsx`): Remove the three `useChoresList` test cases (lines ~76–105 approximately) since the function no longer exists.

**Verification**:
- `grep -r "useChoresList" solune/frontend/src/ --include="*.ts" --include="*.tsx"` → zero results
- `npm run type-check` passes (no dangling imports)
- `npm run test` passes

**Risk**: Low. All consumers already migrated in Steps 4–5. If any unmigrated consumer exists, `npm run type-check` will catch it.

---

### Step 7 — Document Vitest Deprecation Warning (FR-012)

**File**: `solune/frontend/vitest.config.ts`

**Changes**: Add comment block above the export:
```ts
/**
 * NOTE: The "vitest/suite" deprecation warning visible in test output originates
 * from @fast-check/vitest@0.3.0, which imports from the deprecated vitest/suite
 * path. This is an upstream issue and cannot be fixed in project code. Track:
 * https://github.com/dubzzz/fast-check/issues — suppress once @fast-check/vitest
 * publishes a fix.
 */
```

**Verification**: Visual inspection — comment is present and accurate.

**Risk**: None. Documentation-only change.

---

## Execution Order and Dependencies

```
Step 1 (Playwright)  ─┐
Step 2 (Stryker)     ─┤  Independent — can execute in parallel
Step 3 (Workflows)   ─┤
Step 7 (Vitest doc)  ─┘

Step 4 (ChoresPage)  ──┐
Step 5 (CmdPalette)  ──┤  Must complete before Step 6
                        │
Step 6 (Remove hook) ──┘  Depends on Steps 4 & 5
```

**Recommended execution**: Steps 1–3 + 7 first (independent), then Steps 4–5 (migrate consumers), then Step 6 (remove deprecated export). Run full validation after Step 6.

## Final Validation Checklist

| Check | Command | Expected |
|-------|---------|----------|
| Playwright list | `cd solune/frontend && npx playwright test --list` | No `save-auth-state.ts` |
| Playwright tests | `cd solune/frontend && npx playwright test` | 64 tests pass |
| Frontend tests | `cd solune/frontend && npm run test` | 1,364 tests pass |
| Type check | `cd solune/frontend && npm run type-check` | Clean |
| Lint | `cd solune/frontend && npm run lint` | Clean |
| Build | `cd solune/frontend && npm run build` | Success |
| No useChoresList refs | `grep -r "useChoresList" solune/frontend/src/` | Zero results |
| Single mutation workflow | `ls .github/workflows/mutation*.yml` | Only `mutation-testing.yml` |
| Workflow YAML valid | `python -c "import yaml; yaml.safe_load(open(...))"` | No errors |

## Complexity Tracking

No complexity violations. All changes are configuration edits or mechanical refactors aligned with Constitution Principle V (Simplicity and DRY).
