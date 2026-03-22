# Specification Analysis Report

**Feature**: Phase 8 Feature Enhancements — Polling, UX, Board Projection, Concurrency, Collision Fix, Undo/Redo
**Artifacts Analyzed**: `spec.md`, `plan.md`, `tasks.md`, `constitution.md`, `quickstart.md`, `contracts/*`, `data-model.md`
**Directory**: `specs/001-phase8-enhancements/`

---

## Findings Table

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| C1 | Constitution | **CRITICAL** | spec.md (entire file) | Spec.md lacks an explicit **"Out of Scope"** or **"Scope Boundaries"** section. Constitution §I mandates: *"Specifications MUST include… Clear scope boundaries and out-of-scope declarations."* The Assumptions section (L206-214) partially implies boundaries but does not meet the explicit requirement. | Add a dedicated "Scope Boundaries / Out of Scope" section to spec.md listing what this feature explicitly does NOT cover (e.g., real-time WebSocket push, backend pagination API, multi-tenant isolation, cross-project pipelines). |
| F1 | Inconsistency | **HIGH** | quickstart.md:L53, tasks.md:L154-168, contracts/undo-redo-api.yaml:L4 | quickstart.md references **"Backend soft-delete"** for US-7 Undo/Redo, but: (a) all US-7 tasks (T037-T042) are frontend-only, (b) the undo-redo-api.yaml contract header explicitly says *"Type: Frontend context + hook interfaces"*, (c) the data-model.md locates ActionHistoryEntry as *"Frontend — React context state."* The quickstart contradicts the actual design. | Update quickstart.md line 53 to remove "Backend soft-delete" reference. Replace with "Frontend UndoRedoContext + hook (session-scoped)" to match the contract and tasks. |
| F2 | Ambiguity | **HIGH** | tasks.md:L147 (T035), plan.md:L21, contracts/collision-api.yaml:L80,98-104 | T035 adds `expected_version` parameter to MCP update API but does **not specify if optional or required**. The collision-api.yaml contract shows `expected_version: int` in the Python signature (no default → required) and includes it in the JSON request body without an optional marker. If required, this is a **breaking API change** for existing clients, violating the plan constraint *"no breaking API changes"* (plan.md:L21). | Clarify in T035 and the contract that `expected_version` is **optional** with a default behavior (e.g., `expected_version: int | None = None` — skip version check if omitted). This preserves backward compatibility. |
| F3 | Inconsistency | **MEDIUM** | quickstart.md:L42-53, tasks.md:L49-116, tasks.md:L270-278 | **Tier/Phase ordering conflict across artifacts.** quickstart.md Tier 1 = {US-1, US-4} but tasks.md Phase order places US-4 at Phase 6 (after US-2 Phase 4, US-3 Phase 5). tasks.md "Incremental Delivery" (L270-278) reorders US-4 before US-2, contradicting the sequential Phase ordering within the same file. US-2 is spec priority P1 but placed after US-4 (P2) in incremental delivery. | Reconcile: either (a) reorder tasks.md phases to match the Incremental Delivery / quickstart tiers, or (b) add a note to tasks.md explaining that Phase numbers are sequential implementation order while Tier grouping is for parallel team strategy. Prefer option (b). |
| F4 | Inconsistency | **MEDIUM** | quickstart.md:L46,51 vs tasks.md:L193-196 vs plan.md:L139 | **Dependency semantics conflict.** quickstart.md uses hard "Depends on" language ("Tier 2 **Depends on** Tier 1 polling"). tasks.md says "**Benefits from** US-1 polling awareness but independently testable." plan.md asserts "no hidden cross-story dependencies." These three statements describe fundamentally different dependency models (hard → soft → none). | Standardize on "Benefits from" (soft dependency) across all artifacts if stories are truly independent. Update quickstart.md lines 46 and 51 to use "Benefits from" instead of "Depends on". |
| F5 | Coverage Gap | **MEDIUM** | spec.md:L165 (FR-009), tasks.md Phase 5 | FR-009: *"The system MUST apply filters and search queries against the full dataset, not just the currently loaded projection."* No explicit task addresses search-against-full-dataset behavior. The board projection design keeps full data in TanStack Query cache (Phase 5 goal), which implicitly supports this, but no task verifies or implements search interacting with the full cache vs. rendered DOM. | Add a task or clarify within T025 that search/filter operations query the TanStack Query cache (full dataset), not the projected/rendered subset. Alternatively, add this to T047 (integration validation). |
| F6 | Coverage Gap | **MEDIUM** | spec.md:L198 (SC-002), tasks.md:L179 (T045) | SC-002 (*"Total pipeline processing time for 3+ pipelines decreases by ≥40%"*) has **no validation task.** T045 explicitly validates SC-001, SC-003, and FR-008 but omits SC-002. | Add SC-002 to T045's validation checklist, or create a dedicated concurrency performance benchmark task. |
| F7 | Coverage Gap | **MEDIUM** | spec.md:L201 (SC-005), tasks.md Phase 10 | SC-005 (*"95% of items have pipeline state correctly recovered from labels within 30 seconds"*) has **no validation task.** Recovery accuracy and timing are not covered by any Phase 10 validation task. | Add SC-005 validation to T045 or T046 (quickstart validation may partially cover this if quickstart includes recovery verification steps). |
| F8 | Underspec | **MEDIUM** | spec.md:L151, tasks.md Phase 9 | Edge case: *"if the server state has diverged significantly, the undo should warn the user"* — no task addresses the interaction between undo and server-side state divergence caused by polling updates. The undo stack stores local snapshots, but polling may update the same entity server-side, creating a conflict when undo is applied. | Add a sub-task to T039 or T042 to detect when the entity's current server state differs from the undo snapshot and display a warning before applying the reversal. |
| F9 | Underspec | **MEDIUM** | spec.md:L149, tasks.md:L127-128 (T028) | Edge case: *"labels from an older, incompatible pipeline configuration version"* during recovery. T028 mentions "ambiguity detection" but does not explicitly address **version mismatch** handling. The recovery logic could misinterpret labels from a different pipeline schema version. | Clarify in T028 or T027 that `batch_parse_pipeline_labels()` should include a version compatibility check, skipping labels with unrecognized format and logging a version mismatch warning. |
| F10 | Duplication | **LOW** | spec.md:L163 (FR-007), spec.md:L199 (SC-003) | FR-007 and SC-003 express the same "≤2 seconds for 500+ items" constraint. This is acceptable alignment (requirement vs. success criterion), but the slight wording difference ("up to 500 items" vs. "500+ items") creates a subtle boundary ambiguity: does the 2s target apply to exactly 500, more than 500, or up to 500? | Normalize wording: FR-007 should say "500+ items" to match SC-003, or both should say "boards with up to 500 items." |
| F11 | Underspec | **LOW** | spec.md:L153-181 | Non-Functional Requirements are not separated into their own section. Performance (FR-007, FR-008), reliability, and resource efficiency requirements are embedded in Functional Requirements and Success Criteria. While covered, this makes NFR traceability harder. | Consider adding a "Non-Functional Requirements" subsection grouping performance targets (FR-007, FR-008), resource goals (SC-001 idle reduction), and reliability expectations. |
| F12 | Inconsistency | **LOW** | tasks.md:L192 vs tasks.md:L259 | tasks.md Dependencies section (L192) says "User Stories (Phase 3–9): All depend on Foundational phase completion" and "Tier 1 stories (US-1, US-4)" — but Phase 3 is US-1 and Phase 6 is US-4. Saying "Tier 1 stories" in the Dependencies section uses quickstart tier terminology, not the Phase numbering used in the rest of tasks.md. | Use consistent terminology: either "Phase 3 and Phase 6 stories" or explicitly define Tiers in tasks.md before referencing them. |

