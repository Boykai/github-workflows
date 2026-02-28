# Research: MCP Configuration Support for GitHub Agents in Settings Page

**Feature**: 012-mcp-settings-config  
**Date**: 2026-02-28  
**Status**: Complete

## R1: MCP Configuration Storage Pattern

**Decision**: Store MCP configurations in a new `mcp_configurations` SQLite table, keyed by `github_user_id`, with individual rows per MCP entry.

**Rationale**: The existing codebase uses SQLite with aiosqlite for all persistent data (user_sessions, user_preferences, project_settings, global_settings). Using a dedicated table follows the established pattern (one table per domain entity) and allows indexed lookups by user, enforcing per-user scoping naturally via SQL. A JSON blob in user_preferences was considered but rejected because it complicates individual CRUD operations, pagination, and per-row constraints (e.g., max 25 MCPs per user).

**Alternatives considered**:
- JSON column in `user_preferences`: Simpler schema but harder to enforce row-level constraints, no individual deletion without full JSON rewrite, and no indexing on MCP fields.
- Separate microservice/database: Overengineered for the scope; violates YAGNI and the existing single-SQLite architecture.

## R2: API Endpoint Pattern for MCP CRUD

**Decision**: REST endpoints under `/api/v1/settings/mcps` following the existing settings API pattern:
- `GET /settings/mcps` — List user's MCPs
- `POST /settings/mcps` — Add a new MCP
- `DELETE /settings/mcps/{mcp_id}` — Remove an MCP

**Rationale**: The existing codebase uses RESTful patterns throughout (see `settings.py`, `signal.py`, `projects.py`). The settings router already handles user-scoped CRUD at `/settings/*`. Adding MCP endpoints under the same prefix is consistent and reuses the existing auth dependency (`get_session_dep`). The technical notes in the issue explicitly suggest this pattern.

**Alternatives considered**:
- GraphQL: Not used anywhere in the codebase; introducing it for one feature would add unnecessary complexity.
- Separate router prefix (e.g., `/api/v1/mcps`): Would break the logical grouping of user settings and require a new router registration.

## R3: SSRF Prevention for MCP Endpoint URLs

**Decision**: Server-side URL validation using Python's `urllib.parse` to parse and validate MCP endpoint URLs. Reject URLs with:
1. Private/reserved IP ranges (127.0.0.0/8, 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 169.254.0.0/16, ::1, fc00::/7)
2. Non-HTTP(S) schemes (only `http` and `https` allowed)
3. URLs resolving to localhost or internal hostnames

**Rationale**: The spec (FR-010) explicitly requires SSRF prevention. The technical notes call this out specifically. Since MCP endpoint URLs could be used by the system to make outbound requests, validating them server-side before storage prevents SSRF attacks. The validation happens at write time (POST) rather than read time, as the URL is stored for later use.

**Alternatives considered**:
- Network-level egress filtering: Good defense-in-depth but doesn't prevent storage of malicious URLs, and the backend may not have network-level controls.
- DNS resolution at validation time: Adds latency and can be bypassed via DNS rebinding. Hostname-based blocking is a reasonable first layer.

## R4: Frontend Component Architecture

**Decision**: Create a new `McpSettings` component following the existing `SettingsSection` wrapper pattern used by `SignalConnection`, `ProjectSettings`, `GlobalSettings`, etc. Add it to the `SettingsPage` component in the existing settings section list.

**Rationale**: The Settings page is composed of independent `SettingsSection`-wrapped components. Each section manages its own async state (loading/error/success). The `SignalConnection` component is the closest analog — it handles CRUD operations with inline feedback and is independently testable. Following this pattern ensures visual consistency and code reuse.

**Alternatives considered**:
- Separate MCP page: Violates the requirement that MCP management is a sub-section within Settings.
- Shared form state with other settings: Breaks the independent section pattern and adds coupling.

## R5: OAuth Token Error Handling

**Decision**: Reuse the existing `AuthenticationError` exception and `get_session_dep` dependency for auth validation. On the frontend, detect 401 responses and trigger re-authentication via the existing auth flow. The existing `ApiError` class already captures HTTP status codes.

**Rationale**: The backend already has a robust auth flow: `get_session_dep` validates the session cookie, checks expiration, and raises `AuthenticationError` (mapped to 401). The frontend `request()` function throws `ApiError` with the status code. Adding MCP-specific auth handling would duplicate existing logic. The frontend just needs to catch 401 errors from MCP operations and prompt re-login.

**Alternatives considered**:
- Custom auth middleware for MCP routes: Unnecessary; the existing `Depends(get_session_dep)` pattern is sufficient.
- Token refresh in MCP operations: The existing `refresh_token` method in `GitHubAuthService` handles this; no MCP-specific logic needed.

## R6: Database Migration Strategy

**Decision**: Add migration `006_add_mcp_configurations.sql` following the existing numbered migration pattern (001-005 already exist). The migration creates the `mcp_configurations` table with appropriate indexes.

**Rationale**: The codebase uses a sequential numbered migration system (`_discover_migrations()` in `database.py`). The next available number is 006. The migration runner applies pending migrations at startup, so no manual intervention is needed.

**Alternatives considered**:
- Altering existing tables: Not applicable; MCP configurations are a new entity.
- Using an ORM migration tool (Alembic): Not used in the codebase; the raw SQL migration pattern is established and working.

## R7: Input Validation Strategy

**Decision**: Dual validation — client-side for immediate UX feedback, server-side as authoritative check. Validate:
- Name: non-empty, max 100 characters
- Endpoint URL: valid URL format, max 2048 characters, HTTP(S) scheme only
- Per-user limit: max 25 MCPs

**Rationale**: The spec (FR-008, FR-011, FR-012) explicitly requires these validations. Client-side validation provides instant feedback (SC-004: within 1 second). Server-side validation prevents bypass and enforces SSRF rules. Pydantic validators on the backend model handle field-level validation; a pre-insert count check enforces the 25 MCP limit.

**Alternatives considered**:
- Server-side only: Worse UX with network round-trip for every validation error.
- Client-side only: Security risk; validation can be bypassed.
