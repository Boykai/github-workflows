# Specification Analysis Report

**Feature**: `001-auto-merge-pipelines` — Auto Merge: Automatically Squash-Merge Parent PRs When Pipelines Complete
**Analysis Date**: 2026-03-22
**Artifacts Analyzed**: `spec.md` (183 lines), `plan.md` (120 lines), `tasks.md` (362 lines), `constitution.md` (130 lines)
**Supporting Docs**: `data-model.md`, `research.md`, `contracts/` (3 files), `quickstart.md`

---

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| H1 | Coverage Gap | **HIGH** | tasks.md:L161-170, spec.md:L87-92 | US5 (Pipeline-Level Toggle) has 3 acceptance scenarios in spec but **zero test tasks** in tasks.md, despite the feature declaring "Tests: Included" (tasks.md:L6). All other user stories have test tasks. | Add test tasks for US5: toggle renders in pipeline config panel, setting persists independently, OR logic with project level |
| H2 | Inconsistency | **HIGH** | spec.md:L114, spec.md:L132 (FR-009), tasks.md:L129 (T037) | Edge case says "serialize DevOps agent dispatches **per project** to prevent competing invocations" but FR-009 and T037 only implement **per-pipeline** deduplication (`devops_active` per pipeline). Multiple pipelines in the same project with simultaneous CI failures could trigger competing DevOps agents. | Either promote per-project serialization to a formal FR with a task, or explicitly scope out the edge case with rationale |
| H3 | Underspecification | **HIGH** | spec.md:L125 (FR-002), data-model.md:L46-58, tasks.md:L169 (T046) | FR-002 says pipeline-level auto_merge is "persisted in the **pipeline configuration**". Data model defines `PipelineConfig` as a separate entity. But no backend task creates/modifies a `PipelineConfig` model or updates a CRUD endpoint. T046 says "persisted via existing pipeline CRUD endpoints" — this is an unvalidated assumption. | Add a task to verify/update backend pipeline CRUD endpoint to accept `auto_merge` field, or document in research.md that existing CRUD handles arbitrary config passthrough |
| M1 | Ambiguity | MEDIUM | spec.md:L157 (SC-004) | SC-004: "DevOps agent resolves at least **50% of simple CI failures**" — "simple" is undefined and unmeasurable. Examples given (flaky tests, minor conflicts) help but don't constitute a testable criterion. | Rephrase to specify failure categories: "resolves at least 50% of CI failures classified as flaky-test or merge-conflict" |
| M2 | Inconsistency | MEDIUM | data-model.md:L47, tasks.md:L32 (T003), tasks.md:L33 (T004) | `PipelineConfig` location in data-model.md is ambiguous: "pipeline.py **(or dedicated config model)**". T003 adds `auto_merge` to `PipelineState` (runtime model), T004 adds to `PipelineConfig` TypeScript interface — these are different concepts (runtime state vs. configuration template). | Clarify in data-model.md whether `PipelineConfig` is a distinct backend entity or embedded in `PipelineState`, and ensure tasks align |
| M3 | Inconsistency | MEDIUM | spec.md:L125 (FR-002), tasks.md:L48 (T008) | FR-002 says "persisted in the **pipeline configuration**" but T008 serializes `auto_merge` in `PipelineState` **metadata JSON** (runtime state). Configuration persistence ≠ runtime state serialization. | Distinguish between config persistence (user sets toggle → stored in pipeline config) and runtime state (resolved auto_merge flag set at pipeline start) in tasks |
| M4 | Constitution Tension | LOW | tasks.md:L215 (dependencies), constitution.md:L91-98 | US2 (Phase 4) explicitly depends on US1 (Phase 3) in task dependencies. Constitution says stories "MUST be independently implementable and testable" with "no hidden dependencies on other stories." The dependency is explicit and code-level (both modify `pipeline.py`), not a hidden feature-level dependency. | Acceptable — dependency is explicit and constitution targets *hidden* dependencies. Optionally add a note in tasks.md acknowledging the shared file constraint |
| M5 | Coverage Gap | MEDIUM | spec.md:L153-158 (SC-001/002/006) | Non-functional performance targets have no validation tasks: toggle < 10s (SC-001), merge < 60s after completion (SC-002), notifications < 5s (SC-006). These are measurable success criteria with no task coverage. | Add a validation task in Phase 9 to verify performance targets meet success criteria thresholds during end-to-end testing |
| M6 | Coverage Gap | MEDIUM | spec.md:L113 (edge case) | Edge case: "branch protection rules requiring reviews not satisfied by the merge bot" — spec says system "must surface a clear error message guiding the user." No task explicitly handles this error message/guidance. T019's `merge_failed` return is generic. | Add specific error handling in T019 or a sub-task for branch-protection-specific error messages |
| M7 | Coverage Gap | MEDIUM | spec.md:L159 (SC-007) | SC-007 requires "complete audit trail" for "each skipped step, merge action, and DevOps dispatch." Partially covered by T028 (sub-issue closure) and T050 (SKIPPED indicator), but no task ensures merge actions and DevOps dispatches are recorded in the pipeline tracking table or issue comments. | Add explicit audit-trail recording to T019 (merge action) and T037 (DevOps dispatch), or create a cross-cutting audit task in Phase 9 |
| L1 | Duplication | LOW | spec.md:L124 (FR-001), spec.md:L135 (FR-012) | FR-001 says setting is "persisted in the project configuration" and FR-012 says "persist the Auto Merge setting in the database." FR-012 subsumes FR-001's persistence clause. | Minor; consider removing persistence wording from FR-001 since FR-012 covers it explicitly |
| L2 | Ambiguity | LOW | tasks.md:L202 (T052) | T052: "ensure all new code follows existing patterns (error handling via `getErrorHint`, logging, type safety)" — vague scope with no checklist or acceptance criteria. | Convert to a concrete checklist or reference quickstart.md verification items |
| L3 | Underspecification | LOW | data-model.md:L109, tasks.md:L128 (T036) | `BranchRef` model is referenced in `CheckRunPR` fields and T036 but its field definitions (presumably `ref: str`, `sha: str`) are not specified in data-model.md. | Add `BranchRef` field definitions to data-model.md entity section |
| L4 | Ambiguity | LOW | spec.md:L113 | Edge case uses "clear error message" — subjective qualifier without measurable criteria. | Specify minimum content: include branch name, protection rule name, and remediation steps |
| L5 | Ambiguity | LOW | spec.md:L48 (US3) | US3 description uses "transient or simple failures" — imprecise categorization. | Replace with enumerated failure types: flaky tests, merge conflicts, timeout retries |

