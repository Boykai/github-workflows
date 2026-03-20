# Specification Analysis Report: Optimistic UI Updates for Mutations

**Feature**: `054-optimistic-ui-updates` | **Date**: 2026-03-20 | **Analyzer**: speckit.analyze

**Artifacts Analyzed**: spec.md, plan.md, tasks.md, data-model.md, research.md, contracts/board-status-update.yaml, constitution.md v1.0.0

---

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| I1 | Inconsistency | HIGH | spec.md:L55 (US3), data-model.md:L106, plan.md:L121 | **App status terminology mismatch**: Spec US3 acceptance scenario 1 says status badge shows `"running"`, but `AppStatus` type is `'creating' \| 'active' \| 'stopped' \| 'error'` — no `"running"` value exists. Plan Phase 3 step 3.4 correctly uses `"active"`. | Update spec.md US3 acceptance scenario 1 to say `"active"` instead of `"running"` to match the actual `AppStatus` type |
| U1 | Underspecification | HIGH | tasks.md:T015 (L116), usePipelineConfig.ts:L271-285 | **Pipeline delete is not a `useMutation`**: T015 prescribes adding `onMutate`/`onError`/`onSettled` callbacks, but `usePipelineConfig.ts` uses `useCallback` + direct API call + `useReducer` dispatch — zero `useMutation` calls exist in the file. The TanStack Query optimistic pattern cannot be applied without refactoring to `useMutation` first. | Either (a) add a prerequisite task to refactor `deletePipeline` from `useCallback` to `useMutation`, or (b) exclude pipeline delete from scope (same `useReducer` rationale used to exclude pipeline save in FR-010) |
| C1 | Coverage | HIGH | spec.md:FR-008 (L116-117), tasks.md (all tasks) | **No task for `_optimistic` flag type support**: T005 and T009 insert objects with `_optimistic: true` into the cache, but `Chore` and `App` TypeScript types do not include this field. No task extends the types. This will cause TypeScript compilation errors (`npm run type-check` failure). | Add a task (or note in T005/T009) to extend `Chore` and `App` types with `_optimistic?: boolean`, or use a branded type/type assertion approach |
| C2 | Coverage | HIGH | spec.md:FR-008 (L116-117), tasks.md (all phases) | **No task for visual pending indicator rendering**: FR-008 requires optimistically created items to be "visually distinguishable." Tasks T005 and T009 add the `_optimistic: true` flag to cached data, but no task modifies the rendering components (chore list, app list) to check this flag and render with reduced opacity or a spinner. | Add a task per affected component (chore list row, app list row) to render `_optimistic: true` items with visual distinction (e.g., reduced opacity) |
| I2 | Inconsistency | MEDIUM | spec.md:SC-002 (L138), plan.md:L22, tasks.md:T004-T015 | **Mutation count inconsistency (14 vs 12)**: Spec, plan, and scope declarations all claim "14 mutations." SC-002 lists `"1 board status, 4 chore, 5 app, 1 tool delete, 1 pipeline delete, plus inline chore update and board wiring"` — but "4 chore" already includes inline chore update (double-counted). Actual mutation hooks receiving optimistic callbacks: 12 (T004–T015). The "14" count inflates by including infrastructure (API method, wiring) as separate mutations. | Clarify the count: 12 mutation hooks receive optimistic callbacks; 14 includes 2 infrastructure tasks (T002–T003). Update SC-002 parenthetical to avoid double-counting |
| I3 | Inconsistency | MEDIUM | tasks.md:L139-141 (Dependencies section) | **False dependency on Phase 1 for Phases 4/5/6**: Tasks declares Phases 4 (Chores), 5 (Apps), and 6 (Tool/Pipeline) as "Depends on Phase 1 only." Phase 1 is T001 — backend Pydantic models (`StatusUpdateRequest`/`StatusUpdateResponse`). Frontend mutation hooks have zero dependency on backend models. These phases can start immediately with no prerequisites. | Update dependency declarations: Phases 4, 5, and 6 should state "No dependencies — can start immediately" |
| C3 | Coverage | MEDIUM | spec.md:FR-008 (L116-117), tasks.md | **FR-008 rendering gap spans multiple components**: Even if type support is added (C1), the spec mandates visual distinction for creates only. The components that render chore lists and app lists need conditional styling. This is a functional requirement with zero task coverage on the rendering side. | Add explicit rendering tasks or expand T005/T009 scope to include component-level changes |
| U2 | Underspecification | MEDIUM | spec.md:L103 (Edge Case 6), research.md:R9, tasks.md | **Empty cache edge case not in any task**: Spec edge case 6 and research R9 describe the behavior when cache is empty (skip optimistic update, fall back to fire-and-wait). No task includes a guard clause or implementation note for this. It could be omitted during implementation. | Add implementation note to each mutation task: "Guard: if `getQueryData()` returns `undefined`, skip optimistic update and return early from `onMutate`" |
| I4 | Inconsistency | MEDIUM | spec.md:FR-010 (L118), tasks.md:T015 (L116), usePipelineConfig.ts | **Pipeline delete scope conflicts with exclusion rationale**: FR-010 excludes pipeline save because it "already uses a different loading-state mechanism (`useReducer`)." Pipeline delete in `usePipelineConfig.ts` also uses `useReducer` dispatch (lines 273, 276, 282). The same exclusion rationale applies to pipeline delete but it is included in scope. | Either exclude pipeline delete (consistent with FR-010 rationale) or explicitly justify why delete differs from save in the scope decision |
| A1 | Ambiguity | LOW | spec.md:FR-008 (L116-117) | **"Visually distinguishable" lacks measurable criteria**: FR-008 says optimistically created items MUST be visually distinguishable but provides no measurable definition (opacity value, animation, spinner type). Research R7 suggests "reduced opacity or a subtle spinner" but this is guidance, not a requirement. | Add measurable criteria to FR-008 (e.g., "render with 50% opacity") or move to implementation notes as a SHOULD |
| D1 | Duplication | LOW | spec.md:SC-002 (L138) | **SC-002 double-counts inline chore update**: The parenthetical `"4 chore ... plus inline chore update"` lists inline chore update as separate from the 4 chore mutations, but T005–T008 shows inline chore update IS one of the 4. | Rewrite SC-002 parenthetical: `"(1 board status, 4 chore [create/update/delete/inline-update], 5 app, 1 tool delete, 1 pipeline delete)"` |
| A2 | Ambiguity | LOW | spec.md:FR-003 (L111), research.md:R6 | **Error toast specifics unspecified**: FR-003 requires "a human-readable error message" but doesn't specify toast duration, position, or dismissibility. Research R6 shows existing pattern uses `duration: Infinity` (persistent). Consistency is implied but not stated. | Document in tasks that error toasts should follow existing `toast.error(message, { duration: Infinity })` pattern |

