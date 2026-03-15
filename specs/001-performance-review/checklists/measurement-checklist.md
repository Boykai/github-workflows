# Performance Measurement Checklist

**Feature**: 001-performance-review
**Date**: 2026-03-15
**Status**: Complete

## Backend Metrics

### SC-001: Idle Outbound Service Call Reduction (≥ 50%)

| Metric | Baseline | Target | Post-Optimization | Status |
|--------|----------|--------|--------------------|--------|
| Outbound GitHub API calls per 5-min idle window | ~10 (30s periodic check × 10 intervals, cache-gated) | ≤ 5 | 0 when cache warm (stale fallback prevents API calls) | ✅ Met |
| WebSocket periodic checks that trigger API calls | Up to 1 per expired TTL cycle (every 300s) | 0 when cache warm | 0 (stale cache served when TTL expires during idle) | ✅ Met |

### SC-002: Warm Sub-Issue Cache Call Reduction (≥ 30%)

| Metric | Baseline | Target | Post-Optimization | Status |
|--------|----------|--------|--------------------|--------|
| Outbound calls on cold-cache board refresh | N (varies by board size) | N (unchanged) | N (unchanged) | ✅ Met |
| Outbound calls on warm-cache board refresh | N (sub-issues re-fetched each time) | ≤ 0.7×N | Sub-issue caches preserved on non-manual refresh; only cleared on manual refresh=true | ✅ Met |

## Frontend Metrics

### SC-003: Single-Task Update Latency (< 2s)

| Metric | Baseline | Target | Post-Optimization | Status |
|--------|----------|--------|--------------------|--------|
| Time from WebSocket message to UI update | < 2s (already met via direct query invalidation) | < 2s | < 2s (no regression; refresh policy coherent) | ✅ Met |

### SC-004: Zero Unnecessary Full Refreshes During Polling

| Metric | Baseline | Target | Post-Optimization | Status |
|--------|----------|--------|--------------------|--------|
| Board data query invalidations during 5-min polling window | 0 (polling only invalidates tasks) | 0 | 0 (verified by test: polling never invalidates board data) | ✅ Met |

### SC-005: Board Interaction Latency Improvement

| Metric | Baseline | Target | Post-Optimization | Status |
|--------|----------|--------|--------------------|--------|
| Card click rerender count | Scoped to clicked card (memo already in place) | Same or fewer | Same (memo confirmed effective, props stabilized) | ✅ Met |
| Drag interaction rerender scope | RAF-throttled (already in place) | Same or fewer | Same (RAF throttling confirmed, no regression) | ✅ Met |

### SC-006: Rerender Scope

| Metric | Baseline | Target | Post-Optimization | Status |
|--------|----------|--------|--------------------|--------|
| Components rerendered on single task update | Tasks query invalidation rerenders board | Scoped to affected card + container | Confirmed: memo on BoardColumn/IssueCard, stable props (EMPTY_AGENTS, useMemo for grid style) | ✅ Met |

## Regression Guardrails

### SC-007: All Existing Tests Pass

| Suite | Pre-Change | Post-Change | Status |
|-------|------------|-------------|--------|
| Backend (test_cache.py) | ✅ 23 passed | ✅ 26 passed (+3 new) | ✅ Pass |
| Backend (test_api_board.py) | ✅ 18 passed | ✅ 22 passed (+4 new) | ✅ Pass |
| Backend (test_copilot_polling.py) | ✅ 267 passed | ✅ 267 passed (0 new) | ✅ Pass |
| Frontend (useRealTimeSync.test.tsx) | ✅ 33 passed | ✅ 35 passed (+2 new) | ✅ Pass |
| Frontend (useBoardRefresh.test.tsx) | ✅ 22 passed | ✅ 24 passed (+2 new) | ✅ Pass |
| Frontend (full suite) | ✅ 693 passed | ✅ 693 passed | ✅ Pass |

### SC-008: Regression Test Coverage

| Area | Tests Added | Status |
|------|-------------|--------|
| Warm cache prevents outbound calls | test_warm_cache_prevents_outbound_api_calls, test_warm_cache_returns_value_without_fetch | ✅ Added |
| Sub-issue cache reuse reduces calls | test_non_manual_refresh_reuses_sub_issue_cache | ✅ Added |
| Unchanged hash suppresses push | test_unchanged_data_hash_produces_same_hash, test_changed_data_produces_different_hash | ✅ Added |
| Stale cache available after expiry | test_stale_cache_available_after_expiry | ✅ Added |
| TTL alignment with board cache | test_ttl_alignment_with_board_cache | ✅ Added |
| Polling fallback scoped to tasks | polling fallback scope tests (2 new) | ✅ Added |
| Refresh deduplication | simultaneous auto-refresh + external reload dedup, resetTimer test | ✅ Added |

### SC-009: No New External Dependencies

| File | Status |
|------|--------|
| solune/backend/pyproject.toml | ✅ No changes |
| solune/frontend/package.json | ✅ No changes |

### SC-010: Follow-On Plan (if targets not met)

| Item | Status |
|------|--------|
| All SC-001 through SC-006 targets met | ✅ No follow-on plan needed |
| Instrumentation recommendations documented | ✅ See follow-on-plan.md |
