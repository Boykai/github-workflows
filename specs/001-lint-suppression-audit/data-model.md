# Data Model: Lint & Type Suppression Audit

**Feature**: 001-lint-suppression-audit | **Date**: 2026-03-21

## Overview

This feature is an internal code-quality refactoring — it does not introduce new runtime data structures, database tables, or API models. The "data model" here describes the conceptual entities used to organize and track the audit work.

## Entity: Suppression Statement

A single inline directive that disables a specific linter or type-checker rule.

| Field | Type | Description |
|-------|------|-------------|
| `file_path` | `string` | Relative path from repository root (e.g., `solune/backend/src/services/cache.py`) |
| `line_number` | `integer` | 1-based line number in the file |
| `directive_type` | `enum` | One of: `noqa`, `type: ignore`, `pyright:`, `eslint-disable`, `@ts-expect-error` |
| `rule_code` | `string` | Specific rule being suppressed (e.g., `B008`, `return-value`, `react-hooks/exhaustive-deps`) |
| `category` | `enum` | One of: `type-safety`, `lint`, `accessibility`, `test-specific`, `security` |
| `disposition` | `enum` | One of: `removed` (underlying issue fixed), `retained` (justified and documented) |
| `justification` | `string \| null` | If retained: inline comment explaining why suppression is necessary |
| `user_story` | `enum` | US-1 (backend type), US-2 (frontend a11y/hooks), US-3 (backend lint), US-4 (test files) |

## Entity: Suppression Category

A logical grouping of related suppressions by their root cause.

| Category Name | Affected Rules | Count | Resolution Pattern |
|---------------|---------------|-------|-------------------|
| Cache return types | `type: ignore[return-value]` | 12 | `cast(T, value)` |
| Generic type parameters | `type: ignore[type-arg]` | 6 | Add `[None]` or `[Any]` to `asyncio.Task` |
| Conditional imports | `type: ignore[reportMissingImports]` | 5 | Retain with justification (optional packages) |
| Argument type mismatches | `type: ignore[arg-type]` | 7 | Fix type annotations, add guards |
| Dynamic attribute access | `pyright: reportAttributeAccessIssue` | 10 | Retain with justification (GitHub API responses) |
| FastAPI dependency injection | `noqa: B008` | 12 | Global config exemption |
| Module re-exports | `noqa: F401` | 6 | `__all__` declarations |
| Security-critical paths | `noqa: PTH118/PTH119` | 2 | Retain (CodeQL sanitizer) |
| Late imports | `noqa: E402` | 1 | Retain with justification |
| Accessibility patterns | `eslint-disable jsx-a11y` | 5 | Semantic elements for backdrop; retain autofocus |
| React hook dependencies | `eslint-disable react-hooks` | 7 | Fix deps or retain with justification |
| Explicit any types | `eslint-disable no-explicit-any` | 2 | Typed interface or retain |
| Test mock overrides | `type: ignore` (various) | 26 | Typed spies, cast, or retain |
| Test global shims | `@ts-expect-error` | 5 | Retain (read-only DOM globals) |

## Relationships

```text
Suppression Statement  ──belongs to──▶  Suppression Category
Suppression Statement  ──maps to──▶     User Story (1, 2, 3, or 4)
Suppression Category   ──has──▶         Resolution Pattern
```

## State Transitions

Each suppression follows one of two paths:

```text
IDENTIFIED  ──audit──▶  REMOVABLE  ──fix applied──▶  REMOVED
IDENTIFIED  ──audit──▶  JUSTIFIED  ──comment added──▶  RETAINED
```

No suppressions remain in the `IDENTIFIED` state after the audit is complete.

## Validation Rules

1. Every suppression with `disposition = retained` MUST have a non-null `justification` field
2. Every suppression with `disposition = removed` MUST NOT introduce new linter/type-checker errors
3. The total count of `disposition = retained` suppressions MUST be ≤58 (50% of baseline 115)
4. No suppression may be re-suppressed with a different rule code (no rule-swapping)
