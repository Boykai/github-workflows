# Research: Settings Page — Dynamic Value Fetching, Caching, and UX Simplification

**Feature**: `012-settings-dynamic-ux` | **Date**: 2026-02-28

## Research Tasks

### R-001: GitHub Copilot Models API Endpoint

**Context**: The spec requires dynamically fetching available model names from GitHub Copilot. Need to determine the correct API endpoint and authentication method.

**Decision**: Use the GitHub Copilot completions models endpoint via the existing `github-copilot-sdk` package. The SDK's `CopilotClient` exposes model discovery through its configuration or a dedicated models listing method. As a fallback, the GitHub REST API endpoint `GET /copilot/models` (authenticated with the user's OAuth token via `Authorization: Bearer <token>`) returns available models.

**Rationale**: The application already uses `github-copilot-sdk` and stores user OAuth tokens. Reusing the existing authentication infrastructure (from `github_auth.py`) avoids new credential flows. The SDK abstracts the underlying API and handles token-based auth consistently.

**Alternatives considered**:
- **Hardcoded model list**: Rejected because model availability changes over time; static lists become stale.
- **GitHub REST API directly** (`GET /copilot/models`): Viable fallback if SDK does not expose model listing natively. Uses the same OAuth token already managed by `github_auth.py`.

---

### R-002: Caching Strategy for Fetched Model Lists

**Context**: The spec requires caching with configurable TTL (5–15 min), stale-while-revalidate behavior, and cache invalidation on provider change.

**Decision**: Two-layer caching approach:
1. **Backend**: In-memory TTL cache in `model_fetcher.py` using a Python `dict` keyed by `(provider, user_token_hash)` with metadata (fetch_timestamp, TTL, values). Default TTL: 10 minutes. Stale entries served immediately; background `asyncio.create_task` triggers refresh.
2. **Frontend**: TanStack Query's built-in `staleTime` and `gcTime` (already configured with `STALE_TIME_LONG = 5 min`). The `useModelOptions()` hook uses `staleTime: 5 * 60 * 1000` for automatic stale-while-revalidate.

**Rationale**: The backend cache prevents redundant external API calls (rate-limit protection). The frontend cache prevents redundant calls to our own backend. TanStack Query already handles stale-while-revalidate natively — no custom logic needed on the frontend.

**Alternatives considered**:
- **LocalStorage/IndexedDB on frontend**: Rejected — TanStack Query's in-memory cache suffices for session lifetime; persistent cache adds complexity for minimal gain since model lists change infrequently.
- **Redis/external cache on backend**: Rejected — application is single-instance SQLite; an in-memory dict is simpler and sufficient. No horizontal scaling concern.
- **Database cache table**: Rejected — adds migration complexity for data that is inherently ephemeral. In-memory is appropriate given single-instance deployment.

---

### R-003: Rate-Limit Handling and Backoff Strategy

**Context**: The spec requires rate-limit-aware throttling, exponential backoff, and surfacing warnings to the user.

**Decision**: Implement rate-limit handling in the backend `model_fetcher.py`:
1. Parse `X-RateLimit-Remaining`, `X-RateLimit-Reset`, and `Retry-After` headers from GitHub API responses.
2. Track remaining quota per provider. When remaining < 10% of limit, set a `rate_limit_warning` flag returned in the API response.
3. On HTTP 429 response: apply exponential backoff starting at the `Retry-After` value (or 60s default), doubling on consecutive failures, capped at 15 minutes.
4. Frontend displays a non-blocking toast/banner when the API response includes `rate_limit_warning: true`.

**Rationale**: Backend handles throttling centrally so all frontend clients benefit. Exponential backoff with Retry-After respect is the standard pattern for HTTP 429 handling. The warning threshold (10% remaining) gives users advance notice.

**Alternatives considered**:
- **Frontend-only throttling**: Rejected — multiple browser tabs could still overwhelm the backend; centralized throttling is more reliable.
- **Pre-emptive rate checking before each request**: Rejected — adds latency to every call; reactive handling (parse headers after response) is simpler and standard.

---

### R-004: Provider Interface Design

**Context**: The spec requires an abstraction layer so future providers (OpenAI, Anthropic) can plug in. The existing `CompletionProvider` ABC in `completion_providers.py` provides a pattern.

**Decision**: Create a `ModelFetchProvider` protocol/ABC with:
- `async def fetch_models(token: str) -> list[ModelOption]` — retrieve available models
- `provider_name: str` — identifier string
- `requires_auth: bool` — whether authentication is needed

