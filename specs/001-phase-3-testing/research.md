# Research: Phase 3 — Testing

**Feature**: `001-phase-3-testing` | **Date**: 2026-03-22 | **Plan**: [plan.md](./plan.md)

## Research Tasks & Findings

### R-001: Frontend Coverage Gap Analysis

**Task**: Identify which hooks and components lack tests and estimate effort to reach 75/65/65/75 thresholds.

**Decision**: Prioritize 6 untested hooks first (highest ROI per file), then 7 untested high-LOC components.

**Rationale**: Current thresholds are 50/44/41/50 (statements/branches/functions/lines). The spec targets 75/65/65/75 — a gap of ~2,200 covered statements. Hooks are small, well-isolated units that can be tested with the existing TanStack Query wrapper + `createMockApi()` pattern; each hook test covers multiple branches with minimal setup. Components are larger but 7 out of 10 target components already lack tests entirely, so even basic render + interaction tests will significantly boost coverage.

**Untested hooks** (6):
- `useActivityFeed.ts` — activity feed data fetching
- `useBoardDragDrop.ts` — board drag-and-drop interactions
- `useCommandPalette.ts` — command palette state management
- `useEntityHistory.ts` — entity change history
- `useInfiniteList.ts` — infinite scroll pagination
- `useUnsavedPipelineGuard.ts` — unsaved changes warning

**Untested components** (7):
- `ProjectBoard` — main board view (high LOC)
- `ChatInterface` — chat window with streaming (high LOC)
- `CleanUpConfirmModal` — cleanup confirmation dialog
- `PipelineAnalytics` — pipeline metrics visualization
- `MarkdownRenderer` — markdown-to-HTML rendering
- `McpSettings` — MCP tool configuration UI
- `WorkflowSettings` — workflow configuration UI

**Already tested** (3 of 10 target): AgentsPanel, ChoresPanel, AddAgentModal.

**Alternatives considered**:
- Targeting all hooks (53 total) — rejected; 47/53 already have tests, diminishing returns
- Raising thresholds in one step — rejected; two incremental phases reduce risk of CI breakage

---

### R-002: Backend Coverage Gap Analysis

**Task**: Analyze missing statement counts per file and identify highest-impact test additions.

**Decision**: Follow the per-file floors from the spec: board.py ≥80%, pipelines.py ≥80%, pipeline.py ≥85%, agent_creator.py ≥70%.

**Rationale**: These four modules handle the most critical business logic: board state management (rate limiting, caching, token refresh), pipeline orchestration (queue routing, dequeue, status transitions), and agent lifecycle (creation, tool assignment, error recovery). The missing statement counts (116, 108, 230, 246 respectively) represent real untested code paths that could harbor bugs.

**Key areas per file**:

| File | Missing Stmts | Key Untested Paths |
|------|--------------|-------------------|
| board.py (API) | 116 | Column transforms, rate-limit recovery (429), token expiration refresh, cache hash computation, error branches |
| pipelines.py (API) | 108 | Queue mode routing (L388-406), position calculation, dequeue trigger, sub-issue error handling |
| pipeline.py (polling) | 230 | `_dequeue_next_pipeline()`, grace period expiration, BoundedDict race conditions, stale reclaim |
| agent_creator.py | 246 | GitHub API exception paths, config parsing (malformed YAML, missing fields), tool assignment logic |

**Test patterns**: All tests extend existing test files using established patterns from `conftest.py` (mock_settings, mock_github_service, mock_db, etc.). Backend integration tests use `httpx.ASGITransport` + `AsyncClient`.

**Alternatives considered**:
- Setting all files to 80% — rejected; agent_creator.py has 246 missing statements with many intentionally simple error branches; 70% is realistic and still enforces coverage
- Including health.py error paths — rejected per spec; intentionally non-raising by design

---

### R-003: httpx.ASGITransport Integration Pattern

**Task**: Research the established integration test pattern for the full-workflow test.

**Decision**: Follow the `test_webhook_dispatch.py` pattern exactly — build a minimal FastAPI app, configure HMAC signing, use `httpx.AsyncClient` with `ASGITransport`.

**Rationale**: The existing `test_webhook_dispatch.py` provides a proven, working pattern for testing FastAPI endpoints without network I/O. It uses `httpx.ASGITransport` to route requests directly to the ASGI app, making tests fast, deterministic, and free from port conflicts.

