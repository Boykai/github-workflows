# Deprecation Policy Contract

**Feature**: 039-dead-code-cleanup
**Date**: 2026-03-13
**Version**: 1.0

## Purpose

Defines the standardized approach for annotating, monitoring, and removing deprecated code in the codebase. All legacy code paths identified in this feature MUST follow this contract to ensure consistent deprecation lifecycle management.

## Annotation Format

### Code Comments

All deprecated code MUST be annotated with the following format:

```python
# DEPRECATED(v2.0): <removal condition>. See issue #XXXX
```

Or for TypeScript/JSDoc:

```typescript
/** @deprecated Since v2.0. <removal condition>. See issue #XXXX */
```

### Required Fields

| Field | Description | Example |
|-------|-------------|---------|
| Version | Semver version when deprecation was declared | `v2.0` |
| Condition | Specific measurable condition for removal | "Remove once all active issues use 5-column format" |
| Issue | GitHub issue tracking the deprecation | `#XXXX` |

### Optional Fields

| Field | Description | Example |
|-------|-------------|---------|
| Added | Date the deprecation annotation was added | `2026-03-13` |
| Monitoring | How to check removal readiness | "Check legacy_format_encountered logs" |

## Monitoring Strategy

### Legacy Format Encounter Logging

When the system encounters data in a deprecated format, it MUST log the encounter:

```python
logger.info(
    "legacy_format_encountered",
    extra={
        "format_type": "4_column_tracking",  # or "flat_agents", "flat_execution_mode"
        "context": "agent_tracking.parse_rows",
        "issue_number": issue_number,
    },
)
```

**Log level**: INFO (not WARNING — legacy format is expected during migration period)

**Structured fields**:
- `format_type`: Identifies which deprecated format was encountered
- `context`: Code path that triggered the fallback
- `issue_number` / `project_id`: Data identifier for debugging

### Removal Readiness Criteria

Legacy code can be removed when ALL of the following are true:
1. Zero `legacy_format_encountered` log events for the specific `format_type` over 30 consecutive days
2. All unit tests pass without the legacy code path
3. The deprecation tracking issue is updated with removal date

## Deprecated Code Inventory

### Backend

| Code Path | File | Line(s) | Format Type | Replacement |
|-----------|------|---------|-------------|-------------|
| `_ROW_RE_OLD` regex | `agent_tracking.py` | 61–62 | `4_column_tracking` | `_ROW_RE` (5-column) |
| LEGACY pipeline path | `pipeline.py` | 2075+ | `legacy_pipeline` | Pipeline-based tracking |
| `agents` field | `pipeline.py` | 44 | `flat_agents` | `groups[].agents` |
| `execution_mode` field | `pipeline.py` | 46 | `flat_execution_mode` | `groups[].execution_mode` |
| Legacy normalization | `pipelines/service.py` | 215, 238, 300 | `flat_agents` | Group-based normalization |

### Frontend

| Code Path | File | Line(s) | Format Type | Replacement |
|-----------|------|---------|-------------|-------------|
| `old_status` field | `index.ts` | 97 | `old_status` | `current_status` / `target_status` |
| `agents` TS field | `index.ts` | 1072 | `flat_agents` | `groups[].agents` |
| `execution_mode` TS field | `index.ts` | 1075 | `flat_execution_mode` | `groups[].execution_mode` |
| `clearLegacyStorage` | `useChatHistory.ts` | 40–47 | N/A | Keep with `@internal` if security-relevant |

### Test Utilities

| Code Path | File | Line(s) | Action |
|-----------|------|---------|--------|
| `_resetForTesting` | `useScrollLock.ts` | 76–80 | Add `@internal` JSDoc annotation |

## Internal Annotations

For code that is not deprecated but should not be used externally:

```typescript
/**
 * @internal Test-only reset function. Do not use in production code.
 */
export function _resetForTesting(): void { ... }
```

**Rule**: Functions prefixed with `_` that are exported solely for test access MUST have `@internal` JSDoc annotations.

## Documentation Updates

When deprecation annotations are added:
1. Update `docs/configuration.md` if the deprecated feature is documented
2. Update inline code documentation if the deprecated code has JSDoc/docstrings
3. Do NOT update README or public-facing docs until the code is actually removed

## Verification

After annotation:
- Every item in the Deprecated Code Inventory has a corresponding `DEPRECATED(vX.Y)` comment
- Every monitoring point has an `logger.info("legacy_format_encountered", ...)` call
- All existing tests pass — annotations do not change behavior
- No deprecated code is removed prematurely (only annotated)
