# Specification Analysis Report: Performance Review

**Feature**: `051-performance-review`  
**Analyzed**: 2026-03-18  
**Artifacts**: spec.md, plan.md, tasks.md, constitution.md, contracts/, data-model.md, quickstart.md  
**Analysis Agent**: `speckit.analyze`

---

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| F1 | Inconsistency | HIGH | tasks.md:T038 | **Wrong file path for AddAgentPopover**: T038 references `solune/frontend/src/components/agents/AddAgentPopover.tsx` but the actual file is at `solune/frontend/src/components/board/AddAgentPopover.tsx`. The `agents/` directory contains `AddAgentModal.tsx` instead. | Fix the path in T038 to `solune/frontend/src/components/board/AddAgentPopover.tsx`. |
| F2 | Inconsistency | HIGH | spec.md:FR-008, tasks.md:T014, T017 | **FR-008 may be already resolved**: FR-008 requires consolidating duplicated repository-resolution in `workflow.py`. However, `workflow.py` already imports and uses `resolve_repository` from `utils.py` (line 42). T014 and T017 target a problem that may not exist. | Verify whether `workflow.py` contains any *additional* inline resolution logic beyond the existing `resolve_repository` calls. If not, mark FR-008 as already satisfied and remove or repurpose T014/T017. |
| F3 | Underspecification | HIGH | spec.md:FR-004, tasks.md:T002 | **Spec 022 reference is unresolvable**: FR-004 and T002 reference `solune/specs/022-api-rate-limit-protection/spec.md` for verification targets. This file does not exist in the repository. No `022-*` spec directory was found. | Locate the correct Spec 022 path or inline the relevant acceptance criteria directly into T002. Without this reference, the "verify against Spec 022" task cannot be completed as specified. |
| F4 | Coverage Gap | MEDIUM | spec.md:US4, tasks.md:Phase 6 | **User Story 4 has no test-first tasks**: All other user stories with implementation tasks (US1, US2, US3, US5) include explicit test tasks that must fail before implementation ("Write tests FIRST, ensure they FAIL"). US4 (Phase 6) jumps directly to implementation (T033–T039) with zero test tasks, despite FR-018 requiring frontend test coverage. | Add test tasks for US4 covering memoization effectiveness (verifying `BoardColumn` and `IssueCard` do not re-render when sibling data changes) and event throttling behavior. Alternatively, document why US4 is test-exempt (e.g., visual/profiling-only verification). |
| F5 | Coverage Gap | MEDIUM | spec.md:FR-012, tasks.md | **FR-012 (scroll position preservation) has no dedicated task**: FR-012 requires preserving scroll position and open UI elements during real-time updates. T032 is an end-to-end verification step, but no implementation task exists to actually implement scroll preservation logic if it is not already present. | Add an implementation task in Phase 5 (US3) that explicitly addresses scroll position preservation, or document that scroll preservation is already handled by the current architecture (e.g., React Query background refetch does not unmount components). |
| F6 | Ambiguity | MEDIUM | spec.md:US2, SC-002 | **"Target time" is undefined for board TTI**: US2 acceptance scenario 1 says "the board is interactive within a target time" but never defines the absolute target. SC-002 defines a 30% improvement relative to baseline, but no maximum absolute threshold is set. A board that loads in 30 seconds and improves 30% to 21 seconds would technically pass. | Define an absolute maximum TTI (e.g., ≤3 seconds with warm cache) in addition to the relative 30% improvement target, or explicitly state that only the relative improvement matters. |
| F7 | Ambiguity | MEDIUM | spec.md:SC-001 | **SC-001 has dual criteria that may conflict**: SC-001 requires "at least 50% reduction" AND "at or below two calls per minute." If the baseline is already at 1 call/minute, a 50% reduction target (0.5/min) is stricter than the ≤2/min threshold. The success criterion should clarify which takes precedence. | Clarify that SC-001 passes when BOTH conditions are met (conjunction), or when the stricter of the two is met. Currently ambiguous whether both are required or either suffices. |
| F8 | Inconsistency | MEDIUM | tasks.md:T014 | **T014 tests wrong file**: T014 tests that `workflow.py` uses shared `resolve_repository()` but the test file is `test_api_board.py`. Tests for `workflow.py` behavior should be in a `test_api_workflow.py` or `test_workflow.py` file, not `test_api_board.py`. | Move T014's test to a file testing `workflow.py` endpoints, or rename T014 to clarify that it tests board-level behavior that happens to involve repository resolution. |
| F9 | Coverage Gap | MEDIUM | spec.md:Edge Cases, tasks.md | **Edge cases have no corresponding tasks**: The spec defines 6 edge cases (rapid reconnection storms, zero-task boards, cache expiry during interaction, simultaneous manual refreshes, external rate limiting/unavailability, cold cache 100+ task boards). None have dedicated tasks in tasks.md. | Add at least one task per CRITICAL edge case (rapid reconnection, simultaneous refreshes, rate-limit/unavailability graceful degradation). These could be test tasks in Phase 8. |
| F10 | Underspecification | MEDIUM | contracts/baseline-metrics.md:FM-2 | **FM-2 (Render Cycle Count) has no numeric success criterion**: All other metrics have specific pass/fail thresholds (≤2/min, 30% faster, ≥30 FPS, etc.). FM-2 says only "Reduction" — no minimum reduction percentage is defined. This makes it untestable as a success criterion. | Define a minimum reduction target (e.g., "≥25% fewer render cycles") or explicitly mark FM-2 as informational rather than a gating criterion. |
| F11 | Underspecification | MEDIUM | contracts/baseline-metrics.md:FM-4 | **FM-4 (Network Request Count) has no numeric success criterion**: Similar to FM-2, FM-4's target is "Reduction" without a specific threshold. | Define a minimum reduction target or mark FM-4 as informational. |
| F12 | Duplication | LOW | tasks.md:T048–T052 vs T012–T014, T019–T021, T026–T028, T040–T043 | **Phase 8 regression tests may duplicate in-story test tasks**: Phase 8 tasks (T048–T052) "extend" tests for cache, board, polling, real-time sync, and board refresh. The per-story test tasks (T012–T014, T019–T021, T026–T028, T040–T043) also add tests to these same files. The boundary between "story-specific tests" and "regression coverage extension" is unclear. | Clarify the scope distinction: story tests verify the specific behavior being implemented; Phase 8 tests verify cross-cutting contract compliance (e.g., refresh-policy.md contract). If there is no meaningful distinction, consolidate into per-story phases. |
| F13 | Inconsistency | LOW | plan.md:L106 | **Plan references `components/chat/ChatPopup.tsx` under a second `components/` node**: The project structure in plan.md lists `components/` twice — once for `board/` and once for `chat/`. This is a formatting artifact but could confuse tree parsing. | Flatten to a single `components/` tree in the project structure block. |
| F14 | Coverage Gap | LOW | spec.md:Assumptions, tasks.md | **Assumption validation tasks are missing**: The spec lists 6 assumptions (e.g., "Spec 022 has partially landed", "representative board size is 50–100 tasks"). No task validates these assumptions before optimization begins. If an assumption is wrong (e.g., Spec 022 is not partially landed), the optimization plan may need restructuring. | T002 partially covers Spec 022 verification. Consider adding validation for other assumptions (e.g., verifying the real-time channel is actually WebSocket-primary, confirming test infrastructure exists for extensions). |
| F15 | Ambiguity | LOW | spec.md:FR-016, tasks.md:T037–T038 | **"No more frequently than once per animation frame" could mean different things**: FR-016 specifies throttling to "once per animation frame." On a 60Hz display, this is ~16.7ms; on 120Hz, ~8.3ms. The spec doesn't clarify whether `requestAnimationFrame` is the required mechanism or just the throttle frequency. | Specify `requestAnimationFrame` as the mechanism (which tasks.md does), and note that the effective rate depends on the display refresh rate. This is mostly clarified in tasks.md but the spec could be more precise. |

