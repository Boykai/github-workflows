# Specification Analysis Report

**Feature**: 001-lint-suppression-audit | **Date**: 2026-03-21  
**Artifacts Analyzed**: spec.md, plan.md, tasks.md, constitution.md, research.md

---

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| E1 | Coverage Gap | HIGH | spec.md:L119 (SC-004), spec.md:L41 (US2-AS1), tasks.md:L47 (T010) | SC-004 requires ≤1 retained jsx-a11y suppression; US2 acceptance scenario 1 requires ≥4 of 5 resolved. Tasks plan only removes 3 (T035+T036) and retains 2 autofocus patterns (T010). Result: 3 resolved, 2 retained — violates both SC-004 (≤1) and US2-AS1 (≥4). | Either (a) add tasks to resolve the 2 `no-autofocus` patterns (replace with programmatic focus management), OR (b) amend SC-004 to "at most 2" and US2-AS1 to "at least 3" if autofocus is intentional UX. |
| F1 | Inconsistency | MEDIUM | spec.md:L69 (US4), research.md:L14, tasks.md:L149 | Spec US4 says "27 `# type: ignore` directives in backend tests" but research.md inventory and actual grep count both show 26. Tasks.md Phase 6 correctly uses 26. | Update spec.md US4 line 69 to say "26" to match the verified inventory. |
| B1 | Ambiguity | MEDIUM | spec.md:L103 (FR-010), spec.md:L116 (SC-001), research.md:L15 | Baseline count varies: issue title says "~111", FR-010/SC-001 say "~116", research.md actual inventory is 115, plan/tasks use 115. The 115 figure is the verified count. | Standardize on 115 across all artifacts. Update FR-010 and SC-001 from "~116" to "115". |
| B2 | Ambiguity | MEDIUM | spec.md:L121 (SC-006) | SC-006 uses "within 30 seconds" as a success criterion for understanding retained suppressions. This is subjective and cannot be validated by automated verification. | Rephrase to a measurable proxy: e.g., "Every retained suppression includes a justification comment of ≤2 sentences citing a specific technical constraint." |
| C1 | Underspecification | MEDIUM | spec.md:L94-95 (FR-001, FR-002), tasks.md | FR-001 (catalogue all suppressions) and FR-002 (classify as removable/justified) have no corresponding tasks in tasks.md. The research.md produced during the plan phase implicitly satisfies these, but there is no traceability from tasks to these requirements. | Accept research.md as pre-task deliverable for FR-001/FR-002, or add a verification task (e.g., "T000: Verify research.md baseline inventory is current before implementation"). |
| F2 | Inconsistency | MEDIUM | tasks.md:L95 (Phase 3 checkpoint) | Phase 3 checkpoint says "29 removed, 20 retained" (49 total) but detailed task-level counting across T002–T015 (justification) and T016–T034 (removal) yields ~30 removals and 19 retained. Off-by-one in checkpoint narrative. | Update checkpoint to "~30 removed, ~19 retained" or verify exact per-task instance counts. |
| C2 | Underspecification | LOW | spec.md:L136 | Scope Boundaries lists `@ts-ignore` as in-scope but the inventory has zero instances and no tasks reference it. | Add a note to research.md confirming zero `@ts-ignore` instances found, or remove `@ts-ignore` from the scope listing if not applicable. |
| A1 | Duplication | LOW | spec.md:L103 (FR-010), spec.md:L116 (SC-001) | FR-010 and SC-001 both state the 50% reduction target with nearly identical wording. Similarly, FR-005/SC-003 and FR-006/SC-005 overlap. | Acceptable — FRs define requirements, SCs define measurable validation. No action needed. |

---

## Coverage Summary Table

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 (catalogue-all-suppressions) | Partial | — | Satisfied by research.md (pre-task); no explicit task |
| FR-002 (classify-removable-or-justified) | Partial | — | Satisfied by research.md (pre-task); no explicit task |
| FR-003 (resolve-removable-by-fixing-code) | ✅ | T016–T034, T035–T041, T042–T047, T048–T052 | Full coverage across all 4 user stories |
| FR-004 (justified-require-inline-comment) | ✅ | T002–T015, T053–T056 | Phase 2 + US4 retained justifications |
| FR-005 (pass-existing-linters) | ✅ | T057, T058 | Phase 7 verification tasks |
| FR-006 (pass-existing-tests) | ✅ | T057, T058 | Phase 7 verification tasks |
| FR-007 (frontend-a11y-semantic-elements) | ✅ | T035, T036 | 3 backdrop-dismiss patterns resolved |
| FR-008 (init-py-use-all-declarations) | ✅ | T046, T047 | 2 __init__.py files updated |
| FR-009 (b008-global-config) | ✅ | T001 | B008 added to global ignore in pyproject.toml |
| FR-010 (reduce-50-percent) | ✅ | T059 | Verified via suppression count in Phase 7 |
| FR-011 (no-behavioral-changes) | ✅ | T057, T058, T061 | Implicit — verified through test/lint passes |
| SC-001 (count-reduced-50-percent) | ✅ | T059 | Count verification task |
| SC-002 (retained-have-justification) | ✅ | T060 | Scan verification task |
| SC-003 (zero-new-errors) | ✅ | T057, T058 | Linter/type-checker verification |
| SC-004 (jsx-a11y-resolved) | ⚠️ | T035, T036 | **Gap**: Only 3 of 5 resolved; 2 retained (autofocus) — SC-004 requires ≤1 retained |
| SC-005 (all-tests-pass) | ✅ | T057, T058 | Full test suite verification |
| SC-006 (retained-understandable-30s) | ✅ | T060 | Subjective criterion — see finding B2 |

