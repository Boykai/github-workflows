# Specification Analysis Report: ChoresPanel Pagination Migration

**Feature**: 057-chores-pagination-migration
**Date**: 2026-03-21
**Artifacts Analyzed**: spec.md, plan.md, tasks.md, research.md, data-model.md, contracts/, quickstart.md, constitution.md
**Codebase Cross-Reference**: solune/backend/src/models/chores.py, solune/frontend/src/hooks/useChores.ts, solune/frontend/src/components/chores/ChoresPanel.tsx

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| F1 | Inconsistency | CRITICAL | spec.md:L37, spec.md:L69, spec.md:L117 | Spec uses `"completed"` as a chore status value (US2-AS1: "30 active, 30 completed"; US4-AS1: "changes to 'completed'"; Key Entities: "e.g., active, completed") but the actual codebase enum `ChoreStatus` only defines `"active"` and `"paused"`. data-model.md, contracts/, and filter params all correctly use `"active" | "paused"`. | Update spec.md acceptance scenarios and Key Entities to use `"paused"` instead of `"completed"`. This is the only valid alternative status. |
| F2 | Inconsistency | HIGH | research.md:L55, data-model.md:L96-107, tasks.md:L24 | research.md explicitly decides AGAINST creating a `ChoresFilterParams` interface ("inline parameters are simpler and more explicit"), but data-model.md defines `ChoresFilterParams` as a new TypeScript interface, and tasks.md T001 creates it. quickstart.md shows inline params (no interface). Artifacts contradict each other on the approach. | Pick one approach and align all artifacts. Since tasks.md and data-model.md favor the interface, update research.md decision to reflect the chosen approach, or remove T001 and update data-model.md to show inline params. |
| F3 | Underspecification | HIGH | spec.md:L94 | Edge case says server errors should show "error message" with "ability to retry" but no functional requirement, acceptance scenario, or task covers error handling or retry behavior. This is identified as an edge case but has zero implementation coverage. | Either add a functional requirement (e.g., FR-013) and corresponding task for error/retry behavior, or explicitly note this is out of scope and handled by existing infrastructure (if InfiniteScrollContainer already provides retry). |
| F4 | Ambiguity | MEDIUM | spec.md:L135-137 | SC-002 ("within 2 seconds under normal conditions") and SC-004 ("within 1 second") use unmeasurable language. "Normal conditions" is undefined — no network latency, server load, or dataset size criteria are specified. | Define "normal conditions" (e.g., "local development with <1000 chores, <100ms network latency") or reclassify as aspirational targets rather than measurable criteria. |
| F5 | Underspecification | MEDIUM | spec.md:L92 | Edge case says rapid scrolling must be handled "gracefully without duplicate or out-of-order results" but no task or test validates this specific behavior. T043 covers "rapid filter toggling" but not rapid scrolling past page boundaries. | Add a test case (or explicit verification step) for rapid scrolling triggering concurrent page fetches. If InfiniteScrollContainer already handles this, reference the existing mechanism. |
| F6 | Coverage | MEDIUM | tasks.md (all phases) | No task explicitly validates NFR performance targets (SC-002: page load <2s, SC-004: filter reset <1s). All tasks are functional correctness tests. Performance is mentioned in plan.md goals but has no verification task. | Add a polish task (e.g., in Phase 8) for manual performance verification with 50+ chores, or explicitly note performance targets are aspirational and not automated-tested. |
| F7 | Inconsistency | MEDIUM | tasks.md:L183-194 | tasks.md Dependencies section states US3 depends on US2, US4 depends on US3, creating a strict sequential chain. But the constitution requires user stories to be "independently implementable and testable." Each story IS independently testable (has Independent Test criteria), but the task ordering creates implementation dependencies that could be avoided if foundational hook/API changes were complete. | Clarify that implementation dependencies are practical ordering, not logical dependencies. Each story's backend tests CAN run independently; only ChoresPanel.tsx integration requires sequential ordering. |
| F8 | Underspecification | MEDIUM | spec.md:L95, tasks.md | Edge case says chores added/deleted during browsing must be handled "gracefully" with cursor-based pagination, but no acceptance scenario, requirement, or task defines expected behavior. Does the cursor skip/include newly added items? Does deletion cause gaps? | Either add acceptance criteria for concurrent mutation behavior or note it's handled by existing cursor infrastructure (reference how other panels handle it). |
| F9 | Coverage | LOW | tasks.md:L25 | T002 ("Verify ChoresGrid.tsx already accepts pagination props") is a verification task, not an implementation task. If ChoresGrid doesn't support pagination props, there's no remediation task. | Add a contingency: "If verification fails, add a task to update ChoresGrid." Or convert to a prerequisite gate check. |

