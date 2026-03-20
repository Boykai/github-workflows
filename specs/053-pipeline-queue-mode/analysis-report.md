# Specification Analysis Report

**Feature**: 053-pipeline-queue-mode — Pipeline Queue Mode Toggle  
**Analyzed**: 2026-03-20  
**Artifacts**: spec.md, plan.md, tasks.md  
**Constitution**: .specify/memory/constitution.md (v1.0.0)

---

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| C1 | Coverage Gap | CRITICAL | tasks.md:T009, pipeline_state_store.py:L203-231 | T009 adds `queued: bool = False` to `PipelineState` dataclass but does not mention updating `_pipeline_state_to_row()` (L203) or `_row_to_pipeline_state()` (L134) in `pipeline_state_store.py`. Without serialization updates, the `queued` field will be lost on server restart — SQLite persistence will not round-trip the field. | Add a sub-task to T009 (or a new task) to update `_pipeline_state_to_row()` metadata dict and `_row_to_pipeline_state()` to include the `queued` field in the JSON metadata blob. |
| I1 | Inconsistency | HIGH | tasks.md:T011, spec.md:FR-004, plan.md | T011 says "add `queue_mode` to `PipelineStateInfo`" but `queue_mode` is a project setting, not a pipeline state. The correct field is `queued: boolean` (matching the backend `PipelineState.queued` flag from T009). The IssueCard badge (T013) needs `queued` from `PipelineStateInfo`, not `queue_mode`. | Change T011 to add `queued: boolean` to `PipelineStateInfo` (not `queue_mode`). Keep `queue_mode` additions for `ProjectBoardConfig`, `ProjectSettingsUpdate`, and `ProjectSpecificSettings` only. |
| I2 | Inconsistency | HIGH | plan.md, tasks.md:T012 | Plan and tasks reference a "`ToolbarButton`-style pill" pattern for the toggle, but the codebase uses standard `<Button variant="outline">` components (see `ProjectsPage.tsx` L191-196). No `ToolbarButton` component exists in the project. | Update T012 to reference the actual `<Button>` component pattern from the existing toolbar. Use `variant="outline"` or `variant="ghost"` matching existing toolbar buttons. |
| U1 | Underspecification | HIGH | plan.md, tasks.md:T006 | Plan says `is_queue_mode_enabled()` should use "short-TTL BoundedDict cache" but `settings_store.py` has no existing BoundedDict usage — it uses direct SQLite queries. Introducing BoundedDict here creates a new caching pattern inconsistent with the file. No TTL value is specified. | Either (a) use direct SQLite read like existing settings functions (simpler, consistent), or (b) specify the exact TTL value and document why BoundedDict is needed despite the file not using it. Option (a) recommended per Principle V (Simplicity). |
| U2 | Underspecification | HIGH | spec.md:FR-006, tasks.md:T014, plan.md | FR-006 requires "toast notification with queue position #N" and T014 says to show it "when response message indicates 'queued.'" However, no task defines how the backend computes and returns queue position. The `WorkflowResult` response (pipelines.py L404-415) has no `queue_position` field. The frontend cannot display a position it never receives. | Add a response field (e.g., `queue_position: int | None`) to `WorkflowResult` and compute it in T007's queue gate logic by counting queued pipelines for the project. Update T011 to add the field to the frontend response type. |
| I3 | Inconsistency | MEDIUM | plan.md, tasks.md:T007 | T007 says to insert the queue gate "between `set_pipeline_state` (L350) and `assign_agent_for_status` (L363)" but lines 351-361 contain status auto-advancement logic (skip-to-next-status when no agents are configured). The queue gate must also skip this auto-advancement, or the queued pipeline's status will be incorrectly advanced. | Clarify that the queue gate should be inserted BEFORE the status auto-advancement block (after L350, before L352), ensuring both status advancement and agent assignment are skipped for queued pipelines. |
| U3 | Underspecification | MEDIUM | tasks.md:T005 | T005 defines `count_active_pipelines_for_project()` but doesn't specify what "active" means. Does "active" include queued pipelines? For the gate logic in T007, "active" should mean "running with an assigned agent" (i.e., `not queued`). If "active" includes queued pipelines, the count will be wrong. | Define "active" as pipelines where `queued == False` (i.e., pipelines that have an assigned agent and are currently executing). Add this clarification to T005. |
| C2 | Coverage Gap | MEDIUM | spec.md:FR-009, tasks.md | FR-009 states "Toggling Queue Mode OFF MUST NOT affect currently queued or active pipelines; they remain in their current state." No task explicitly implements or tests this behavior. The gate check in T007 implicitly handles future launches (by checking `is_queue_mode_enabled()`), but existing queued pipelines' state is not addressed. | Add a test case in T015 verifying that toggling OFF does not auto-start queued pipelines and does not change their `queued` state. |
| C3 | Coverage Gap | MEDIUM | spec.md:FR-008, tasks.md:T013 | FR-008 requires "remove the 'Queued' badge when pipeline transitions from queued to active." T013 adds the badge but does not explicitly address badge removal logic. The badge should automatically disappear when `queued` becomes `false`, but this needs to be reactive (re-render on state change). | Clarify in T013 that the badge is conditionally rendered based on `pipelineState.queued === true`, so it naturally disappears when the pipeline becomes active. Add a test case for badge removal. |
| I4 | Inconsistency | MEDIUM | tasks.md:T008, T010 | T008 says dequeue happens in `_transition_after_pipeline_complete()` after `remove_pipeline_state()` (L1928). T010 says add dequeue trigger in `check_in_review_issues()`. However, `check_in_review_issues()` (L2172) transitions issues to "Done" — it doesn't detect the "In Review" arrival. The "In Review" slot-release trigger needs to fire when a pipeline's status first reaches "In Review", not when a review completes. | Clarify the exact dequeue trigger points: (a) in `_transition_after_pipeline_complete()` when status changes TO "In Review" (slot release), and (b) in `_transition_after_pipeline_complete()` when status changes TO "Done/Closed" (slot release). `check_in_review_issues()` may not be the right insertion point for the "In Review" trigger. |
| A1 | Ambiguity | MEDIUM | spec.md:SC-003 | SC-003 says "Queued pipelines automatically start within 30 seconds of the active pipeline's parent issue reaching 'In Review' or 'Done/Closed.'" The 30-second window is tied to the polling interval, but no task validates this timing. If the polling interval is >30 seconds, this criterion will fail. | Add a note in plan.md confirming the polling interval is ≤30 seconds, or add a test case in T015 to verify dequeue latency. |
| U4 | Underspecification | MEDIUM | plan.md, tasks.md:T010 | T010 says "Add dequeue trigger in `check_in_review_issues()` and done-detection in the polling loop" but provides no details about the "done-detection" component. What function handles done-detection in the polling loop? How does it differ from the dequeue in T008? | Specify the exact function and line number for done-detection. If it's the same as `_transition_after_pipeline_complete()`, clarify that T008 and T010 share the same insertion point, and T010 only adds the "In Review" path. |
| D1 | Duplication | LOW | tasks.md:T008, T010 | T008 (dequeue on completion) and T010 (dequeue trigger for In Review/Done paths) overlap significantly. Both modify the same file (`copilot_polling/pipeline.py`) and both implement dequeue logic. T010 could be merged into T008 as sub-steps. | Consider merging T008 and T010 into a single task with two sub-steps: (a) dequeue after `remove_pipeline_state()` for Done/Closed path, (b) dequeue on "In Review" status arrival. |
| I5 | Inconsistency | LOW | plan.md, tasks.md | Plan says "queue_mode INTEGER NOT NULL DEFAULT 0" but `ProjectBoardConfig` uses `queue_mode: bool = False`. SQLite stores integers (0/1), Python model uses bool. This is standard SQLite/Python mapping but should be explicitly noted to avoid confusion during implementation. | Add a note in plan.md that SQLite `INTEGER 0/1` maps to Python `bool` via Pydantic coercion. No code change needed. |
| A2 | Ambiguity | LOW | spec.md (Edge Cases) | Edge case says "If neither [In Review nor Done] status is reached, the queue remains blocked." This is a known limitation but no monitoring or alerting is mentioned. A stalled pipeline could block the queue indefinitely. | Consider adding a note about potential future timeout-based release as an enhancement. No action needed for initial release (explicitly out of scope). |
| U5 | Underspecification | LOW | tasks.md:T017 | T017 says "Frontend tests — test toggle renders, toggles `queue_mode` in settings, 'Queued' badge visibility, launch toast message" but doesn't specify which test file(s) to create or which test framework patterns to follow. | Specify test file paths (e.g., `solune/frontend/src/pages/__tests__/ProjectsPage.test.tsx` for toggle, `solune/frontend/src/components/board/__tests__/IssueCard.test.tsx` for badge). |

