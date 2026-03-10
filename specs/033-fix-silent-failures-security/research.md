# Research: Fix Silent Failures & Security

**Feature**: 033-fix-silent-failures-security
**Date**: 2026-03-10
**Status**: Complete

## Research Tasks

### RT-001: Python Logging Best Practices for Exception Handlers

**Decision**: Use Python's built-in `logging` module with `exc_info=True` for all exception log statements.

**Rationale**: The codebase already uses `logging.getLogger(__name__)` consistently across all backend modules. The `exc_info=True` parameter includes the full traceback in log output, which is the standard Python pattern for exception logging. This approach is zero-dependency (stdlib only), works with all log formatters (including the project's `StructuredJsonFormatter`), and is already the established convention in this codebase.

**Alternatives considered**:
- `exc_info=e` (passing exception object directly) — Also valid in Python 3.x but `exc_info=True` is more idiomatic and used throughout the existing codebase
- `traceback.format_exc()` as string — Loses structured log metadata; harder to filter in log aggregators
- Sentry/structured error tracking — Over-engineering for this scope; the project doesn't use Sentry

### RT-002: Log Severity Level Selection for Exception Types

**Decision**: Apply the following severity mapping:
- `logger.debug()` — Expected/acceptable failures in non-critical paths (cleanup, rate-limit header parsing)
- `logger.warning()` — Degraded-but-recoverable states (fallback to defaults, missing context)
- `logger.error()` — Failures that may cause data loss or broken references (DB write failures)

**Rationale**: This follows the Python logging documentation and the project's existing conventions. The severity levels map directly to the impact categories defined in the issue (critical → warning/error, high → error, medium → warning). Cleanup operations use `debug` to avoid log flooding during shutdown.

**Alternatives considered**:
- Using `logger.exception()` everywhere — Automatically includes traceback but always logs at ERROR level, which would over-escalate debug-level issues like cleanup failures
- Using `logger.critical()` for DB failures — Too severe; these are recoverable failures that don't crash the application

### RT-003: Exception Type Narrowing Strategy

**Decision**: Narrow `except Exception:` to specific types only when the set of possible exceptions is clearly identifiable from the code context. Keep broad `except Exception as e:` when the try block calls external libraries or performs multiple operations that could raise diverse exception types.

**Rationale**: Overly aggressive narrowing risks catching fewer exceptions than before, which would change the existing error-recovery behavior (violating FR-011). The high-priority narrowing targets identified in the issue are cases where the code context clearly indicates which exceptions can occur:
- `httpx.HTTPStatusError` for HTTP client calls
- `aiosqlite.Error` for database operations
- `KeyError` for dictionary access
- `ValueError` for type conversion

**Alternatives considered**:
- Narrow all 37 bare `except Exception:` blocks — Too risky; many call into third-party libraries where the full exception taxonomy is unknown
- Leave all as broad `except Exception:` — Misses the opportunity to make exception handling more precise for clearly-scoped blocks
- Use custom exception hierarchy — Over-engineering; the project doesn't need a custom exception tree for this feature

### RT-004: Preventing Information Disclosure in User-Facing Messages

**Decision**: Replace all user-facing exception messages with hardcoded generic strings. Log full exception details server-side. Use the existing `safe_error_response()` utility from `logging_utils.py` where applicable.

**Rationale**: The `safe_error_response()` function already exists in the codebase (lines 215-238 of `logging_utils.py`) and follows the exact pattern needed: log detailed error information server-side, return a generic message to the caller. For Signal message handlers, hardcoded friendly messages (e.g., "⚠️ Something went wrong...") are appropriate since the response format is plain text, not structured API responses.

**Alternatives considered**:
- Error code system (e.g., "Error #E1234") — Over-engineering for a messaging bot; codes are meaningless to Signal users
- Per-command custom error messages — Unnecessary complexity; a consistent generic message is clearer and easier to maintain
- No user-facing message (silent failure) — Worse UX than a friendly error; users need to know their command failed

### RT-005: Resilience Blocks in Logging Utilities

**Decision**: Preserve the 4 bare `except Exception:` blocks in `logging_utils.py` (lines 105, 131, 165, 190) without modification. These are intentional resilience patterns that prevent the logging infrastructure from crashing.

**Rationale**: These blocks exist in the `redact()`, `SanitizingFormatter.format()`, `StructuredJsonFormatter.format()`, and `RequestIDFilter.filter()` methods. Adding `as e` or logging within these blocks would be counterproductive — they ARE the logging infrastructure, so using the logger to report logger failures could cause infinite recursion. Each block already has a clear fallback behavior (safe default string, minimal representation, etc.) and inline comments documenting the intentional design.

**Alternatives considered**:
- Adding `as e` for consistency — Would capture the variable but can't use it safely (can't log from within the logger)
- Writing to stderr as a last resort — Could be considered but adds complexity for extremely rare edge cases; the current fallback behavior is sufficient
- No change (selected) — Correct approach per the codebase memory and issue specification

### RT-006: Existing Implementation State Audit

**Decision**: Many of the originally-identified critical fixes have already been partially implemented on the parent branch (`copilot/fix-silent-failures-security`). The plan must account for this and focus on completing remaining work.

**Rationale**: Audit findings as of 2026-03-10:
- `service.py:927` (workflow config) — Already has `except Exception as e:` with `logger.warning()` ✅
- `__init__.py:49` (client cleanup) — Already has `except Exception as e:` with `logger.debug()` ✅
- `metadata_service.py:112` (SQLite read) — Already has `except Exception as e:` with `logger.warning()` ✅
- `agent_creator.py:727,768,880,1107` — All have `except Exception as e:` with `logger.error()/warning()` ✅
- `signal_chat.py:159` — Has `except Exception as e:` with `logger.warning()` ✅
- `signal_chat.py:177-182` — User-facing message is now generic (no leak) ✅
- `safe_error_response()` — Already exists in `logging_utils.py` ✅
- `logging_utils.py` resilience blocks — Correctly bare with comments ✅

Remaining work:
- 37 bare `except Exception:` (without `as e`) still exist across `backend/src/`
- Exception type narrowing for high-priority targets not yet applied
- Intentional broad catches need documentation comments
- Verification that all user-facing paths are safe

**Alternatives considered**: N/A — audit is factual

## Summary

All NEEDS CLARIFICATION items have been resolved. The technical approach is well-defined:
1. Use stdlib `logging` with `exc_info=True` (existing pattern)
2. Apply severity levels per impact category (debug/warning/error)
3. Narrow exception types conservatively (only when clearly identifiable)
4. Use generic messages for all user-facing error responses
5. Preserve `logging_utils.py` resilience blocks untouched
6. Account for existing implementation — focus on completing remaining 37 bare `except Exception:` blocks
