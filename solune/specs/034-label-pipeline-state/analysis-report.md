# Specification Analysis Report

**Feature**: 034-label-pipeline-state — GitHub Label-Based Agent Pipeline State Tracking  
**Analyzed**: 2026-03-11  
**Artifacts**: spec.md, plan.md, tasks.md, constitution.md, research.md, data-model.md, quickstart.md, contracts/

---

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| F1 | Inconsistency | CRITICAL | spec.md:L147, research.md:L63, tasks.md:T005 | **GraphQL query assumption is incorrect.** Spec assumption states "The GraphQL board query already fetches `labels(first: 20)` — no changes to the query are needed." Research R-003 states "The GraphQL query used by `get_project_items()` fetches `labels(first: 20)` — the data is in the response but ignored." **Both are factually wrong.** `GET_PROJECT_ITEMS_QUERY` (graphql.py:66-118) does NOT include labels. Only `BOARD_GET_PROJECT_ITEMS_QUERY` (graphql.py:716+) fetches labels. Task T005 assumes labels exist in the response but they don't for the polling/task path. | Add a task to extend `GET_PROJECT_ITEMS_QUERY` with `labels(first: 20)` in the `Issue` fragment. Update spec assumption and research R-003 to reflect the actual state. Move graphql.py into "Relevant Files" as a file that needs modification. |
| F2 | Inconsistency | CRITICAL | plan.md:L93, tasks.md:T030, parent issue Step 16 | **`_self_heal_tracking_table()` file location is wrong.** Plan project structure says `agent_tracking.py — _self_heal_tracking_table() simplified with pipeline: label`. Task T030 targets `backend/src/services/agent_tracking.py`. **Actual location**: `backend/src/services/copilot_polling/pipeline.py:23`. The function does not exist in `agent_tracking.py`. | Fix T030 file path to `backend/src/services/copilot_polling/pipeline.py`. Update plan.md project structure to show `_self_heal_tracking_table()` under `pipeline.py`. |
| F3 | Inconsistency | HIGH | spec.md:L146, contracts/label-write-path.md:L26-33, quickstart.md:L76-81, data-model.md:L234-244 | **`assign_agent_for_status()` signature mismatch.** Spec, contracts, quickstart, and data-model all show the signature as `(self, ctx, issue_number, status, agents, ...) -> dict[str, Any] | None`. **Actual signature**: `(self, ctx: WorkflowContext, status: str, agent_index: int = 0) -> bool`. Parameters `issue_number` and `agents` do not exist; return type is `bool`, not `dict`. Implementation tasks T013/T014 will need to work with the actual signature. | Update contracts/label-write-path.md and quickstart.md to reflect actual `assign_agent_for_status()` signature. Tasks T013/T014 descriptions should reference `status` and `agent_index` parameters, not `issue_number` and `agents`. |
| F4 | Inconsistency | HIGH | plan.md:L108, tasks.md:T025 | **Frontend component name mismatch.** Plan project structure (line 108) lists `BoardCard.tsx — Agent badge, pipeline tag, stalled indicator`. **No `BoardCard.tsx` exists** — the actual component is `IssueCard.tsx`. Tasks T025 correctly references `IssueCard.tsx`. | Fix plan.md project structure line 108 to reference `IssueCard.tsx` instead of `BoardCard.tsx`. |
| F5 | Underspecification | HIGH | spec.md:L175-179, tasks.md:T005 | **Scope boundary conflict with required implementation.** Spec scope boundaries (line 179) explicitly state: "Changes to the GraphQL board query itself (labels are already fetched)" is out of scope. However, `GET_PROJECT_ITEMS_QUERY` (used by `get_project_items()`) does NOT fetch labels and MUST be modified for T005 to work. This creates a contradiction: the spec says no query changes are needed, but the implementation requires one. | Clarify scope: either (a) add `graphql.py` query modification as explicitly in-scope (since only the polling query needs changes, not the board query), or (b) rewrite T005 to use a different approach (e.g., re-use `BOARD_GET_PROJECT_ITEMS_QUERY` for polling). |
| F6 | Underspecification | MEDIUM | tasks.md:T008 | **Async I/O function placed in pure-utility module.** T008 places `ensure_pipeline_labels_exist()` in `constants.py`, but this function is `async` and calls the GitHub REST API. `constants.py` currently contains only constants and pure functions (no I/O, no async). Adding an async API-calling function violates the module's purpose. Research R-005 acknowledged this: "constants.py (or a thin wrapper in the orchestrator)". | Move `ensure_pipeline_labels_exist()` to `orchestrator.py` or a new `label_service.py` file. Keep constants and pure functions in `constants.py`. |
| F7 | Ambiguity | MEDIUM | spec.md:L138 | **SC-004 "without adding measurable latency" is vague.** Success criterion SC-004 states label operations should "complete within the existing polling cycle time without adding measurable latency." No threshold is defined for "measurable." | Define a concrete threshold, e.g., "label operations add ≤200ms per transition" or "total polling cycle time increase ≤5%." |
| F8 | Ambiguity | MEDIUM | spec.md:L142 | **SC-008 "reducing recovery time proportionally" is vague.** Success criterion SC-008 says recovery should reduce "recovery time proportionally to the number of completed agents." No baseline or target ratio is given. | Quantify: e.g., "For a pipeline with N agents where agent K is current, recovery checks only agents K..N (saving K-1 checks)." |
| F9 | Underspecification | MEDIUM | spec.md:L92-99, tasks.md | **Edge case: pipeline config deletion/rename after labeling.** Edge cases cover label removal, label limits, concurrent recovery, and special characters — but not what happens if a pipeline configuration is renamed or deleted after the `pipeline:<config>` label is set. Fast-path (T019) looks up config by name; a renamed config would cause fast-path failure with silent fallthrough. | Add edge case: "What happens when a pipeline config is renamed after the `pipeline:<config>` label was applied? Fast-path returns None; system falls through to existing reconstruction. The stale label remains until manually removed." |
| F10 | Inconsistency | MEDIUM | plan.md:L93, spec.md:L159 | **Relevant files list references `agent_tracking.py` for the wrong function.** Plan relevant files (line 93) says `agent_tracking.py — _self_heal_tracking_table() simplified`. Spec dependencies (line 159) correctly says `agent_tracking.py` has "agent tracking table parsing utilities." These are different claims. The parsing utilities (build, render, parse tracking) ARE in `agent_tracking.py` but `_self_heal_tracking_table` is in `pipeline.py`. | Update plan relevant files to clarify: `agent_tracking.py` is for tracking table parsing utilities; `pipeline.py` is where `_self_heal_tracking_table()` lives. |
| F11 | Underspecification | MEDIUM | tasks.md:T005, plan.md:L92 | **Missing task for GraphQL query modification.** T005 says "Map label data from GraphQL response `content.labels.nodes` to `Task.labels` during construction." However, there is no preceding task to ADD `labels(first: 20)` to `GET_PROJECT_ITEMS_QUERY` in `graphql.py`. Without this, `content.labels.nodes` will be `undefined`. | Add a new task between T004 and T005: "Add `labels(first: 20) { nodes { id name color } }` to the `Issue` and `PullRequest` content fragments in `GET_PROJECT_ITEMS_QUERY` in `backend/src/services/github_projects/graphql.py`." |
| F12 | Inconsistency | MEDIUM | quickstart.md:L82-97, contracts/label-write-path.md:L26-33 | **Quickstart code example shows non-existent parameters.** Quickstart Section 2 "After" code shows `assign_agent_for_status()` being called with `issue_number` and `agents` parameters that don't exist in the actual function. The code examples will mislead implementers. | Update quickstart.md code examples to match the actual `assign_agent_for_status(self, ctx, status, agent_index)` signature. Show how `ctx.issue_number` and pipeline config agents are accessed within the function body. |
| F13 | Underspecification | LOW | tasks.md:T025-T027 | **Frontend component naming inconsistency across tasks.** T025 targets `IssueCard.tsx`, T026 targets `BoardToolbar.tsx`, T027 targets `ProjectBoard.tsx`. These are all correct file names, but T027 introduces "parsed pipeline label metadata" concept without specifying the data shape or prop interface. | Add detail to T027: specify the prop type for pipeline metadata (e.g., `{ agentSlug?: string, configName?: string, isStalled: boolean }`) and how it's derived from `item.labels`. |
| F14 | Underspecification | LOW | spec.md:L147 | **Assumption about `labels_add`/`labels_remove` not verified against all use cases.** Spec assumes `update_issue_state()` handles both add and remove. Verified: it does (issues.py:107-165). However, the spec doesn't address the ordering concern: adds are processed before removes. If add fails, the remove may not execute. | Acknowledge in edge cases: "If label add succeeds but remove fails, a parent issue may temporarily have two `agent:` labels. The fast-path handles this by selecting the first match, and the next polling cycle reconciles." (This IS covered by Research R-002 but not in spec edge cases.) |
| F15 | Duplication | LOW | spec.md:L129, data-model.md:L22-30 | **Label color scheme defined in two places.** Spec Key Entities (line 129) and data-model.md both define the label color scheme. The values are consistent but duplicated. | Single source of truth: reference data-model.md from spec or vice versa. Minor — no conflict currently. |

