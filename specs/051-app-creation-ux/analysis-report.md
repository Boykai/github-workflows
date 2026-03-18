# Specification Analysis Report

**Feature**: 051-app-creation-ux — Debug & Fix Apps Page — New App Creation UX
**Artifacts**: `specs/051-app-creation-ux/spec.md` | `plan.md` | `tasks.md`
**Constitution**: `.specify/memory/constitution.md` (v1.0.0)
**Analysis Date**: 2026-03-18

---

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| **F1** | Inconsistency | **HIGH** | tasks.md:L76, L242–244 | T014 is marked `[P]` (parallel) with T010, but T014 modifies `_create_app_parent_issue()` which T010 *creates*. The "Parallel Example" section explicitly shows them running simultaneously, yet T014 cannot start until T010 exists. | Remove `[P]` from T014; make it sequential after T010. Update Parallel Example to show T014 after T010 completes. |
| **F2** | Inconsistency | **HIGH** | constitution.md:L51–58; plan.md:L44–47; tasks.md:L6 | Constitution Principle IV states: *"When tests are included, they follow strict phase ordering: test tasks precede implementation tasks (Red-Green-Refactor)."* Plan and tasks place tests in Phase 10 *after* all implementation (Phases 3–9), justified as "not TDD". The constitution's statement is unconditional on TDD choice. | Either (a) justify the deviation in `plan.md` Complexity Tracking section (currently empty) per constitution §Compliance Review, or (b) restructure test phases to interleave with implementation per each user story, or (c) amend the constitution to clarify TDD is optional ordering. |
| **D1** | Duplication | **HIGH** | tasks.md:L41 (T005), L57 (T008) | T005: *"unpack (template_files, template_warnings)…append each template warning to warnings list"*. T008: *"ensure template_warnings from build_template_files() are added to the warnings[] array on the App response"*. Both describe appending template warnings in `create_app_with_new_repo()`. Only distinction is T008 adds format string `"Failed to read template file: {path}"`. | Merge T008 into T005 (add the format string there) or clarify T005 = unpack tuple only, T008 = format + append. Currently they read as the same operation. |
| **A1** | Ambiguity | **MEDIUM** | tasks.md:L59 (T009) | T009 says *"confirm whether [.specify/memory/] is intentionally excluded or should be included per R7 research decision"* — this is an unresolved decision embedded as a task. Spec assumption L25 already says *"The .specify/memory/ directory is intentionally excluded."* | Resolve ambiguity: update T009 to implement the exclusion filter per spec assumption, not to re-investigate. |
| **A2** | Ambiguity | **MEDIUM** | tasks.md:L122 (T021); spec.md:L190 (FR-021) | FR-021 says *"display the associated pipeline name"* but T021 shows displaying `associated_pipeline_id`. The App model has no pipeline name field — only the FK `associated_pipeline_id`. Displaying an ID is not the same as displaying a name. | Clarify: either (a) display the pipeline ID as-is with a label, or (b) add a lookup to fetch the pipeline display name from `pipeline_configs`, or (c) update FR-021 to say "pipeline identifier". |
| **A3** | Ambiguity | **MEDIUM** | tasks.md:L92–93 (T017) | T017 says *"query available pipeline configs from the backend API"* but doesn't specify which endpoint. A `list_pipelines` endpoint exists at `solune/backend/src/api/pipelines.py:142`, but T017 doesn't reference it. Frontend currently has zero pipeline references in `AppsPage.tsx`. | Add explicit API endpoint reference to T017 (e.g., `GET /api/projects/{id}/pipelines`) and note any needed query hook. |
| **C1** | Coverage Gap | **MEDIUM** | spec.md:L149 (edge case); tasks.md Phase 4 | Spec edge case: *"When the selected pipeline has no agent mappings defined? The parent issue is still created, but no sub-issues are generated and no polling is started. A warning is added."* No task covers this scenario. T012 assumes agent mappings exist. | Add acceptance check to T012 for empty agent mappings: skip `create_all_sub_issues()` + `ensure_polling_started()`, add warning. |
| **C2** | Underspec | **MEDIUM** | spec.md:L186–188 (FR-019); tasks.md:L152–154 (T025–T026) | FR-019 structured success toast references *"✓ Repository created / ✓ Template files committed / ✓ Pipeline started"* — these steps only apply to `new-repo` type. For `same-repo` and `external-repo`, there's no repo creation or template commit. No task addresses these variants. | Add note to T025/T026 covering non-new-repo summary variants (e.g., omit "Repository created" and "Template files committed" lines for same-repo/external-repo). |
| **C3** | Coverage Gap | **MEDIUM** | spec.md:L143 (edge case) | Spec edge case: *"What happens when a user creates a new-repo app but the repository already exists with the same name? The system should return a clear validation error before attempting creation."* No task implements proactive name-collision validation. | Add task or acceptance criterion for pre-creation repo name validation, or document that GitHub API error is the intended handling. |
| **F3** | Inconsistency | **MEDIUM** | spec.md:L19,L72; tasks.md:L92; plan.md:L6 | Terminology drift: the same concept is called *"pipeline presets"* (spec), *"pipeline configs"* (tasks), and *"pipeline configurations"* (plan). This creates confusion about whether these are the same entity. | Standardize to one term across all three artifacts — suggest *"pipeline presets"* (user-facing) and *"pipeline_configs"* (code-level) with explicit glossary entry. |
| **C4** | Underspec | **LOW** | tasks.md:L77 (T015) | T015 says *"call GitHub REST API to PATCH issue state to 'closed'"* but doesn't specify whether to use `githubkit` (existing dependency) or raw REST. The codebase already uses `githubkit` for all GitHub operations via `github_projects/issues.py`. | Reference existing `github_service` pattern from `issues.py` for consistency. |
| **C5** | Underspec | **LOW** | tasks.md:L74 (T012) | T012 references `WorkflowContext` and `PipelineState` but doesn't specify construction parameters. The reference to `execute_full_workflow()` is helpful but insufficient for implementation without reading the source. | Add parameter hints: `WorkflowContext(owner, repo, issue_number, ...)` and `PipelineState(pipeline_id, issue_number, ...)` from existing signatures. |
| **S1** | Style | **LOW** | spec.md (overall) | Constitution requires *"Clear scope boundaries and out-of-scope declarations"* (§I). Spec has Assumptions (L17–27) and Edge Cases (L142–149) but no explicit "Out of Scope" section. | Add a brief "Out of Scope" section declaring what this feature intentionally does NOT address (e.g., pipeline editing, multi-project pipeline sharing). |

