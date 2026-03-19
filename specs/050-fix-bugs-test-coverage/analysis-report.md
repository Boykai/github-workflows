# Specification Analysis Report

**Feature**: 050-fix-bugs-test-coverage — Find/Fix Bugs & Increase Test Coverage  
**Analyzed**: 2026-03-19  
**Artifacts**: spec.md, plan.md, tasks.md  
**Constitution**: .specify/memory/constitution.md (v1.0.0)

---

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| F1 | Inconsistency | HIGH | tasks.md:L65 (T016) | T016 references `solune/backend/mutants/pyproject.toml` which does not exist. The actual mutmut config (`[tool.mutmut]`, `paths_to_mutate`) is in `solune/backend/pyproject.toml` (line 128–129). No `mutants/` directory exists in the repo. | Update T016 file path to `solune/backend/pyproject.toml` |
| F2 | Inconsistency | HIGH | plan.md:L109, tasks.md:L141 (T049) | Plan project structure shows `src/utils/` (directory) but T049 references `src/utils.py` (file). Codebase has `solune/backend/src/utils.py` (a single file, not a directory). Plan has an inaccuracy. | Fix plan.md project structure to show `src/utils.py` instead of `src/utils/` |
| F3 | Underspecification | MEDIUM | spec.md:L72 (US4 AS2) | Acceptance scenario says board component coverage "increases measurably" — vague, no specific percentage target. All other acceptance scenarios have concrete thresholds. | Add a specific target (e.g., "rises above 60%") or define "measurably" as a delta (e.g., "increases by at least 10 percentage points") |
| F4 | Coverage Gap | MEDIUM | spec.md:L98 (Edge Case 1), tasks.md | Edge case specifies "a process to re-enable quarantined tests after fixes" but no task addresses creating this process. T035 quarantines tests but does not define the re-enabling workflow. Partial coverage of FR-006. | Add a task to document the quarantine-removal process (e.g., CI job or manual checklist) |
| F5 | Coverage Gap | MEDIUM | spec.md:L100 (Edge Case 3), tasks.md | Edge case requires "a documented override process for emergency hotfix merges" that bypass coverage thresholds. No task addresses this. | Add a task to document the CI bypass mechanism (e.g., a label-based override with post-merge restoration requirement) |
| F6 | Coverage Gap | MEDIUM | spec.md:L168 (SC-009), tasks.md | SC-009 requires pre-commit hooks to complete "in under 30 seconds for typical changesets" but no task includes a timing verification step. | Add a verification step to T075 that measures hook execution time and validates <30s |
| F7 | Coverage Gap | MEDIUM | spec.md:L102 (Edge Case 5), tasks.md | Edge case requires E2E failures from environment issues to be "distinguishable from genuine test failures" but no task addresses adding environment-health checks or error categorization to the E2E suite. | Add a task for E2E environment-health pre-check or failure categorization in Playwright config |
| F8 | Coverage Gap | MEDIUM | spec.md:L99 (Edge Case 2), tasks.md | Edge case requires mutation testing shards to "handle shard failures gracefully" but no task addresses shard failure recovery or timeout handling. | Add a task to verify or implement graceful shard failure handling in `run_mutmut_shard.py` |
| F9 | Inconsistency | MEDIUM | plan.md:L29, plan.md:L9 | Plan states "151+ test files" for backend (actual count: 165) and "130+ test files" for frontend (actual count: 130 unit/component + 10 E2E = 140). The issue description uses different numbers (121+ backend, 140 frontend). While plan approximations are acceptable, they drift from reality. | Update plan.md counts to reflect current actuals (165 backend, 140 frontend) or use "~" prefix to signal approximation |
| F10 | Ambiguity | MEDIUM | tasks.md:L48 (T013) | T013 requires triaging findings as "fix-now, fix-later, or false-positive" but no criteria are defined for these categories. T031–T034 depend on this triage output. | Define triage criteria (e.g., fix-now = blocks tests or CI, fix-later = cosmetic, false-positive = tool error) in T013 or in a referenced document |
| F11 | Inconsistency | LOW | plan.md:L145-146 | Plan labels Phase 1 as "(P2 — User Story 2)" and Phase 2 as "(P1 — User Story 1)". This inverts priority labels vs. phase numbers. The execution order is justified (analysis before fixes) but the labeling may confuse readers. | Add a brief note in plan.md explaining why P2 work precedes P1 in execution order, or relabel phases by execution order rather than priority |
| F12 | Duplication | LOW | tasks.md:L29,L45 (T003/T010) | T003 runs backend tests with coverage; T010 runs them with JUnit output. Both execute the full backend suite in separate phases. Could be combined with `--cov --junitxml` flags. | Consider combining into a single task with both `--cov` and `--junitxml` flags |
| F13 | Duplication | LOW | tasks.md:L30,L46 (T004/T011) | T004 runs frontend tests with coverage; T011 runs with verbose reporter. Both execute the full frontend suite. Could be combined. | Consider combining into a single task with both coverage and verbose output |
| F14 | Duplication | LOW | tasks.md:L31,L196 (T005/T070) | T005 runs baseline E2E; T070 verifies ≥14 specs post-expansion. Intentional checkpoint pattern but noted for completeness. | No action needed — intentional verification checkpoints |
| F15 | Inconsistency | LOW | tasks.md:L215 (T073) | T073 includes `ruff format` verification which is not mentioned in spec FR-023 (which requires only "lint and type-check"). However, the actual pre-commit hook already runs `ruff format`, so T073 accurately reflects reality. The spec is slightly underspecified. | Consider updating FR-023 to include formatting verification, or note that T073 exceeds FR-023 scope (acceptable since it matches existing behavior) |

