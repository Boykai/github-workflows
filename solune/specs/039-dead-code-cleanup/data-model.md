# Data Model: Dead Code & Technical Debt Cleanup

**Feature**: 039-dead-code-cleanup
**Date**: 2026-03-13
**Status**: Complete

## Overview

This feature does not introduce new persistent data entities. It modifies existing code structure through refactoring, annotation, and consolidation. The entities below describe the conceptual models used to track cleanup progress and the runtime structures affected by the changes.

## Entities

### 1. DeprecationAnnotation

**Description**: A structured code comment marking legacy code for future removal. Not a runtime entity — exists only as source code annotations.

| Field | Type | Description |
|-------|------|-------------|
| format | string | `DEPRECATED(vX.Y)` prefix in comment |
| target_version | string | Version at which removal is planned (e.g., `v2.0`) |
| condition | string | Removal prerequisite (e.g., "all issues use pipeline-based tracking") |
| tracking_issue | string | GitHub issue number for tracking (e.g., `#XXXX`) |
| location | string | File path and line number of annotated code |

**Validation Rules**:
- Every legacy code path must have exactly one deprecation annotation
- Annotation must include both a removal condition and a tracking issue
- Version number must follow semver format

**Relationships**:
- Applied to LegacyCodePath entities
- Monitored by LegacyFormatEncounter logging

---

### 2. LegacyCodePath

**Description**: A code branch maintained for backward compatibility with older data formats or workflows. Identified during the audit and annotated with deprecation metadata.

| Field | Type | Description |
|-------|------|-------------|
| name | string | Descriptive identifier (e.g., `_ROW_RE_OLD`, `LEGACY pipeline path`) |
| file | string | Source file containing the legacy code |
| line_range | string | Start–end line numbers |
| purpose | string | Why this code exists (e.g., "parses old 4-column format") |
| replacement | string | New code path that supersedes this one |
| active_usage | boolean | Whether the legacy path is still hit in production |

**Validation Rules**:
- Each legacy code path must have a documented replacement
- Active-usage status must be verified before annotating as deprecated

**Relationships**:
- Annotated with DeprecationAnnotation
- Monitored via LegacyFormatEncounter

**Instances identified**:

| Name | File | Replacement |
|------|------|-------------|
| `_ROW_RE_OLD` | `agent_tracking.py` L61–62 | `_ROW_RE` (5-column format) |
| LEGACY pipeline path | `pipeline.py` L2075+ | Pipeline-based tracking |
| `agents` field | `pipeline.py` L44 | `groups[].agents` |
| `execution_mode` field | `pipeline.py` L46 | `groups[].execution_mode` |
| `old_status` field | `index.ts` L97 | `current_status` / `target_status` |
| `agents` TS field | `index.ts` L1072 | `groups[].agents` |
| `execution_mode` TS field | `index.ts` L1075 | `groups[].execution_mode` |
| `clearLegacyStorage` | `useChatHistory.ts` L40–47 | N/A (security cleanup, may be kept) |

---

### 3. LegacyFormatEncounter

**Description**: A runtime log event emitted when the system encounters data in a deprecated format. Used to monitor migration adoption rate and determine when legacy code can be safely removed.

| Field | Type | Description |
|-------|------|-------------|
| timestamp | datetime | UTC timestamp of encounter |
| format_type | string | `"4_column_tracking"` \| `"flat_agents"` \| `"flat_execution_mode"` |
| context | string | Which code path triggered the encounter |
| issue_number | int \| None | GitHub issue number (if applicable) |
| project_id | string \| None | Project ID (if applicable) |

**Validation Rules**:
- Log level must be INFO (not WARNING or ERROR — legacy format is expected during migration)
- Context must identify the specific code path for debugging

**Relationships**:
- Emitted by LegacyCodePath fallback branches
- Aggregated to determine DeprecationAnnotation removal readiness

---

### 4. ErrorHandler (Refactored Pattern)

**Description**: The consolidated error handling pattern replacing 20 inline exception handlers. Not a new entity — describes the refactored usage of the existing `handle_service_error` function.

| Field | Type | Description |
|-------|------|-------------|
| operation | string | Human-readable description of the failed operation |
| error_cls | type | `AppException` subclass to raise (e.g., `ValidationError`, `GitHubAPIError`) |
| exc | Exception | The caught exception |

**Validation Rules**:
- Operation string must be descriptive enough for log analysis
- Error class must be an `AppException` subclass (never raw `Exception`)
- Function always raises — return type is `NoReturn`

**Pattern**:
```python
# Before (inline):
except Exception as e:
    logger.error("Failed to fetch project: %s", e, exc_info=True)
    raise ValidationError(message="Failed to fetch project") from e

# After (consolidated):
except Exception as e:
    handle_service_error(e, "fetch project", ValidationError)
```

