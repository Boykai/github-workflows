# Data Model: Fix Silent Failures & Security

**Feature**: 033-fix-silent-failures-security
**Date**: 2026-03-10
**Status**: Complete

## Entities

### Exception Handler

An `except` block in the Python codebase that catches exceptions during runtime operations.

| Field | Type | Description |
|-------|------|-------------|
| `file_path` | string | Relative path to the source file (e.g., `backend/src/services/agent_creator.py`) |
| `line_number` | int | Line number of the `except` clause |
| `severity` | enum | `critical` \| `high` \| `medium` \| `intentional` — impact if the exception is silently swallowed |
| `exception_type` | string | The caught exception type (e.g., `Exception`, `httpx.HTTPStatusError`, `aiosqlite.Error`) |
| `has_binding` | bool | Whether the exception is captured with `as e` |
| `has_logging` | bool | Whether the handler includes a `logger.*()` call |
| `handler_action` | enum | `pass` \| `log` \| `fallback` \| `reraise` — what the handler does after catching |
| `log_level` | enum \| null | `debug` \| `warning` \| `error` \| null — the logging severity if `has_logging` is true |

**Validation Rules**:
- If `severity` is `critical` or `high`, then `has_logging` MUST be `true`
- If `has_logging` is `true`, then `has_binding` MUST be `true` (exception variable needed for log message)
- If `severity` is `intentional`, a documentation comment MUST exist in the code

**State Transitions**:

```text
[bare except + pass] → [except as e + logging]     (critical/high/medium fix)
[bare except + log]  → [except as e + log with e]   (binding improvement)
[broad Exception]    → [specific types as e]         (type narrowing)
[intentional bare]   → [intentional bare + comment]  (documentation only)
```

### Log Entry

A structured log statement added to an exception handler.

| Field | Type | Description |
|-------|------|-------------|
| `level` | enum | `debug` \| `warning` \| `error` — severity of the logged event |
| `message_template` | string | The log format string with `%s` placeholders (e.g., `"Failed to update branch_name for agent %s"`) |
| `context_identifiers` | list[string] | Variables included in the log message (e.g., `project_id`, `agent_id`, `branch_name`) |
| `exc_info` | bool | Whether the full traceback is included (always `True` for this feature) |

**Validation Rules**:
- `message_template` MUST include at least one context identifier for critical/high severity handlers
- `exc_info` MUST be `True` for all newly added log statements (per FR-005)
- `level` MUST match the severity mapping: `debug` for cleanup/parsing, `warning` for degraded states, `error` for data loss risks

### User-Facing Error Message

A sanitized message sent to end users when an internal error occurs.

| Field | Type | Description |
|-------|------|-------------|
| `channel` | enum | `signal` \| `api` — the external-facing channel |
| `message_text` | string | The generic friendly message shown to the user |
| `original_leak` | string | Description of what was previously leaked (for audit trail) |
| `server_log_level` | enum | `error` — internal logging severity for user-facing failures |

**Validation Rules**:
- `message_text` MUST NOT contain: exception class names, file paths, stack traces, database schemas, library versions, or internal identifiers
- `message_text` MUST be a hardcoded string (no f-string interpolation with exception variables)
- Every user-facing error MUST have a corresponding server-side log at `error` level with full exception details

## Relationships

```text
Exception Handler 1──* Log Entry
    │                   (each handler has 0 or 1 log entry;
    │                    0 only for intentional bare catches)
    │
    └──0..1 User-Facing Error Message
            (only handlers in external-facing code paths
             have associated user messages)
```

## Exception Handler Inventory

### Tier 1: Critical — Silent Failures (4 locations)

| ID | File | Line | Current State | Target State |
|----|------|------|--------------|--------------|
| EH-001 | `services/github_projects/service.py` | 927 | ✅ Fixed (logged) | Verify + narrow type |
| EH-002 | `services/github_projects/service.py` | ~4983 | ✅ Fixed (logged) | Verify + narrow type |
| EH-003 | `services/github_projects/__init__.py` | 49 | ✅ Fixed (logged) | Verify |
| EH-004 | `services/metadata_service.py` | 112 | ✅ Fixed (logged) | Verify + narrow type |

### Tier 2: High — DB Update Failures (4 locations)

| ID | File | Line | Current State | Target State |
|----|------|------|--------------|--------------|
| EH-005 | `services/agent_creator.py` | 727 | ✅ Fixed (logged) | Verify |
| EH-006 | `services/agent_creator.py` | 768 | ✅ Fixed (logged) | Verify |
| EH-007 | `services/agent_creator.py` | 877 | ✅ Fixed (logged) | Verify |
| EH-008 | `services/agent_creator.py` | 1095 | ✅ Fixed (logged) | Verify |

### Tier 3: Medium — Signal Context (1 location)

| ID | File | Line | Current State | Target State |
|----|------|------|--------------|--------------|
| EH-009 | `services/signal_chat.py` | 159 | ✅ Fixed (logged) | Verify |

### Tier 4: Security — Exception Detail Leaks (3 locations)

| ID | File | Line | Current State | Target State |
|----|------|------|--------------|--------------|
| EH-010 | `services/signal_chat.py` | 166-170 | ✅ Fixed (generic msg) | Verify |
| EH-011 | `services/signal_chat.py` | TBD | Audit needed | Verify all `_reply` paths |
| EH-012 | `services/signal_chat.py` | TBD | Audit needed | Verify all `_reply` paths |

### Tier 5: Code Quality — Bare Exception Blocks (37 remaining)

| ID | File | Count | Action |
|----|------|-------|--------|
| EH-100 | `services/workflow_orchestrator/config.py` | 9 | Add `as e`, add/improve logging |
| EH-101 | `services/chores/service.py` | 5 | Add `as e`, add/improve logging |
| EH-102 | `services/agents/service.py` | 4 | Add `as e`, add/improve logging |
| EH-103 | `services/copilot_polling/pipeline.py` | 2 | Add `as e`, add/improve logging |
| EH-104 | `services/chores/template_builder.py` | 1 | Add `as e`, add/improve logging |
| EH-105 | `services/blocking_queue.py` | 1 | Add `as e`, add/improve logging |
| EH-106 | `api/tasks.py` | 1 | Add `as e`, add/improve logging |
| EH-107 | `api/projects.py` | 1 | Add `as e`, add/improve logging |
| EH-108 | `api/signal.py` | 2 | Add `as e`, add/improve logging |
| EH-109 | `api/chores.py` | 2 | Add `as e`, add/improve logging |
| EH-110 | `api/workflow.py` | 2 | Add `as e`, add/improve logging |
| EH-111 | `api/auth.py` | 1 | Add `as e`, add/improve logging |
| EH-112 | `api/chat.py` | 1 | Add `as e`, add/improve logging |
| EH-113 | `logging_utils.py` | 4 | NO CHANGE — intentional resilience blocks |

### Tier 6: Intentional — Document Only (11 locations per spec)

These are already-verified intentional catches that need only documentation comments:
- `main.py:350,357` — `CancelledError` shutdown
- `services/signal_bridge.py:494` — `CancelledError`
- `api/workflow.py:472` — `ImportError` optional module
- `api/chat.py:137` — `RuntimeError` no event loop
- `services/model_fetcher.py:356` — `ValueError/TypeError` header parsing
- `services/github_projects/service.py:152,196` — `ValueError/TypeError` rate-limit parsing
- `services/chores/service.py:605` — `_BlockedIssueSkip` flow control
- `services/ai_agent.py:658` — `JSONDecodeError` with regex fallback
- `services/workflow_orchestrator/models.py:46` — `ValueError` status order fallback