---

## Coverage Summary Table

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 (adaptive-polling-frequency) | ✅ | T010, T011, T012 | Backend activity tracking + frontend hook |
| FR-002 (tab-focus-immediate-poll) | ✅ | T013 | Tab visibility handler |
| FR-003 (exponential-backoff) | ✅ | T010, T011 | Backoff logic in hook + polling loop |
| FR-004 (concurrent-pipeline-execution) | ✅ | T015, T017 | Dispatch + concurrent execution |
| FR-005 (fault-isolation) | ✅ | T017 | try/except per pipeline |
| FR-006 (queue-mode-backward-compat) | ✅ | T015 | Queue-mode gate check |
| FR-007 (initial-board-2s-render) | ✅ | T020, T021, T022 | Projection hook + integration |
| FR-008 (scroll-batch-500ms) | ✅ | T022, T023 | Column rendering + debounce |
| **FR-009 (filter-search-full-dataset)** | **❌** | — | **No explicit task; implicitly supported by cache design** |
| FR-010 (pipeline-filter-dropdown) | ✅ | T026 | Radix UI Select component |
| FR-011 (client-side-filtering) | ✅ | T025 | Filter logic in useBoardControls |
| FR-012 (filter-persists-polling) | ✅ | T024 | Filter state in BoardFilterState |
| FR-013 (label-state-reconstruction) | ✅ | T027, T028, T029, T031 | Parse → reconstruct → orchestrate → startup wire |
| FR-014 (correct-stage-placement) | ✅ | T028, T029 | RecoveryState with confidence scoring |
| FR-015 (ambiguous-labels-warning) | ✅ | T028, T029 | Ambiguity detection + manual review flagging |
| FR-016 (no-duplicate-actions-recovered) | ✅ | T030 | recovered_at timestamp check |
| FR-017 (collision-detection-resolution) | ✅ | T033, T034 | Collision resolver + optimistic concurrency |
| FR-018 (user-priority-over-automation) | ✅ | T033 | Resolution priority in collision_resolver.py |
| FR-019 (collision-event-logging) | ✅ | T033, T036 | log_collision_event + table persistence |
| FR-020 (failed-resolution-manual-review) | ✅ | T033 | Manual review fallback in resolve_collision |
| FR-021 (undo-destructive-actions) | ✅ | T037, T039 | UndoRedoContext + action wiring |
| FR-022 (redo-undone-actions) | ✅ | T037, T038 | Context + hook convenience methods |
| FR-023 (lifo-undo-order) | ✅ | T037 | Stack data structure |
| FR-024 (new-action-clears-redo) | ✅ | T037 | pushAction clears redo stack |
| FR-025 (undo-window-expired-guidance) | ✅ | T042 | Expiry logic + notification |