---

## Coverage Summary Table

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 project-level-toggle | ✅ | T001, T002, T005, T006, T007 | Fully covered |
| FR-002 pipeline-level-toggle | ⚠️ | T003, T008, T046 | Backend config persistence gap (see H3) |
| FR-003 effective-flag-resolution | ✅ | T017, T020 | OR logic at pipeline start |
| FR-004 auto-merge-label | ✅ | T021 | Single task, clear scope |
| FR-005 skip-human-agent | ✅ | T024-T029 | 3 tests + 3 implementation |
| FR-006 squash-merge-pr | ✅ | T012-T016, T019, T022 | Well-covered with multiple test paths |
| FR-007 ci-failure-devops-dispatch | ✅ | T030, T031, T036-T038 | Webhook routing + dispatch logic |
| FR-008 devops-retry-cap | ✅ | T033, T037 | Test + implementation |
| FR-009 prevent-duplicate-dispatch | ⚠️ | T032, T037 | Per-pipeline only; per-project serialization unaddressed (see H2) |
| FR-010 devops-repository-agent | ✅ | T035, T051 | Agent file + discovery validation |
| FR-011 retroactive-activation | ✅ | T022 | Lazy check at merge decision point |
| FR-012 db-persistence | ✅ | T001, T005, T007, T008, T017, T018 | Migration + store + tests |
| FR-013 projects-page-toggle-ui | ✅ | T040-T041, T043-T044 | Tests + implementation |
| FR-014 pipeline-config-toggle-ui | ✅ | T046 | Single task, no tests (see H1) |
| FR-015 confirmation-dialog | ✅ | T042, T045 | Test + implementation |
| FR-016 real-time-notifications | ✅ | T023, T047-T049 | Backend broadcast + frontend toast |

---

## Constitution Alignment Issues

| Principle | Status | Details |
|-----------|--------|---------|
| I. Specification-First | ✅ PASS | All required sections present; 6 stories with Given-When-Then, 16 FRs, 9 SCs |
| II. Template-Driven | ✅ PASS | All artifacts follow canonical templates |
| III. Agent-Orchestrated | ✅ PASS | Proper agent handoff chain: specify → plan → tasks |
| IV. Test Optionality | ⚠️ TENSION | Tests declared "Included" (tasks.md:L6) but US5 has zero test tasks despite 3 acceptance scenarios. All other stories have tests. See H1 |
| V. Simplicity/DRY | ✅ PASS | Reuses queue_mode patterns; Complexity Tracking section shows no violations |
| Branch Naming | ✅ PASS | `001-auto-merge-pipelines` follows `###-short-name` |
| Phase-Based Execution | ✅ PASS | Strict phase ordering maintained |
| Independent Stories | ✅ PASS (noted) | US2→US1 code-level dependency is explicit (not hidden); acceptable per constitution intent. See M4 (LOW) |
| Constitution Check | ✅ PASS | Present in plan.md with all gates passing |
| Compliance Review | ✅ PASS | plan.md includes Constitution Check section with per-principle evaluation |