---

## Coverage Summary Table

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 (immediate UI update) | ✅ | T004–T015 | Covered by all 12 mutation tasks |
| FR-002 (revert on failure) | ✅ | T004–T015 | Each task includes `onError` rollback |
| FR-003 (error notification) | ✅ | T004–T015 | Each task includes error toast |
| FR-004 (reconcile with server) | ✅ | T004–T015 | Each task includes `onSettled` invalidation |
| FR-005 (board status endpoint) | ✅ | T001, T002 | Backend models + endpoint |
| FR-006 (concurrent mutations) | ⚠️ | T004–T015 | Covered by TanStack Query's natural handling (R8); no explicit task |
| FR-007 (snapshot-and-restore) | ✅ | T004–T015 | Each task snapshots before mutation |
| FR-008 (visual pending indicator) | ❌ | — | Flag insertion in T005/T009 but **no rendering task** and **no type extension** |
| FR-009 (no visual for update/delete) | ✅ | T006–T008, T010–T015 | Implicitly covered (no `_optimistic` flag added) |
| FR-010 (excluded operations) | ⚠️ | — | No explicit validation; pipeline delete conflicts with exclusion rationale |
| FR-011 (board endpoint contract) | ✅ | T001, T002 | Covered by models + endpoint + contract YAML |
| FR-012 (invalidate after settle) | ✅ | T004–T015 | Each task includes `onSettled` → `invalidateQueries` |

