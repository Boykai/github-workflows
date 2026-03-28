# Research: Fix Playwright Auth Setup, Mutation-Testing CI Noise, and Deprecated Chores Hook Usage

**Feature Branch**: `001-fix-ci-auth-chores`  
**Date**: 2026-03-28  
**Status**: Complete

## R1 — Playwright Auth Project Isolation

### Decision
Use Playwright `testIgnore` combined with a conditional `auth-setup` project gated on `AUTH_SETUP=1`.

### Rationale
Playwright's `testIgnore` config option accepts glob patterns and excludes matching files from default test discovery — this is the simplest way to hide `save-auth-state.ts` from `npx playwright test`. A dedicated project named `auth-setup` that explicitly includes `save-auth-state.ts` via `testMatch` and gates on `process.env.AUTH_SETUP === '1'` follows the [Playwright recommended authentication pattern](https://playwright.dev/docs/auth). The performance project (`perf`) can then declare `dependencies: ['auth-setup']` to guarantee auth state is saved before performance tests run.

### Alternatives Considered
- **Directory-based separation** (moving `save-auth-state.ts` out of `e2e/`): Rejected because it changes import paths, breaks the existing `AUTH_FILE` constant in `project-load-performance.spec.ts`, and adds unnecessary file moves.
- **Environment-variable guard inside the test file** (`test.skip` unless `AUTH_SETUP`): Rejected because the file still appears in `--list` output, which is confusing, and requires modifying each guarded test file.

---

## R2 — Playwright Performance Project Dependency Chain

### Decision
Define three projects: `chromium` (default), `firefox` (default), `auth-setup` (conditional), and `perf` (depends on `auth-setup`). The `perf` project uses `storageState` from `e2e/.auth/state.json`.

### Rationale
The existing `project-load-performance.spec.ts` already checks for `AUTH_FILE` existence at runtime and uses it as `storageState`. Making `perf` depend on `auth-setup` ensures the file is created before performance tests execute. When `AUTH_SETUP` is not set, the `auth-setup` project is effectively empty (zero tests matched via `testMatch`), so the dependency is harmless.

### Alternatives Considered
- **Global setup script**: Rejected because global setup runs unconditionally and would attempt OAuth login on every CI run.

---

## R3 — Mutation Testing CI Error Handling

### Decision
Use job-level `continue-on-error: true` on both backend and frontend mutation jobs.

### Rationale
Stryker (frontend) and mutmut (backend) exit with code 1 when surviving mutants are found. This is expected and informational. Step-level `continue-on-error` (current `mutation-testing.yml`) marks individual steps as passed but does not suppress the overall job annotation. Job-level `continue-on-error` (current `mutation.yml`) marks the entire job as green regardless of individual step exit codes, which is the desired UX for informational mutation results.

### Alternatives Considered
- **Wrapper script with `|| true`**: Rejected because it loses the actual exit code and makes debugging harder.
- **Custom action to translate exit codes**: Over-engineering for a simple boolean pass/fail need.

---

## R4 — Stryker Concurrency and Timeout Tuning

### Decision
Update `stryker.config.mjs` to `concurrency: 4` and add `timeoutFactor: 2.5`.

### Rationale
CI runners have 2–4 vCPUs; `concurrency: 4` maximizes parallelism without oversubscription. The default `timeoutFactor` of 1.5 causes false timeouts on CI due to resource contention; 2.5 provides headroom while still catching genuinely hanging mutants. The explicit `timeoutMS: 30000` is retained as a baseline.

### Alternatives Considered
- **Concurrency 8**: Rejected because CI runners typically have 2 vCPUs; 8 would cause context-switching overhead.
- **timeoutFactor 5**: Excessively permissive; would mask genuinely hanging tests.

---

## R5 — Mutation Workflow Consolidation

### Decision
Update `mutation-testing.yml` (the canonical filename) to incorporate all improvements from `mutation.yml`, then delete `mutation.yml`.

### Rationale
Two workflows running on different schedules (Sunday vs. Monday) with different configurations (Node 20 vs. 22, 14-day vs. 30-day retention) creates confusion. The newer `mutation.yml` already contains the improved configuration (Node 22, 30-day retention, job-level continue-on-error, `npm run test:mutate` script). Merging these improvements into the canonical `mutation-testing.yml` and deleting the duplicate produces a single source of truth.

### Consolidated configuration
- **Schedule**: Weekly (single schedule, Monday 3am UTC)
- **Node**: 22
- **Retention**: 30 days
- **Error handling**: Job-level `continue-on-error: true`
- **Frontend command**: `npm run test:mutate` (uses the package.json script)

### Alternatives Considered
- **Keep `mutation.yml` and delete `mutation-testing.yml`**: Rejected because `mutation-testing.yml` is the more descriptive canonical name and may be referenced in documentation/dashboards.

---

## R6 — useChoresList → useChoresListPaginated Migration

### Decision
Replace `useChoresList` with `useChoresListPaginated` in both `ChoresPage.tsx` and `useCommandPalette.ts`, adapting data access from `.data` to `.allItems`. Remove the deprecated `useChoresList` export from `useChores.ts`.

### Rationale
`useChoresListPaginated` returns `allItems: Chore[]` (a flattened array from all fetched pages) which is equivalent to the previous `data: Chore[]` for consumers that only need the list. The paginated hook's `allItems` contains at minimum the first page (25 items), which covers typical chore counts. Both consumers (`ChoresPage.tsx` and `useCommandPalette.ts`) only iterate the list without pagination controls — they need the array, not pagination metadata.

### Key data shape differences
| Property | `useChoresList` | `useChoresListPaginated` |
|----------|----------------|--------------------------|
| Data array | `.data` (Chore[]) | `.allItems` (Chore[]) |
| Loading | `.isLoading` | `.isLoading` |
| Query type | `useQuery` | `useInfiniteQuery` |
| Extra | — | `.totalCount`, `.hasNextPage`, `.fetchNextPage`, `.invalidate()` |

### Additional consumer: ChoresPanel.tsx
`ChoresPanel.tsx` already uses `useChoresListPaginated` — no migration needed.

### Test impact
- `ChoresPage.test.tsx`: Mock must change from `useChoresList` to `useChoresListPaginated`; mock return shape changes from `{ data }` to `{ allItems }`.
- `useCommandPalette.test.tsx`: Same mock update needed.
- `useChores.test.tsx`: Tests for `useChoresList` should be removed since the function is deleted.

### Alternatives Considered
- **Keep `useChoresList` for command palette (simple use case)**: Rejected because the spec explicitly requires removal of the deprecated export, and `allItems` provides equivalent functionality.

---

## R7 — Vitest Deprecation Warning Documentation

### Decision
Add a comment block in `vitest.config.ts` above the config export explaining the `vitest/suite` deprecation warning.

### Rationale
The warning originates from `@fast-check/vitest@0.3.0` which imports from the deprecated `vitest/suite` path. This is not fixable in project code — it requires an upstream fix in `@fast-check/vitest`. A comment prevents contributors from wasting investigation time.

### Alternatives Considered
- **Pin `@fast-check/vitest` to an older version**: Rejected because older versions may lack other fixes/features.
- **Suppress the warning in Vitest config**: Vitest does not expose a mechanism to suppress specific deprecation warnings.