**Exceptions to migration**:
- WebSocket handlers (different error propagation semantics)
- Non-fatal catches (e.g., `logger.warning(...)` with fallback return value)
- Chat error-response patterns (create ChatMessage and return, don't raise)

---

### 5. CachedFetch (New Utility)

**Description**: A generic async utility that wraps the repeated cache-check/fetch/set pattern. Added to `backend/src/services/cache.py`.

| Field | Type | Description |
|-------|------|-------------|
| cache | InMemoryCache | The cache instance to use |
| key | string | Cache key for the data |
| fetch_fn | Callable | Async function to call on cache miss |
| ttl_seconds | int | Cache entry TTL (default: 300) |
| refresh | bool | If true, bypass cache and fetch fresh data |
| stale_fallback | bool | If true, serve expired data when fetch fails |

**Validation Rules**:
- Cache key must be non-empty
- TTL must be > 0
- fetch_fn must be an async callable

**Relationships**:
- Uses InMemoryCache.get(), .get_stale(), .set()
- Adopted by board.py, projects.py, chat.py cache patterns

---

### 6. ComplexityTarget

**Description**: A function identified as a complexity hotspot with a decomposition plan. Not a runtime entity — used for tracking decomposition progress.

| Field | Type | Description |
|-------|------|-------------|
| function_name | string | Fully qualified function name |
| file | string | Source file path |
| current_cc | int | Current cyclomatic complexity |
| target_cc | int | Maximum CC after decomposition |
| sub_functions | list[string] | Names of extracted sub-functions |
| status | enum | `"planned"` \| `"in_progress"` \| `"complete"` \| `"verified"` |

**Instances**:

| Function | File | Current CC | Target CC |
|----------|------|-----------|-----------|
| `post_agent_outputs_from_pr` | `agent_output.py` | 123 | < 30 |
| `assign_agent_for_status` | `orchestrator.py` | 91 | < 25 |
| `recover_stalled_issues` | `recovery.py` | 72 | < 20 |
| `GlobalSettings` | `GlobalSettings.tsx` | 96 | < 30 |
| `LoginPage` | `LoginPage.tsx` | 90 | < 30 |

---

### 7. MigrationPlan (Planning Artifact)

**Description**: A planning document for architectural migrations deferred to separate specifications. Not a runtime entity — exists as documentation.

| Field | Type | Description |
|-------|------|-------------|
| name | string | Migration identifier (e.g., `singleton-removal`, `sqlite-migration`) |
| affected_files | list[string] | All files requiring changes |
| affected_count | int | Number of code paths to update |
| current_pattern | string | Description of current (legacy) approach |
| target_pattern | string | Description of desired (new) approach |
| blocking_issues | list[string] | Prerequisites that must be resolved first |

**Instances**:

| Name | Affected Files | Count |
|------|---------------|-------|
| Singleton removal (`github_projects_service`) | 17+ files | 17+ import sites |
| In-memory store migration (`chat.py` dicts → SQLite) | 1 file, 15+ code paths | 15+ paths |

---

## State Transitions

### Deprecation Lifecycle

```
  UNDOCUMENTED ──────▶ ANNOTATED ──────▶ MONITORING ──────▶ REMOVAL-READY ──────▶ REMOVED
       │                   │                  │                    │                  │
   (no comment)      (DEPRECATED(vX.Y)   (logging active,    (0 encounters       (code deleted,
                      annotation added)   encounters tracked)  over 30 days)       tests pass)
```

### Error Handler Migration Lifecycle

```
  INLINE ──────▶ IDENTIFIED ──────▶ MIGRATED ──────▶ VERIFIED
    │                │                  │                │
  (raw try/     (categorized as     (replaced with   (tests pass,
   except)       candidate/skip)     handle_service_  no regressions)
                                     error)
```

### Complexity Reduction Lifecycle

```
  HOTSPOT ──────▶ ANALYZED ──────▶ DECOMPOSED ──────▶ VERIFIED
     │                │                 │                  │
  (CC > target)   (sub-functions    (extract method    (CC measured,
                   identified)       refactoring done)   all < target)
```

## Entity Relationship Diagram

```
  ┌─────────────────────┐       ┌──────────────────────┐
  │  LegacyCodePath     │──────▶│ DeprecationAnnotation │
  │  (8 instances)      │ 1:1   │  (structured comment) │
  └──────────┬──────────┘       └──────────────────────┘
             │
             │ emits
             ▼
  ┌─────────────────────┐
  │ LegacyFormatEncounter│
  │  (runtime log)      │
  └─────────────────────┘

  ┌─────────────────────┐       ┌──────────────────────┐
  │  ErrorHandler        │──────▶│  handle_service_error │
  │  (20 inline → 0)   │ uses  │  (existing utility)   │
  └─────────────────────┘       └──────────────────────┘

  ┌─────────────────────┐       ┌──────────────────────┐
  │  CachedFetch         │──────▶│  InMemoryCache       │
  │  (new utility)      │ wraps │  (existing class)     │
  └─────────────────────┘       └──────────────────────┘

  ┌─────────────────────┐       ┌──────────────────────┐
  │  ComplexityTarget    │──────▶│  Extracted Functions  │
  │  (5 hotspots)       │ 1:N   │  (private, co-located)│
  └─────────────────────┘       └──────────────────────┘

  ┌─────────────────────┐
  │  MigrationPlan       │
  │  (2 deferred specs) │
  └─────────────────────┘
```
