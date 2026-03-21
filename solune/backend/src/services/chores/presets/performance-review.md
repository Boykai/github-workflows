---
name: Performance Review
about: Recurring chore — Performance Review
title: '[CHORE] Performance Review'
labels: chore
assignees: ''
---

## Performance Review

Perform a balanced first pass focused on measurable, low-risk performance gains across backend and frontend. Start by capturing baselines and instrumentation, then fix the highest-value issues already surfaced by the codebase: backend GitHub API churn around board refreshes and polling, and frontend board responsiveness issues caused by broad query invalidation, full-list rerenders, and hot event listeners. Defer broader architectural refactors like virtualization and large service decomposition unless the first pass fails to meet targets.

**Steps**
1. Phase 1 — Baseline and guardrails. Capture current backend and frontend performance baselines before changing behavior. Measure idle API activity for an open board, board endpoint request cost, WebSocket/polling refresh behavior, and frontend render hot spots. Reuse existing tests around cache, polling, WebSocket fallback, and board refresh to define a before/after checklist. This phase blocks all optimization work because the success criteria and regression guardrails depend on it.
2. Phase 1 — Confirm current backend state against the targeted idle-rate-limit goals. Verify whether WebSocket change detection, board cache TTL alignment, and sub-issue cache invalidation are fully implemented or only partially landed. The current board endpoint already appears to set a 300-second TTL and clears sub-issue cache on manual refresh, so the remaining work should target any still-missing pieces rather than redoing completed items. This step can run in parallel with frontend baseline inspection once the measurement checklist is defined.
3. Phase 2 — Backend API consumption fixes. Prioritize the highest-value remaining server-side issues: WebSocket subscription refresh logic in the projects API, sub-issue caching behavior for board data, and any remaining unnecessary GitHub calls in polling or repository resolution. Explicitly validate that idle board viewing no longer emits repeated refreshes when data is unchanged, that warm sub-issue caches materially reduce board refresh call count, and that fallback polling does not trigger expensive board refreshes unintentionally. This depends on Phase 1 baselines.
4. Phase 2 — Frontend refresh-path fixes. Update the real-time and fallback refresh paths so lightweight task updates stay decoupled from the expensive board data query except on manual refresh. Review the interaction between WebSocket updates, fallback polling, auto-refresh, and manual refresh to ensure they use a single coherent policy and do not recreate the prior polling storm. This can proceed in parallel with backend API work once the desired refresh contract is confirmed.
5. Phase 3 — Frontend render optimization. Target low-risk rendering costs in board and chat surfaces: reduce repeated derived-data work in page components and hooks, stabilize props where useful, memoize heavy card/list components when it actually reduces rerenders, and throttle or rationalize hot event listeners such as drag and popover positioning. Keep this phase intentionally low-risk; avoid introducing new dependencies or virtualization in the first pass unless baseline results show large boards still regress after the lighter fixes.
6. Phase 3 — Verification and regression coverage. Extend or adjust unit/integration coverage around backend cache behavior, WebSocket change detection, fallback polling, and frontend board refresh logic. Validate with backend tests, frontend tests, and at least one manual network/profile pass to confirm the target improvements are real rather than inferred. This depends on Phases 2 and 3.
7. Phase 4 — Optional second-wave work. If the first pass still leaves material UI lag on large boards or excessive backend complexity, prepare a follow-on plan for structural changes: board virtualization, deeper service decomposition around GitHub project fetching/polling, bounded cache policies, and stronger instrumentation around request budgets and render timings. This phase is explicitly out of scope for the first implementation unless measurements prove it is necessary.

