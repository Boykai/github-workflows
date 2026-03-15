# Performance Measurement Checklist

**Feature**: 001-performance-review
**Date**: 2026-03-15
**Status**: In Progress

## Backend Metrics

### SC-001: Idle Outbound Service Call Reduction (≥ 50%)

| Metric | Baseline | Target | Post-Optimization | Status |
|--------|----------|--------|--------------------|--------|
| Outbound GitHub API calls per 5-min idle window | ~10 (30s periodic check × 10 intervals, cache-gated) | ≤ 5 | — | Pending |
| WebSocket periodic checks that trigger API calls | Up to 1 per expired TTL cycle (every 300s) | 0 when cache warm | — | Pending |

### SC-002: Warm Sub-Issue Cache Call Reduction (≥ 30%)

| Metric | Baseline | Target | Post-Optimization | Status |
|--------|----------|--------|--------------------|--------|
| Outbound calls on cold-cache board refresh | N (varies by board size) | N (unchanged) | — | Pending |
| Outbound calls on warm-cache board refresh | N (sub-issues re-fetched each time) | ≤ 0.7×N | — | Pending |

## Frontend Metrics

### SC-003: Single-Task Update Latency (< 2s)

| Metric | Baseline | Target | Post-Optimization | Status |
|--------|----------|--------|--------------------|--------|
| Time from WebSocket message to UI update | < 2s (already met via direct query invalidation) | < 2s | — | Pending |

### SC-004: Zero Unnecessary Full Refreshes During Polling

| Metric | Baseline | Target | Post-Optimization | Status |
|--------|----------|--------|--------------------|--------|
| Board data query invalidations during 5-min polling window | 0 (polling only invalidates tasks) | 0 | — | Pending |

### SC-005: Board Interaction Latency Improvement

| Metric | Baseline | Target | Post-Optimization | Status |
|--------|----------|--------|--------------------|--------|
| Card click rerender count | Scoped to clicked card (memo already in place) | Same or fewer | — | Pending |
| Drag interaction rerender scope | RAF-throttled (already in place) | Same or fewer | — | Pending |

### SC-006: Rerender Scope

| Metric | Baseline | Target | Post-Optimization | Status |
|--------|----------|--------|--------------------|--------|
| Components rerendered on single task update | Tasks query invalidation rerenders board | Scoped to affected card + container | — | Pending |

## Regression Guardrails

### SC-007: All Existing Tests Pass

| Suite | Pre-Change | Post-Change | Status |
|-------|------------|-------------|--------|
| Backend (test_cache.py) | ✅ 23 passed | — | Pending |
| Backend (test_api_board.py) | ✅ 18 passed | — | Pending |
| Frontend (useRealTimeSync.test.tsx) | ✅ 33 passed | — | Pending |
| Frontend (useBoardRefresh.test.tsx) | ✅ 22 passed | — | Pending |

### SC-008: Regression Test Coverage

| Area | Tests Added | Status |
|------|-------------|--------|
| Warm cache prevents outbound calls | — | Pending |
| Sub-issue cache reuse reduces calls | — | Pending |
| Unchanged hash suppresses push | — | Pending |
| Polling fallback scoped to tasks | — | Pending |
| Refresh deduplication | — | Pending |

### SC-009: No New External Dependencies

| File | Pre-Change Hash | Post-Change Hash | Status |
|------|-----------------|------------------|--------|
| solune/backend/pyproject.toml | — | — | Pending |
| solune/frontend/package.json | — | — | Pending |

### SC-010: Follow-On Plan (if targets not met)

| Item | Status |
|------|--------|
| Follow-on plan created if needed | Pending |
