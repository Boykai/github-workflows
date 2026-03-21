# Specification Analysis Report: Performance Review

**Feature Branch**: `056-performance-review`
**Date**: 2026-03-21
**Status**: Complete
**Artifacts Analyzed**: spec.md, plan.md, tasks.md, research.md, data-model.md, contracts/refresh-policy.md, constitution.md

---

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| I1 | Inconsistency | HIGH | tasks.md:T024, plan.md:L89 | T024 references `solune/frontend/src/components/agents/AddAgentPopover.tsx` but the file is at `solune/frontend/src/components/board/AddAgentPopover.tsx`. plan.md correctly places it under `components/board/`. | Fix the path in tasks.md T024 to `solune/frontend/src/components/board/AddAgentPopover.tsx`. |
| I2 | Inconsistency | HIGH | tasks.md:T005,T040, spec.md:L6 | T005 and Phase 2 header reference "Spec 022" (`solune/specs/022-api-rate-limit-protection/spec.md`). This file does not exist in the repository. The audit tasks cannot be verified against a non-existent artifact. | Clarify whether Spec 022 exists elsewhere (another branch, merged/deleted) or replace with the actual verification source (e.g., research.md R1 findings or codebase inspection). |
| A1 | Ambiguity | HIGH | tasks.md:T026 | T026 says "Stabilize `onResizeStart` callback using `useCallback`" but `onResizeStart` in `ChatPopup.tsx` is ALREADY wrapped in `useCallback`. The actual issue is the `[size]` dependency that causes re-creation on every resize. | Rewrite T026 to: "Remove `size` dependency from `onResizeStart` `useCallback` in ChatPopup.tsx by capturing initial size via ref — prevent callback recreation on every resize." |
| A2 | Ambiguity | HIGH | tasks.md:T022 | T022 says "Stabilize `onCardClick` callback prop...using `useCallback`" but `handleCardClick` in `ProjectsPage.tsx` (L125) is ALREADY wrapped in `useCallback` with `[]` dependencies and passed to `BoardColumn` as `onCardClick`. | Verify whether T022 is still needed. If `handleCardClick` is already stable, T022 may be unnecessary or should target a different unstable prop (e.g., `availableAgents` array reference). |
| C1 | Coverage Gap | HIGH | spec.md:FR-007 | FR-007 ("repository resolution results are reused") has no explicit task. Research R4 concluded it's already satisfied by caching, but no audit or verification task confirms this claim. | Add a verification task in Phase 2 (e.g., "Verify repository resolution caching in `utils.py` prevents duplicate upstream calls across call sites — confirm FR-007 is satisfied"). |
| U1 | Underspecification | MEDIUM | tasks.md:T025 | T025 says "Stabilize `RateLimitContext` value in `solune/frontend/src/pages/ProjectsPage.tsx`" but the provider value is defined in `solune/frontend/src/context/RateLimitContext.tsx`. The task conflates context consumption (ProjectsPage) with value stability (RateLimitContext.tsx). | Clarify T025 to specify whether the fix is in the provider (`RateLimitContext.tsx` — memoize provider value) or consumer (`ProjectsPage.tsx` — memoize data passed to `updateRateLimit`), or both. |
| I3 | Inconsistency | MEDIUM | tasks.md:T001-T010 | Tasks in Phases 1–2 serve User Story 1 (Baselines) but lack the `[USn]` label format used in Phases 3–7. The notes section explains this ("embedded in Phases 1–2") but labeling inconsistency could confuse traceability tracking. | Add `[US1]` labels to T001–T010 for consistency, or document the labeling exception more prominently. |
| C2 | Coverage Gap | MEDIUM | spec.md:FR-009 | FR-009 ("manual refresh bypasses caches") has no explicit task. Assumed already implemented per research, but no audit task confirms current behavior matches the requirement. | Add an audit verification in Phase 2 (e.g., "Confirm manual refresh with `refresh=True` bypasses server cache and clears sub-issue caches — verify FR-009 is satisfied"). |
| U2 | Underspecification | MEDIUM | spec.md:L118-119 | Edge case "cached data expires during an active user session" specifies transparent refresh without disrupting open modals or in-progress drags, but no task addresses modal/drag interruption handling. | Either add a task to verify this behavior or explicitly mark it as out-of-scope for the first pass. |
| U3 | Underspecification | MEDIUM | spec.md:L122 | Edge case "user switches between multiple boards rapidly" specifies in-flight request cancellation, but no task addresses request cancellation on board switch. | Either add a task to verify/implement request cancellation via `AbortController` or explicitly mark it as deferred. |
| A3 | Ambiguity | LOW | spec.md:SC-005 | SC-005 says "measurable reduction in unnecessary rerenders" — "measurable" is vague without a specific threshold or profiling methodology. | Define a minimum threshold (e.g., ≥30% fewer component rerenders on representative board interaction) or specify the profiling tool (React DevTools Profiler). |
| D1 | Duplication | LOW | spec.md:FR-003, FR-004 | FR-003 ("MUST NOT send redundant API requests when data has not changed") and FR-004 ("MUST reuse cached data within validity window") describe the same caching behavior from different angles. | Consider consolidating into a single requirement, or keep both if they serve distinct verification scenarios (server-push path vs. request path). |
| I4 | Inconsistency | LOW | tasks.md:T027 | T027 says "Stabilize `onClick` and `availableAgents` props passed to `IssueCard`" — `onClick` is already stable (`useCallback` with `[]` in ProjectsPage). The actual unstable prop is likely only `availableAgents` (new array reference from `useAvailableAgents` hook on each render). | Rewrite T027 to focus specifically on `availableAgents` stabilization, or verify whether `onClick` is truly unstable via a different code path. |

