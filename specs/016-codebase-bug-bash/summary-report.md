# Bug Bash Findings Summary Report

**Date**: 2026-03-03
**Branch**: `copilot/bug-bash-code-review`
**Scope**: Full codebase audit on `main` — backend (Python), frontend (TypeScript/React), infrastructure (Docker, GitHub Actions)

## Overview

| Category | Findings | ✅ Fixed | ⚠️ Flagged |
|----------|----------|----------|------------|
| 🔴 Security | 11 | 8 | 3 |
| 🟠 Runtime | 0 | 0 | 0 |
| 🟡 Logic | 2 | 2 | 0 |
| 🔵 Test Quality | 0 | 0 | 0 |
| ⚪ Code Quality | 0 | 0 | 0 |
| **Total** | **13** | **10** | **3** |

**Test Suite Status**: ✅ All tests pass (1236 backend + 277 frontend = 1513 total, including 11 new regression tests)
**Linting Status**: ✅ All clean (`ruff check`, `ruff format`, `eslint`, `tsc --noEmit`)

---

## Findings Table

| # | File | Line(s) | Category | Description | Status |
|---|------|---------|----------|-------------|--------|
| 1 | `backend/src/api/chat.py` | 205 | 🔴 Security | `#agent` command error leaks raw exception text (`{exc}`) to user in chat response | ✅ Fixed |
| 2 | `backend/src/api/chat.py` | 299 | 🔴 Security | Issue recommendation failure leaks `str(e)` in chat response (`Error: {str(e)}`) | ✅ Fixed |
| 3 | `backend/src/api/chat.py` | 420 | 🔴 Security | Task generation failure leaks `str(e)` in chat response (`Error: {str(e)}`) | ✅ Fixed |
| 4 | `backend/src/api/chat.py` | 682 | 🔴 Security | `confirm_proposal` error leaks exception in `ValidationError(f"Failed to create issue: {e}")` | ✅ Fixed |
| 5 | `backend/src/api/board.py` | 64 | 🔴 Security | `list_board_projects` error leaks `str(e)` via `details={"error": str(e)}` in API response | ✅ Fixed |
| 6 | `backend/src/api/board.py` | 117–119 | 🔴 Security | `get_board_data` error leaks `str(e)` via `details={"error": str(e)}` in API response | ✅ Fixed |
| 7 | `backend/src/api/workflow.py` | 252 | 🔴 Security | `confirm_recommendation` fallback error leaks `str(e)` in `WorkflowResult.message` | ✅ Fixed |
| 8 | `backend/src/api/workflow.py` | 344 | 🔴 Security | `retry_pipeline` error leaks `{e}` in `ValidationError(f"Failed to fetch issue: {e}")` | ✅ Fixed |
| 9 | `backend/src/services/signal_chat.py` | 175 | 🔴 Security | `#agent` via Signal leaks `{exc}` in reply to user's phone | ⚠️ Flagged |
| 10 | `backend/src/services/signal_chat.py` | 534 | 🔴 Security | Signal CONFIRM failure leaks `str(e)[:200]` in reply to user's phone | ⚠️ Flagged |
| 11 | `backend/src/services/signal_chat.py` | 808–813 | 🔴 Security | Signal AI pipeline failure leaks `str(e)[:200]` in reply to user's phone | ⚠️ Flagged |
| 12 | `backend/src/api/webhooks.py` | 18, 243–247 | 🟡 Logic | Webhook deduplication used `set` (no insertion-order guarantee) with manual eviction; "remove oldest" sliced a set which has no ordering guarantee per Python spec | ✅ Fixed |
| 13 | `backend/src/api/webhooks.py` | 448–451 | 🟡 Logic | Issue matching compared `str(issue_number) in str(item.github_item_id)` but `github_item_id` is a GraphQL node ID (`PVTI_...`), never containing the issue number; match always fails | ✅ Fixed |

---

## Fix Details

### Finding 1–4: Error Information Leakage in Chat API (`chat.py`)

**What**: Four error paths in the chat API endpoint leaked raw Python exception messages to end users in chat responses. Exception messages may contain internal URLs, DB connection strings, file paths, or stack trace fragments.

**Fix**: Replaced all `f"...{e}"` / `f"...{str(e)}"` patterns with static, user-friendly messages. Internal details are still logged at `logger.error` / `logger.warning` level.

**Regression tests**: `TestErrorMessageSanitization` (4 tests) in `backend/tests/unit/test_api_chat.py`

