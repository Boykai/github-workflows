# Specification Analysis Report: Phase 2 — Code Quality & DRY Consolidation

**Feature**: 001-code-quality-dry  
**Date**: 2026-03-22  
**Artifacts Analyzed**: spec.md, plan.md, tasks.md  
**Supporting Docs**: research.md, data-model.md, contracts/internal-api-contracts.md, constitution.md

---

## Findings Table

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| F1 | Coverage Gap | HIGH | Issue desc: "521-540", plan.md:L137 (D2), tasks.md:L59 (T007) | **board.py error site at lines 521-540 (`update_board_item_status`) is in the issue description but absent from plan.md and tasks.md.** The plan identifies 3 board.py sites as 246-260, 405-407, 408-433; the issue identifies them as 246-260, 408-432, 521-540. The plan splits the 405-433 region into two migration steps (counting as 2 of its 3 sites) while dropping the 521-540 site entirely. The actual codebase has 4 distinct catch→raise blocks in board.py (246-294, 405-407, 408-433, 521-539), meaning either the "3 in board" count should be "4" or one compound block needs explicit clarification. | Update plan.md D2 and tasks.md T007 to include the 521-540 error site. Adjust the board.py count from 3 to 4 and the total from 14 to 15; OR clarify that 405-433 is a single compound migration (restoring total to 14) and add 521-540 as the fourth site. |
| F2 | Inconsistency | HIGH | tasks.md:L42-43 (T003, T004) | **T003 and T004 are both marked `[P]` (parallel) but both modify the same function (`cached_fetch()`) in the same file (`cache.py`).** The tasks format legend defines `[P]` as "Can run in parallel (different files, no dependencies)". These tasks cannot be safely implemented in parallel — they modify the same function signature. | Remove `[P]` from T003 or T004, or mark T004 as depending on T003. See also F7 for the related "four different files" claim. |
| F3 | Underspecification | MEDIUM | spec.md:FR-001, tasks.md:T008 | **The 7 tools.py error-handling sites are not individually identified by line number** in the spec or tasks. The codebase has 12+ exception handlers in tools.py. Task T008 says "evaluate each of the 7 sites individually" but doesn't specify which 7. Research.md Task 1 provides the decision framework but doesn't enumerate the specific 7 line locations. | Add a migration mapping table to T008 or plan.md D3 listing each of the 7 tools.py sites by line number and the per-site decision (migrate vs. keep), matching data-model.md Entity 3 format. |
| F4 | Coverage Gap | MEDIUM | spec.md Edge Cases §, tasks.md | **Edge case 3 (dual-cache-key partial failure) has no explicit test coverage.** The edge case states: "The successfully cached data must not be rolled back; the failed key should follow the standard stale-fallback path." T014 implements the dual-cache migration, and T018 tests cached_fetch extensions, but neither explicitly tests the scenario where one cache key succeeds and the other fails. | Add an explicit test scenario to T018 or create a sub-item under T014 covering the partial-failure case for the composed fetch_fn. |
| F5 | Coverage Gap | MEDIUM | spec.md Edge Cases §, tasks.md | **Edge case 5 (REST returns inaccessible repository) has no explicit test.** The edge case states the resolution utility must treat this as a lookup failure. T026 tests the REST fallback path generally but doesn't cover the specific inaccessible-repo scenario. | Add an explicit test case to T026 or plan.md A4 that mocks the REST endpoint returning a repo the caller cannot access and verifies it falls through to the next step. |
| F6 | Ambiguity | MEDIUM | spec.md:L106 (FR-010) | **FR-010 mandates migrating send_message() cache reads to `cached_fetch()`, but these are cache-read-only (no set).** The plan (B6) and task (T016) both acknowledge this ambiguity and defer the decision, but the FR uses the word "MUST migrate" while the task says "evaluate at implementation time whether `cached_fetch()` with a no-op `fetch_fn` or direct `cache.get()` is more appropriate". The MUST in the FR conflicts with the evaluative language in the task. | Downgrade FR-010 from MUST to SHOULD, or clarify that the MUST applies to simplifying the pattern (not necessarily to using `cached_fetch()` specifically). |
| F7 | Inconsistency | MEDIUM | plan.md:L186, tasks.md:L212-213 | **Plan and tasks claim T003, T004, T005, T006 run in parallel across "four different files"** but T003 and T004 both target `cache.py`. The parallel opportunities list (tasks.md L186, plan.md Dependencies) should say "three different files: cache.py (sequential), service.py, main.py". | Correct the parallel claim to accurately reflect that T003→T004 are sequential within cache.py while T005 and T006 are independent. |
| F8 | Underspecification | MEDIUM | spec.md Edge Cases §, tasks.md | **Edge case 4 (concurrent error handling under load) has no test coverage.** The edge case requires `handle_service_error()` to be stateless and async-safe. No task explicitly verifies this property. | This is architecturally addressed (the function is stateless) but could benefit from a brief note in T012 or the grep audit (T029) confirming no shared mutable state. LOW priority — no code change needed. |
| F9 | Inconsistency | LOW | spec.md:L188-191, plan.md:L93-163 | **Spec Phase Parallelism labels differ from plan labels.** Spec says "Phase A (repository resolution)" while plan uses "Phase A" for the same. Both are consistent on content but the spec's parenthetical references use different numbering than the issue description's "Phase A (2.1)" notation. | No action needed — the plan's labeling is self-consistent. The issue description's "2.x" numbering is from the parent issue context, not the spec. |
| F10 | Underspecification | LOW | plan.md:L84-86, tasks.md:L84-86 | **`test_service.py` is listed as "New/extended" in plan.md but does not exist yet.** T022 references creating tests in this file. While this is expected (it's a new file to create), the plan's project structure implies it already exists alongside `test_cache.py` and `test_utils.py`. | Add "(new file)" annotation in plan.md project structure for `test_service.py` to distinguish from existing test files. |
| F11 | Duplication | LOW | spec.md:L186-191, plan.md:L157-163 | **Phase parallelism is described in both spec.md (Scope Boundaries) and plan.md (Dependencies).** Both convey the same dependency information but with slightly different phrasing. | Acceptable — the spec establishes requirements and the plan operationalises them. No action needed unless consolidation improves clarity. |
| F12 | Inconsistency | LOW | issue desc, spec.md:FR-017 | **Issue says "REST pattern in issues.py:289" while spec says "same pattern used in the existing REST-based issue-lookup implementation".** The spec uses abstract language while the issue gives a specific line number. Research.md Task 5 correctly traces this to `_add_issue_to_project_rest()` around lines 282-350. | No action needed — spec abstraction is appropriate; research.md provides the concrete reference. |

---

## Coverage Summary Table

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 (migrate 14 catch→raise patterns) | ✅ | T007, T008, T009, T010, T011 | Count may be 15 not 14 — see finding F1 |
| FR-002 (preserve client-visible behaviour) | ✅ | T007–T011 | Implicitly covered by each migration task |
| FR-003 (exclude error-returning handlers) | ✅ | T012 | Explicit verification task |
| FR-004 (verify tools.py exception types) | ✅ | T006, T008 | T006 inspects middleware; T008 applies decision |
| FR-005 (rate_limit_fallback parameter) | ✅ | T003 | |
| FR-006 (data_hash_fn parameter) | ✅ | T004 | |
| FR-007 (migrate list_projects) | ✅ | T013 | |
| FR-008 (migrate list_board_projects) | ✅ | T014 | |
| FR-009 (migrate get_board_data) | ✅ | T015 | |
| FR-010 (migrate send_message cache) | ✅ | T016 | Ambiguity: MUST vs. evaluative — see F6 |
| FR-011 (evaluate send_tasks) | ✅ | T017 | Decision pre-made: do not migrate |
| FR-012 (create _with_fallback) | ✅ | T005 | |
| FR-013 (soft-failure contract) | ✅ | T005 | |
| FR-014 (verify_fn support) | ✅ | T005 | |
| FR-015 (refactor add_issue_to_project) | ✅ | T019 | |
| FR-016 (evaluate copilot/PR operations) | ✅ | T020, T021 | Decision pre-made: do not apply |
| FR-017 (REST fallback in resolve_repository) | ✅ | T023, T024 | |
| FR-018 (REST pattern matching) | ✅ | T023 | |
| FR-019 (replace inline extraction) | ✅ | T025 | |
| FR-020 (existing tests pass) | ✅ | T001, T027 | Baseline + final verification |
| FR-021 (cached_fetch tests) | ✅ | T018 | 5 test scenarios specified |
| FR-022 (_with_fallback tests) | ✅ | T022 | 6 test scenarios specified |
| FR-023 (REST fallback test) | ✅ | T026 | |
| FR-024 (integration smoke tests) | ✅ | T030 | |
| FR-025 (grep audit) | ✅ | T029 | |

---

## Constitution Alignment Issues

**No CRITICAL violations found.** All five constitution principles are satisfied:

| # | Principle | Status | Notes |
|---|-----------|--------|-------|
| I | Specification-First Development | ✅ PASS | spec.md includes prioritised user stories (P1–P3), acceptance scenarios, clear scope boundaries |
| II | Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates |
| III | Agent-Orchestrated Execution | ✅ PASS | Clear single-responsibility phase decomposition |
| IV | Test Optionality with Clarity | ✅ PASS | Tests explicitly required by spec (FR-020–FR-025); tasks.md correctly notes "Tests are REQUIRED" |
| V | Simplicity and DRY | ✅ PASS | send_tasks() left in place (research Task 6), copilot/PR non-adoption (research Task 7), no premature abstractions |

The plan.md includes a Constitution Check section with both pre-research and post-design passes, satisfying the "Compliance Review" governance requirement.

---

## Unmapped Tasks

The following tasks do not map to a specific functional requirement but serve legitimate cross-cutting concerns:

| Task ID | Description | Justification |
|---------|-------------|---------------|
| T001 | Baseline test suite | Setup/verification — ensures clean starting state |
| T002 | Baseline lint/type checks | Setup — captures pre-existing issues |
| T028 | Run ruff + pyright | Quality gate — no new lint/type errors |
| T031 | Quickstart validation | Documentation quality — verifies examples match implementation |

These are appropriate and expected for a refactoring feature.

---

## Metrics

| Metric | Value |
|--------|-------|
| **Total Functional Requirements** | 25 (FR-001 through FR-025) |
| **Total Tasks** | 31 (T001 through T031) |
| **Coverage %** | 100% (25/25 requirements have ≥1 task) |
| **Total Findings** | 12 |
| **CRITICAL Issues** | 0 |
| **HIGH Issues** | 2 (F1: board.py site gap, F2: T003/T004 [P] conflict) |
| **MEDIUM Issues** | 6 (F3–F8) |
| **LOW Issues** | 4 (F9–F12) |
| **Ambiguity Count** | 1 (F6: FR-010 MUST vs. evaluative) |
| **Duplication Count** | 1 (F11: phase parallelism in spec + plan) |
| **User Stories** | 4 (US1–US4, all independently testable) |
| **Success Criteria** | 8 (SC-001 through SC-008) |
| **Edge Cases Specified** | 6 (4 covered by tasks, 2 with partial coverage) |

---

## Next Actions

### Before `/speckit.implement`

No CRITICAL issues exist, but **2 HIGH issues should be resolved** to prevent implementation errors:

1. **F1 (board.py coverage gap)**: Resolve the discrepancy between the issue description's 3 board.py sites (246-260, 408-432, 521-540) and the plan's 3 sites (246-260, 405-407, 408-433). The codebase has 4 distinct error sites in board.py. Update:
   - Run `/speckit.specify` with refinement to clarify whether the count is 14 or 15 total migration sites
   - OR manually edit `tasks.md` T007 to include line 521-540 and adjust the count
   - OR manually edit `plan.md` D2 to list all 4 board.py sites

2. **F2 (T003/T004 parallel conflict)**: Remove `[P]` marker from T004 and correct the "four different files" claim in both `plan.md` and `tasks.md`.

### Recommended (non-blocking)

3. **F3**: Add a migration mapping table for the 7 tools.py sites with line numbers and per-site decisions
4. **F4, F5**: Add explicit test scenarios for dual-cache-key partial failure and inaccessible-repo REST fallback
5. **F6**: Clarify FR-010 — either downgrade to SHOULD or specify that "migrate" includes the option of simplifying to direct `cache.get()`

### Safe to proceed as-is

All LOW findings (F9–F12) are documentation improvements that do not affect implementation correctness.

---

## Remediation Offer

Would you like me to suggest concrete remediation edits for the top 3 issues (F1, F2, F3)? (Edits will NOT be applied automatically — approval required before any changes.)
