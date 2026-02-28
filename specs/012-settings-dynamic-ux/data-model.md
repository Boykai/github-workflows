# Data Model: Settings Page — Dynamic Value Fetching, Caching, and UX Simplification

**Feature**: `012-settings-dynamic-ux` | **Date**: 2026-02-28

## Entities

### ModelOption

Represents a single model option returned by a provider.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| id | string | Unique model identifier (e.g., `gpt-4o`, `claude-3.5-sonnet`) | Required, non-empty |
| name | string | Human-readable display name | Required, non-empty |
| provider | string | Provider that owns this model | Required, must match a known provider |

**Relationships**: Belongs to a `Provider`. Displayed within a `DynamicDropdown`.

---

### CachedModelSet

Represents a cached set of model options for a specific provider and user.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| cache_key | string | Composite key: `{provider}:{user_token_hash}` | Required, unique |
| models | list[ModelOption] | List of available models | May be empty |
| fetched_at | datetime (UTC) | Timestamp when models were last fetched | Required |
| ttl_seconds | int | Time-to-live in seconds | Default: 600 (10 min), range 60–3600 |
| is_stale | bool (derived) | `True` if `now() > fetched_at + ttl_seconds` | Computed, not stored |

**Relationships**: Keyed by provider + user identity. Referenced by `ModelFetchState`.

**Validation rules**:
- `ttl_seconds` must be between 60 and 3600 seconds.
- `fetched_at` must be in the past.

---

### ModelFetchState

Represents the current retrieval state for a dynamic dropdown in the frontend.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| status | enum | Current state: `idle`, `loading`, `success`, `error`, `auth_required`, `rate_limited` | Required |
| error_message | string | null | User-friendly error description | Present only when status is `error` or `rate_limited` |
| retry_count | int | Number of retry attempts made | Default: 0, max: 5 |
| last_fetched_at | string | null | ISO 8601 timestamp of last successful fetch | Present when cached data available |
| rate_limit_warning | bool | Whether API rate limit is being approached | Default: false |

**State transitions**:

```
idle → loading         (provider selected, fetch initiated)
loading → success      (fetch completed successfully)
loading → error        (fetch failed — network, server error)
loading → auth_required (provider credentials missing)
loading → rate_limited (HTTP 429 received)
success → loading      (background refresh or provider change)
error → loading        (retry button clicked)
rate_limited → loading (backoff period expired)
auth_required → loading (credentials configured)
```

---

### Provider (extended)

Extends the existing `AIProvider` enum with model-fetching metadata.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| name | string (enum) | Provider identifier: `copilot`, `azure_openai` | Existing enum values |
| supports_dynamic_models | bool | Whether this provider supports runtime model enumeration | `copilot` = true, `azure_openai` = false |
| requires_auth | bool | Whether fetching requires user-specific credentials | `copilot` = true, `azure_openai` = false (uses env config) |
| fetch_endpoint | string | null | API endpoint for model listing | Provider-specific |

---

### SettingsCategory

Categorizes settings fields as primary or secondary for layout purposes.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| name | string | Category display name | Required |
| priority | enum | `primary` or `secondary` | Required |
| collapsed_by_default | bool | Whether the section starts collapsed | `primary` = false, `secondary` = true |

**Categorization of existing settings**:

| Setting Section | Category | Rationale |
|----------------|----------|-----------|
| Model Provider (AI) | primary | Core user action — selecting provider |
| Chat Model (AI) | primary | Core user action — selecting model |
| GitHub Agent Model (AI) | primary | Core user action — selecting agent model |
| Signal Connection | primary | Key integration — connection management |
| Display Preferences | secondary | Appearance settings, changed infrequently |
| Workflow Defaults | secondary | Repository/assignee defaults, set once |
| Notification Preferences | secondary | Notification toggles, set once |
| Allowed Models | secondary | Admin-level configuration |
| Project-Specific Settings | secondary | Per-project overrides, advanced use |

## API Response Models

### ModelsResponse (backend → frontend)

```python
class ModelOption(BaseModel):
    id: str
    name: str
    provider: str

class ModelsResponse(BaseModel):
    status: str          # "success", "auth_required", "rate_limited", "error"
    models: list[ModelOption] = []
    fetched_at: str | None = None      # ISO 8601 timestamp
    cache_hit: bool = False
    rate_limit_warning: bool = False
    message: str | None = None         # For auth_required/error status
```

### Frontend Query State

```typescript
interface ModelOption {
  id: string;
  name: string;
  provider: string;
}

interface ModelsResponse {
  status: "success" | "auth_required" | "rate_limited" | "error";
  models: ModelOption[];
  fetched_at: string | null;
  cache_hit: boolean;
  rate_limit_warning: boolean;
  message: string | null;
}
```

## No Database Migrations Required

All caching is in-memory on the backend (Python dict with TTL metadata) and in TanStack Query's cache on the frontend. The existing `global_settings` table already stores `allowed_models` as a JSON field — no schema changes needed. The `AIProvider` enum in `backend/src/models/settings.py` may be extended with new values as new providers are added, but this is a code change, not a migration.