---

## Coverage Summary Table

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001: label-constants | ✅ | T001 | |
| FR-002: parsing-utilities | ✅ | T002 | |
| FR-003: builder-utilities | ✅ | T002 | Covered with FR-002 in same task |
| FR-004: pre-create-labels | ✅ | T008 | ⚠️ Placed in constants.py (see F6) |
| FR-005: pipeline-label-at-creation | ✅ | T011, T012 | |
| FR-006: agent-label-swap | ✅ | T013 | ⚠️ Signature mismatch (see F3) |
| FR-007: active-label-on-sub-issue | ✅ | T014 | |
| FR-008: remove-agent-on-completion | ✅ | T015 | |
| FR-009: stalled-label-lifecycle | ✅ | T022 (apply), T013 (remove) | |
| FR-010: labels-in-task-model | ✅ | T004 | |
| FR-011: fast-path-reconstruction | ✅ | T018, T019 | |
| FR-012: fallthrough-chain | ✅ | T019 | Implicit in fast-path design |
| FR-013: api-response-labels | ✅ | T021 | |
| FR-014: validation-function | ✅ | T029 | |
| FR-015: tracking-table-preserved | ✅ | T034 | Verification only |
| FR-016: one-agent-label | ✅ | T034 | Verification only |
| FR-017: non-blocking-failures | ✅ | T013, T014, T015, T022 | |

