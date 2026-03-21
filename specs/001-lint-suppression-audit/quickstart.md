# Quickstart: Lint & Type Suppression Audit

**Feature**: 001-lint-suppression-audit | **Date**: 2026-03-21

## What This Feature Does

This feature audits and resolves ~115 inline suppression statements (`# noqa`, `# type: ignore`, `# pyright:`, `eslint-disable`, `@ts-expect-error`) across the Solune backend and frontend, reducing them by at least 50%. Each remaining suppression is documented with an inline justification comment.

## Prerequisites

- Python ≥3.12 (3.13 recommended)
- Node.js ≥18
- Repository cloned at `solune/`

## Verification Commands

### Backend

```bash
cd solune/backend

# Install dependencies
pip install -e ".[dev]"

# Run linter (should pass with zero errors)
ruff check src/

# Run type checker (should pass with zero errors)
python -m pyright src/

# Run tests (all 3,365+ should pass)
python -m pytest tests/unit/ -x -q --timeout=30

# Count remaining suppressions (target: significant reduction from baseline)
grep -rn "# type: ignore\|# noqa\|# pyright:" src/ tests/ | wc -l
```

### Frontend

```bash
cd solune/frontend

# Install dependencies
npm ci

# Run linter (should pass with zero errors)
npx eslint .

# Run type checker (should pass with zero errors)
npx tsc --noEmit

# Run tests (all 1,219+ should pass)
npx vitest run

# Count remaining suppressions (target: significant reduction from baseline)
grep -rn "eslint-disable\|@ts-expect-error" src/ | wc -l
```

## Implementation Order

The feature is organized into 4 independent user stories that can be implemented in any order:

| Phase | User Story | Priority | Scope |
|-------|-----------|----------|-------|
| 1 | Backend type suppressions | P1 | 39 `type: ignore` + 10 `pyright:` in `src/` |
| 2 | Frontend a11y & hooks | P2 | 14 `eslint-disable` in `src/` |
| 3 | Backend linter suppressions | P3 | 21 `noqa` in `src/` |
| 4 | Test file suppressions | P4 | 26 `type: ignore` in tests + 5 `@ts-expect-error` |

## Key Design Decisions

1. **`cast(T, value)` for cache returns** — chosen over generic cache refactoring (simpler, no behavioral change)
2. **Global B008 ignore** in `pyproject.toml` — FastAPI `Depends()` is a well-known false positive; per-rule config is cleaner than 12 inline suppressions
3. **Retain `os.path` in `api/chat.py`** — CodeQL recognizes `os.path.basename` as a path-traversal sanitizer; switching to `pathlib` could break security analysis
4. **Retain file-level `pyright: reportAttributeAccessIssue=false`** in `github_projects/*.py` — GitHub API responses use dynamic attribute access; typing all response shapes is out of scope
5. **Retain `@ts-expect-error` in test files** — overriding read-only DOM globals (`WebSocket`, `crypto`) is necessary for test setup; no typed alternative exists

## Files Changed

See the **Project Structure** section in [plan.md](./plan.md) for the complete list of affected files.
