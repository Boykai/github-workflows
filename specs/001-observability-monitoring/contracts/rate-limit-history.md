# Contract: Rate-Limit History Endpoint (Optional, P3)

**Endpoint**: `GET /api/v1/rate-limit/history`
**Feature**: 001-observability-monitoring
**Requirements**: FR-022, FR-023, FR-024

## Purpose

Provides historical rate-limit snapshots for capacity planning and trend analysis. Returns time-ordered data points captured during polling cycles.

## Request

```
GET /api/v1/rate-limit/history?hours=24
```

### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `hours` | `int` | No | `24` | Number of hours of history to return (1–168) |

## Response: Data Available (HTTP 200)

```json
{
  "snapshots": [
    {
      "timestamp": "2026-03-22T13:00:00Z",
      "remaining": 4850,
      "limit": 5000,
      "reset_at": 1742655600
    },
    {
      "timestamp": "2026-03-22T13:01:00Z",
      "remaining": 4847,
      "limit": 5000,
      "reset_at": 1742655600
    }
  ],
  "hours": 24,
  "count": 2
}
```

## Response: No Data (HTTP 200)

```json
{
  "snapshots": [],
  "hours": 24,
  "count": 0
}
```

## Response: Invalid Parameters (HTTP 422)

Standard FastAPI validation error response when `hours` is out of range.

## Data Collection

- Snapshots are recorded once per polling cycle (default: every 60 seconds)
- Data source: `get_last_rate_limit()` from `github_projects/service.py`
- Fields captured: `remaining`, `limit`, `reset_at` from GitHub API response headers
- Snapshots older than 24 hours are automatically pruned after each insert

## Storage

- SQLite table: `rate_limit_snapshots`
- Expected volume: ~1,440 rows/day at 60s polling interval
- Index on `timestamp` for efficient range queries

## Constraints

- This feature is optional (SHOULD, not MUST)
- Empty results return HTTP 200 with empty array, not an error
- `hours` parameter is validated to range 1–168 (1 hour to 1 week)
