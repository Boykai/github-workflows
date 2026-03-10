# Quickstart: Fix Silent Failures & Security

**Feature**: 033-fix-silent-failures-security
**Date**: 2026-03-10

## Prerequisites

- Python 3.12+
- `uv` package manager (for running backend tools)
- Repository cloned with `backend/` directory accessible

## Implementation Order

### Phase 1: Verify Critical Fixes (Stories 1-3, P1)

These fixes address silent exception swallowing and security leaks. Most have been partially implemented on the parent branch.

```bash
# 1. Verify critical silent failures are logged (Story 1)
grep -n "exc_info" backend/src/services/github_projects/service.py
grep -n "exc_info" backend/src/services/github_projects/__init__.py
grep -n "exc_info" backend/src/services/metadata_service.py

# 2. Verify DB update failures are logged (Story 2)
grep -n "exc_info" backend/src/services/agent_creator.py

# 3. Verify no exception leaks to users (Story 3)
grep -n "_reply.*exc\|_reply.*error" backend/src/services/signal_chat.py
# Should show zero matches with exception variables in _reply calls
```

### Phase 2: Complete Remaining Bare Exception Blocks (Story 5, P2)

Address the 37 remaining `except Exception:` blocks without `as e`:

```bash
# Find all bare except Exception: blocks
grep -rn "except Exception:" backend/src/ --include="*.py" | grep -v "as e"

# For each result (except logging_utils.py):
# 1. Add `as e` to capture the exception
# 2. If the block has `pass`, replace with appropriate logging
# 3. If the block has `logger.*`, include `e` in the log message
# 4. If possible, narrow to specific exception type
```

### Phase 3: Document Intentional Catches (Story 5, P2)

Add inline comments to intentional broad catches:

```bash
# Files to document:
# - main.py:350,357 (CancelledError)
# - services/signal_bridge.py:494 (CancelledError)
# - api/workflow.py:472 (ImportError)
# - api/chat.py:137 (RuntimeError)
# - services/model_fetcher.py:356 (ValueError/TypeError)
# - services/github_projects/service.py:152,196 (rate-limit parsing)
# - services/chores/service.py:605 (_BlockedIssueSkip)
# - services/ai_agent.py:658 (JSONDecodeError)
# - services/workflow_orchestrator/models.py:46 (ValueError)
```

## Validation

### Lint Check

```bash
cd backend
uv run --extra dev ruff check src/
```

### Type Check

```bash
cd backend
uv run --extra dev pyright src/
```

### Unit Tests

```bash
cd backend
uv run --extra dev pytest tests/unit/ -x
```

### Static Verification

```bash
# Verify: No bare except Exception: pass remaining
grep -rn "except Exception:" backend/src/ --include="*.py" | grep -v "as e" | grep -v "logging_utils.py" | wc -l
# Target: 0

# Verify: All log statements include exc_info
grep -c "exc_info=True" backend/src/services/agent_creator.py
# Target: >= 4

# Verify: No exception text in user-facing messages
grep -rn "_reply.*{exc\|_reply.*{e}" backend/src/ --include="*.py" | wc -l
# Target: 0
```

## Key Files

| File | Changes | Story |
|------|---------|-------|
| `backend/src/services/github_projects/service.py` | Add logging to silent catches, narrow types | 1, 5 |
| `backend/src/services/github_projects/__init__.py` | Add logging to cleanup catch | 1 |
| `backend/src/services/metadata_service.py` | Add logging to SQLite fallback, narrow type | 1, 5 |
| `backend/src/services/agent_creator.py` | Add logging to DB update catches | 2 |
| `backend/src/services/signal_chat.py` | Replace exception leaks with generic messages | 3, 4 |
| `backend/src/logging_utils.py` | `safe_error_response()` utility (already exists) | 3 |
| `backend/src/services/workflow_orchestrator/config.py` | Add `as e` to 9 bare catches | 5 |
| `backend/src/services/chores/service.py` | Add `as e` to 5 bare catches | 5 |
| `backend/src/services/agents/service.py` | Add `as e` to 4 bare catches | 5 |
| `backend/src/api/*.py` | Add `as e` to API-layer catches | 5 |

## Common Patterns

### Adding Logging to a Silent Pass Block

```python
# BEFORE
try:
    result = await some_operation()
except Exception:
    pass

# AFTER
try:
    result = await some_operation()
except Exception as e:
    logger.warning("some_operation failed for %s", context_id, exc_info=True)
```

### Narrowing Exception Types

```python
# BEFORE
try:
    data = await db.execute("SELECT ...")
except Exception as e:
    logger.warning("DB read failed", exc_info=True)

# AFTER
try:
    data = await db.execute("SELECT ...")
except aiosqlite.Error as e:
    logger.warning("DB read failed", exc_info=True)
```

### Replacing Exception Leaks

```python
# BEFORE
except Exception as exc:
    await _reply(phone, f"Error: {exc}")

# AFTER
except Exception as exc:
    logger.error("Command failed for %s: %s", phone, exc, exc_info=True)
    await _reply(phone, "⚠️ Something went wrong. Please try again.")
```