---

## Constitution Alignment Issues

**No violations detected.** All five constitution principles pass:

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Specification-First | ✅ PASS | spec.md has 4 prioritized user stories with Given-When-Then acceptance scenarios |
| II. Template-Driven | ✅ PASS | All artifacts follow canonical templates; additional sections (Assumptions, Scope Boundaries) are documented |
| III. Agent-Orchestrated | ✅ PASS | Clear specify → plan → tasks → implement pipeline |
| IV. Test Optionality | ✅ PASS | Explicitly noted: no new tests — verification via existing linters/suites |
| V. Simplicity & DRY | ✅ PASS | Each fix is the simplest correct resolution; no new abstractions |

plan.md includes a Constitution Check section as required. No complexity justifications needed.

---

## Unmapped Tasks

**None.** All 61 tasks (T001–T061) map to at least one functional requirement or success criterion.

| Phase | Tasks | Mapped To |
|-------|-------|-----------|
| Phase 1 (Setup) | T001 | FR-009 |
| Phase 2 (Foundational) | T002–T015 | FR-004 |
| Phase 3 (US1) | T016–T034 | FR-003 |
| Phase 4 (US2) | T035–T041 | FR-003, FR-007 |
| Phase 5 (US3) | T042–T047 | FR-003, FR-008, FR-009 |
| Phase 6 (US4) | T048–T056 | FR-003, FR-004 |
| Phase 7 (Polish) | T057–T061 | FR-005, FR-006, FR-010, FR-011, SC-001–SC-006 |

---

## Metrics

| Metric | Value |
|--------|-------|
| Total Functional Requirements | 11 |
| Total Success Criteria | 6 |
| Total Requirements (FR + SC) | 17 |
| Total Tasks | 61 |
| Total User Stories | 4 |
| Coverage % (requirements with ≥1 task) | 88% (15 of 17) |
| Partial Coverage (pre-task satisfied) | 2 (FR-001, FR-002 — research.md) |
| Insufficient Coverage | 1 (SC-004 — jsx-a11y gap) |
| Ambiguity Count | 2 |
| Duplication Count | 1 (acceptable) |
| Underspecification Count | 2 |
| Inconsistency Count | 2 |
| Critical Issues | 0 |
| High Issues | 1 (E1 — jsx-a11y coverage gap) |
| Medium Issues | 5 |
| Low Issues | 2 |

---

## Next Actions

### ⚠️ HIGH Issue — Resolve Before `/speckit.implement`

**E1 (jsx-a11y coverage gap)** must be resolved before implementation begins. Two options:

1. **Option A — Add resolution tasks**: Add tasks to resolve the 2 `jsx-a11y/no-autofocus` suppressions in `AddAgentPopover.tsx` and `AddChoreModal.tsx` by replacing `autoFocus` with programmatic focus management (e.g., `useEffect` + `ref.focus()`). This aligns with US2 acceptance scenario 1 ("autofocus patterns with proper focus management"). Update T010 from "retain with justification" to "resolve with programmatic focus".

2. **Option B — Amend spec targets**: If autofocus is intentional UX and should be retained, update:
   - SC-004: Change "at most 1" to "at most 2"
   - US2 acceptance scenario 1: Change "at least 4" to "at least 3"
   - Add explicit justification in spec.md explaining why autofocus suppressions are acceptable

   Run: `/speckit.specify` with refinement to update SC-004 and US2-AS1.

### MEDIUM Issues — Proceed with Caution

These do not block implementation but should be addressed for consistency:

- **F1**: Update spec.md US4 to say "26" instead of "27" (verified count)
- **B1**: Standardize baseline count to 115 across spec.md FR-010 and SC-001
- **B2**: Consider rephrasing SC-006 to a measurable proxy
- **C1**: Accept research.md as pre-task deliverable for FR-001/FR-002
- **F2**: Reconcile Phase 3 checkpoint arithmetic (29 vs ~30 removals)

### LOW Issues — No Action Required

- **C2**: Zero `@ts-ignore` instances is a non-issue
- **A1**: FR/SC overlap is expected pattern

---

## Remediation Summary

Would you like me to suggest concrete remediation edits for the top issues? Specifically:

1. **E1**: Exact task additions or spec amendments for the jsx-a11y gap
2. **F1 + B1**: Line-level edits to fix count inconsistencies in spec.md
3. **B2**: Alternative wording for SC-006

*(Do NOT apply them automatically — user must explicitly approve before any edits are made.)*