---

## Constitution Alignment Issues

No constitution violations detected. All five principles are satisfied:

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | 5 user stories with Given-When-Then scenarios, 17 FRs, clear scope boundaries |
| II. Template-Driven | ✅ PASS | All artifacts follow canonical templates |
| III. Agent-Orchestrated | ✅ PASS | Clear agent handoffs (specify → plan → tasks → analyze) |
| IV. Test Optionality | ✅ PASS | Tests are spec-mandated (Verification items 1-4); TDD ordering enforced in tasks |
| V. Simplicity and DRY | ✅ PASS | Reuses `update_issue_state()`, pure functions, no premature abstraction |

---

## Unmapped Tasks

All 35 tasks (T001-T035) map to at least one requirement or user story:

- **Setup/Foundational (no story)**: T001-T009 → Support FR-001 through FR-010
- **US2**: T010-T016 → FR-005 through FR-009, FR-017
- **US1**: T017-T021 → FR-011, FR-012, FR-013
- **US3**: T022-T024 → FR-009
- **US4**: T025-T027 → SC-002
- **US5**: T028-T032 → FR-014, SC-001, SC-008
- **Polish**: T033-T035 → FR-015, FR-016, integration verification

No orphan tasks found.

---

## Metrics

| Metric | Value |
|--------|-------|
| Total Functional Requirements | 17 |
| Total Success Criteria | 8 |
| Total Tasks | 35 |
| Total User Stories | 5 |
| Requirement Coverage (FRs with ≥1 task) | **100%** (17/17) |
| User Story Coverage (stories with tasks) | **100%** (5/5) |
| Ambiguity Count | 2 (F7, F8) |
| Duplication Count | 1 (F15) |
| Critical Issues Count | **2** (F1, F2) |
| High Issues Count | **3** (F3, F4, F5) |
| Medium Issues Count | **6** (F6, F7, F8, F9, F10, F11) |
| Low Issues Count | **4** (F13, F14, F15) |
| Total Findings | **15** |

---

## Next Actions

### ⚠️ CRITICAL issues must be resolved before `/speckit.implement`

1. **F1 + F5 + F11 (GraphQL query gap)**: The most impactful finding. Three findings are interconnected:
   - `GET_PROJECT_ITEMS_QUERY` does not fetch labels (F1)
   - Spec says query changes are out of scope, contradicting the requirement (F5)
   - No task exists to modify the query (F11)
   
   **Action**: Run `/speckit.specify` with refinement to:
   - Correct spec assumption about GraphQL queries (line 147)
   - Add `graphql.py` to relevant files
   - Adjust scope boundaries to include `GET_PROJECT_ITEMS_QUERY` modification
   - Then update tasks.md to add a GraphQL query modification task

2. **F2 (`_self_heal_tracking_table` wrong file)**: Task T030 targets `agent_tracking.py` but the function is in `pipeline.py`.
   
   **Action**: Manually edit tasks.md to fix T030 file path from `backend/src/services/agent_tracking.py` to `backend/src/services/copilot_polling/pipeline.py`.

### Recommended improvements (HIGH/MEDIUM)

3. **F3 (Signature mismatch)**: Update contracts and quickstart to reflect actual `assign_agent_for_status()` signature. Run `/speckit.plan` to adjust architecture documentation.

4. **F4 (BoardCard → IssueCard)**: Update plan.md project structure to reference `IssueCard.tsx`.

5. **F6 (async in constants.py)**: Move `ensure_pipeline_labels_exist()` out of `constants.py` into orchestrator or a service module.

6. **F9 (Missing edge case)**: Add pipeline config rename/deletion edge case to spec.md.

### Proceed with caution (LOW)

- F7, F8: Quantify vague success criteria for better testability
- F13, F14, F15: Minor improvements that won't block implementation

---

## Remediation Summary

Would you like me to suggest concrete remediation edits for the top 5 issues (F1, F2, F3, F4, F5)?

These are the highest-impact corrections that should be applied before running `/speckit.implement`. The edits would update:
1. `spec.md` — Fix assumption about GraphQL query, add scope clarification
2. `tasks.md` — Fix T030 file path, add GraphQL query task
3. `plan.md` — Fix project structure (BoardCard → IssueCard, agent_tracking.py → pipeline.py)
4. `contracts/label-write-path.md` — Fix `assign_agent_for_status()` signature
5. `quickstart.md` — Fix code examples with correct signature

**Note**: These edits are NOT applied automatically. User must explicitly approve before any modifications are made.