---

## Coverage Summary

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 (measure idle API calls) | ✅ | T003 | Covered by Phase 2 baseline capture |
| FR-002 (measure board request cost) | ✅ | T004 | Covered by Phase 2 baseline capture |
| FR-003 (profile frontend load) | ✅ | T006, T007, T009 | TTI, render cycles, network requests |
| FR-004 (verify vs Spec 022) | ⚠️ | T002 | Reference file `022-api-rate-limit-protection/spec.md` is missing (see F3) |
| FR-005 (change detection in WS) | ✅ | T015, T016 | WebSocket cache-hit short-circuit and hash comparison |
| FR-006 (reuse sub-issue cache) | ✅ | T022, T023 | Cache check before external calls + manual refresh clearing |
| FR-007 (polling no expensive refresh) | ✅ | T044, T045, T046 | Client-side change detection + backend stale fallback |
| FR-008 (consolidate repo resolution) | ⚠️ | T017 | May already be resolved — `workflow.py` already uses shared function (see F2) |
| FR-009 (≤2 calls/min idle) | ✅ | T015, T016, T018 | WebSocket handler fixes + end-to-end verification |
| FR-010 (decouple task updates) | ✅ | T029 | Scope WS message handlers to tasks query only |
| FR-011 (single refresh policy) | ✅ | T029, T030, T031 | Unified via refresh-policy contract |
| FR-012 (preserve scroll/popovers) | ⚠️ | T032 | Verification only — no implementation task (see F5) |
| FR-013 (manual refresh bypasses cache) | ✅ | T023, T030 | Backend cache clearing + frontend refresh policy |
| FR-014 (eliminate redundant recalcs) | ✅ | T035 | `useMemo` for derived data |
| FR-015 (stabilize component identity) | ✅ | T033, T034 | `React.memo` wrappers with stable keys |
| FR-016 (throttle event listeners) | ✅ | T037, T038 | rAF throttling for drag/positioning |
| FR-017 (backend test coverage) | ✅ | T012–T014, T048–T050 | Per-story + regression test tasks |
| FR-018 (frontend test coverage) | ⚠️ | T026–T028, T040–T042, T051–T052 | US4 has no test tasks (see F4) |
| FR-019 (manual E2E verification) | ✅ | T018, T032, T047, T057 | Per-story + final verification |