## Coverage Summary Table

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001: filter-query-params | ✅ | T003, T004, T005, T006 | Well covered with per-filter tasks |
| FR-002: sort-query-params | ✅ | T003, T007 | Sort field + direction covered |
| FR-003: filter-before-pagination | ✅ | T004, T005, T006, T007 | Implicit — filters applied in chores.py before apply_pagination() |
| FR-004: page-size-25 | ✅ | T009 | Implicit via limit:25 in hook — no dedicated task |
| FR-005: cursor-infinite-scroll | ✅ | T013, T014 | Hook swap + pagination props forwarding |
| FR-006: reset-on-filter-change | ✅ | T032, T031 | Verification + test; relies on queryKey reactivity |
| FR-007: pass-pagination-to-grid | ✅ | T014 | Single task, clear scope |
| FR-008: remove-client-side-logic | ✅ | T023, T030 | Filter useMemo + sort useMemo removal |
| FR-009: search-debouncing | ✅ | T033 | Verification that useDeferredValue is preserved |
| FR-010: combined-filters-intersection | ✅ | T019 | Dedicated combined filters test |
| FR-011: cleanup-non-paginated | ✅ | T034–T039 | Search + conditional removal + deprecation path |
| FR-012: filter-in-cache-key | ✅ | T009, T024 | Hook includes filters in queryKey + test |

## Constitution Alignment Issues

| Principle | Status | Detail |
|-----------|--------|--------|
| I. Specification-First Development | ✅ PASS | 5 prioritized user stories with Given-When-Then scenarios; edge cases identified |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates |
| III. Agent-Orchestrated Execution | ✅ PASS | Clear specify → plan → tasks → implement handoffs |
| IV. Test Optionality with Clarity | ✅ PASS | Tests explicitly requested; test tasks precede implementation (Red-Green-Refactor) |
| V. Simplicity and DRY | ✅ PASS | Reuses existing infrastructure; no premature abstractions |
| Independent User Stories | ⚠️ ADVISORY | Stories are independently testable but tasks chain US2→US3→US4→US5 sequentially. This is a practical ordering, not a logical dependency — backend tests for each story CAN run independently. See finding F7. |

## Unmapped Tasks

All 44 tasks map to at least one functional requirement or user story. No orphaned tasks.

## Codebase Cross-Reference Notes

**`useChoresList` usage (relevant to US5 cleanup):**
The non-paginated `useChoresList` hook is used in **3 locations**, not just ChoresPanel:
1. `solune/frontend/src/components/chores/ChoresPanel.tsx` (line 11, 39) — will be replaced
2. `solune/frontend/src/hooks/useCommandPalette.ts` (line 29, 124) — **active usage**
3. `solune/frontend/src/pages/ChoresPage.tsx` (line 10, 51) — **active usage**

Tasks T034–T038 correctly handle this via search-then-decide, so this is not a gap. However, the issue description's assumption ("if not used elsewhere, remove") will not hold — `useChoresList` IS used elsewhere and must be retained (with deprecation comment per T038).

## Metrics

| Metric | Value |
|--------|-------|
| Total Functional Requirements | 12 |
| Total User Stories | 5 |
| Total Tasks | 44 |
| Requirement Coverage | 100% (12/12 requirements have ≥1 task) |
| Ambiguity Count | 1 (F4) |
| Duplication Count | 0 |
| Inconsistency Count | 3 (F1, F2, F7) |
| Underspecification Count | 3 (F3, F5, F8) |
| Coverage Gap Count | 2 (F6, F9) |
| Critical Issues | 1 (F1) |
| High Issues | 2 (F2, F3) |
| Medium Issues | 4 (F4, F5, F6, F7) |
| Low Issues | 1 (F9) |

## Non-Functional Observation

The spec does not include a formal "Non-Functional Requirements" section, though success criteria SC-002 and SC-004 serve as implicit performance targets. The plan correctly identifies performance goals (initial load <2s, page transitions <1s). Consider adding explicit NFRs if the team wants enforceable performance contracts.

## Next Actions

### CRITICAL — Resolve Before `/speckit.implement`

1. **F1 (Status terminology)**: Update spec.md acceptance scenarios US2-AS1 and US4-AS1 to use `"paused"` instead of `"completed"`. Update the Key Entities description to list actual status values (`active`, `paused`) instead of `(e.g., active, completed)`. Run `/speckit.specify` with refinement or manually edit spec.md.

### HIGH — Strongly Recommended Before `/speckit.implement`

2. **F2 (ChoresFilterParams contradiction)**: Decide whether to use a `ChoresFilterParams` interface (per tasks.md/data-model.md) or inline params (per research.md/quickstart.md). Update the conflicting artifact(s) to match. If keeping the interface, update research.md decision text.

3. **F3 (Error/retry edge case)**: Either add an explicit task for error handling behavior, or note in the edge case that existing `InfiniteScrollContainer` error handling covers this. No new code may be needed if the infrastructure already handles errors.

### MEDIUM — Improve But Safe to Proceed

4. **F4**: Define "normal conditions" for performance criteria or accept them as aspirational.
5. **F5**: Add a rapid-scroll test or reference InfiniteScrollContainer's built-in debouncing.
6. **F6**: Add a manual performance verification step to Phase 8.
7. **F7**: Add a note in tasks.md clarifying that user story ordering is practical, not logical.

### LOW — Optional Improvement

8. **F9**: Convert T002 to a prerequisite gate check with a contingency action.

---

**Would you like me to suggest concrete remediation edits for the top 3 issues (F1, F2, F3)?** _(Edits will not be applied automatically — this analysis is read-only.)_
