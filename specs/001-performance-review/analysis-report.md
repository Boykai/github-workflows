# Specification Analysis Report: Performance Review

**Feature**: `001-performance-review`
**Date**: 2026-03-21
**Artifacts Analyzed**: `spec.md` (188 lines), `plan.md` (277 lines), `tasks.md` (327 lines), `constitution.md` (130 lines)

---

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| D1 | Duplication | HIGH | tasks.md:L68 (T015) vs L167 (T051) | **Duplicate test task**: Both T015 [US1] and T051 [US6] add a test for `refresh_ttl()` preserving data hash when data is unchanged in `test_cache.py`. Identical objective. | Remove T051; T015 already covers this in Phase 3. Add cross-reference in Phase 7 noting it was completed earlier. |
| D2 | Duplication | HIGH | tasks.md:L71 (T018) vs L168 (T052) | **Duplicate test task**: Both T018 [US1] and T052 [US6] add a test for sub-issue cache preservation during auto-refresh (`refresh=False`) in `test_api_board.py`. | Remove T052; T018 already covers this in Phase 3. |
| D3 | Duplication | HIGH | tasks.md:L70 (T017) vs L169 (T053) | **Duplicate test task**: Both T017 [US1] and T053 [US6] add a test for sub-issue filtering correctness (child issues removed before pipeline) in `test_copilot_polling.py`. | Remove T053; T017 already covers this in Phase 3. |
| D4 | Duplication | HIGH | tasks.md:L95 (T024) vs L174 (T055) | **Near-duplicate test task**: T024 [US4] tests `task_update` messages don't invalidate board query. T055 [US6] tests "any WebSocket task message type" — a superset of T024. Both in `useRealTimeSync.test.tsx`. | Merge: broaden T024's scope to cover all task message types (absorbing T055's intent). Remove T055. |
| D5 | Duplication | HIGH | tasks.md:L122 (T035) vs L176 (T056) | **Duplicate test task**: Both T035 [US3] and T056 [US6] add a test for manual refresh cancelling concurrent auto-refresh in `useBoardRefresh.test.tsx`. | Remove T056; T035 already covers this in Phase 5. |
| C1 | Coverage | HIGH | spec.md:L135 (FR-010) | **MUST requirement with zero tasks**: FR-010 states "The system MUST return stale cached data with appropriate warnings when a refresh fails due to rate limiting or transient errors." No task in tasks.md verifies or implements this behavior. | Add a verification + test task pair in Phase 3 (US1) or Phase 5 (US3) to cover rate-limit fallback to stale cached data with warnings. |
| C2 | Coverage | MEDIUM | spec.md:L109 | **Edge case with no task**: "What happens when a user opens multiple boards in separate tabs?" — spec requires independent timer/WS management per tab without multiplying API consumption. No task addresses this. | Add a verification task in Phase 4 (US4) or Phase 8 to confirm tab isolation behavior, or document as explicitly deferred. |
| C3 | Coverage | MEDIUM | spec.md:L111 | **Edge case with no task**: "What happens when the board data cache expires during a period of WebSocket inactivity?" — spec requires silent re-fetch without blank flash. No task directly verifies this transition. | Add a verification task in Phase 3 (US1) covering the cache-expired + WS-idle → auto-refresh path. |
| C4 | Coverage | MEDIUM | spec.md:L112 | **Edge case partially uncovered**: "What happens when a manual refresh and a WebSocket-driven task update arrive simultaneously?" T035 covers manual vs. auto-refresh, but not manual refresh vs. WebSocket task update specifically. | Extend T035's scope or add a companion test in Phase 5 for the manual-refresh + WS-task-update race condition. |
| I1 | Inconsistency | MEDIUM | plan.md:L160,188,212,236 vs tasks.md:L24,35,59,85,112,136,159,183 | **Phase numbering drift**: Plan uses 4 phases (Phase 1–4, with two sub-sections each for Phases 2 and 3). Tasks use 8 phases (Phase 1–8). Cross-references like "compare against Phase 2 baseline" in tasks mean tasks' Phase 2 (US5 Baselines), but plan's Phase 2 is "Backend API Consumption Fixes." | Align numbering: either renumber plan phases to match tasks, or add a mapping table in tasks.md clarifying the correspondence. |
| I2 | Inconsistency | MEDIUM | tasks.md:L193, L322 | **"Phase 4" ambiguity**: T065 says "Evaluate whether Phase 4 second-wave work…" referencing plan.md's Phase 4 (deferred). But tasks.md Phase 4 is US4 (Real-Time Updates). The Notes section (L322) also references "Phase 4 optional second-wave." | Rename T065's reference to "second-wave work (plan Phase 4)" or use "deferred second-wave" consistently to avoid confusion with tasks' Phase 4. |
| A1 | Ambiguity | MEDIUM | spec.md:L180 (SC-002) vs plan.md:L18 | **Ambiguous target**: SC-002 says render time "ideally improves by at least 20%." Plan.md:L18 treats 20% as a firm performance goal ("≥ 20% board render improvement"). The spec's "ideally" weakens this to aspirational. | Align: either firm up SC-002 in spec to say "MUST improve by at least 20%" or soften plan's performance goal to "target" rather than a hard requirement. |
| A2 | Ambiguity | LOW | spec.md:L186 (SC-008) | **Subjective criterion**: "remain responsive with no user-perceptible degradation" — no measurable threshold. Contrast with SC-001/SC-009 which have concrete percentages. | Add a measurable bound (e.g., "interaction latency does not increase by more than 50ms compared to baseline" or "no frame drops below 30fps during drag"). |
| A3 | Ambiguity | LOW | spec.md:L37 (US2 scenario 2) | **Subjective criterion**: "responsive with no perceptible frame drops or freezing" during drag — mirrors SC-008's vagueness. | Same as A2: bind to a measurable threshold or explicitly mark as manual/subjective verification. |
| U1 | Underspec | LOW | tasks.md:L149 (T046) | **Uncertain file path**: T046 says "locate useBoardControls or equivalent hook" — the path is unknown at task-generation time. May cause implementer confusion. | Research the actual hook name/path and update the task with the concrete file path. |
| U2 | Underspec | LOW | spec.md:L135 (FR-010) | **Undefined warning format**: FR-010 says "appropriate warnings" but doesn't define what form the warning takes (UI toast, banner, inline message, HTTP header). | Clarify the warning format in spec or link to a UI contract. |
| I3 | Inconsistency | LOW | tasks.md:L187–193 (T059–T065) | **Unmapped tasks lack story labels**: Phase 8 tasks (T059–T065) have no `[US]` story label, unlike all other phases. While they're cross-cutting, this breaks the traceability pattern established in the rest of the file. | Add `[Cross-cutting]` or map each to its primary story (e.g., T059→US1, T060→US2, T061→US3/US4). |
| D6 | Duplication | LOW | tasks.md:L30 (T003) vs L191 (T063) | **Duplicate linting tasks (backend)**: T003 and T063 both run `ruff check src/` and `pyright src/` in solune/backend. Intentionally placed in Setup vs. Polish, but tasks are identical. | Acceptable as bookend validation. Add a note "(repeat from T003)" in T063 for clarity. |
| D7 | Duplication | LOW | tasks.md:L31 (T004) vs L192 (T064) | **Duplicate linting tasks (frontend)**: T004 and T064 both run eslint, tsc, and vite build in solune/frontend. Same pattern as D6. | Acceptable as bookend validation. Add a note "(repeat from T004)" in T064 for clarity. |
| D8 | Duplication | LOW | tasks.md:L79 (T023) vs L187 (T059) | **Duplicate measurement tasks (backend)**: Both re-measure idle API activity against the Phase 2 baseline for SC-001. T023 is a Phase 3 checkpoint; T059 is a Phase 8 final validation. | Acceptable if additional changes occur between Phases 3–8. Add note in T059: "(final re-measurement; compare with T023 checkpoint)". |

---

## Coverage Summary Table

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 (backend baselines) | ✅ | T005, T006, T010 | |
| FR-002 (frontend baselines) | ✅ | T005, T011, T012 | |
| FR-003 (post-optimization comparison) | ✅ | T023, T050, T059, T060, T062 | |
| FR-004 (no fetch when unchanged) | ✅ | T014, T019 | |
| FR-005 (suppress WS refresh cycles) | ✅ | T014, T019 | |
| FR-006 (fallback polling no expensive refreshes) | ✅ | T016, T021, T022 | |
| FR-007 (reuse warm sub-issue caches) | ✅ | T009, T018 | |
| FR-008 (manual refresh bypasses caches) | ✅ | T008, T036, T039 | |
| FR-009 (auto-refresh uses cache within TTL) | ✅ | T007, T020 | |
| FR-010 (stale data with warnings on rate limit) | ❌ | — | **No task coverage** |
| FR-011 (WS task messages → task query only) | ✅ | T024, T029 | |
| FR-012 (board query refresh triggers) | ✅ | T024, T026, T029 | |
| FR-013 (fallback polling same policy as WS) | ✅ | T026, T030 | |
| FR-014 (manual refresh priority) | ✅ | T033, T035, T037 | |
| FR-015 (column re-render minimization) | ✅ | T041, T043 | |
| FR-016 (card re-render isolation) | ✅ | T042, T044 | |
| FR-017 (throttle hot event listeners) | ✅ | T047, T048, T049 | |
| FR-018 (memoize derived data) | ✅ | T045, T046 | T046 path uncertain (U1) |
| FR-019 (existing backend tests pass) | ✅ | T001, T054 | |
| FR-020 (existing frontend tests pass) | ✅ | T002, T057 | |
| FR-021 (new tests for changed behaviors) | ✅ | T014–T018, T024–T028, T033–T036 | |

---

## Constitution Alignment

**No CRITICAL constitution violations found.** All five principles pass:

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | 6 prioritized user stories with independent tests, GWT scenarios, clear scope boundaries |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates. Spec adds "Assumptions" section (justified by scope-deferral clarity). |
| III. Agent-Orchestrated Execution | ✅ PASS | Clear phase handoffs: specify → plan → tasks → analyze |
| IV. Test Optionality with Clarity | ✅ PASS | Tests explicitly required (FR-019–FR-021). Test-first ordering followed in tasks. |
| V. Simplicity and DRY | ⚠️ MINOR | 5 duplicate test tasks between story phases and Phase 7 (D1–D5) violate DRY but are literal duplicates, not wrong-abstraction avoidance. |

---

## Unmapped Tasks

Tasks in Phase 1 (Setup) and Phase 8 (Polish) lack `[US]` story labels. These are cross-cutting:

| Task | Suggested Story Mapping | Rationale |
|------|------------------------|-----------|
| T001–T004 | Cross-cutting (setup) | Validate prerequisites across all stories |
| T059 | US1 (SC-001) | Backend idle API measurement |
| T060 | US2 (SC-002) | Frontend render measurement |
| T061 | US1/US3/US4 (SC-004, SC-005, SC-008) | End-to-end manual verification |
| T062 | US5 (FR-003) | Document before/after results |
| T063–T064 | Cross-cutting (validation) | Final linting/type-check |
| T065 | Cross-cutting (planning) | Second-wave go/no-go |

---

## Edge Case Coverage

| Edge Case (spec.md:L106–L112) | Covered by Tasks? | Notes |
|-------------------------------|-------------------|-------|
| Unstable WebSocket (reconnect cascade) | ✅ | T027, T028, T031 |
| Multiple boards in separate tabs | ❌ | No task (C2) |
| Rate limit exhausted mid-refresh | ❌ | No task — linked to FR-010 gap (C1) |
| Cache expires during WS inactivity | ❌ | No task (C3) |
| Manual refresh + WS task update simultaneous | ⚠️ Partial | T035 covers manual vs. auto-refresh, not manual vs. WS update (C4) |

---

## Metrics

| Metric | Value |
|--------|-------|
| Total Functional Requirements (FR-xxx) | 21 |
| Total Success Criteria (SC-xxx) | 9 |
| Total Tasks | 65 |
| Requirements with ≥1 Task | 20/21 |
| **Coverage %** | **95.2%** |
| Ambiguity Count | 3 (A1, A2, A3) |
| Duplication Count | 8 (D1–D8; 5 HIGH, 3 LOW) |
| Coverage Gap Count | 4 (C1–C4) |
| Inconsistency Count | 3 (I1–I3) |
| Underspecification Count | 2 (U1, U2) |
| **Critical Issues** | **0** |
| **High Issues** | **6** (D1–D5, C1) |
| **Medium Issues** | **5** (C2, C3, C4, I1, I2, A1) |
| **Low Issues** | **9** (A2, A3, U1, U2, I3, D6, D7, D8) |

---

## Next Actions

### Priority Fixes (6 HIGH issues — resolve before `/speckit.implement`)

1. **C1 — Add task for FR-010** (stale data fallback on rate limiting): This is a MUST requirement with zero task coverage. Add a verification + test task pair in Phase 3 (US1) or Phase 5 (US3).

2. **D1–D5 — Consolidate 5 duplicate test tasks**: Remove T051, T052, T053, T055, T056 from Phase 7 (US6) since identical tests are already written in Phases 3–5. Phase 7 should reference the earlier tasks and focus only on _net new_ regression tests not already covered.

   **Suggested commands**:
   - Run `/speckit.tasks` with refinement guidance to de-duplicate Phase 7 against Phases 3–5
   - Or manually edit `tasks.md` to remove duplicates and add cross-references

### Recommended Improvements (5 MEDIUM issues — improve before implementation)

3. **I1/I2 — Add phase mapping table**: Add a brief plan↔tasks phase correspondence table in tasks.md to resolve numbering drift. Rename "Phase 4 second-wave" references in T065/Notes to "deferred second-wave (plan Phase 4)" to disambiguate from tasks' Phase 4 (US4).

4. **A1 — Align SC-002 target**: Decide whether the 20% render improvement is a hard MUST or an aspirational target. The plan says MUST (≥ 20%); the spec says "ideally." One must change.

5. **C2/C3/C4 — Add edge case tasks**: Add verification tasks for the 3 uncovered spec edge cases (multi-tab isolation, cache-expiry-during-WS-idle, manual-refresh-vs-WS-update race).

### Acceptable to Proceed (9 LOW issues — address during implementation)

- A2/A3 (subjective responsiveness criteria): Acceptable for manual testing; consider adding thresholds if automated performance gates are desired later.
- U1 (T046 uncertain path): Resolve during implementation research.
- U2 (FR-010 warning format): Clarify when implementing the FR-010 task.
- D6/D7/D8, I3 (bookend task duplicates, missing labels): Cosmetic; add notes for clarity.

---

## Overall Assessment

The artifacts are well-structured and highly consistent. The 95.2% requirement coverage is strong. The primary concerns are **FR-010** (a MUST requirement with zero tasks) and **5 duplicate test tasks** that will cause redundant work if not consolidated before implementation. No constitution violations were found.

---

*Would you like concrete remediation edits for the top 6 HIGH issues (C1, D1–D5)?*
