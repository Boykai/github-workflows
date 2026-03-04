# Quick Start: Codebase Cleanup — Reduce Technical Debt

**Feature**: 018-code-cleanup | **Date**: 2026-03-04

## What This Feature Does

Removes unused dependencies, consolidates duplicated test fixtures, and verifies the codebase is free of dead code, stale tests, and orphaned configurations. No new features are added — this is a maintenance-only change.

## Prerequisites

- Python ≥3.11 with pip
- Node.js ≥18 with npm
- Access to the repository on branch `018-code-cleanup`

## Implementation Order

Execute changes in this order to minimize risk and enable incremental CI verification:

### Phase 1: Remove Unused Backend Dependencies (lowest risk)

```bash
cd backend

# Edit pyproject.toml: remove these two lines from [project] dependencies:
#   "python-jose[cryptography]>=3.3.0",
#   "agent-framework-core>=1.0.0a1",

# Verify
pip install -e ".[dev]"
ruff check src tests
ruff format --check src tests
# Run tests file-by-file (running all at once may hang)
for f in tests/unit/test_*.py; do timeout 30 python -m pytest "$f" -q; done
```

### Phase 2: Remove Unused Frontend Dependencies (lowest risk)

```bash
cd frontend

# Remove unused packages
npm uninstall socket.io-client jsdom

# Verify
npx tsc --noEmit
npx eslint .
npx vitest run
npx vite build
```

### Phase 3: Consolidate Duplicated Test Fixtures (moderate risk)

```bash
cd backend

# 1. Add new factory functions to tests/helpers/mocks.py:
#    - make_mock_provider()
#    - make_mock_ai_service()
#    - make_mock_github_service()

# 2. Update consuming test files to import from helpers/mocks.py
#    instead of defining inline fixtures

# Verify each file after updating
python -m pytest tests/unit/test_ai_agent.py -q
python -m pytest tests/unit/test_workflow_orchestrator.py -q
# ... repeat for each modified test file
```

### Phase 4: Final Verification

```bash
# Backend
cd backend
ruff check src tests && ruff format --check src tests
pyright src
for f in tests/unit/test_*.py; do timeout 30 python -m pytest "$f" -q; done

# Frontend
cd frontend
npx tsc --noEmit
npx eslint .
npx vitest run
npx vite build
```

## What NOT to Change

- **DO NOT remove `github-copilot-sdk`** — it is lazily imported at runtime
- **DO NOT remove migration files** — they are loaded dynamically
- **DO NOT remove TODO comments** — they reference open work items
- **DO NOT modify public API contracts** (route paths, request/response shapes)
- **DO NOT remove the legacy token fallback** in `EncryptionService` — active sessions may use it

## Commit Convention

- `chore: remove unused dependency <name>` — for dependency removals
- `refactor: consolidate <fixture> test fixtures into helpers/mocks.py` — for test consolidation
- `chore: remove dead code in <file>` — for dead code removal (if any found during implementation)

## Risk Assessment

| Change | Risk | Mitigation |
|--------|------|------------|
| Remove `python-jose` | Very Low | Zero imports verified |
| Remove `agent-framework-core` | Very Low | Zero imports verified |
| Remove `socket.io-client` | Very Low | Frontend uses native WebSocket |
| Remove `jsdom` | Very Low | vitest uses happy-dom |
| Consolidate test fixtures | Low | Run affected tests after each change |