**Key patterns from test_webhook_dispatch.py**:
```python
# Build minimal app with required routers
app = FastAPI()
app.include_router(webhooks_router, prefix="/api/v1/webhooks")

# Configure HMAC webhook signing
def _sign_payload(payload: bytes, secret: str) -> str:
    digest = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return f"sha256={digest}"

# Use ASGITransport for in-process HTTP
transport = ASGITransport(app=app)
async with AsyncClient(transport=transport, base_url="http://test") as client:
    response = await client.post("/api/v1/webhooks/github", ...)
```

**Full-workflow test will need**:
- All relevant routers (webhooks, pipelines, board)
- Integration-level fixtures from `tests/integration/conftest.py` (thin_mock_client, GitHubProjectsStub)
- State management via `pipeline_state_store` functions
- Assertions on pipeline state transitions through all 4 statuses

**Alternatives considered**:
- Docker-compose with real services — rejected; much higher setup cost, flakiness risk, and the httpx approach already provides integration-level confidence
- TestClient from Starlette — rejected; httpx.AsyncClient with ASGITransport is already the established pattern and supports async natively

---

### R-004: Hypothesis RuleBasedStateMachine Best Practices

**Task**: Research best practices for extending the existing pipeline state machine with queue rules.

**Decision**: Add queue rules (`enqueue_pipeline`, `dequeue_pipeline`, `cancel_queued`) to the existing `PipelineStateMachine` class in `test_pipeline_state_machine.py` and create a separate `test_blocking_queue.py` for queue-function-level property tests.

**Rationale**: The existing state machine (200 max examples, 50 steps per execution) tests sequential agent execution transitions. Queue behavior adds a new dimension: multiple pipelines per project with FIFO ordering. Adding rules to the existing machine keeps the state space unified, while a separate file for function-level property tests (`count_active_pipelines_for_project`, `get_queued_pipelines_for_project`) provides focused coverage of the queue data layer.

**Key design decisions**:
- The state machine maintains a list of pipelines (not just one) to model queue behavior
- Preconditions ensure valid transitions (e.g., can only enqueue when an active pipeline exists)
- Invariants check FIFO ordering by `started_at`, no agent on queued pipelines, single active pipeline per project
- `should_skip_agent_trigger()` tests model the grace period (skip within window, allow after 120s stale reclaim)

**Hypothesis profiles** (from `tests/property/conftest.py`):
- CI: `max_examples=200, deadline=None, suppress_health_check=[too_slow]`
- Dev: `max_examples=20, deadline=400ms`
- Default: dev profile; CI overrides via `HYPOTHESIS_PROFILE=ci` environment variable

**Alternatives considered**:
- Separate state machine class for queue — rejected; shared state transitions between pipeline lifecycle and queue behavior make a unified machine more valuable
- Fewer examples (50) — rejected; ≥200 is required by spec and matches the CI profile

---

### R-005: Mutation Testing CI Configuration

**Task**: Research how to make mutation testing blocking in the CI workflow.

**Decision**: Three configuration changes — Stryker `break: 50`, remove `continue-on-error` from both mutation jobs, and add a mutmut aggregation step.

**Rationale**: Both mutation testing jobs (Stryker for frontend, mutmut for backend) currently run with `continue-on-error: true`, making them informational only. Making them blocking requires:

1. **Stryker**: The `break` threshold in `stryker.config.mjs` controls when Stryker exits with non-zero. Setting it to `50` means CI fails if the mutation score drops below 50%. Combined with removing `continue-on-error`, this makes the job blocking.

2. **mutmut**: Backend mutation testing uses 4 sharded runs. Each shard produces a report file. An aggregation job needs to:
   - Wait for all 4 shards via `needs: [backend-mutation]`
   - Download all report artifacts
   - Parse kill ratios from report text
   - Fail if any shard has kill ratio < 60%

3. **Timeout**: The 60-minute timeout per job is preserved. PR-level `--since` mode is explicitly deferred.

**Current workflow structure**:
```yaml
# mutation-testing.yml
backend-mutation:   # 4 shards, continue-on-error: true
frontend-mutation:  # single job, continue-on-error: true
```

**Target workflow structure**:
```yaml
backend-mutation:          # 4 shards, NO continue-on-error
backend-mutation-check:    # NEW: aggregation, fails on kill ratio < 60%
frontend-mutation:         # single job, NO continue-on-error
```

**Alternatives considered**:
- PR-level `--since` mode — explicitly deferred per spec; need stable weekly runs first
- Lower thresholds (30% frontend, 40% backend) — rejected; 50/60 reflects achievable quality floors
- Single aggregation for both frontend and backend — rejected; they use different tools with different output formats

---

### R-006: Keyboard Navigation E2E Patterns

**Task**: Research Playwright keyboard testing patterns and axe-core integration.