---

## Constitution Alignment

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | 6 prioritized user stories with Given-When-Then scenarios, clear scope boundaries |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates |
| III. Agent-Orchestrated Execution | ✅ PASS | Clear phase transitions: specify → plan → tasks → implement |
| IV. Test Optionality with Clarity | ⚠️ PARTIAL | Tests are explicitly requested (FR-017/018/019), but US4 lacks test tasks despite being in scope for FR-018. Constitution says "When tests are included, they follow strict phase ordering: test tasks precede implementation tasks." US4 violates this. |
| V. Simplicity and DRY | ✅ PASS | Extends existing patterns, no new abstractions |

**Constitution Alignment Issues**: One partial violation — Principle IV requires test tasks to precede implementation tasks when tests are mandated. US4 (Phase 6) has implementation tasks but no test tasks, despite FR-018 mandating frontend test coverage for "board refresh hooks, and query invalidation behavior." While US4's memoization changes may not directly involve hooks/query behavior, the throttling changes (T037, T038) affect event handler behavior that should have test coverage.

---

## Unmapped Tasks

All tasks map to at least one requirement or user story. No orphan tasks were found.

---

## Metrics

| Metric | Value |
|--------|-------|
| Total Functional Requirements | 19 |
| Total Success Criteria | 8 |
| Total Tasks | 58 |
| Total User Stories | 6 |
| Requirement Coverage (FR with ≥1 task) | 15/19 (79%) |
| Requirements with Coverage Warnings | 4 (FR-004, FR-008, FR-012, FR-018) |
| Total Findings | 15 |
| CRITICAL Issues | 0 |
| HIGH Issues | 3 |
| MEDIUM Issues | 8 |
| LOW Issues | 4 |
| Ambiguity Count | 3 |
| Duplication Count | 1 |
| Underspecification Count | 3 |
| Inconsistency Count | 4 |
| Coverage Gap Count | 4 |

---

## Next Actions

### Priority Resolution (HIGH findings)

1. **F1 — Fix AddAgentPopover path** (quick fix): Update T038 in `tasks.md` to reference `solune/frontend/src/components/board/AddAgentPopover.tsx` instead of `solune/frontend/src/components/agents/AddAgentPopover.tsx`.

2. **F2 — Verify FR-008 necessity** (investigation required): Inspect `solune/backend/src/api/workflow.py` to confirm whether duplicate repository-resolution logic exists beyond the already-imported `resolve_repository()`. If not, remove or repurpose T014 and T017 and mark FR-008 as pre-satisfied.

3. **F3 — Resolve Spec 022 reference** (investigation required): Locate the actual Spec 022 file or inline its relevant acceptance criteria into T002. Without this, the baseline verification task is blocked.

### Recommended Improvements (MEDIUM findings)

4. **F4 — Add US4 test tasks**: Add 2–3 test tasks in Phase 6 before the implementation tasks, covering `React.memo` effectiveness and event throttling behavior.

5. **F5 — Add FR-012 implementation task**: Add a task in Phase 5 to verify or implement scroll position preservation during real-time updates.

6. **F9 — Add edge case test tasks**: Add at least tasks for rapid reconnection handling and simultaneous manual refresh deduplication in Phase 8.

7. **F10/F11 — Define FM-2 and FM-4 thresholds**: Set numeric success criteria for render cycle count and network request count, or explicitly mark them as informational.

### Proceed If

- If only LOW/MEDIUM issues remain after fixing the 3 HIGH findings, implementation can proceed. The MEDIUM findings are improvements that can be addressed during implementation.
- **Recommended**: Run `/speckit.tasks` with refinements after fixing F1–F3, or manually edit `tasks.md` to address F1, F4, and F9.
- **Optional**: Run `/speckit.specify` to tighten SC-001 dual criteria (F7) and add absolute TTI threshold (F6).

---

## Remediation Offer

Would you like me to suggest concrete remediation edits for the top 5 issues (F1–F5)? These would be specific text changes to `tasks.md` and `spec.md`. (Edits will NOT be applied automatically — this analysis is read-only.)