---

## Unmapped Tasks

All 54 tasks map to either a user story, foundational infrastructure, or polish/validation. No orphan tasks found.

| Task Range | Mapping | Notes |
|------------|---------|-------|
| T001-T004 | Setup (shared infrastructure) | Supports FR-001, FR-002, FR-012 |
| T005-T011 | Foundational (blocking prereqs) | Supports FR-001, FR-003, FR-006, FR-012 |
| T012-T023 | US1 (P1 — auto merge on success) | 7 tests + 5 implementation |
| T024-T029 | US2 (P1 — human agent skip) | 3 tests + 3 implementation |
| T030-T039 | US3 (P2 — DevOps CI recovery) | 5 tests + 5 implementation |
| T040-T045 | US4 (P2 — project toggle UI) | 3 tests + 3 implementation |
| T046 | US5 (P3 — pipeline toggle UI) | **0 tests + 1 implementation** ⚠️ |
| T047-T049 | US6 (P3 — notifications) | 1 test + 2 implementation |
| T050-T054 | Polish & cross-cutting | Integration validation |

---

## Metrics

| Metric | Value |
|--------|-------|
| **Total Functional Requirements** | 16 |
| **Total Success Criteria** | 9 |
| **Total User Stories** | 6 |
| **Total Tasks** | 54 |
| **FR Coverage** | 16/16 = **100%** (2 with caveats: FR-002, FR-009) |
| **Story↔Task Coverage** | 6/6 = 100% |
| **Stories with Test Tasks** | 5/6 = **83%** (US5 missing) |
| **Ambiguity Count** | 5 (1 MEDIUM, 4 LOW) |
| **Duplication Count** | 1 (LOW) |
| **Underspecification Count** | 3 (1 HIGH, 1 MEDIUM, 1 LOW) |
| **Inconsistency Count** | 3 (1 HIGH, 2 MEDIUM) |
| **Coverage Gaps** | 4 (3 MEDIUM, 1 HIGH) |
| **Constitution Tensions** | 1 (LOW — acknowledged and accepted) |
| **Critical Issues** | **0** |
| **High Issues** | **3** |
| **Medium Issues** | **6** |
| **Low Issues** | **6** |

---

## Next Actions

**Overall Assessment**: The artifacts are well-structured with strong cross-referencing and 100% FR-to-task coverage. No CRITICAL issues were found. The 3 HIGH issues are addressable without rearchitecting and should be resolved before `/speckit.implement`.

### Recommended Before Implementation

1. **Resolve H1** (US5 missing tests): Run `/speckit.tasks` with refinement to add 2-3 test tasks for US5 acceptance scenarios, or explicitly declare US5 as exempt from tests with justification in tasks.md.

2. **Resolve H2** (per-project DevOps serialization): Either:
   - Add FR-017 for per-project DevOps dispatch serialization and a corresponding task in Phase 5, **or**
   - Explicitly scope out the edge case in spec.md with rationale (e.g., "V1 handles per-pipeline dedup only; per-project serialization is a future enhancement").

3. **Resolve H3** (pipeline-level backend persistence): Add a task in Phase 2 or Phase 7 to verify/update the backend pipeline CRUD endpoint accepts `auto_merge` field and persists it. Alternatively, document in research.md that the existing CRUD handles arbitrary config passthrough.

### Suggested Improvements (Non-Blocking)

4. **M1**: Refine SC-004 measurability — specify failure categories instead of "simple."
5. **M2/M3**: Clarify PipelineConfig vs PipelineState storage distinction in data-model.md.
6. **M5**: Add a performance validation task in Phase 9 for SC-001/SC-002/SC-006 thresholds.
7. **M6/M7**: Strengthen error messaging and audit trail tasks for branch protection edge case and SC-007.

### Proceed If

All 3 HIGH issues are resolved → safe to run `/speckit.implement`. The MEDIUM and LOW issues can be addressed during implementation or in a subsequent polish pass.

---

## Remediation

Would you like me to suggest concrete remediation edits for the top 3 HIGH issues? (Edits will **not** be applied automatically — read-only analysis only.)