---

## Coverage Summary

| Requirement Key | Has Task? | Task ID(s) | Notes |
|-----------------|-----------|------------|-------|
| FR-001 template-failure-tracking | ✅ | T004 | |
| FR-002 template-warnings-in-response | ✅ | T005, T008 | ⚠️ T005/T008 overlap (see D1) |
| FR-003 exponential-backoff-branch-poll | ✅ | T006 | |
| FR-004 parent-issue-fields-on-app | ✅ | T001, T002, T003, T011 | |
| FR-005 load-pipeline-config | ✅ | T007 | |
| FR-006 create-parent-issue | ✅ | T010 | |
| FR-007 parent-issue-title-format | ✅ | T010 | |
| FR-008 parent-issue-body-content | ✅ | T010 | |
| FR-009 parent-issue-best-effort | ✅ | T013 | |
| FR-010 create-sub-issues | ✅ | T012 | ⚠️ Missing empty-mappings case (see C1) |
| FR-011 start-polling-service | ✅ | T012 | |
| FR-012 handle-repo-types | ✅ | T014 | |
| FR-013 close-parent-issue-on-delete | ✅ | T015, T016 | |
| FR-014 pipeline-selector-dropdown | ✅ | T017, T018 | ⚠️ API endpoint unspecified (see A3) |
| FR-015 pipeline-default-none | ✅ | T017 | |
| FR-016 send-pipeline-id | ✅ | T017 | |
| FR-017 display-all-warnings | ✅ | T019 | |
| FR-018 warning-toast-style | ✅ | T019 | |
| FR-019 structured-success-toast | ✅ | T025, T026 | ⚠️ Non-new-repo variants missing (see C2) |
| FR-020 parent-issue-url-link | ✅ | T020 | |
| FR-021 display-pipeline-name | ✅ | T021 | ⚠️ Name vs ID ambiguity (see A2) |
| FR-022 app-card-badge | ✅ | T023 | |
| FR-023 backward-compatibility | ✅ | T022, T024, T037, T039 | |
| FR-024 database-migration | ✅ | T001 | |

---

## Constitution Alignment Issues

| Principle | Status | Detail |
|-----------|--------|--------|
| I. Specification-First Development | ✅ PASS | 7 prioritized stories with GWT scenarios. Missing explicit "Out of Scope" section (LOW). |
| II. Template-Driven Workflow | ✅ PASS | All required artifacts present (spec, plan, tasks, research, data-model, contracts, quickstart). |
| III. Agent-Orchestrated Execution | ✅ PASS | Clear single-responsibility agent handoffs. |
| IV. Test Optionality with Clarity | ⚠️ **DEVIATION** | Constitution states *"When tests are included, they follow strict phase ordering: test tasks precede implementation tasks."* Plan places tests in Phase 10 after all implementation. Justification provided in Constitution Check but not in Complexity Tracking as required. (see **F2**) |
| V. Simplicity and DRY | ✅ PASS | Reuses existing primitives (`create_issue`, `create_all_sub_issues`, `ensure_polling_started`). No premature abstraction. |
| Compliance Review | ⚠️ **PARTIAL** | Constitution Check section present in plan ✅. Complexity Tracking section is empty but should justify the test-ordering deviation. |

---