**Relevant files**
- `solune/backend/tests/unit/test_cache.py`, `solune/backend/tests/unit/test_api_board.py`, `solune/frontend/src/hooks/useBoardRefresh.test.tsx` — in-repo regression guardrails for idle-rate-limit reduction, cache TTL alignment, and refresh behavior.
- `solune/backend/src/api/projects.py` — projects tasks endpoints and WebSocket subscription flow; likely location for change-detection verification and refresh semantics.
- `solune/backend/src/api/board.py` — board-data cache behavior, manual refresh semantics, and sub-issue cache invalidation path.
- `solune/backend/src/services/copilot_polling/polling_loop.py` — polling hot path and expensive background work that can still consume rate limit budget.
- `solune/backend/src/services/github_projects/service.py` — board/project fetching path and candidate reuse points for sub-issue caching or batching.
- `solune/backend/src/services/cache.py` — cache TTLs, cache-key helpers, and any bounded-cache improvements if needed.
- `solune/backend/src/utils.py` — shared repository resolution logic to reuse instead of duplicated fallback flows.
- `solune/backend/src/api/workflow.py` — known duplicate repository-resolution path that may add inconsistency and avoidable work.
- `solune/frontend/src/hooks/useRealTimeSync.ts` — current WebSocket/fallback polling behavior; today it still invalidates board data during polling fallback.
- `solune/frontend/src/hooks/useBoardRefresh.ts` — board auto-refresh policy and manual refresh coordination.
- `solune/frontend/src/hooks/useProjectBoard.ts` — board query ownership and invalidation/refetch strategy.
- `solune/frontend/src/components/board/BoardColumn.tsx` — full column list rendering without memoization or virtualization.
- `solune/frontend/src/components/board/IssueCard.tsx` — likely high-frequency rerender unit for board interactions.
- `solune/frontend/src/pages/ProjectsPage.tsx` — render-time sorting/aggregation and board-level derived state.
- `solune/frontend/src/components/chat/ChatPopup.tsx` — hot drag listener path worth throttling.
- `solune/frontend/src/components/board/AddAgentPopover.tsx` — positioning listeners and update frequency.
- `solune/backend/tests/unit/test_cache.py` — backend cache TTL and stale fallback coverage to extend.
- `solune/backend/tests/unit/test_api_board.py` — board cache and board endpoint behavior to reuse for regression tests.
- `solune/backend/tests/unit/test_copilot_polling.py` — polling behavior and rate-limit-aware logic to reuse.
- `solune/frontend/src/hooks/useRealTimeSync.test.tsx` — refresh invalidation and WebSocket fallback coverage to extend.
- `solune/frontend/src/hooks/useBoardRefresh.test.tsx` — refresh timer and deduplication behavior to reuse.

**Verification**
1. Backend baseline: measure idle API activity for an open board over a fixed interval and compare against the idle-rate-limit goals above; confirm no repeated unchanged refreshes are sent.
2. Backend automated checks: run Ruff, Pyright, and the targeted pytest files covering cache, board, projects/WebSocket, and polling behavior.
3. Frontend baseline: profile board load and interaction on a representative project size, inspect network activity for WebSocket, fallback polling, and board query invalidation, and identify repeated rerender sources.
4. Frontend automated checks: run ESLint, type-checking, Vitest coverage for real-time sync and board refresh hooks, and a build check.
5. Manual end-to-end check: verify that WebSocket updates refresh task data quickly, fallback polling remains safe, manual refresh still bypasses caches when intended, and board interactions remain responsive.

**Decisions**
- Selected approach: balanced pass across backend and frontend rather than a single-area optimization.
- Recommended implementation scope for the first pass: low-risk optimizations first, even though the user left the aggressiveness undecided.
- Included scope: measurement, idle API reduction, refresh-path cleanup, low-risk render optimization, and regression coverage.
- Excluded from the first pass unless metrics justify it: board virtualization, major service decomposition, dependency changes, and larger architectural rewrites.
- Baseline measurement is mandatory before code changes so the improvements can be proven and not just assumed.

**Further Considerations**
1. If large boards still feel slow after the low-risk frontend fixes, the next recommended option is virtualization rather than additional scattered memoization.
2. If backend API churn remains high after the targeted rate-limit fixes above, the next recommended option is deeper consolidation in the GitHub projects service and polling pipeline rather than more cache-layer patching.
3. If repeated performance work is expected in this repo, add lightweight instrumentation or logging around board refresh cost, sub-issue cache hit rate, and refresh-source attribution so regressions are visible earlier.
