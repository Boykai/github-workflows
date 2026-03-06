# Data Model: Reduce GitHub API Rate Limit Consumption

**Feature**: 022-api-rate-limit-protection  
**Date**: 2026-03-06

## Overview

This feature introduces no new database entities or API models. All changes modify existing in-memory state and cache behavior. This document describes the data structures affected.

## Entities

### 1. WebSocket Refresh Hash (new in-memory state)

**Location**: Local variable in `backend/src/api/projects.py` WebSocket handler  
**Scope**: Per-connection, lives for the duration of a WebSocket session  
**Not persisted**: Dies when WebSocket disconnects

| Field | Type | Description |
|-------|------|-------------|
| `last_sent_hash` | `str \| None` | SHA-256 hex digest of the last sent task list JSON. `None` on first cycle. |

**Lifecycle**:
- Initialized to `None` when WebSocket connection opens
- Updated to new hash value each time a refresh message is sent
- Compared against current data hash on each 30-second cycle
- Garbage collected when WebSocket connection closes

### 2. Sub-Issue Cache Entry (new cache entries in existing InMemoryCache)

**Location**: `backend/src/services/cache.py` global `cache` instance  
**Key format**: `sub_issues:{owner}/{repo}#{issue_number}`  
**TTL**: 600 seconds (10 minutes)

| Field | Type | Description |
|-------|------|-------------|
| `value` | `list[dict]` | Raw sub-issue data from GitHub REST API response |
| `expires_at` | `datetime` | UTC expiration timestamp (entry creation + 600s) |

**Lifecycle**:
- Created on first `get_sub_issues()` call for an issue
- Served from cache on subsequent calls within TTL window
- Expires automatically after 600 seconds
- Force-cleared when `refresh=true` is passed to the board endpoint

### 3. Board Data Cache Entry (existing, TTL changed)

**Location**: `backend/src/services/cache.py` global `cache` instance  
**Key format**: `board_data:{project_id}`  
**TTL**: Changed from 120 → 300 seconds

No structural changes. Only the TTL value changes to align with the frontend auto-refresh interval.

## Relationships

```text
WebSocket Connection
  └── last_sent_hash (per-connection, in-memory)
        └── compared against SHA-256(current_tasks_json)

Board Data Request
  ├── Board Data Cache (TTL: 300s)
  │     └── contains aggregated board items
  └── Sub-Issue Cache (TTL: 600s, per-issue)
        └── contains list[dict] of sub-issue data per parent issue
```

## State Transitions

### WebSocket Refresh Cycle

```text
[Connection Open] → last_sent_hash = None
    │
    ▼
[30s Timer] → fetch tasks → compute hash
    │
    ├── hash == last_sent_hash → skip send (no-op)
    │
    └── hash != last_sent_hash → send refresh message
                                  → last_sent_hash = new_hash
```

### Sub-Issue Cache Lookup

```text
[get_sub_issues(owner, repo, issue_number)] 
    │
    ├── cache hit (not expired) → return cached value
    │
    └── cache miss or expired → REST API call
                                → cache.set(key, result, ttl=600)
                                → return result
```

## Validation Rules

- `last_sent_hash` must use deterministic JSON serialization (`json.dumps(sort_keys=True)`) to ensure consistent hashing
- Sub-issue cache keys must include owner, repo, and issue number to avoid cross-repo collisions
- Cache TTL values are positive integers (enforced by `InMemoryCache.set()`)