---

## Coverage Summary

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 (per-project toggle in toolbar) | ✅ | T001, T002, T003, T004, T011, T012 | Full coverage |
| FR-002 (only one pipeline at a time) | ✅ | T005, T006, T007 | `count_active_pipelines` needs "active" definition (U3) |
| FR-003 (queued in Backlog, no agent) | ✅ | T007, T009 | |
| FR-004 (queued badge on issue card) | ✅ | T009, T013 | `PipelineStateInfo` field naming issue (I1) |
| FR-005 (auto-dequeue on In Review/Done) | ✅ | T008, T010 | Dequeue trigger points need clarification (I4) |
| FR-006 (toast with queue position) | ⚠️ Partial | T014 | No backend response field for position (U2) |
| FR-007 (default OFF) | ✅ | T001 | `DEFAULT 0` in migration |
| FR-008 (remove badge when active) | ⚠️ Partial | T013 | Badge removal not explicitly addressed (C3) |
| FR-009 (toggle OFF doesn't affect queued) | ❌ | — | No task addresses this behavior (C2) |
| FR-010 (tooltip on toggle) | ✅ | T012 | |
| FR-011 (per-project scope) | ✅ | T001, T002 | |

### Success Criteria Coverage

| Criterion | Has Task? | Task IDs | Notes |
|-----------|-----------|----------|-------|
| SC-001 (toggle <2 seconds) | ⚠️ Implicit | T012 | No explicit performance validation task |
| SC-002 (only one agent per project) | ✅ | T007, T015 | |
| SC-003 (auto-start within 30 seconds) | ⚠️ Implicit | T008, T010 | No timing validation; depends on polling interval (A1) |
| SC-004 (100% badge accuracy) | ✅ | T013, T017 | |
| SC-005 (no regressions when OFF) | ✅ | T015 | |
| SC-006 (accurate queue position) | ⚠️ Partial | T014 | Backend must compute and return position (U2) |
| SC-007 (persistence reliability) | ✅ | T001, T003, T004 | |

### Edge Case Coverage

| Edge Case | Has Task? | Notes |
|-----------|-----------|-------|
| Toggle OFF while pipelines queued | ❌ | FR-009 not covered (C2) |
| Active pipeline stalls indefinitely | ✅ | Out of scope per spec (acknowledged) |
| Race condition on simultaneous dequeue | ⚠️ Implicit | No explicit test but single-threaded model assumed |
| Queued pipeline's issue deleted/moved | ⚠️ Implicit | Relies on existing lifecycle handling |
| Single pipeline with queue ON | ⚠️ Implicit | T007 gate logic handles (active count = 0 → start immediately) |
| Queue enabled with no pipelines | ⚠️ Implicit | T001 persists setting; no pipelines affected |

---

## Constitution Alignment

### Principle I: Specification-First Development ✅ PASS

- ✅ Feature began with spec.md containing 5 prioritized user stories (P1–P2)
- ✅ Given-When-Then acceptance scenarios for all 5 stories (15 scenarios total)
- ✅ Clear scope boundaries (timeout-based release explicitly out of scope)
- ✅ Independent testing criteria for each story
- ✅ 6 edge cases documented

### Principle II: Template-Driven Workflow ✅ PASS

- ✅ spec.md follows spec-template.md structure
- ✅ plan.md follows plan-template.md structure
- ✅ tasks.md follows tasks-template.md structure
- ✅ No unjustified custom sections

### Principle III: Agent-Orchestrated Execution ✅ PASS

- ✅ Clear phase ordering: specify → plan → tasks → implement
- ✅ Single-responsibility phases with explicit handoffs
- ✅ Tasks organized by phase with clear dependencies

### Principle IV: Test Optionality with Clarity ✅ PASS

- ✅ Tests are explicitly requested in the parent issue specification
- ✅ Test tasks (T015-T017) are grouped in a dedicated phase
- ✅ Unit, integration, and frontend tests are specified
- ⚠️ Test tasks could be more granular (T015 covers multiple scenarios in one task)

### Principle V: Simplicity and DRY ✅ PASS

- ✅ Extends existing `project_settings` table — no new tables
- ✅ Extends existing `PipelineState` dataclass — no new data structures
- ⚠️ Plan proposes BoundedDict cache in settings_store.py (new pattern for this file) — potential simplicity concern (U1)
- ✅ Uses existing UI component patterns
- ✅ No premature abstraction

**Constitution Alignment Issues**: None critical. One MEDIUM concern about introducing BoundedDict to settings_store.py (U1) which may conflict with Principle V's "favor simplicity" guidance — direct SQLite read would be simpler and consistent with existing file patterns.

---

## Unmapped Tasks

All tasks (T001–T017) map to at least one requirement or user story. No orphan tasks found.

| Category | Task IDs | Purpose |
|----------|----------|---------|
| Data Model (FR-001, FR-007, FR-011) | T001–T004 | Foundation for queue mode setting |
| Queue Logic (FR-002, FR-003, FR-005) | T005–T010 | Core queue enforcement and dequeue |
| Frontend (FR-001, FR-004, FR-006, FR-010) | T011–T014 | UI toggle, badge, and toast |
| Tests (all FRs) | T015–T017 | Verification |

---

## Metrics

| Metric | Value |
|--------|-------|
| Total Functional Requirements | 11 |
| Total Success Criteria | 7 |
| Total Edge Cases | 6 |
| Total Tasks | 17 |
| Requirements with ≥1 Task | 9/11 (82%) |
| Requirements with Full Coverage | 7/11 (64%) |
| Success Criteria with ≥1 Task | 4/7 (57%) |
| Edge Cases with ≥1 Task | 0/6 (0%) |
| Ambiguity Count | 2 (A1, A2) |
| Duplication Count | 1 (D1) |
| Inconsistency Count | 5 (I1, I2, I3, I4, I5) |
| Underspecification Count | 5 (U1, U2, U3, U4, U5) |
| Coverage Gap Count | 3 (C1, C2, C3) |
| Critical Issues | 1 (C1) |
| High Issues | 4 (I1, I2, U1, U2) |
| Medium Issues | 6 (I3, U3, C2, C3, I4, A1) |
| Low Issues | 5 (D1, I5, A2, U4, U5) |

---

## Next Actions

### One CRITICAL issue and four HIGH issues should be resolved before `/speckit.implement`.

**CRITICAL priority (must resolve):**

1. **C1** — `PipelineState.queued` field persistence: T009 must include updating `_pipeline_state_to_row()` and `_row_to_pipeline_state()` in `pipeline_state_store.py` to serialize/deserialize the `queued` field in the JSON metadata blob. Without this, queued state is lost on server restart.

**HIGH priority (resolve before implementation):**

2. **I1** — Fix `PipelineStateInfo` field naming: T011 should add `queued: boolean` (not `queue_mode`) to `PipelineStateInfo`. The `queue_mode` field belongs only in `ProjectBoardConfig`, `ProjectSettingsUpdate`, and `ProjectSpecificSettings`.
3. **I2** — Fix `ToolbarButton` reference: T012 should reference the actual `<Button>` component pattern from `ProjectsPage.tsx`, not a non-existent `ToolbarButton` component.
4. **U1** — Simplify `is_queue_mode_enabled()` caching: Use direct SQLite read (consistent with existing `settings_store.py` pattern) instead of introducing BoundedDict (new pattern, per Principle V).
5. **U2** — Define queue position response: Add `queue_position` field to `WorkflowResult` and compute it in T007's queue gate. Without this, T014's toast cannot display "position #N."

**MEDIUM priority (recommended before implementation):**

6. **I3** — Clarify queue gate insertion point relative to status auto-advancement logic (L351-361).
7. **U3** — Define "active" in `count_active_pipelines_for_project()` as `queued == False`.
8. **C2** — Add test case for FR-009 (toggle OFF doesn't affect queued pipelines).
9. **C3** — Clarify badge removal is reactive (conditional render on `queued === true`).
10. **I4** — Clarify dequeue trigger points for "In Review" vs "Done" paths.
11. **A1** — Confirm polling interval ≤30 seconds for SC-003 compliance.

**LOW priority (proceed without fixing):**

12. **D1** — Consider merging T008 and T010 (both modify same file with similar logic).
13. **I5** — SQLite INTEGER ↔ Python bool mapping is standard; no action needed.
14. **A2** — Stalled pipeline queue blocking is acknowledged as out of scope.
15. **U4** — T010's "done-detection" needs clarification but is low-impact.
16. **U5** — Frontend test file paths should be specified for T017.

**Suggested commands:**

- `Manually edit tasks.md` — to fix T009 (add serialization update), T011 (fix `queued` vs `queue_mode` in `PipelineStateInfo`), T012 (fix `ToolbarButton` → `Button`), add queue position response field task
- `Run /speckit.plan with refinement` — to simplify `is_queue_mode_enabled()` caching approach and clarify dequeue trigger architecture
- `Manually edit tasks.md` — to add test cases for FR-009 (toggle OFF behavior) and FR-008 (badge removal)

---

## Remediation Offer

Would you like me to suggest concrete remediation edits for the top 5 issues (C1, I1, I2, U1, U2)? *(Edits will NOT be applied automatically — review and approval required.)*
