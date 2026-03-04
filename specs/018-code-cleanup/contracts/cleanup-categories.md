# Cleanup Contracts: Codebase Cleanup — Reduce Technical Debt

**Feature**: 018-code-cleanup | **Date**: 2026-03-04

## Overview

This document defines the change contracts for each cleanup category. Since this feature modifies only internal implementation (no public API changes), these contracts specify what will change, what will NOT change, and how to verify each change.

---

## Contract 1: Remove Backwards-Compatibility Shims

### Scope

**No actionable shims identified.** The only backwards-compatibility pattern (legacy plaintext token fallback in `EncryptionService.decrypt()`) is explicitly retained because active user sessions may still contain pre-encryption tokens.

### Changes

None.

### Invariants (must NOT change)

- `EncryptionService.decrypt()` behavior for both encrypted and plaintext tokens
- All public API response shapes
- All migration file contents

### Verification

- `ruff check src tests` — passes
- `pytest tests/unit/test_token_encryption.py` — all tests pass

---

## Contract 2: Eliminate Dead Code — Unused Dependencies

### Scope

Remove 4 unused package dependencies (2 backend, 2 frontend).

### Changes

| File | Change | Reason |
|------|--------|--------|
| `backend/pyproject.toml` | Remove `python-jose[cryptography]>=3.3.0` from `dependencies` | Zero imports anywhere in codebase |
| `backend/pyproject.toml` | Remove `agent-framework-core>=1.0.0a1` from `dependencies` | Zero imports; only referenced in code comments |
| `frontend/package.json` | Remove `socket.io-client` from `dependencies` | Frontend uses native `WebSocket`, not Socket.IO |
| `frontend/package.json` | Remove `jsdom` from `devDependencies` | Tests use `happy-dom`; `jsdom` never configured or imported |

### Invariants (must NOT change)

- No source code changes required (these packages are never imported)
- All existing imports continue to resolve
- No public API contracts affected
- `github-copilot-sdk` is NOT removed (lazily imported at runtime)

### Verification

**Backend**:
```bash
cd backend
pip install -e ".[dev]"
ruff check src tests
ruff format --check src tests
python -m pytest tests/unit/test_completion_providers.py -q  # verify copilot SDK still works
python -m pytest tests/unit/ -q  # run per-file for stability
```

**Frontend**:
```bash
cd frontend
npm install
npx tsc --noEmit
npx eslint .
npx vitest run
npx vite build
```

---

## Contract 3: Consolidate Duplicated Test Fixtures

### Scope

Extract 3 families of duplicated test fixtures into shared helpers in `tests/helpers/mocks.py`.

### Changes

| Fixture | From | To | Signature |
|---------|------|----|-----------|
| `mock_provider()` | 7 inline defs in `test_ai_agent.py` | `tests/helpers/mocks.py` | `make_mock_provider() -> AsyncMock` |
| `mock_ai_service()` | 4 inline defs in `test_workflow_orchestrator.py` | `tests/helpers/mocks.py` | `make_mock_ai_service() -> AsyncMock` |
| `mock_github_service()` | 6 inline defs across files | `tests/helpers/mocks.py` | `make_mock_github_service() -> AsyncMock` |

### Invariants (must NOT change)

- All test assertions produce identical results
- No production code is modified
- Existing shared helpers in `mocks.py` and `factories.py` are preserved
- Public API contracts are unaffected

### Verification

```bash
cd backend
python -m pytest tests/unit/test_ai_agent.py -q
python -m pytest tests/unit/test_workflow_orchestrator.py -q
# Plus all files that previously defined mock_github_service()
ruff check tests
```

---

## Contract 4: Delete Stale Tests

### Scope

**No stale tests identified.** All test files test currently-existing production code. No action required.

### Changes

None.

### Verification

Full test suite passes (baseline confirmation):
```bash
cd backend && python -m pytest tests/unit/ -q
cd frontend && npx vitest run
```

---

## Contract 5: General Hygiene

### Scope

No actionable hygiene items beyond the dependency removals in Contract 2.

- All TODO/FIXME/HACK comments reference genuinely open work items → RETAIN
- No orphaned migrations, configs, or environment variables found
- No stale Docker Compose services found

### Changes

None beyond Contract 2.

### Verification

- Grep for `TODO|FIXME|HACK` confirms all remaining comments are legitimate
- All CI checks pass
