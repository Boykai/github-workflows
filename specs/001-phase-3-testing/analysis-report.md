# Specification Analysis Report

**Feature**: Phase 3 — Testing: Coverage, Mutation Enforcement, E2E, Property-Based & Keyboard Navigation  
**Artifacts Analyzed**: spec.md, plan.md, tasks.md  
**Constitution**: `.specify/memory/constitution.md` v1.0.0  
**Date**: 2026-03-22  
**Analyzer**: speckit.analyze

---

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| I1 | Inconsistency | HIGH | spec.md:L142, plan.md:L81, research.md:L32 | spec.md FR-002 claims "~20 untested hooks" but only 6 hooks lack tests (confirmed by research.md and actual codebase). Plan correctly narrows to 6; spec overstates the count | Amend FR-002 from "~20 untested hooks" to "6 untested hooks" to match codebase reality. Update spec.md L14 similarly ("~6 untested hooks and 7 untested high-LOC components") |
| I2 | Inconsistency | HIGH | tasks.md:L66, codebase | T011 references `solune/frontend/src/components/modals/CleanUpConfirmModal.test.tsx` but CleanUpConfirmModal.tsx actually lives at `solune/frontend/src/components/board/CleanUpConfirmModal.tsx` | Fix T011 test path to `solune/frontend/src/components/board/CleanUpConfirmModal.test.tsx` |
| I3 | Inconsistency | HIGH | tasks.md:L68, codebase | T013 references `solune/frontend/src/components/common/MarkdownRenderer.test.tsx` but MarkdownRenderer.tsx actually lives at `solune/frontend/src/components/chat/MarkdownRenderer.tsx` | Fix T013 test path to `solune/frontend/src/components/chat/MarkdownRenderer.test.tsx` |
| I4 | Inconsistency | HIGH | tasks.md:L108-110, codebase | T026–T028 reference `solune/backend/tests/unit/test_pipeline.py` but the actual test file for copilot_polling/pipeline.py is `solune/backend/tests/unit/test_polling_pipeline.py` | Fix T026–T028 file reference to `test_polling_pipeline.py` |
| I5 | Inconsistency | MEDIUM | spec.md:L142, tasks.md:L53-61 | FR-002 lists 10 high-LOC component targets (ProjectBoard, ChatInterface, AgentsPanel, ChoresPanel, AddAgentModal, CleanUpConfirmModal, PipelineAnalytics, MarkdownRenderer, McpSettings, WorkflowSettings) but tasks.md only includes 7 component test tasks (T009–T015). Missing: AgentsPanel, ChoresPanel, AddAgentModal | No change needed — research.md confirms these 3 are "already tested." FR-002 wording should clarify: "target the 7 untested high-LOC components" to avoid confusion |
| A1 | Ambiguity | MEDIUM | spec.md:L14 | "approximately 2,200 new covered statements" lacks verification criteria — how is this number validated post-implementation? | Add a verification step in SC-001 or quickstart.md that records before/after statement counts (e.g., diff of `npm run test:coverage` output) |
| A2 | Ambiguity | MEDIUM | spec.md:L148, tasks.md:L224 | FR-008 and T050 reference `should_skip_agent_trigger()` — it's unclear whether this function lives in `transitions.py` or `pipeline_state_store.py`. Tasks don't specify the import path | Clarify source module for `should_skip_agent_trigger()` in T050 description (it's in `workflow_orchestrator/transitions.py`) |
| A3 | Ambiguity | LOW | spec.md:L151, tasks.md:L254 | FR-011 says add axe-core to 5 specs but SC-008 says "at least 8 Playwright specs (up from 3)". The arithmetic (3+5=8) is correct but the wording could confuse: "at least 8" implies axe-core may need to be in more than 8 specs | Clarify SC-008 to "exactly 8 Playwright specs" or explicitly list the 8 target specs |
| U1 | Underspecification | MEDIUM | spec.md:L141, tasks.md:L74-78 | FR-001 requires "two incremental phases via separate PRs" but tasks.md has T016 (Phase 1) and T017 (Phase 2) as sequential tasks in the same feature branch. No guidance on how "separate PRs" is enforced within this single feature | Clarify whether T016 and T017 should be delivered in separate PRs or whether the "separate PRs" language in FR-001 refers to the implementation workflow (commit-by-commit) |
| U2 | Underspecification | MEDIUM | tasks.md:L190 | T040 (mutmut aggregation job) describes parsing kill ratios from shard reports but doesn't specify the report format, artifact naming convention, or the exact script/command to parse mutmut output | Add implementation detail: specify mutmut report format (JSON vs text), artifact naming pattern, and parsing command (e.g., `mutmut results --json`) |
| U3 | Underspecification | LOW | tasks.md:L30-31 | T001 and T002 are "verify existing infrastructure" tasks but have no failure criteria — what happens if baseline verification fails? No branching logic defined | Add failure handling: if baseline verification fails, halt and report infrastructure issues before proceeding |
| C1 | Coverage Gap | MEDIUM | spec.md:L150, tasks.md | FR-010 says extend "existing E2E specs (board-navigation, agent-creation, chat-interaction)" with focus assertions, but the parent issue description also mentions "pipeline-monitoring" should have focus assertions. Tasks follow spec (3 specs only) — potential scope gap vs parent issue intent | Verify with stakeholders whether pipeline-monitoring should also get focus assertions (FR-010 scope). If yes, add T056b for pipeline-monitoring focus assertions |
| D1 | Duplication | LOW | spec.md:L24, spec.md:L142 | US1 acceptance scenario 5 and FR-002 both enumerate the same 10 high-LOC components. The list appears in 3 places (US1, FR-002, plan.md Phase A) | Minor redundancy — no action needed; serves as cross-reference reinforcement |
| D2 | Duplication | LOW | tasks.md:L345-380 | Parallel example sections repeat task descriptions verbatim from the task list above. These examples don't add new information | Minor redundancy — no action needed; serves as execution guidance for implementers |

---

## Coverage Summary Table

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 (frontend-coverage-thresholds) | ✅ | T016, T017 | Two-phase threshold raise covered |
| FR-002 (hook-and-component-tests) | ✅ | T003–T015 | 6 hooks + 7 components = 13 tasks. 3 components correctly omitted (already tested per research.md) |
| FR-003 (backend-coverage-floors) | ✅ | T018–T031 | 4 modules × 3-4 tasks each = 14 tasks |
| FR-004 (full-workflow-integration) | ✅ | T032–T035 | 4 sub-tasks covering scaffold, issue lifecycle, status transitions, PR lifecycle |
| FR-005 (fifo-queue-integration) | ✅ | T036, T037 | 2-pipeline and 3-pipeline FIFO tests |
| FR-006 (mutation-ci-blocking) | ✅ | T038–T041 | Stryker threshold, Stryker CI, mutmut aggregation, mutmut CI |
| FR-007 (state-machine-queue-rules) | ✅ | T042–T047 | 3 rules + 3 invariants = 6 tasks |
| FR-008 (property-test-blocking-queue) | ✅ | T048–T050 | count_active, get_queued, should_skip_agent_trigger |
| FR-009 (keyboard-nav-e2e) | ✅ | T051–T055 | Tab order, Enter/Space, Escape, focus trapping, initial focus |
| FR-010 (focus-assertions-existing) | ✅ | T056–T058 | board-navigation, agent-creation, chat-interaction |
| FR-011 (axe-core-extension) | ✅ | T059–T063 | 5 specs getting axe-core scans |
| FR-012 (cross-service-e2e-evaluation) | ✅ | T064 | Document in research.md R-007 |

---

## Constitution Alignment Issues

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | spec.md has prioritized user stories with Given-When-Then scenarios and edge cases |
| II. Template-Driven | ✅ PASS | All artifacts follow canonical templates |
| III. Agent-Orchestrated | ✅ PASS | Clear phase handoffs: specify → plan → tasks → analyze |
| IV. Test Optionality | ✅ PASS | Tests are explicitly the deliverable — correctly marked as mandatory |
| V. Simplicity and DRY | ✅ PASS | No new abstractions; extends existing patterns. Complexity tracked in plan.md |

**No constitution violations found.**

---

## Unmapped Tasks

| Task ID | Description | Notes |
|---------|-------------|-------|
| T001 | Verify existing test infrastructure | Setup/validation — not mapped to a specific FR (correct: infrastructure baseline) |
| T002 | Document current coverage baselines | Setup/validation — not mapped to a specific FR (correct: metrics baseline) |
| T065 | Run full frontend test suite | Polish/validation — cross-cutting verification |
| T066 | Run full backend test suite | Polish/validation — cross-cutting verification |
| T067 | Verify CI workflows pass without continue-on-error | Polish/validation — maps to SC-009 |
| T068 | Run quickstart.md verification checklist | Polish/validation — cross-cutting verification |
| T069 | Update quickstart.md with final results | Documentation — cross-cutting |

All unmapped tasks are setup, validation, or polish tasks — correctly outside the FR scope.

---

## Metrics

| Metric | Value |
|--------|-------|
| Total Functional Requirements | 12 (FR-001 through FR-012) |
| Total Tasks | 69 (T001 through T069) |
| Requirements with ≥1 Task | 12/12 |
| **Coverage %** | **100%** |
| Ambiguity Count | 3 (A1, A2, A3) |
| Duplication Count | 2 (D1, D2) |
| Inconsistency Count | 5 (I1–I5) |
| Underspecification Count | 3 (U1, U2, U3) |
| Coverage Gap Count | 1 (C1) |
| **Critical Issues** | **0** |
| **High Issues** | **4** (I1, I2, I3, I4) |
| **Medium Issues** | **6** (I5, A1, A2, U1, U2, C1) |
| **Low Issues** | **4** (A3, U3, D1, D2) |
| Total Findings | 14 |

---

## Next Actions

### Recommended Before `/speckit.implement`

All 4 HIGH-severity issues are **file path or count inaccuracies** in tasks.md and spec.md. They will cause implementers to create test files in wrong directories or reference non-existent files. **These should be corrected before implementation begins:**

1. **I1**: Update spec.md FR-002 — change "~20 untested hooks" to "6 untested hooks"
2. **I2**: Update tasks.md T011 — change path from `components/modals/` to `components/board/`
3. **I3**: Update tasks.md T013 — change path from `components/common/` to `components/chat/`
4. **I4**: Update tasks.md T026–T028 — change `test_pipeline.py` to `test_polling_pipeline.py`

### Optional Improvements (Can Proceed Without)

5. **I5**: Clarify FR-002 that only 7 of 10 listed components need new tests (3 already tested)
6. **A2**: Specify the source module for `should_skip_agent_trigger()` in T050
7. **U1**: Clarify "separate PRs" intent for threshold phases (FR-001 vs tasks.md workflow)
8. **U2**: Add mutmut report parsing details to T040
9. **C1**: Confirm with stakeholders whether pipeline-monitoring needs focus assertions

### Suggested Commands

- Run `/speckit.specify` with refinement to fix spec.md hook count (I1) and component list clarification (I5)
- Manually edit tasks.md to fix file paths in T011, T013, T026–T028 (I2, I3, I4)
- Proceed to `/speckit.implement` after path corrections — no blocking issues remain

---

## Remediation Offer

Would you like me to suggest concrete remediation edits for the top 4 HIGH-severity issues (I1–I4)? These are all straightforward path/count corrections. *(Do NOT apply them automatically — this analysis is read-only.)*