---

## Constitution Alignment Issues

| Constitution Principle | Status | Finding |
|------------------------|--------|---------|
| I. Specification-First | ⚠️ **PARTIAL** | Prioritized user stories ✅, GWT acceptance scenarios ✅, **Out-of-scope declarations MISSING** (see C1) |
| II. Template-Driven | ✅ PASS | All artifacts follow canonical templates |
| III. Agent-Orchestrated | ✅ PASS | Clear phase transitions with well-defined inputs/outputs |
| IV. Test Optionality | ✅ PASS | Tests explicitly marked as optional in tasks.md |
| V. Simplicity & DRY | ✅ PASS | All changes extend existing services; only 2 new files (collision_resolver.py, UndoRedoContext.tsx) |
| Branch/Dir Naming | ✅ PASS | `001-phase8-enhancements` follows convention |
| Phase-Based Execution | ✅ PASS | Specify → Plan → Tasks completed in order |
| Independent Stories | ✅ PASS | All 7 stories independently implementable (but see F4 for dependency language inconsistency) |
| Constitution Check in plan.md | ✅ PASS | Two constitution checks present (pre-design and post-design) |
| Complexity Tracking | ✅ PASS | Present in plan.md (no violations noted) |

---

## Unmapped Tasks

**None.** All 47 tasks (T001–T047) map to at least one user story or cross-cutting concern.

---

## Metrics

| Metric | Value |
|--------|-------|
| Total Functional Requirements | 25 |
| Total Tasks | 47 |
| Requirement → Task Coverage | **96%** (24/25 requirements have ≥1 task) |
| User Stories | 7 |
| Success Criteria | 8 |
| SC with Validation Tasks | 3/8 (SC-001, SC-003 via T045; SC-004 implicit via T026 UX) |
| Ambiguity Count | 2 (F2, F10) |
| Duplication Count | 1 (F10) |
| Underspecification Count | 3 (F8, F9, F11) |
| Inconsistency Count | 4 (F1, F3, F4, F12) |
| Coverage Gap Count | 3 (F5, F6, F7) |
| **Critical Issues** | **1** (C1) |
| **High Issues** | **2** (F1, F2) |
| Medium Issues | 7 |
| Low Issues | 3 |
| **Total Findings** | **13** |

---

## Next Actions

### 🚨 Before `/speckit.implement`:

1. **Resolve C1 (CRITICAL)**: Add an explicit "Scope Boundaries / Out of Scope" section to `spec.md`. Run `/speckit.specify` with a refinement pass, or manually add the section. Constitution compliance gates implementation.

2. **Resolve F1 (HIGH)**: Update `quickstart.md` line 53 — remove "Backend soft-delete" for US-7. This is factually incorrect per the contract and task design.

3. **Resolve F2 (HIGH)**: Clarify in T035 and `contracts/collision-api.yaml` that `expected_version` is **optional** (with default `None` = skip version check). This preserves the "no breaking API changes" constraint.

### ⚠️ Recommended improvements (can proceed without, but improve quality):

4. **Address F5**: Add FR-009 coverage to T025 or T047 — explicitly verify search operates on full TanStack Query cache, not rendered projection.

5. **Address F6–F7**: Expand T045 validation to include SC-002 (pipeline concurrency benchmark) and SC-005 (recovery accuracy and timing).

6. **Address F4**: Standardize dependency language across `quickstart.md` and `tasks.md` — use "Benefits from" consistently if stories are independent.

7. **Address F8**: Add undo-polling divergence detection to T039 or T042.

### Command suggestions:
- Run `/speckit.specify` with a refinement prompt to add the Out-of-Scope section (fixes C1)
- Manually edit `quickstart.md` line 53 (fixes F1)
- Manually edit `tasks.md` T035 description to add "(optional, defaults to None for backward compatibility)" (fixes F2)
- Run `/speckit.tasks` with refinement to add FR-009 and SC-002/SC-005 validation coverage (fixes F5–F7)

---

## Remediation Offer

Would you like me to suggest concrete remediation edits for the top 3 issues (C1, F1, F2)? I will **not** apply them automatically — I will present the exact text changes for your review and approval first.