---

## Constitution Alignment Issues

**No CRITICAL constitution violations detected.**

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | spec.md has prioritized user stories with Given-When-Then acceptance scenarios |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates |
| III. Agent-Orchestrated Execution | ✅ PASS | Clear phase handoffs between specify → plan → tasks → analyze |
| IV. Test Optionality | ✅ PASS | Tests not mandated; existing suites validate regressions (T016–T018) |
| V. Simplicity and DRY | ✅ PASS | Uses TanStack Query built-in pattern; no new libraries or abstractions |
| Constitution Check in plan.md | ✅ PASS | Present and comprehensive (plan.md:L26–36) |
| Complexity Tracking in plan.md | ✅ PASS | Present; no violations noted (plan.md:L148–150) |

---

## Unmapped Tasks

All tasks (T001–T018) map to at least one requirement or user story. No orphan tasks detected.

---

## Metrics

| Metric | Value |
|--------|-------|
| Total Functional Requirements | 12 (FR-001 through FR-012) |
| Total Tasks | 18 (T001 through T018) |
| Mutation Tasks | 12 (T004 through T015) |
| Infrastructure Tasks | 3 (T001 through T003) |
| Validation Tasks | 3 (T016 through T018) |
| Coverage % (FRs with ≥1 task) | 83% (10/12 — FR-008 and FR-010 lack full coverage) |
| Ambiguity Count | 2 (A1, A2) |
| Duplication Count | 1 (D1) |
| Inconsistency Count | 4 (I1, I2, I3, I4) |
| Underspecification Count | 2 (U1, U2) |
| Coverage Gap Count | 3 (C1, C2, C3) |
| Critical Issues | 0 |
| High Issues | 4 (I1, U1, C1, C2) |
| Medium Issues | 5 (I2, I3, C3, U2, I4) |
| Low Issues | 3 (A1, D1, A2) |
| Total Findings | 12 |

---

## Next Actions

### Before `/speckit.implement`

The 4 HIGH-severity findings should be resolved to prevent implementation failures:

1. **I1 — App status term**: Run `/speckit.specify` with refinement to change spec.md US3 `"running"` → `"active"` (or update plan.md to match spec's intent)
2. **U1 — Pipeline delete pattern**: Decide scope: either add a refactoring prerequisite task to convert `deletePipeline` to `useMutation`, or exclude pipeline delete from scope (consistent with pipeline save exclusion in FR-010). Update tasks.md accordingly.
3. **C1 — Type extension**: Add `_optimistic?: boolean` to `Chore` and `App` types in a new task or expand T005/T009 scope. Alternatively, document the type assertion approach.
4. **C2 — Rendering task**: Add explicit tasks for component-level rendering of the `_optimistic` visual indicator, or relax FR-008 to SHOULD.

### MEDIUM findings (can proceed but recommended to address)

5. **I2**: Clarify mutation count (12 hooks vs 14 including infrastructure) in spec.md SC-002
6. **I3**: Remove false Phase 1 dependency from Phases 4/5/6 in tasks.md
7. **I4**: Resolve pipeline delete scope conflict with FR-010 exclusion rationale
8. **U2**: Add empty-cache guard note to mutation tasks
9. **C3**: Expand FR-008 rendering coverage

### Suggested commands

- `Run /speckit.specify` with refinement to fix I1 (app status terminology)
- `Run /speckit.tasks` to regenerate with fixes for U1, C1, C2, I3, U2
- Manually edit tasks.md to add `_optimistic` type extension task (C1) and rendering tasks (C2)

---

## Remediation Offer

Would you like me to suggest concrete remediation edits for the top 4 HIGH-severity issues? (Edits will NOT be applied automatically — read-only analysis only.)
