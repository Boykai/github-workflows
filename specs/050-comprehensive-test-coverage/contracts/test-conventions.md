# Contract: Test File Naming and Organization

**Feature**: `050-comprehensive-test-coverage`
**Date**: 2026-03-17

---

## Backend Test File Conventions

### Directory Structure

```
solune/backend/tests/
├── unit/                           # Fast, isolated tests
│   ├── test_api_*.py               # API endpoint tests (one per router)
│   ├── test_*_service.py           # Service layer tests
│   └── test_*.py                   # Other unit tests
├── integration/                    # Cross-component tests
│   ├── test_pipeline_lifecycle.py  # Pipeline end-to-end
│   ├── test_chat_flow.py           # Chat interaction flow
│   ├── test_webhook_processing.py  # Webhook end-to-end
│   ├── test_db_migrations.py       # Migration correctness
│   ├── test_websocket_lifecycle.py # WebSocket lifecycle
│   ├── test_rate_limiting.py       # Rate limiting end-to-end
│   ├── test_guard_config.py        # Guard config validation
│   └── test_chore_scheduling.py    # Chore scheduling cycle
├── property/                       # Hypothesis property-based tests
│   ├── test_graphql_invariants.py
│   ├── test_model_roundtrips.py
│   ├── test_encryption_roundtrip.py
│   ├── test_state_machines.py
│   └── test_pipeline_config.py
├── fuzz/                           # Fuzz tests
│   ├── test_webhook_fuzz.py
│   ├── test_chat_injection.py
│   └── test_upload_fuzz.py
├── chaos/                          # Chaos engineering tests
├── concurrency/                    # Concurrency tests
├── architecture/                   # Architecture tests
├── helpers/                        # Shared test utilities
│   ├── factories.py
│   └── assertions.py
└── conftest.py                     # Shared fixtures
```

### Naming Conventions

- Unit test files: `test_{module_name}.py` (e.g., `test_signal_bridge.py`)
- API test files: `test_api_{router_name}.py` (e.g., `test_api_chat.py`)
- Integration test files: `test_{workflow_name}.py` (e.g., `test_pipeline_lifecycle.py`)
- Property test files: `test_{invariant_name}.py` (e.g., `test_model_roundtrips.py`)
- Fuzz test files: `test_{target}_fuzz.py` (e.g., `test_webhook_fuzz.py`)

### Test Function Patterns

```python
# Happy path
async def test_{function}_success():
    """Test {function} with valid input returns expected result."""

# Error path
async def test_{function}_error_{condition}():
    """Test {function} raises {exception} when {condition}."""

# Parameterized API tests
@pytest.mark.parametrize("status_code,setup", [
    (200, {"valid": True}),
    (401, {"no_auth": True}),
    (403, {"wrong_user": True}),
    (404, {"missing": True}),
    (422, {"invalid_body": True}),
    (429, {"rate_limited": True}),
    (500, {"server_error": True}),
])
async def test_{endpoint}_{method}_status_codes(status_code, setup, client):
    """Test {endpoint} returns correct status for various conditions."""
```

---

## Frontend Test File Conventions

### Directory Structure

```
solune/frontend/src/
├── hooks/
│   ├── useChat.ts
│   ├── useChat.test.tsx           # Hook tests alongside source
│   └── ...
├── components/
│   ├── TopBar.tsx
│   ├── TopBar.test.tsx            # Component tests alongside source
│   └── settings/
│       ├── SettingsSection.tsx
│       └── SettingsSection.test.tsx
├── services/
│   ├── api.ts
│   └── api.test.ts
├── lib/
│   └── schemas/
│       ├── pipeline.ts
│       └── pipeline.test.ts
└── test/
    ├── setup.ts                   # Global test setup
    ├── test-utils.tsx             # renderWithProviders, createTestQueryClient
    └── factories/
        └── index.ts               # createMockUser, createMockProject, etc.
```

### Naming Conventions

- Test files: `{source_file}.test.{ts,tsx}` (colocated with source)
- Property test files: `{source_file}.property.test.ts`
- E2E test files: `{feature}.spec.ts` (in `e2e/` directory)

### Test Function Patterns

```typescript
// Hook tests
describe('useChat', () => {
  it('should return messages on successful fetch', async () => {});
  it('should handle error state', async () => {});
  it('should handle loading state', () => {});
  it('should handle empty/null response', async () => {});
  it('should invalidate cache on mutation', async () => {});
});

// Component tests
describe('TopBar', () => {
  it('should render correctly', () => {});
  it('should handle user interaction', async () => {});
  it('should have no accessibility violations', async () => {
    const { container } = renderWithProviders(<TopBar />);
    await expectNoA11yViolations(container);
  });
});

// Schema negative tests
describe('pipelineSchema', () => {
  it('should reject malformed payload', () => {});
  it('should reject missing required fields', () => {});
  it('should handle type coercion', () => {});
});
```

---

## E2E Test Conventions

### Spec File Structure

```typescript
// e2e/{feature}.spec.ts
import { test, expect } from './fixtures';

test.describe('{Feature} Page', () => {
  test('should {action} when {condition}', async ({ page }) => {
    // Navigate
    await page.goto('/{route}');
    // Interact
    await page.click('[data-testid="{element}"]');
    // Assert
    await expect(page.locator('[data-testid="{result}"]')).toBeVisible();
  });
});
```

### Visual Regression Pattern

```typescript
test('visual regression - {page} - {viewport} - {mode}', async ({ page }) => {
  await page.goto('/{route}');
  await page.emulateMedia({ colorScheme: '{light|dark}' });
  await expect(page).toHaveScreenshot('{page}-{viewport}-{mode}.png', {
    maxDiffPixelRatio: 0.01,
  });
});
```

### Viewport Definitions

| Name | Width | Height |
|------|-------|--------|
| `mobile` | 375 | 667 |
| `tablet` | 768 | 1024 |
| `desktop` | 1280 | 720 |
