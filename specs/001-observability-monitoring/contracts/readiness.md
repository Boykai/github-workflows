# Contract: Readiness Endpoint

**Endpoint**: `GET /api/v1/ready`
**Feature**: 001-observability-monitoring
**Requirements**: FR-001, FR-002, FR-003, FR-004, FR-005

## Purpose

Kubernetes-style readiness probe that validates all critical subsystems are operational before routing traffic. Returns HTTP 200 when the application is fully ready to serve requests, HTTP 503 when any subsystem is degraded.

## Request

```
GET /api/v1/ready
```

No request body, no query parameters, no authentication required.

## Response: All Checks Pass (HTTP 200)

```json
{
  "status": "pass",
  "checks": {
    "database:writeable": [
      {
        "component_id": "database:writeable",
        "component_type": "component",
        "status": "pass",
        "time": "2026-03-22T14:00:00Z"
      }
    ],
    "oauth:configured": [
      {
        "component_id": "oauth:configured",
        "component_type": "component",
        "status": "pass",
        "time": "2026-03-22T14:00:00Z"
      }
    ],
    "encryption:enabled": [
      {
        "component_id": "encryption:enabled",
        "component_type": "component",
        "status": "pass",
        "time": "2026-03-22T14:00:00Z"
      }
    ],
    "polling:alive": [
      {
        "component_id": "polling:alive",
        "component_type": "component",
        "status": "pass",
        "time": "2026-03-22T14:00:00Z"
      }
    ]
  }
}
```

## Response: One or More Checks Fail (HTTP 503)

```json
{
  "status": "fail",
  "checks": {
    "database:writeable": [
      {
        "component_id": "database:writeable",
        "component_type": "component",
        "status": "fail",
        "time": "2026-03-22T14:00:00Z",
        "output": "Database write check failed: disk full"
      }
    ],
    "oauth:configured": [
      {
        "component_id": "oauth:configured",
        "component_type": "component",
        "status": "pass",
        "time": "2026-03-22T14:00:00Z"
      }
    ],
    "encryption:enabled": [
      {
        "component_id": "encryption:enabled",
        "component_type": "component",
        "status": "pass",
        "time": "2026-03-22T14:00:00Z"
      }
    ],
    "polling:alive": [
      {
        "component_id": "polling:alive",
        "component_type": "component",
        "status": "fail",
        "time": "2026-03-22T14:00:00Z",
        "output": "Polling task has crashed and is not intentionally disabled"
      }
    ]
  }
}
```

## Subsystem Checks

### 1. Database Writeable (`database:writeable`)

- **Check**: INSERT a row into `_readiness_scratch` table, then DELETE it
- **Pass**: INSERT and DELETE both succeed without error
- **Fail**: Any database error (connection failure, read-only filesystem, disk full, table lock)
- **Note**: Table is auto-created if missing (`CREATE TABLE IF NOT EXISTS`)

### 2. OAuth Configured (`oauth:configured`)

- **Check**: Verify `github_client_id` and `github_client_secret` are non-empty strings
- **Pass**: Both values are present and non-empty
- **Fail**: Either value is empty or missing

### 3. Encryption Enabled (`encryption:enabled`)

- **Check**: Verify `EncryptionService.enabled` is `True`
- **Pass**: Encryption service reports enabled
- **Fail**: Encryption service reports disabled

### 4. Polling Alive (`polling:alive`)

- **Check**: Inspect the polling asyncio.Task state from `state.py`
- **Pass**: Polling task is running (not done) OR polling is intentionally disabled via configuration
- **Fail**: Polling task has crashed (task is done with exception) and was not intentionally disabled

## Constraints

- Response time MUST be under 2 seconds (SC-001)
- The `GET /health` liveness endpoint MUST remain completely unchanged (FR-005)
- All four checks MUST always be present in the response, even when some pass and others fail
- The `output` field is only included for failed checks
