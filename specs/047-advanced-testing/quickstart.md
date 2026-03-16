# Quickstart: Advanced Testing for Deep Unknown Bugs

**Feature**: 047-advanced-testing  
**Branch**: `047-advanced-testing`

## Prerequisites

- Python ≥ 3.12 with backend virtualenv activated
- Node.js 22+ with frontend dependencies installed
- Docker Compose (for full-stack integration tests)
- Existing test infrastructure from feature 046 on `main`

## Quick Verification

### Backend Tests

```bash
cd solune/backend

# Run all new test directories
source .venv/bin/activate
pytest tests/concurrency/ -v      # Phase 7: Race condition tests
pytest tests/chaos/ -v             # Phase 8: Fault injection tests
pytest tests/property/ -v          # Phase 9: Stateful property tests (+ existing)
pytest tests/fuzz/ -v              # Phase 11: Fuzz tests
pytest tests/integration/ -v       # Phase 12: Thin-mock + migration tests

# Run specific test suites
pytest tests/property/test_pipeline_state_machine.py -v  # Pipeline state machine
pytest tests/property/test_bounded_cache_stateful.py -v  # Bounded cache stateful
pytest tests/concurrency/test_polling_races.py -v        # Polling race conditions
pytest tests/chaos/test_fault_injection.py -v            # External service faults
pytest tests/chaos/test_background_loops.py -v           # Watchdog/cleanup resilience
pytest tests/fuzz/test_webhook_fuzz.py -v                # Webhook payload fuzzing
pytest tests/fuzz/test_markdown_fuzz.py -v               # Markdown rendering fuzz
pytest tests/integration/test_migrations.py -v           # Migration regression
pytest tests/integration/test_thin_mock_flows.py -v      # Real-wiring integration

# Full suite with timing report
pytest --durations=20
```

### Frontend Tests

```bash
cd solune/frontend

# Run fuzz tests
npx vitest run src/__tests__/fuzz/

# Run with Zod validation active (dev mode)
npx vitest run --reporter=verbose
```

### CI Validation

```bash
# Flaky test detection (runs suite 3x)
# Triggered via: .github/workflows/flaky-detection.yml
# Schedule: Weekly cron (not per-PR)
gh workflow run flaky-detection.yml
```

## Key Files

| File | Purpose |
|---|---|
| `tests/concurrency/test_polling_races.py` | Concurrent polling state access tests |
| `tests/concurrency/test_transaction_safety.py` | Multi-step operation rollback tests |
| `tests/chaos/test_fault_injection.py` | External service failure injection |
| `tests/chaos/test_background_loops.py` | Watchdog & cleanup loop resilience |
| `tests/chaos/test_signal_message_loss.py` | Signal message loss demonstration |
| `tests/property/test_pipeline_state_machine.py` | Hypothesis stateful pipeline model |
| `tests/property/test_bounded_cache_stateful.py` | Hypothesis stateful cache model |
| `tests/fuzz/test_webhook_fuzz.py` | Random webhook payload generation |
| `tests/fuzz/test_markdown_fuzz.py` | Adversarial markdown rendering |
| `tests/integration/conftest.py` | Thin-mock test client fixture |
| `tests/integration/test_migrations.py` | Sequential migration regression |
| `tests/integration/test_thin_mock_flows.py` | Real-wiring user flow tests |
| `src/api/webhooks.py` | Webhook Pydantic model integration |
| `src/api/webhook_models.py` | New: typed webhook payload models |
| `frontend/src/services/schemas/*.ts` | New: Zod response validation schemas |
| `frontend/src/__tests__/fuzz/jsonParse.test.ts` | Frontend JSON.parse fuzz tests |
| `.github/workflows/flaky-detection.yml` | New: scheduled flaky test detection |

## Expected Outcomes

After implementation, running the full backend test suite should:
1. Surface at least one concurrency race condition in polling state
2. Demonstrate the Signal message loss bug (message dropped on processing error)
3. Verify 10,000+ pipeline state machine transitions without invalid states
4. Reject malformed webhook payloads with clear Pydantic validation errors
5. Complete all new tests within 60 additional seconds of CI time