### Finding 5–6: Error Information Leakage in Board API (`board.py`)

**What**: Two error paths in the board API passed `details={"error": str(e)}` to `GitHubAPIError`, exposing raw exception text in the JSON error response body.

**Fix**: Removed the `details` parameter from `GitHubAPIError` raises. The error is logged server-side.

**Regression tests**: `TestBoardErrorSanitization` (2 tests) in `backend/tests/unit/test_api_board.py`

### Finding 7–8: Error Information Leakage in Workflow API (`workflow.py`)

**What**: Two error paths leaked exception details — one via `WorkflowResult.message` and one via a `ValidationError` detail string.

**Fix**: Replaced with static error messages. Internal details are logged.

**Regression tests**: `TestWorkflowErrorSanitization` (1 test) in `backend/tests/unit/test_api_workflow.py`

### Finding 9–11: Signal Error Message Leakage (Flagged)

**What**: Three error paths in `signal_chat.py` send raw exception text to the user's Signal phone. These are private 1:1 messages (not public API responses), so the risk level is lower.

**Flag rationale**: Signal messages go to the authenticated user's own device, which is a different threat model than a public API response. Sanitizing these may reduce debuggability for the user without a clear security benefit. Added `# TODO(bug-bash)` comments at each location for human review.

### Finding 12: Webhook Deduplication Ordering (`webhooks.py`)

**What**: The `_processed_delivery_ids` variable was a plain `set`. The eviction code attempted to "remove oldest entries" by converting to a list and slicing, but Python's `set` type does not guarantee insertion order. This means random entries could be evicted instead of the oldest, leading to false-positive duplicate detection or unbounded memory growth in adversarial scenarios.

**Fix**: Replaced `set[str]` with `BoundedSet[str]` from `src/utils.py`, which maintains FIFO insertion order and automatically evicts the oldest entry when capacity is reached. Removed the manual eviction code.

**Regression tests**: `TestDeduplicationBoundedSet` (3 tests) in `backend/tests/unit/test_webhooks.py`

### Finding 13: Issue Matching Logic (`webhooks.py`)

**What**: The webhook handler matched issues by checking `str(issue_number) in str(item.github_item_id)`. However, `github_item_id` is a GraphQL Project V2 item node ID (e.g., `PVTI_lADOABCDEF`), which never contains the numeric issue number. This meant the webhook could never find a matching issue in a project, causing all webhook-triggered status updates to silently fail.

**Fix**: Changed the comparison to use `item.issue_number == issue_number` (the Task model has an `issue_number` field specifically for this purpose).

**Regression tests**: `TestIssueMatchingByNumber` (1 test) in `backend/tests/unit/test_webhooks.py`

---

## Audited Files (No Findings)

The following critical files were audited and found to have no bugs in the categories reviewed:

- `backend/src/config.py` — Secure defaults, proper env var handling
- `backend/src/dependencies.py` — Proper admin authorization with race condition protection
- `backend/src/main.py` — Proper exception handlers, sanitized generic error responses
- `backend/src/services/database.py` — Parameterized queries, proper migration handling
- `backend/src/services/encryption.py` — Correct Fernet usage, graceful legacy token handling
- `backend/src/services/session_store.py` — Proper token encryption/decryption
- `backend/src/services/github_auth.py` — Secure OAuth state management with BoundedDict
- `backend/src/api/auth.py` — Sanitized error responses (previously fixed in security review)
- `backend/src/api/projects.py` — No information leakage
- `backend/src/api/settings.py` — Proper admin authorization
- `backend/src/api/tasks.py` — Clean error handling
- `backend/src/utils.py` — Correct BoundedSet/BoundedDict implementations
- `backend/src/services/cleanup_service.py` — Proper permission checks, sequential deletion
- `frontend/src/services/api.ts` — Correct credential handling
- `frontend/src/components/**/*.tsx` — No `dangerouslySetInnerHTML` usage
- `.github/workflows/ci.yml` — Reviewed for secret exposure
- `docker-compose.yml` — Environment variable substitution for secrets

---

## Verification

- **Backend tests**: 1236 tests across 43 files — all passing
- **Frontend tests**: 277 tests across 29 files — all passing
- **Backend linting**: `ruff check` + `ruff format --check` — all clean
- **Frontend linting**: `eslint` + `tsc --noEmit` — all clean
- **New regression tests**: 11 tests across 4 test files — all passing
- **TODO(bug-bash) comments**: 3 comments in `backend/src/services/signal_chat.py` (verified via `grep`)