---

## Coverage Summary

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 (backend lint + type-check) | ✅ | T006, T007 | |
| FR-002 (frontend lint + type-check) | ✅ | T008, T009 | |
| FR-003 (backend test results report) | ✅ | T010 | |
| FR-004 (frontend test results) | ✅ | T011 | |
| FR-005 (flaky test detection) | ✅ | T012 | |
| FR-006 (quarantine + re-enable process) | ⚠️ Partial | T035 | Quarantine covered; re-enable process not addressed (F4) |
| FR-007 (mutmut trampoline fix) | ✅ | T014, T015, T016, T017 | T016 has wrong file path (F1) |
| FR-008 (cache clearing) | ✅ | T018, T019, T020, T021 | |
| FR-009 (no async mock warnings) | ✅ | T022, T023, T024 | |
| FR-010 (pipeline transitions) | ✅ | T025, T026, T027, T028, T029 | |
| FR-011 (API route integration tests) | ✅ | T037, T038, T039, T040 | |
| FR-012 (high-risk service unit tests) | ✅ | T041, T042, T043, T044, T045, T046 | |
| FR-013 (property-based tests) | ✅ | T047, T048 | |
| FR-014 (mutation testing expansion) | ✅ | T049, T050, T051 | |
| FR-015 (characterization tests) | ✅ | T052, T053 | |
| FR-016 (App.tsx tests) | ✅ | T055 | |
| FR-017 (board component tests) | ✅ | T056, T057, T058 | |
| FR-018 (hook branch coverage) | ✅ | T059, T060, T061, T062 | |
| FR-019 (E2E expansion) | ✅ | T063, T064, T065, T066 | |
| FR-020 (frontend mutation testing) | ✅ | T067, T068 | |
| FR-021 (backend threshold ratchet) | ✅ | T071 | |
| FR-022 (frontend threshold ratchet) | ✅ | T072 | |
| FR-023 (backend pre-commit hooks) | ✅ | T073 | T073 exceeds scope with `ruff format` (F15) |
| FR-024 (frontend pre-commit hooks) | ✅ | T074 | |
| FR-025 (chaos/concurrency tests) | ✅ | T076, T077, T078 | |

### Success Criteria Coverage

| Criterion | Has Task? | Task IDs | Notes |
|-----------|-----------|----------|-------|
| SC-001 (bugs fixed) | ✅ | T030 | |
| SC-002 (backend 80%) | ✅ | T054, T079, T083 | |
| SC-003 (frontend thresholds) | ✅ | T069, T080, T084 | |
| SC-004 (zero flaky) | ✅ | T036, T085 | |
| SC-005 (mutation >60%/shard) | ✅ | T050, T088 | |
| SC-006 (Stryker thresholds) | ✅ | T067, T089 | |
| SC-007 (14 E2E specs) | ✅ | T070, T087 | |
| SC-008 (zero AsyncMock warnings) | ✅ | T024, T086 | |
| SC-009 (pre-commit <30s) | ❌ | — | No timing verification task (F6) |
| SC-010 (CI threshold enforcement) | ✅ | T079, T080 | |

### Edge Case Coverage

| Edge Case | Has Task? | Notes |
|-----------|-----------|-------|
| Quarantine re-enable process | ❌ | F4 |
| Mutation testing timeout/shard failure | ❌ | F8 |
| Emergency hotfix coverage override | ❌ | F5 |
| Pre-commit hook performance (<30s) | ❌ | F6 |
| E2E environment unavailability | ❌ | F7 |

---

## Constitution Alignment

### Principle I: Specification-First Development ✅ PASS

- ✅ Feature began with spec.md containing prioritized user stories (P1–P5)
- ✅ Given-When-Then acceptance scenarios for all 5 stories
- ✅ Clear scope boundaries (DRY refactoring explicitly excluded)
- ✅ Independent testing criteria for each story

### Principle II: Template-Driven Workflow ✅ PASS

