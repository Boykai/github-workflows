# Quickstart: Performance Review — Balanced First Pass

**Feature Branch**: `028-performance-review`

## Prerequisites

- Docker Compose environment running (`docker compose up`)
- A GitHub project with 50+ issues for representative testing
- Chrome DevTools (for frontend profiling)
- React DevTools extension (for component render profiling)

## Baseline Measurement Protocol

Run these measurements BEFORE making any optimization code changes. Record all values. Re-run the same protocol AFTER changes to produce before/after comparisons.

### Measurement 1: Backend Idle API Call Count (SC-001)

```bash
# 1. Start the application
docker compose up -d

# 2. Open a project board in the browser and leave it idle

# 3. Monitor backend logs for 5 minutes
# Count outbound GitHub API calls (look for githubkit request logs)
docker compose logs -f backend 2>&1 | tee /tmp/baseline-idle-5min.log &
LOGPID=$!
sleep 300
kill $LOGPID

# 4. Count API calls in the log (match githubkit HTTP request lines)
grep -c "githubkit" /tmp/baseline-idle-5min.log
# Target: ≤2 calls (excluding initial load) after optimization
# Baseline: record current count for comparison
```

### Measurement 2: Backend Per-Refresh API Call Count (SC-003)

```bash
# 1. With the board already loaded and sub-issue cache warm (wait 30s after load)

# 2. Trigger an automatic refresh. Either wait for the 5-min timer, or use
#    browser devtools console to force-invalidate the board query:
#    queryClient.invalidateQueries({queryKey: ['board', 'data', 'YOUR_PROJECT_ID']})
#    Replace YOUR_PROJECT_ID with the actual project ID from the URL.

# 3. Count outbound API calls in backend logs during the refresh
# Target: ≤3 calls with warm sub-issue cache
# Baseline: record current count for comparison
```

### Measurement 3: Frontend Component Render Count (SC-005)

```bash
# 1. Open React DevTools Profiler in Chrome

# 2. Start recording

# 3. Trigger a single-card status change (e.g., move a card between columns
#    on another client, or update an issue status via GitHub UI)

# 4. Stop recording after the update is reflected

# 5. Count the number of component renders
# Target: ≤3 renders (card + column + board container)
# Baseline: record current count (likely all cards re-render if parent props unstable)
```

### Measurement 4: Frontend Drag Frame Rate (SC-006)

```bash
# 1. Open Chrome DevTools Performance tab

# 2. Start recording

# 3. Drag the chat popup continuously for 5 seconds

# 4. Stop recording

# 5. Check the FPS meter in the Performance tab
# Target: ≥30 fps during continuous drag
# Baseline: record current fps
```

### Measurement 5: Frontend Network Activity on Fallback Polling (SC-009)

```bash
# 1. Open Chrome DevTools Network tab, filter to /api/

# 2. Simulate WebSocket failure:
#    - In browser console: close the WebSocket connection manually
#    - Or: block WebSocket in DevTools Network conditions

# 3. Wait for fallback polling to activate (observe polling requests in Network tab)

# 4. Verify that board data endpoint is NOT called during polling
#    Only /api/v1/projects/{id}/tasks should appear, not /api/v1/board/{id}/data
# Target: Zero board data requests during polling fallback (unless 5-min timer fires)
# Baseline: record current behavior
```

## Verification Commands

After implementing all optimization changes, run these commands to verify.

### Backend Verification

```bash
# 1. Run backend linter
cd backend
ruff check src/

# 2. Run backend type checker
pyright src/

# 3. Run targeted backend tests (cache, board, polling)
python -m pytest tests/unit/test_cache.py tests/unit/test_api_board.py tests/unit/test_copilot_polling.py -v --tb=short

# 4. Run full backend test suite (regression check — run each file individually to avoid hangs)
python -m pytest tests/unit/test_cache.py -v --tb=short
python -m pytest tests/unit/test_api_board.py -v --tb=short
python -m pytest tests/unit/test_copilot_polling.py -v --tb=short
```

### Frontend Verification

```bash
# 1. Run frontend linter
cd frontend
npx eslint src/

# 2. Run frontend type checker
npx tsc --noEmit

# 3. Run targeted frontend tests (refresh hooks)
npx vitest run src/hooks/useRealTimeSync.test.tsx src/hooks/useBoardRefresh.test.tsx

# 4. Run full frontend test suite (regression check)
npx vitest run

# 5. Build check
npm run build
```

### End-to-End Verification

```bash
# 1. Start the full application
docker compose up -d

# 2. Open a project board with 50+ issues

# 3. Verify WebSocket updates:
#    - Change an issue status on GitHub
#    - Confirm the board reflects the change within 30 seconds
#    - Confirm NO board data endpoint call in Network tab (only tasks query)

# 4. Verify manual refresh:
#    - Click the refresh button
#    - Confirm board data endpoint is called with ?refresh=true
#    - Confirm fresh data is displayed

# 5. Verify fallback polling:
#    - Block WebSocket in DevTools
#    - Confirm polling activates and updates tasks
#    - Confirm board data is NOT refetched during polling

# 6. Verify idle behavior:
#    - Leave the board idle for 5 minutes
#    - Confirm ≤2 GitHub API calls in backend logs

# 7. Verify board responsiveness:
#    - Drag a card between columns
#    - Confirm smooth interaction (≥30 fps)
#    - Confirm only affected card and column re-render (React DevTools Profiler)
```

## Post-Optimization Comparison Template

| Metric | Baseline (Before) | After Optimization | Change | Target Met? |
|--------|-------------------|--------------------|--------|:-:|
| Idle API calls (5 min) | ___ | ___ | ___% | ≤2 |
| Per-refresh API calls (warm cache) | ___ | ___ | ___% | ≤3 |
| Single-card rerender count | ___ | ___ | ___% | ≤3 |
| Chat drag FPS | ___ fps | ___ fps | ___% | ≥30 |
| Board initial render (100 cards) | ___ ms | ___ ms | ___% | Within 10% |
| Fallback poll board requests | ___ | ___ | → 0 | 0 |
| Existing tests passing | ✅/❌ | ✅/❌ | — | ✅ |
