# Logging Contract: Fix Silent Failures & Security

**Feature**: 033-fix-silent-failures-security
**Date**: 2026-03-10
**Status**: Complete

## Overview

This contract defines the logging and error-response standards for all exception handlers modified in this feature. Since this feature does not introduce new API endpoints or data models, the contract covers the internal logging interface and user-facing error message format.

## Logging Severity Contract

All exception handlers in `backend/src/` MUST follow this severity mapping:

| Severity | Log Level | When to Use | Example |
|----------|-----------|-------------|---------|
| Critical | `logger.warning()` | Core service operation fails but system can degrade gracefully | Workflow config fetch, metadata read, branch OID update |
| High | `logger.error()` | Data persistence fails — may cause orphaned resources or broken references | DB update of issue number, branch name, PR number |
| Medium | `logger.warning()` | Context information is lost — may cause confusing downstream behavior | Signal repo resolution failure, owner/repo resolution |
| Low | `logger.debug()` | Expected/acceptable failure in non-critical path | Client cleanup during shutdown, rate-limit header parsing |
| Intentional | None | Catch is correct by design; handler has documented fallback logic | `CancelledError`, `ImportError`, `_BlockedIssueSkip` |

## Log Message Format Contract

All log messages MUST follow this format:

```python
logger.<level>("<descriptive message> for %s", <context_identifier>, exc_info=True)
```

### Required Fields

| Field | Requirement |
|-------|-------------|
| Message template | Descriptive string using `%s` lazy formatting (NOT f-strings) |
| Context identifier | At least one identifying variable (`project_id`, `agent_id`, `branch_name`, etc.) |
| `exc_info` | MUST be `True` to include full traceback |

### Examples

```python
# Critical: Service operation failure
logger.warning("Workflow config fetch failed for project: %s", project_id, exc_info=True)

# High: DB write failure
logger.error("Failed to update github_issue_number for agent %s", agent_id, exc_info=True)

# Medium: Context loss
logger.warning("Signal: could not resolve repository for project %s", project_id, exc_info=True)

# Low: Cleanup failure
logger.debug("Client cleanup failed", exc_info=True)
```

## Exception Binding Contract

All `except` clauses MUST bind the exception variable:

```python
# ✅ Correct
except Exception as e:
    logger.warning("Operation failed: %s", context, exc_info=True)

# ✅ Correct — narrowed type
except (httpx.HTTPStatusError, KeyError) as e:
    logger.warning("Operation failed: %s", context, exc_info=True)

# ❌ Incorrect — no binding
except Exception:
    logger.warning("Operation failed: %s", context, exc_info=True)

# ✅ Exception — logging_utils.py resilience blocks
except Exception:
    # Resilience: never let sanitization crash the caller.
    message = "[REDACTION_ERROR] <message could not be sanitized>"
```

## User-Facing Error Response Contract

All external-facing error messages MUST follow these rules:

### Signal Messages

```python
# ✅ Correct — generic message, details logged server-side
logger.error("Signal #agent command failed for %s: %s", source_phone, exc, exc_info=True)
await _reply(source_phone, "⚠️ Something went wrong processing your #agent command. Please try again.")

# ❌ Incorrect — leaks exception details
await _reply(source_phone, f"Error processing #agent command: {exc}")
```

### Rules

1. User-facing messages MUST be hardcoded strings (no exception interpolation)
2. Messages MUST use the ⚠️ prefix for consistency
3. Messages MUST include a call-to-action ("Please try again", "Please contact support")
4. Full exception details MUST be logged server-side at `error` level before sending the user message
5. The `safe_error_response()` utility from `logging_utils.py` SHOULD be used for API-layer error handling

## Exception Type Narrowing Contract

High-priority narrowing targets:

| Location | Current | Target | Rationale |
|----------|---------|--------|-----------|
| `service.py` workflow config | `except Exception` | `except (KeyError, httpx.HTTPStatusError)` | Only dict access and HTTP calls in try block |
| `service.py` branch OID | `except Exception` | `except (httpx.HTTPStatusError, ValueError)` | HTTP call + type conversion |
| `metadata_service.py` SQLite | `except Exception` | `except (aiosqlite.Error, KeyError)` | DB operation + dict access |
| `__init__.py` cleanup | `except Exception` | `except Exception` (keep broad) | Cleanup can fail in many ways; keep broad but bind `as e` |

## Verification Contract

After implementation, the following checks MUST pass:

```bash
# No bare except Exception: pass (outside logging_utils.py)
grep -rn "except Exception:" backend/src/ --include="*.py" | grep -v "as e" | grep -v "logging_utils.py"
# Expected: 0 results (or only documented intentional catches)

# All exception handlers have exc_info
grep -rn "logger\.\(warning\|error\|debug\)" backend/src/ --include="*.py" | grep "exc_info"
# Expected: all new log statements include exc_info=True

# No exception text in user-facing messages
grep -rn "_reply.*exc\|_reply.*error\|_reply.*traceback" backend/src/ --include="*.py"
# Expected: 0 results with exception variables in _reply calls
```