- ✅ All artifacts follow canonical templates
- ✅ Plan, research, data-model, contracts, quickstart all present
- ✅ No unjustified custom sections

### Principle III: Agent-Orchestrated Execution ✅ PASS

- ✅ Clear phase ordering: specify → plan → tasks → implement
- ✅ Single-responsibility phases with explicit handoffs
- ✅ Tasks organized by user story for parallel implementation

### Principle IV: Test Optionality with Clarity ✅ PASS

- ✅ Tests are the primary deliverable (explicitly requested in spec)
- ✅ Test types appropriate to each target
- ✅ TDD not mandated; test-writing is the implementation work itself

### Principle V: Simplicity and DRY ✅ PASS

- ✅ No new abstractions introduced
- ✅ Uses existing tools (pytest, vitest, mutmut, stryker)
- ✅ DRY refactoring explicitly deferred
- ✅ No complexity justifications needed

**Constitution Alignment Issues**: None. All five principles are satisfied.

---

## Unmapped Tasks

All tasks (T001–T090) map to at least one requirement, user story, or verification checkpoint. No orphan tasks found.

| Category | Task IDs | Purpose |
|----------|----------|---------|
| Setup (no FR mapping — infrastructure) | T001–T005 | Environment verification — prerequisite for all FRs |
| Foundational (maps to FR-001–FR-006) | T006–T013 | Static analysis and triage — drives all subsequent work |
| Verification checkpoints | T030, T054, T069, T070, T079–T090 | Cross-cutting verification — validates multiple FRs/SCs simultaneously |

---

## Metrics

| Metric | Value |
|--------|-------|
| Total Functional Requirements | 25 |
| Total Success Criteria | 10 |
| Total Edge Cases | 5 |
| Total Tasks | 90 |
| Requirements with ≥1 Task | 25/25 (100%) |
| Requirements with Full Coverage | 24/25 (96%) |
| Success Criteria with ≥1 Task | 9/10 (90%) |
| Edge Cases with ≥1 Task | 0/5 (0%) |
| Ambiguity Count | 2 (F3, F10) |
| Duplication Count | 3 (F12, F13, F14) |
| Inconsistency Count | 5 (F1, F2, F9, F11, F15) |
| Underspecification Count | 1 (F3) |
| Coverage Gap Count | 5 (F4, F5, F6, F7, F8) |
| Critical Issues | 0 |
| High Issues | 2 (F1, F2) |
| Medium Issues | 8 (F3–F10) |
| Low Issues | 5 (F11–F15) |

---

## Next Actions

### No CRITICAL issues detected. Two HIGH issues should be resolved before `/speckit.implement`.

**HIGH priority (resolve before implementation):**

1. **F1** — Fix T016 file path: Change `solune/backend/mutants/pyproject.toml` → `solune/backend/pyproject.toml` in tasks.md. The `mutants/` directory does not exist; mutmut config (`[tool.mutmut]`, `paths_to_mutate`) lives in the main `pyproject.toml`.
2. **F2** — Fix plan.md project structure: Change `src/utils/` → `src/utils.py`. The codebase has a single `utils.py` file, not a directory.

**MEDIUM priority (recommended before implementation, not blocking):**

3. **F3** — Define a concrete coverage target for board components in spec.md US4 AS2 (replace "increases measurably").
4. **F4** — Add a task for quarantine-removal process documentation (supports FR-006 completeness).
5. **F5** — Add a task for emergency hotfix override documentation.
6. **F6** — Add timing verification to pre-commit hook testing (supports SC-009).
7. **F7–F8** — Add tasks for E2E environment-health checks and mutation shard failure handling.
8. **F10** — Define triage criteria for T013 "fix-now / fix-later / false-positive" categories.

**LOW priority (proceed without fixing):**

9. **F11** — Consider adding a note about phase vs. priority ordering in plan.md.
10. **F12–F13** — Consider combining duplicate baseline test runs (T003/T010, T004/T011).
11. **F14** — No action needed (intentional checkpoint duplication).
12. **F15** — Consider aligning FR-023 with actual pre-commit hook behavior (adds formatting).

**Suggested commands:**

- `Run /speckit.specify with refinement` — to update US4 AS2 with concrete board coverage target and add edge case coverage notes
- `Manually edit tasks.md` — to fix T016 file path (`mutants/pyproject.toml` → `pyproject.toml`)
- `Manually edit plan.md` — to fix `src/utils/` → `src/utils.py` in project structure
- `Manually edit tasks.md` — to add tasks for edge case coverage (quarantine removal, hotfix override, E2E env-health, shard failure, pre-commit timing)

---

## Remediation Offer

Would you like me to suggest concrete remediation edits for the top 5 issues (F1, F2, F3, F4, F6)? *(Edits will NOT be applied automatically — review and approval required.)*
