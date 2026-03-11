# Contracts: Code Quality Check — Error Handling

**Feature**: 001-code-quality-check | **Date**: 2026-03-11

## Overview

This feature is a behavior-preserving refactoring initiative. It does not introduce new API endpoints or change existing API contracts. This document defines the internal contracts (patterns and conventions) that the refactored code must follow.

## 1. Exception Handling Contract

### 1.1 Backend Exception Block Rules

Every `except` block in `backend/src/` (excluding `logging_utils.py` resilience guards) MUST follow one of these patterns:

#### Pattern A: Log and Propagate

```python
try:
    result = await some_operation()
except SpecificError as e:
    logger.error("Operation failed: %s", e, exc_info=True)
    raise
```

**When to use**: Service-layer operations where the caller should handle the failure.

#### Pattern B: Log and Return Default

```python
try:
    result = await some_operation()
except SpecificError as e:
    logger.warning("Operation failed, using default: %s", e)
    result = default_value
```

**When to use**: Non-critical operations where a sensible default exists (e.g., cache miss, optional metadata).

#### Pattern C: Log Debug and Continue

```python
try:
    optional_step()
except SpecificError as e:
    logger.debug("Optional step skipped: %s", e)
```

**When to use**: Best-effort operations in loops or cleanup paths where individual failures should not abort the overall operation.

#### Pattern D: Sanitize for External Response

```python
try:
    result = await external_integration()
except Exception as e:
    logger.error("External call failed: %s", e, exc_info=True)
    external_response = "An internal error occurred. Please try again."
```

**When to use**: Any path where error information reaches an external system (Signal API, webhook responses, etc.).

### 1.2 Prohibited Patterns

```python
# ❌ PROHIBITED: Silent swallowing
except Exception:
    pass

# ❌ PROHIBITED: Unbound exception
except Exception:
    logger.error("Something failed")  # No 'e' — loses context

# ❌ PROHIBITED: Leaking details externally
except Exception as e:
    send_to_external_api(f"Error: {str(e)}")  # Exposes internals

# ❌ PROHIBITED: Overly broad catch
except Exception as e:  # When only ValueError/KeyError is expected
    logger.error("Failed: %s", e)
```

### 1.3 Exception Allowlist (logging_utils.py)

The following 4 locations in `logging_utils.py` are exempt from the binding rule because they are resilience guards preventing recursive logging failures:

- Line ~105: Fallback formatter exception guard
- Line ~131: Log record sanitization guard
- Line ~165: Structured output guard
- Line ~190: Log emit guard

---

## 2. Shared Helper Contracts

### 2.1 resolve_repository() — Already Implemented

```python
# Contract: utils.resolve_repository(session, owner, repo) -> tuple[str, str]
# Returns: (owner, repo) tuple
# Fallback chain: explicit params → selected project → env default
# Raises: ValueError if no repository context can be resolved
```

**All route handlers** that need repository context MUST call this function. No inline resolution logic permitted.

### 2.2 require_selected_project() — Already Implemented

```python
# Contract: require_selected_project(session) -> str
# Returns: selected_project_id
# Raises: ValidationError("No project selected") if session lacks project
```

**All endpoints** requiring a selected project MUST use this guard.

### 2.3 cached_fetch() — Already Implemented

```python
# Contract: cached_fetch(cache_key, fetch_fn, *args, refresh=False) -> Any
# Returns: Cached value if available and not refreshing, otherwise fetches and caches
# Cache miss: Calls fetch_fn(*args), stores result, returns it
# Refresh: Bypasses cache, calls fetch_fn, updates cache
```

**All endpoints** with cache-through patterns MUST use this helper.

### 2.4 handle_service_error() — Already Implemented

```python
# Contract: handle_service_error(e, context_msg, status_code=500) -> never
# Logs the error with context
# Raises: HTTPException with the specified status code
```

**All route handlers** MUST use this for service-layer error handling instead of ad-hoc catch-log-raise.

---

## 3. Frontend Module Contracts

### 3.1 API Client Contract

```typescript
// api/client.ts exports:
export async function request<T>(
  path: string,
  init?: RequestInit  // Supports AbortSignal
): Promise<T>;

export class ApiError extends Error {
  status: number;
  data: unknown;
}

// Auth state listener
export function onAuthStateChange(callback: (authenticated: boolean) => void): () => void;
```

**All domain API modules** MUST import `request` from `./client` and NOT define their own fetch logic.

### 3.2 Domain API Module Contract

Each domain module in `api/` MUST:

1. Import `request` from `./client`
2. Export a single named object (e.g., `export const chatApi = { ... }`)
3. Contain ≤300 LOC
4. Be re-exported from `api/index.ts`

```typescript
// Example: api/chat.ts
import { request } from "./client";

export const chatApi = {
  getMessages(sessionId: string): Promise<Message[]> {
    return request<Message[]>(`/chat/${sessionId}/messages`);
  },
  // ... other chat methods
};
```

### 3.3 Hook Decomposition Contract

Each extracted sub-hook MUST:

1. Own a single concern (state, computation, or side-effect)
2. Accept explicit parameters (no implicit coupling to parent hook state)
3. Return a typed interface
4. Be independently testable

```typescript
// Example: hooks/useBoardFilters.ts
export interface BoardFilterState {
  filters: FilterConfig;
  setFilters: (filters: FilterConfig) => void;
  resetFilters: () => void;
}

export function useBoardFilters(projectId: string): BoardFilterState;
```

---

## 4. Migration Contract

### 4.1 Prefix Uniqueness

- All migration files MUST have unique numeric prefixes
- Automated test MUST verify no duplicate prefixes exist in `backend/src/migrations/`
- Format: `NNN_descriptive_name.sql` where NNN is zero-padded

### 4.2 Chat Retention

- `chat_messages` table retains at most 1,000 messages per `session_id`
- Trimming occurs on insert when count exceeds threshold
- Trimming removes oldest messages first (by `timestamp`)

---

## 5. Backward Compatibility Contract

### FR-028 Compliance

All changes MUST preserve:

- Existing HTTP API endpoint paths and response shapes
- Existing WebSocket message formats
- Existing frontend route behavior and component props
- Existing database schema (additive migrations only)
- Existing CI/CD pipeline behavior

**Breaking change detection**: Any change to an exported function signature, API response type, or database column requires explicit documentation in the PR and spec linkage.