**Decision**: Create a dedicated `keyboard-navigation.spec.ts` using Playwright's keyboard API and `AxeBuilder` from `@axe-core/playwright`.

**Rationale**: Playwright provides built-in keyboard support (`page.keyboard.press('Tab')`, `page.keyboard.press('Enter')`, etc.) and focus assertions (`expect(locator).toBeFocused()`). The existing `@axe-core/playwright` package is already installed (used in 3 specs). The dedicated suite covers systematic keyboard navigation; existing specs get targeted focus assertions for their specific flows.

**Key patterns**:
```typescript
// Focus assertion
await page.keyboard.press('Tab');
await expect(page.getByRole('button', { name: 'Submit' })).toBeFocused();

// Escape closes modal
await page.keyboard.press('Escape');
await expect(page.getByRole('dialog')).not.toBeVisible();

// axe-core accessibility scan
import AxeBuilder from '@axe-core/playwright';
const results = await new AxeBuilder({ page }).analyze();
expect(results.violations).toEqual([]);
```

**Pages to cover**:
- Dashboard / Board view
- Agents page
- Settings page
- Chat interface
- Pipeline monitoring
- MCP tool configuration

**Existing axe-core usage** (3 specs):
- `board-navigation.spec.ts` — full page scan
- `ui.spec.ts` — full page scan
- `protected-routes.spec.ts` — full page scan

**Specs needing axe-core addition** (5):
- `agent-creation.spec.ts`
- `pipeline-monitoring.spec.ts`
- `mcp-tool-config.spec.ts`
- `chat-interaction.spec.ts`
- `keyboard-navigation.spec.ts` (new)

**Alternatives considered**:
- Testing with real screen readers — out of scope; axe-core provides automated WCAG verification
- Using Cypress instead of Playwright — rejected; Playwright is already the established E2E framework

---

### R-007: Cross-Service E2E Feasibility

**Task**: Evaluate feasibility of cross-service Playwright E2E against a real backend.

**Decision**: Document as future work. The httpx-based integration test (Phase C) provides higher value with lower setup cost.

**Rationale**: The existing docker-compose stack defines 3 services (backend, frontend, signal-api). However:
- All current E2E fixtures mock API calls — no real backend interaction
- Real backend requires: SQLite DB setup, GitHub API mocking (OAuth, Projects API, Issues API), auth bypass for test sessions
- The signal-api service adds complexity without testing value
- The httpx ASGITransport integration test already verifies the full pipeline lifecycle without network I/O

**What would be needed for cross-service E2E**:
1. Docker-compose test profile with test database
2. GitHub API mock server (or VCR-style recording)
3. Auth bypass middleware for test sessions
4. Playwright fixtures that wait for service health checks
5. Test data seeding scripts

**Estimated effort**: 2-3 sprints beyond Phase 3 scope.

**Recommendation**: Implement as a separate Phase 4 feature after Phase 3 blocking CI is stable. The httpx integration test from Phase C covers the critical integration path without infrastructure overhead.

---

### R-008: FIFO Queue Integration Test Patterns

**Task**: Research how to test strict FIFO ordering with 3+ pipelines.

**Decision**: Extend `test_queue_mode.py` with integration-level tests that simulate concurrent pipeline submissions and verify dequeue ordering.

**Rationale**: The existing `test_queue_mode.py` tests individual queue operations. The extension needs to verify the full lifecycle: submit pipeline A (starts running) → submit B (queued) → submit C (queued) → complete A → B starts → complete B → C starts. Strict FIFO is verified by checking `started_at` timestamps and agent assignment order.

**Key test structure**:
```python
# Submit 3 pipelines
pipeline_a = launch_pipeline(issue_number=1, project_id="PVT_test")
pipeline_b = launch_pipeline(issue_number=2, project_id="PVT_test")  # queued
pipeline_c = launch_pipeline(issue_number=3, project_id="PVT_test")  # queued

# Assert A is running, B and C are queued
assert not pipeline_a.queued
assert pipeline_b.queued
assert pipeline_c.queued

# Complete A, trigger dequeue
complete_pipeline(pipeline_a)
# Assert B is now running, C still queued
assert not pipeline_b.queued
assert pipeline_c.queued

# Complete B, trigger dequeue
complete_pipeline(pipeline_b)
# Assert C is now running
assert not pipeline_c.queued
```

**Alternatives considered**:
- Testing with real async concurrency — rejected; deterministic state transitions via direct function calls are more reliable and debuggable
- Using a separate test file — rejected; extending the existing `test_queue_mode.py` keeps queue tests collocated
