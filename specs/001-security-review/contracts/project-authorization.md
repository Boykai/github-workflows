# Contract: Project Authorization

**Feature**: 001-security-review | **Date**: 2026-03-11

## Overview

Defines the authorization contract for project-scoped operations. Every API endpoint and WebSocket handler that accepts a `project_id` must verify the authenticated user has access to that project before performing any action.

## Dependency Signature

```python
async def verify_project_access(
    project_id: str,
    session: UserSession = Depends(get_current_session),
) -> str:
    """
    Returns: verified project_id
    Raises: HTTPException(403) if access denied
    Raises: HTTPException(401) if not authenticated
    """
```

## Protected Endpoints

| Endpoint | File | Parameter Source |
|----------|------|-----------------|
| `POST /tasks/{project_id}/*` | `tasks.py` | Path parameter |
| `GET/PUT /projects/{project_id}/*` | `projects.py` | Path parameter |
| `GET/PUT /settings/project/{project_id}` | `settings.py` | Path parameter |
| `POST /workflow/{project_id}/*` | `workflow.py` | Path parameter |
| `WS /ws/{project_id}` | WebSocket handler | Path parameter |

## Authorization Logic

```text
1. Extract project_id from request
2. Extract session from authentication cookie
3. Query GitHub API: can this user's token access the project?
4. IF yes → return project_id, continue to endpoint
5. IF no  → return 403 Forbidden, do NOT execute endpoint body
6. IF not authenticated → return 401 Unauthorized
```

## Response Contract

### Success (200/201/etc.)

Normal endpoint response — authorization is transparent to the caller.

### Access Denied (403)

```json
{
  "detail": "Access denied: you do not have access to this project"
}
```

### Not Authenticated (401)

```json
{
  "detail": "Not authenticated"
}
```

## WebSocket Contract

WebSocket connections targeting an unowned project must be rejected **before** any project data is streamed:

```text
1. Client connects to WS /ws/{project_id}
2. Server authenticates session from cookie
3. Server verifies project access
4. IF denied → close WebSocket with code 4003 (forbidden) immediately
5. IF allowed → accept connection and begin streaming
```

## Test Contract

| # | Input | Expected |
|---|-------|----------|
| 1 | Valid session, owned project | 200/201 — endpoint executes normally |
| 2 | Valid session, unowned project | 403 Forbidden — no data returned |
| 3 | Valid session, nonexistent project | 403 Forbidden — no data returned |
| 4 | No session (unauthenticated) | 401 Unauthorized |
| 5 | WebSocket to owned project | Connection accepted, data streams |
| 6 | WebSocket to unowned project | Connection rejected with 4003 before any data |
| 7 | Same user, different endpoints, same unowned project | All return 403 consistently |

## Caching

Project access results may be cached per `(session_id, project_id)` tuple for the duration of a single HTTP request to avoid redundant GitHub API calls. Cache must not persist across requests.