## Unmapped Tasks

| Task ID | Description | Mapping Status |
|---------|-------------|----------------|
| T009 | Verify `.specify/memory/` directory handling | Maps to spec Assumption L25, not a numbered FR. Valid support task. |
| T038 | Quickstart verification checklist | Verification task — validates multiple FRs. No dedicated mapping needed. |
| T039 | Backward compatibility verification | Maps to FR-023. |
| T040 | Verify app deletion closes parent issue | Maps to FR-013. |
| T027–T037 | Test tasks | Provide test coverage for corresponding FRs. |

**All tasks map to at least one requirement or verification concern. No orphan tasks.**

---

## Spec Edge Cases vs Task Coverage

| Edge Case (spec.md) | Covered? | Task(s) | Gap |
|---------------------|----------|---------|-----|
| Repo name collision | ❌ | — | No proactive validation task (C3) |
| GitHub rate limits on issue creation | ✅ | T013 | Best-effort wrapper handles API errors |
| Delete app with parent issue | ✅ | T015, T016, T040 | |
| Polling fails to start | ✅ | T013 | Best-effort wrapper |
| Existing apps without parent issue | ✅ | T022, T024, T037, T039 | |
| Pipeline with no agent mappings | ❌ | — | T012 doesn't handle empty case (C1) |
| Same-repo app with pipeline | ✅ | T014 | |

---

## Metrics

| Metric | Value |
|--------|-------|
| **Total Functional Requirements** | 24 |
| **Total Tasks** | 40 |
| **Requirements with ≥1 Task** | 24 / 24 |
| **Coverage %** | **100%** |
| **User Stories** | 7 (P1: 2, P2: 3, P3: 2) |
| **Success Criteria** | 10 |
| **Edge Cases Documented** | 7 |
| **Edge Cases with Task Coverage** | 5 / 7 (71%) |
| **Ambiguity Count** | 3 |
| **Duplication Count** | 1 |
| **Critical Issues** | 0 |
| **High Issues** | 3 |
| **Medium Issues** | 6 |
| **Low Issues** | 3 |
| **Total Findings** | **13** |

---

## Codebase Validation Summary

All 16 file paths referenced in tasks.md were verified against the actual repository:

| Validation | Result |
|------------|--------|
| All referenced source files exist | ✅ 16/16 |
| `build_template_files()` exists with `list[dict[str, str]]` return type | ✅ Confirmed |
| `create_app_with_new_repo()` exists | ✅ Confirmed |
| `delete_app()` exists | ✅ Confirmed |
| `_create_parent_issue_sub_issues()` reference pattern exists | ✅ Confirmed |
| Branch poll: `range(5)` + `sleep(1)` matches spec description | ✅ Confirmed |
| `showError(createdApp.warnings[0])` first-warning-only pattern | ✅ Confirmed |
| Migration `030` follows highest existing `029` | ✅ Correct sequence |
| `ensure_polling_started()` exported | ✅ Confirmed |
| `create_all_sub_issues()` exists | ✅ Confirmed |
| `list_pipelines` API endpoint exists | ✅ Confirmed |
| Correct repo paths (`solune/backend/`, not `apps/solune/`) | ✅ Documented in plan + tasks |

---

## Next Actions

**Overall Assessment: GOOD — Proceed with caution on HIGH issues**

The artifacts are well-structured with 100% requirement-to-task coverage. No CRITICAL issues were found. Three HIGH issues should be addressed before `/speckit.implement`:

1. **Fix T014 parallel marking (F1)** — This will cause a merge conflict or runtime error if T014 is launched before T010 creates the function. Quick fix: remove `[P]` from T014, update the parallel example.

2. **Resolve T005/T008 duplication (D1)** — Merge the tasks or sharpen their boundaries to avoid implementing the same logic twice. Quick fix: fold the format string from T008 into T005 and remove T008.

3. **Address constitution test-ordering deviation (F2)** — The safest path is to add a justification paragraph to the `Complexity Tracking` section of `plan.md` explaining why implementation-first ordering was chosen despite Principle IV. This satisfies the constitution's §Compliance Review requirement.

**MEDIUM issues** are recommended but non-blocking:
- Resolve A1 (T009 decision is already answered by spec assumption)
- Clarify A2 (pipeline name vs ID) and A3 (API endpoint reference)
- Add empty-agent-mappings handling to T012 (C1)
- Address non-new-repo toast variants (C2)
- Standardize terminology (F3)

**Suggested commands:**
- `Run /speckit.tasks` with refinements to fix D1 (merge T005/T008), F1 (remove T014 [P] marker), and add C1 coverage
- `Manually edit plan.md` Complexity Tracking section to justify test-ordering deviation (F2)
- `Run /speckit.specify` with refinement to add Out of Scope section and resolve A2 (pipeline name)

---

**Would you like me to suggest concrete remediation edits for the top 3 HIGH issues?** (Read-only analysis — no automatic modifications applied.)
