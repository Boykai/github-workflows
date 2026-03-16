# Research: Settings Page Refactor with Secrets

**Feature**: 047-settings-page-refactor | **Date**: 2026-03-16

## Phase 0: Unknowns Resolution

All items initially marked as NEEDS CLARIFICATION have been resolved through codebase analysis and technology research. This document captures the research findings, decisions, and rationale for each area.

---

### 1. GitHub Environment Secrets API & NaCl Sealed-Box Encryption

**Context**: The secrets service must encrypt secret values before uploading them to GitHub. GitHub's environment secrets API requires NaCl sealed-box encryption using the repository's public key.

- **Decision**: Use `pynacl` (PyNaCl) library for NaCl sealed-box encryption. Fetch the environment public key via `client.rest.actions.async_get_environment_public_key()`, encrypt the secret value with `nacl.public.SealedBox`, then Base64-encode the result for upload via `client.rest.actions.async_create_or_update_environment_secret()`.
- **Rationale**: GitHub's API specification explicitly requires libsodium sealed-box encryption. PyNaCl is the canonical Python binding for libsodium, is well-maintained, and is widely used in production systems. The existing `cryptography` package in pyproject.toml does not provide NaCl sealed-box primitives.
- **Alternatives considered**:
  - `cryptography` library (rejected: does not expose NaCl sealed-box; only provides X25519 key exchange, which is not the same operation)
  - `libnacl` (rejected: less popular, less maintained than PyNaCl; PyNaCl has better documentation and wider adoption)
  - Direct `libsodium` FFI via `ctypes` (rejected: unnecessary complexity when PyNaCl exists)
- **Encryption flow**:
  ```
  1. GET /repos/{owner}/{repo}/environments/{env}/secrets/public-key → { key_id, key (base64) }
  2. Decode base64 public key → 32-byte Curve25519 public key
  3. nacl.public.SealedBox(PublicKey(decoded_key)).encrypt(secret_value.encode())
  4. Base64-encode the encrypted bytes
  5. PUT /repos/{owner}/{repo}/environments/{env}/secrets/{name} with { encrypted_value, key_id }
  ```

---

### 2. githubkit Environment Secrets API Coverage

**Context**: The secrets service needs to list, create/update, and delete environment secrets. Need to verify githubkit (≥0.14.6) covers these endpoints.

- **Decision**: Use githubkit's REST API methods which map to GitHub's REST endpoints. The required methods are available:
  - `client.rest.actions.async_list_environment_secrets(owner, repo, environment_name)` → list
  - `client.rest.actions.async_get_environment_public_key(owner, repo, environment_name)` → public key
  - `client.rest.actions.async_create_or_update_environment_secret(owner, repo, environment_name, secret_name, data)` → upsert
  - `client.rest.actions.async_delete_environment_secret(owner, repo, environment_name, secret_name)` → delete
  - `client.rest.repos.async_create_or_update_environment(owner, repo, environment_name)` → ensure environment
