# Data Model: Codebase Cleanup — Reduce Technical Debt

**Feature**: 018-code-cleanup | **Date**: 2026-03-04

## Overview

This feature introduces **no new entities, tables, or data models**. It is a cleanup-only feature that removes dead code, consolidates duplicates, and removes unused dependencies. This document serves as the cleanup inventory — the structured catalog of all items identified for action.

---

## Cleanup Inventory

### Entity: Unused Backend Dependencies

| Item | File | Action | Validation |
|------|------|--------|------------|
| `python-jose[cryptography]>=3.3.0` | `backend/pyproject.toml` | REMOVE | Zero imports in `src/` and `tests/` |
| `agent-framework-core>=1.0.0a1` | `backend/pyproject.toml` | REMOVE | Zero imports; only in code comments |

**Relationships**: None — these packages have no transitive dependents in the project.

**Validation Rule**: After removal, `pip install -e ".[dev]"` must succeed and all tests must pass.

---

### Entity: Unused Frontend Dependencies

| Item | File | Action | Validation |
|------|------|--------|------------|
| `socket.io-client` | `frontend/package.json` (dependencies) | REMOVE | No imports; frontend uses native `WebSocket` API |
| `jsdom` | `frontend/package.json` (devDependencies) | REMOVE | vitest config uses `happy-dom`; `jsdom` never referenced |

**Relationships**: None — no other packages depend on these.

**Validation Rule**: After removal, `npm install && npm run build && npm test` must succeed.

---

### Entity: Duplicated Test Fixtures

| Fixture | Current Locations | Target Location | Action |
|---------|-------------------|-----------------|--------|
| `mock_provider()` | `test_ai_agent.py` (7 definitions) | `tests/helpers/mocks.py` | CONSOLIDATE |
| `mock_ai_service()` | `test_workflow_orchestrator.py` (4 definitions) | `tests/helpers/mocks.py` | CONSOLIDATE |
| `mock_github_service()` | Multiple test files (6 definitions) | `tests/helpers/mocks.py` | CONSOLIDATE |

**Relationships**: Each test file that defines a duplicate fixture must be updated to import from the consolidated location.

**Validation Rule**: After consolidation, all affected test files must pass with identical behavior.

---

### Entity: Retained Items (No Action)

These items were evaluated during research and explicitly retained:

| Item | Reason for Retention |
|------|---------------------|
| Legacy plaintext token fallback (`encryption.py`) | Active migration safety net; users may have pre-encryption sessions |
| Migration files (001–010) | Loaded dynamically by migration runner; must not be deleted |
| `github-copilot-sdk` dependency | Lazily imported at runtime in `CopilotCompletionProvider` |
| All TODO comments | Reference genuinely open work items |
| Service CRUD patterns | Domain-specific; forced abstraction violates Simplicity principle |
| Signal API docker service | Active production code, not orphaned |

---

## State Transitions

No state transitions apply. This feature does not modify runtime behavior, data flow, or entity lifecycle.

## Schema Changes

No database schema changes. No migrations added or removed.