A registry `dict[str, ModelFetchProvider]` maps provider enum values to implementations. Initially two implementations:
- `GitHubCopilotModelFetcher`: Calls GitHub API with user's OAuth token
- `AzureOpenAIModelFetcher`: Returns static list from environment config (Azure doesn't have a public models API with user tokens)

**Rationale**: Follows the existing pattern in `completion_providers.py`. A simple registry (dict) is lighter than a plugin system and sufficient for the current 2-provider scope. New providers are added by implementing the protocol and registering in the dict.

**Alternatives considered**:
- **Single function with if/else**: Rejected — violates OCP (Open/Closed Principle); adding providers requires modifying the function.
- **Plugin-based auto-discovery**: Rejected — premature for 2 providers (YAGNI per Constitution Principle V).

---

### R-005: Settings Page UX Reorganization

**Context**: The spec requires grouping primary settings prominently and collapsing secondary/advanced settings.

**Decision**: Reorganize `SettingsPage.tsx` into two sections:
1. **Primary Settings** (always visible): Model Provider dropdown, Chat Model dropdown (dynamic), GitHub Agent Model dropdown (dynamic), Signal Connection status/config
2. **Advanced Settings** (collapsible, collapsed by default): Display preferences (theme, default view, sidebar), Workflow defaults (repository, assignee, polling), Notification preferences, Allowed models list, Project-specific settings

Use a `<details>`/`<summary>` element (or shadcn Collapsible/Accordion) for the advanced section. The primary group uses a card-based layout for visual prominence.

**Rationale**: The current `SettingsPage.tsx` renders all sections equally with no hierarchy. Grouping the 4 most-used settings (identified in the spec) at the top and collapsing the rest reduces cognitive load. The `<details>` element provides native accessibility; shadcn Collapsible adds consistent styling.

**Alternatives considered**:
- **Tabs for primary vs. advanced**: Rejected — hides advanced settings completely, making them harder to discover. Collapsible section is one click away.
- **Sidebar navigation within settings**: Rejected — over-engineered for the current number of settings (~5 sections).

---

### R-006: Prerequisite Validation for Dynamic Fetching

**Context**: The spec requires that the system not attempt external fetches when credentials are missing and instead show a prerequisite message.

**Decision**: The backend `/settings/models/{provider}` endpoint checks authentication status before fetching:
1. For GitHub Copilot: Verify user has a valid, non-expired OAuth token via `github_auth.py` session lookup. If missing/expired, return `{ "status": "auth_required", "message": "Connect your GitHub account to see available models" }`.
2. For Azure OpenAI: Verify Azure API key is configured in environment. If missing, return `{ "status": "auth_required", "message": "Azure OpenAI credentials not configured" }`.
3. Frontend `DynamicDropdown` component renders the prerequisite message inline when it receives `auth_required` status, with a link/button to the appropriate setup flow.

**Rationale**: Checking prerequisites on the backend is authoritative — the frontend cannot reliably determine whether the backend has valid credentials. Returning a structured status code allows the frontend to render appropriate UI without guessing.

**Alternatives considered**:
- **Frontend-only prerequisite check**: Rejected — frontend doesn't have direct access to token validity; would need another API call anyway.
- **Returning HTTP 401**: Rejected — 401 implies the user is not authenticated to *our* app. A 200 with status field distinguishes "authenticated to our app but missing provider credentials."

---

### R-007: Accessibility Patterns for Dynamic Dropdowns

**Context**: The spec requires full ARIA labels, keyboard navigation, and screen reader announcements for loading/error states.

**Decision**: The `DynamicDropdown` component will:
1. Use `role="combobox"` with `aria-expanded`, `aria-controls`, `aria-activedescendant` for the dropdown.
2. Add `aria-busy="true"` and `aria-label="Loading available models"` during fetch.
3. Use `aria-live="polite"` region for status announcements (loading complete, error occurred, cache freshness).
4. On error: `role="alert"` for the error message, retry button is keyboard-focusable.
5. Collapsible advanced section: `<button aria-expanded>` toggle with `aria-controls` pointing to the collapsible content.

**Rationale**: These patterns follow WAI-ARIA Authoring Practices for comboboxes and disclosure widgets. The existing shadcn/ui components already implement many ARIA patterns; we extend them for the dynamic states.

**Alternatives considered**:
- **Custom select from scratch**: Rejected — shadcn/ui Select component already handles basic ARIA; we augment rather than replace.