- **Rationale**: githubkit is already a core dependency (≥0.14.6). Its auto-generated REST bindings cover the full GitHub API surface, including Actions environment secrets. Using the typed methods avoids raw HTTP calls and benefits from built-in retry/throttle logic via `GitHubClientFactory`.
- **Alternatives considered**:
  - Direct httpx calls to GitHub API (rejected: loses auto-retry, throttling, token management from GitHubClientFactory)
  - PyGithub (rejected: not async, would be a new dependency, duplicates githubkit's role)

---

### 3. GitHubClientFactory Reuse for Secrets Service

**Context**: The secrets service needs authenticated GitHub API access. The existing `GitHubClientFactory` in `services/github_projects/__init__.py` pools clients by token hash.

- **Decision**: Import and reuse the existing `GitHubClientFactory` singleton. The secrets service will accept `access_token` as a parameter (same as existing services) and call `factory.get_client(access_token)` to obtain a pooled client.
- **Rationale**: The factory already implements token-based pooling, double-check locking, auto-retry (rate limit + server error), HTTP caching, and throttling. Creating a separate client would duplicate this infrastructure. The factory's `BoundedDict(maxlen=50)` pool has sufficient capacity for concurrent users.
- **Alternatives considered**:
  - New GitHub client per request (rejected: no pooling, no retry, wasteful)
  - Pass pre-built client from dependency injection (rejected: current API pattern passes `access_token` string; changing would break consistency across all services)

---

### 4. Shadcn Tabs Component for Settings Layout

**Context**: The Settings page needs to be restructured from a collapsible layout to a tabbed layout. The frontend uses Shadcn UI components.

- **Decision**: Use Shadcn `Tabs`, `TabsList`, `TabsTrigger`, `TabsContent` components. These are already part of the Shadcn component library that the project uses. The tabs will be controlled by URL hash fragments for deep-linking.
- **Rationale**: Shadcn Tabs are built on Radix UI primitives, which provide proper ARIA roles (`role="tablist"`, `role="tab"`, `role="tabpanel"`, `aria-selected`, `aria-controls`, `aria-labelledby`) out of the box. This satisfies FR-030 (accessibility roles and labels) without custom implementation. The existing codebase already uses Shadcn components.
- **Alternatives considered**:
  - Custom tab implementation (rejected: would need manual ARIA attribute management)
  - React Router nested routes (rejected: tabs are a UI concern, not routing; hash fragments are simpler and don't need route definitions)
  - Accordion/collapsible (rejected: current approach, identified as UX problem in the spec — hides too much)
- **URL hash synchronization**: Use `useEffect` with `window.location.hash` to read initial tab on mount, and update hash on tab change via `onValueChange` callback. Support `#essential`, `#secrets`, `#preferences`, `#admin`.

---

### 5. Admin User Detection Pattern

**Context**: The Admin tab should only be visible to admin users. The spec states: check `github_user_id === admin_github_user_id`.

- **Decision**: Reuse the existing admin detection pattern from the backend's `dependencies.py` (lines 132–150). The frontend already has access to `github_user_id` from the auth context. The `admin_github_user_id` is available from global settings. Compare these values to conditionally render the Admin tab.
- **Rationale**: The backend already enforces admin-only access on global settings PUT endpoints, so the frontend check is a UX optimization (hiding the tab) rather than a security control. The pattern is consistent with existing admin checks in the codebase.
- **Alternatives considered**:
  - Separate `/api/v1/auth/is-admin` endpoint (rejected: over-engineering; the data is already available client-side from user session + global settings)
  - Role-based access control system (rejected: YAGNI; single admin user is the current model)

---

### 6. Secret Name Validation Pattern

**Context**: Secret names must match `^[A-Z][A-Z0-9_]*$`, max 255 characters. Values must not exceed 64 KB. Need to determine where validation occurs.

- **Decision**: Validate on both frontend and backend. Frontend uses a Zod schema for form validation with real-time feedback. Backend uses a Pydantic validator on the path parameter and request body. The regex pattern and size limits are defined as constants shared by reference in documentation.
- **Rationale**: Dual validation provides immediate user feedback (frontend) and security enforcement (backend). The backend must always validate regardless of frontend state. The `^[A-Z][A-Z0-9_]*$` pattern matches GitHub's own secret name requirements.
- **Alternatives considered**:
  - Frontend-only validation (rejected: easily bypassed)
  - Backend-only validation (rejected: poor UX; user sees error only after form submission)

---

### 7. Component Consolidation Strategy

**Context**: Several existing settings components need to be consolidated into the new tab structure. Need to decide on the approach: move, rename, delete, or refactor.

- **Decision**: Preserve existing leaf components (`DisplayPreferences`, `WorkflowDefaults`, `NotificationPreferences`, `SignalConnection`) as-is. Create new tab container components (`EssentialSettings`, `PreferencesTab`, `AdminTab`) that compose these existing components. Delete only wrapper/intermediary components that become redundant (`AdvancedSettings`, `AIPreferences`, `AISettingsSection`, `DisplaySettings`, `WorkflowSettings`, `NotificationSettings`).
- **Rationale**: Leaf components already implement per-section save logic via `SettingsSection` and are independently testable. Rewriting them would risk regressions. The intermediary wrappers (e.g., `DisplaySettings` wrapping `DisplayPreferences`) add no value in the new tab structure.
- **Alternatives considered**:
  - Rewrite all components from scratch (rejected: high regression risk, violates YAGNI/simplicity principle)
  - Keep all existing components and just reorganize imports (rejected: leaves dead wrapper code)
  - Merge leaf components into tab components (rejected: creates oversized files, reduces reusability)

---

### 8. TanStack Query Key Pattern for Secrets

**Context**: The secrets hooks need a query key factory consistent with the existing `settingsKeys` and `signalKeys` patterns.

- **Decision**: Follow the established factory pattern:
  ```typescript
  export const secretsKeys = {
    all: ['secrets'] as const,
    list: (owner: string, repo: string, env: string) =>
      [...secretsKeys.all, 'list', owner, repo, env] as const,
    check: (owner: string, repo: string, env: string, names: string[]) =>
      [...secretsKeys.all, 'check', owner, repo, env, ...names] as const,
  };
  ```
- **Rationale**: Consistent with `settingsKeys` and `signalKeys` patterns in `useSettings.ts`. Enables granular cache invalidation (e.g., invalidating a specific repo's secrets list after mutation without clearing all secrets data). The hierarchical key structure supports TanStack Query's `queryClient.invalidateQueries({ queryKey: secretsKeys.all })` for broad invalidation.
- **Alternatives considered**:
  - Flat string keys (rejected: no hierarchical invalidation support)
  - Object-based keys (rejected: inconsistent with existing factory pattern)

---

### 9. MCP Preset `required_secrets` Integration

**Context**: MCP presets need to declare required secrets so the Tools page can show warnings for unconfigured API keys.

- **Decision**: Add an optional `required_secrets: list[str]` field to `McpPresetResponse` in `models/tools.py`. Default to an empty list. Only the Context7 preset currently needs it (`required_secrets=["COPILOT_MCP_CONTEXT7_API_KEY"]`). Add a lightweight bulk-check endpoint `GET /secrets/{owner}/{repo}/{env}/check?names=KEY1,KEY2` that returns a name→boolean map.
- **Rationale**: The `required_secrets` field is simple metadata on the preset model. A separate check endpoint avoids N+1 queries (one per preset) — a single call can verify all required secrets for all visible presets. The field defaults to an empty list so existing presets are backward-compatible.
- **Alternatives considered**:
  - Store required_secrets in the database (rejected: presets are static/hardcoded; adding DB storage is over-engineering)
  - Check secrets inline during preset listing (rejected: would require access_token/repo context in the presets service, violating separation of concerns)
  - Frontend-only matching (rejected: frontend doesn't know which secrets exist without an API call anyway)

---

### 10. Multiple Environments Support

**Context**: The spec mentions defaulting to the `copilot` environment. Need to decide if other environments should be supported.

- **Decision**: Default to `copilot` only. Display the environment name as a read-only field with an "Advanced" text input toggle for power users who need different environment names. The backend accepts any valid environment name — the default is a frontend UX choice only.
- **Rationale**: GitHub Copilot's MCP convention uses the `copilot` environment for `$COPILOT_MCP_*` prefixed secrets. 99% of users will never need a different environment. Making it editable but defaulted covers the power-user edge case without complicating the common flow.
- **Alternatives considered**:
  - Hard-code `copilot` everywhere (rejected: blocks power users, may not work for all GitHub configurations)
  - Multi-environment selector with dropdown (rejected: over-engineering; there's no existing endpoint to list environments)

---

### 11. Custom Secret Prefix Enforcement

**Context**: Should custom secrets be forced to use the `COPILOT_MCP_` prefix?

- **Decision**: Warn but do not block. When a user enters a custom secret name that doesn't start with `COPILOT_MCP_`, display an informational warning: "GitHub Copilot only exposes secrets with the COPILOT_MCP_ prefix to MCP servers." Allow the secret to be saved regardless.
- **Rationale**: Users may have legitimate use cases for non-prefixed secrets (e.g., other CI/CD workflows using the same environment). Hard-blocking would be overly restrictive. The warning educates users about the convention without preventing valid operations.
- **Alternatives considered**:
  - Hard enforcement of `COPILOT_MCP_` prefix (rejected: too restrictive for edge cases)
  - No warning at all (rejected: users would be confused when MCP servers can't access non-prefixed secrets)
