# Data Model: Chat Agent Auto-Generate Full GitHub Issue Metadata

**Feature**: 018-issue-metadata-autogen | **Date**: 2026-03-05

## Entity Relationship Overview

```text
┌──────────────────────┐         ┌──────────────────────────┐
│   RepositoryContext   │ 1───M  │  MetadataCacheEntry      │
│                       │        │                          │
│ repo_key (PK)         │        │ id (PK, auto)            │
│ last_refresh_at       │        │ repo_key (FK)            │
│ ttl_seconds           │        │ field_type               │
│                       │        │ value (JSON)             │
└──────────────────────┘        │ fetched_at               │
                                 └──────────────────────────┘

┌──────────────────────────────────────────────────────┐
│                   IssueMetadata                       │
│  (Pydantic model — not persisted, part of            │
│   IssueRecommendation)                               │
│                                                       │
│ priority: IssuePriority (P0–P3)                       │
│ size: IssueSize (XS–XL)                              │
│ estimate_hours: float                                 │
│ start_date: str (ISO 8601)                           │
│ target_date: str (ISO 8601)                          │
│ labels: list[str]              ← validated against   │
│ assignees: list[str]             cached repo values   │
│ milestone: str | None                                 │
│ branch: str | None                                    │
└──────────────────────────────────────────────────────┘
```

---

## E1: MetadataCacheEntry (SQLite table)

**Table name**: `github_metadata_cache`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Row identifier |
| `repo_key` | TEXT | NOT NULL | Repository identifier (`"owner/repo"`) |
| `field_type` | TEXT | NOT NULL | One of: `"label"`, `"branch"`, `"milestone"`, `"collaborator"` |
| `value` | TEXT | NOT NULL | JSON-encoded metadata value (see Value Schemas below) |
| `fetched_at` | TEXT | NOT NULL | ISO 8601 timestamp of last fetch |

**Indexes**:
- `UNIQUE(repo_key, field_type, value)` — prevents duplicates
- `idx_metadata_cache_repo_type ON (repo_key, field_type)` — fast lookups by repo + type

**Migration file**: `backend/src/migrations/011_metadata_cache.sql`

### Value Schemas (JSON stored in `value` column)

**Label**:
```json
{
  "name": "feature",
  "color": "0075ca",
  "description": "New functionality"
}
```

**Branch**:
```json
{
  "name": "main",
  "protected": true
}
```

**Milestone**:
```json
{
  "number": 3,
  "title": "v2.0 Release",
  "due_on": "2026-04-01T00:00:00Z",
  "state": "open"
}
```

**Collaborator**:
```json
{
  "login": "octocat",
  "avatar_url": "https://avatars.githubusercontent.com/u/1?v=4"
}
```

---

## E2: IssueMetadata (Pydantic model — extended)

**File**: `backend/src/models/recommendation.py`

**Existing fields** (no changes):

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `priority` | `IssuePriority` | `P2` | Issue priority P0–P3 |
| `size` | `IssueSize` | `M` | T-shirt sizing XS–XL |
| `estimate_hours` | `float` | `4.0` | Hours estimate (0.5–40) |
| `start_date` | `str` | `""` | ISO 8601 date |
| `target_date` | `str` | `""` | ISO 8601 date |
| `labels` | `list[str]` | `["ai-generated"]` | Label names |

**New fields**:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `assignees` | `list[str]` | `[]` | GitHub usernames to assign |
| `milestone` | `str \| None` | `None` | Milestone title (mapped to number at submission) |
| `branch` | `str \| None` | `None` | Development/parent branch name |

### Validation Rules

- `labels`: Every entry MUST exist in the cached label list for the target repository. If a label doesn't exist, it is silently dropped before submission (with a log warning).
- `assignees`: Every entry MUST be a valid collaborator login from the cached collaborator list.
- `milestone`: MUST match a cached open milestone title. If no match, field is set to `None`.
- `branch`: MUST match a cached branch name. If no match, field is set to `None`.
- `priority` and `size`: Validated against `IssuePriority` and `IssueSize` enums respectively. Additionally, at submission time, must be mapped to repo labels if matching labels exist (e.g., `"P1"`, `"size:M"`).

---

## E3: RepositoryMetadataContext (Pydantic model — new)

**File**: `backend/src/services/metadata_service.py` (inline model)

| Field | Type | Description |
|-------|------|-------------|
| `repo_key` | `str` | `"owner/repo"` |
| `labels` | `list[dict]` | Cached label objects |
| `branches` | `list[dict]` | Cached branch objects |
| `milestones` | `list[dict]` | Cached milestone objects |
| `collaborators` | `list[dict]` | Cached collaborator objects |
| `fetched_at` | `str` | ISO 8601 timestamp of last fetch |
| `is_stale` | `bool` | True if fetched_at + TTL < now |
| `source` | `str` | `"fresh"`, `"cache"`, or `"fallback"` |

This model is returned by `MetadataService.get_metadata()` and consumed by:
1. The AI prompt builder (to inject available values)
2. The frontend metadata API endpoint (to populate dropdowns)
3. The submission validator (to verify selections)

---

## E4: Frontend Types (TypeScript)

**File**: `frontend/src/types/index.ts`

### Updated `IssueMetadata` interface

```typescript
export interface IssueMetadata {
  priority: 'P0' | 'P1' | 'P2' | 'P3';
  size: 'XS' | 'S' | 'M' | 'L' | 'XL';
  estimate_hours: number;
  start_date: string;
  target_date: string;
  labels: string[];
  assignees: string[];          // NEW
  milestone: string | null;     // NEW
  branch: string | null;        // NEW
}
```

### New `RepositoryMetadata` interface

```typescript
export interface RepositoryMetadata {
  repo_key: string;
  labels: Array<{ name: string; color: string; description: string }>;
  branches: Array<{ name: string; protected: boolean }>;
  milestones: Array<{ number: number; title: string; due_on: string | null; state: string }>;
  collaborators: Array<{ login: string; avatar_url: string }>;
  fetched_at: string;
  is_stale: boolean;
  source: 'fresh' | 'cache' | 'fallback';
}
```

---

## State Transitions

### Metadata Cache Lifecycle

```text
  ┌─────────┐   First access    ┌──────────┐   TTL expired   ┌──────────────┐
  │  EMPTY   │ ────────────────→ │  FRESH   │ ──────────────→ │    STALE     │
  └─────────┘                    └──────────┘                  └──────────────┘
       │                              ↑                              │
       │  API error                   │   Refresh success            │  Refresh attempt
       ↓                              │                              ↓
  ┌─────────────┐              ┌──────────┐                  ┌──────────────┐
  │  FALLBACK   │              │  FRESH   │ ←────────────── │  REFRESHING  │
  │ (hardcoded) │              └──────────┘   Success        └──────────────┘
  └─────────────┘                                                   │
                                                                    │  API error
                                                                    ↓
                                                             ┌──────────────┐
                                                             │  STALE       │
                                                             │ (keep old)   │
                                                             └──────────────┘
```

### IssueRecommendation Status (unchanged)

```text
  PENDING ──→ CONFIRMED (metadata validated + submitted)
     │
     └──→ REJECTED (user declined)
```