---

## Coverage Summary

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 (backend baselines) | ✅ | T001, T003, T005–T008 | Covered by Phase 1 setup and Phase 2 audit |
| FR-002 (frontend baselines) | ✅ | T002, T004, T009–T010 | Covered by Phase 1 setup and Phase 2 audit |
| FR-003 (no redundant API calls) | ✅ | T011, T013 | WebSocket and cache-first verification |
| FR-004 (cache reuse within TTL) | ✅ | T013 | `get_project_items()` cache verification |
| FR-005 (sub-issue cache reuse) | ✅ | T012, T015 | Non-manual refresh reuse + test |
| FR-006 (polling safety) | ✅ | T014, T018 | Backend polling + frontend polling fallback |
| FR-007 (repo resolution reuse) | ❌ | — | Research R4 says already cached; no verification task |
| FR-008 (decouple task updates) | ✅ | T017, T018, T019 | Frontend refresh policy tasks |
| FR-009 (manual refresh bypasses) | ❌ | — | Assumed implemented; no verification task |
| FR-010 (coherent refresh policy) | ✅ | T017, T018, T019 | Refresh source coordination |
| FR-011 (reduce rerenders) | ✅ | T022–T027 | Component memoization and prop stabilization |
| FR-012 (throttle event listeners) | ✅ | T026 | ChatPopup resize handler (note: already partially done) |
| FR-013 (avoid repeated derived data) | ✅ | T023, T024, T025 | `useMemo` for computed values |
| FR-014 (extend test coverage) | ✅ | T015, T016, T020, T021 | Backend and frontend test extensions |
| FR-015 (before/after comparison) | ✅ | T033 | Measurement documentation task |

---

## Constitution Alignment Issues

No CRITICAL constitution violations found.

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | 6 prioritized user stories with Given-When-Then acceptance scenarios |
| II. Template-Driven | ✅ PASS | All artifacts follow canonical templates |
| III. Agent-Orchestrated | ✅ PASS | Clear phase handoffs between agents |
| IV. Test Optionality | ✅ PASS | Tests explicitly requested (US5, FR-014); follow implementation |
| V. Simplicity and DRY | ✅ PASS | No new abstractions, no new dependencies, deferred complexity |

---

## Unmapped Tasks

All tasks map to at least one requirement or user story. No orphan tasks found.

Phase 1–2 tasks (T001–T010) are correctly attributed to User Story 1 via the notes section, though they lack explicit `[US1]` labels (finding I3).

---

## Metrics

| Metric | Value |
|--------|-------|
| Total Requirements (FR) | 15 |
| Total Tasks | 38 |
| Coverage % (requirements with ≥1 task) | 86.7% (13/15) |
| Ambiguity Count | 3 |
| Duplication Count | 1 |
| Inconsistency Count | 4 |
| Underspecification Count | 3 |
| Coverage Gap Count | 2 |
| **Critical Issues** | **0** |
| **High Issues** | **4** |
| **Medium Issues** | **5** |
| **Low Issues** | **3** |

---

## Next Actions

No CRITICAL issues were found. The artifacts are well-structured and ready for implementation with the following recommended adjustments:

### Before `/speckit.implement` (HIGH priority)

1. **Fix path in T024**: Change `solune/frontend/src/components/agents/AddAgentPopover.tsx` → `solune/frontend/src/components/board/AddAgentPopover.tsx`.
2. **Resolve Spec 022 reference**: Clarify the status of `solune/specs/022-api-rate-limit-protection/spec.md` — either locate the correct path or replace audit references with codebase inspection criteria from research.md.
3. **Rewrite T026**: Change description from "Stabilize using `useCallback`" to "Remove `size` dependency by using ref" since `useCallback` is already in use.
4. **Validate T022**: Confirm whether `onCardClick` stabilization is still needed — code shows it is already `useCallback`-wrapped with `[]` deps. If unnecessary, remove the task or retarget to `availableAgents` prop stabilization.

### Recommended improvements (MEDIUM priority)

5. **Add FR-007 verification task**: Add an audit step in Phase 2 to confirm repository resolution caching.
6. **Add FR-009 verification task**: Add an audit step to confirm manual refresh cache-bypass behavior.
7. **Clarify T025 scope**: Specify whether the fix targets `RateLimitContext.tsx` (provider) or `ProjectsPage.tsx` (consumer).
8. **Address edge case gaps**: Either add tasks for request cancellation on board switch and cache expiry during interactions, or explicitly defer them.

### Optional improvements (LOW priority)

9. Add `[US1]` labels to Phase 1–2 tasks for traceability consistency.
10. Consider consolidating FR-003 and FR-004 into a single requirement.
11. Define a concrete threshold for SC-005 "measurable reduction."

---

## Remediation Offer

Would you like me to suggest concrete remediation edits for the top 4 HIGH-severity issues? (Edits will not be applied automatically — user must explicitly approve.)
