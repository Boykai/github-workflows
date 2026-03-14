# Research: Solune Rebrand & App Builder Architecture

**Feature**: `041-solune-rebrand-app-builder` | **Date**: 2026-03-14
**Input**: Technical Context from [`plan.md`](plan.md)

## Research Tasks

### R1: Monorepo Restructure Strategy

**Question**: What is the safest approach to restructure a live repository into a monorepo with nested `solune/` and `apps/` directories?

**Decision**: Use git archive for pre-restructure snapshot, then in-place directory moves with bulk path updates via scripted find-and-replace.

**Rationale**: The spec requires a fresh `git init` for the "solune" repo, but the practical approach within the existing repo is to:
1. Tag the current state as `pre-solune-archive` for recovery
2. Move all non-`.github` files into `solune/` using `git mv`
3. Create `apps/` with `.gitkeep`
4. Update all internal path references in a single scripted pass
5. Create root-level `README.md` and `docker-compose.yml`

This preserves git history for the moved files and is safer than a fresh `git init` which loses all history. The spec mentions fresh git init as an option; in-place restructure achieves the same end state with history preservation.

**Alternatives Considered**:
- **Fresh `git init` + copy**: Loses all git history, breaks blame/log tracking. Only useful if explicitly wanting a clean break. Rejected because history is valuable for debugging and attribution.
- **Git subtree/submodule**: Over-engineered for a single-repo restructure. Rejected because there's no need for separate repos.
- **GitHub repo rename + restructure**: Renames the existing repo URL. Could be done separately. Not mutually exclusive with directory restructure.

---

### R2: Path Reference Update Strategy

**Question**: How to reliably update all internal path references across ~70+ files when restructuring?

**Decision**: Use a layered approach — automated regex-based find/replace for known patterns, followed by targeted manual review for edge cases.

**Rationale**: The codebase has well-defined patterns for path references:
- `docker-compose.yml`: Build contexts (`./backend` → `./solune/backend`), volume paths
- CI workflows (`.github/workflows/ci.yml`): Working directory references
- `mcp.json` / `.vscode/mcp.json`: Tool paths
- `.devcontainer/`: Container configuration paths
- Backend configuration: `DATABASE_PATH`, data directory references
- Scripts: Any hardcoded paths in `scripts/`

A scripted pass handles the bulk, with a validation step that greps for remaining old paths.

**Alternatives Considered**:
- **Manual file-by-file editing**: Error-prone for 70+ files. Rejected.
- **AST-based rewriting**: Overkill for config file path updates. Rejected.
- **Search-and-replace tool (sed/ripgrep)**: Selected. Simple, auditable, reversible.

---

### R3: String Replacement Mapping for Rebrand

**Question**: What is the complete mapping of old → new strings for the rebrand?

**Decision**: Use the following canonical replacement table, applied in order (longest match first to avoid partial replacements):

| Old String | New String | File Patterns |
|-----------|-----------|--------------|
| `Agent Projects` | `Solune` | `*.md`, `*.tsx`, `*.ts`, `*.py`, `*.yml` |
| `agent-projects-backend` | `solune-backend` | `pyproject.toml`, `docker-compose.yml` |
| `agent-projects-frontend` | `solune-frontend` | `package.json`, `docker-compose.yml` |
| `ghchat-backend` | `solune-backend` | `docker-compose.yml` |
| `ghchat-frontend` | `solune-frontend` | `docker-compose.yml` |
| `ghchat-signal-api` | `solune-signal-api` | `docker-compose.yml` |
| `ghchat-network` | `solune-network` | `docker-compose.yml` |
| `ghchat-data` | `solune-data` | `docker-compose.yml` |
| `/var/lib/ghchat/data` | `/var/lib/solune/data` | `docker-compose.yml`, `*.py`, `*.env*` |
| `GitHub Workflows Chat` | `Solune` | `copilot-instructions.md` |
| `github-workflows` (product name context) | `solune` | `*.md`, badges, links |

**Rationale**: Longest-match-first ordering prevents `ghchat-backend` from being partially matched by a `ghchat` rule. The product-name context for `github-workflows` needs care — the GitHub repo URL may still contain `github-workflows` until a repo rename happens.

**Alternatives Considered**:
- **Single regex**: Too fragile for the variety of patterns. Rejected.
- **Per-file manual editing**: Selected for complex files (README rewrite, copilot-instructions rewrite). Automated for simple string swaps.

---

### R4: App Data Model Design

**Question**: What is the best data model for managed applications in the existing SQLite schema?

**Decision**: A single `apps` table in the existing SQLite database, following the established migration pattern.

**Rationale**: The existing codebase uses SQLite with sequential migration files (`001_*.sql` through `023_consolidated_schema.sql`). The new `apps` table follows the same pattern as existing tables:
- Text primary keys (app name as unique identifier)
- Enum-like status via CHECK constraint (matching `chat_recommendations.status` pattern)
- RFC3339 timestamps with trailing 'Z' (matching existing convention)
- Foreign key to `workflow_configurations` for pipeline association

The model aligns with `FR-012` requirements: name, display_name, description, directory_path, associated_pipeline_id, status, repo_type, external_repo_url, created_at.

**Alternatives Considered**:
- **Separate SQLite database for apps**: Unnecessary complexity, complicates transactions. Rejected.
- **File-based app registry (JSON/YAML)**: Lacks ACID properties, harder to query. Rejected.
- **PostgreSQL migration**: Overkill for the scale. Existing SQLite works well. Rejected.

---

### R5: App Lifecycle and Process Management

**Question**: How should the platform start/stop application processes?

**Decision**: Docker Compose-based process management for applications.

**Rationale**: Each app in `apps/<app-name>/` can have its own `docker-compose.yml` or `Dockerfile`. The platform's `app_service.py` manages lifecycle by:
1. **Start**: Run `docker compose up -d` in the app's directory, assign a port, update status to `active`
2. **Stop**: Run `docker compose down` in the app's directory, update status to `stopped`
3. **Status check**: Inspect running containers for the app's service name

This leverages the existing Docker infrastructure and provides process isolation. For simple apps without Docker, a subprocess-based fallback (e.g., `npm start`, `python -m http.server`) can be used with port allocation tracked in the database.

**Alternatives Considered**:
- **Direct subprocess management**: Less isolated, harder to clean up on crashes. Suitable as fallback only.
- **Kubernetes**: Over-engineered for single-server deployment. Rejected.
- **systemd services**: Platform-dependent, harder to manage programmatically from Python. Rejected.

---

### R6: App Preview Iframe Strategy

**Question**: How should the frontend embed live app previews?

**Decision**: Standard HTML `<iframe>` pointing to the app's dynamically assigned local URL.

**Rationale**: Each running app exposes a local port (e.g., `http://localhost:3001`). The frontend renders an `<iframe src="http://localhost:{port}">` in the app detail view. Key considerations:
- **Same-origin policy**: Since both the platform and apps run on `localhost` (different ports), cross-origin restrictions apply. The app's server should set appropriate CORS headers, or the platform can proxy through the backend.
- **Error handling**: If the app is stopped or crashes, the iframe loads a blank page or error. The frontend should detect load failures and show an appropriate offline state.
- **Security**: The iframe uses `sandbox` attribute to restrict navigation and scripts if needed.

**Alternatives Considered**:
- **Server-side rendering/proxy**: More complex, adds latency. Could be a future enhancement. Rejected for MVP.
- **WebSocket-based remote viewer**: Over-engineered. Rejected.
- **Screenshot/thumbnail preview**: Loses interactivity. Rejected.

---

### R7: Slash Command Architecture

**Question**: How does the existing chat infrastructure support slash commands, and how should `/<app-name>` context switching integrate?

**Decision**: Extend the existing chat command system with a dynamic app-context command.

**Rationale**: The frontend has `lib/commands/` for chat command handlers. The backend processes messages and detects special prefixes. Adding `/<app-name>` requires:
1. **Frontend**: Intercept messages starting with `/` in the command autocomplete component, query the apps API for matching app names, and display suggestions.
2. **Backend**: When a message matches `/<app-name>`, update the session's active app context (stored in `chat_messages` or a session-level attribute), and return a system message confirming the switch.
3. **Context indicator**: The chat UI displays the current app context in the header or input area.

This follows the existing pattern of command handling in the chat interface.

**Alternatives Considered**:
- **Dedicated context-switch API endpoint (not via chat)**: Less natural, breaks the chat-first UX. Rejected as primary method; could be added as supplementary.
- **Global app selector (dropdown in navbar)**: Complementary but not a replacement for chat-based switching. Could be added alongside.

---

### R8: Admin Guard Implementation Strategy

**Question**: How should `@admin` and `@adminlock` guards be enforced at the system level?

**Decision**: Middleware-based path evaluation in the agent operation routing layer.

**Rationale**: Agent operations flow through the backend before reaching the file system. The guard can be implemented as:
1. **Configuration**: A YAML/JSON config file listing protected paths and their guard level (`admin` or `adminlock`).
2. **Middleware**: Before any file operation dispatched by an agent, the guard middleware checks the target path against the config.
3. **`@admin`**: Logs the attempt, returns a permission-elevation prompt to the user. If approved, the operation proceeds.
4. **`@adminlock`**: Unconditionally blocks the operation and returns an explanation.
5. **Per-file evaluation**: When an operation spans `solune/` and `apps/`, each file path is evaluated independently.

The guard configuration defaults to: `solune/` → `@admin`, `.github/` → `@adminlock`, `apps/` → no guard.

**Alternatives Considered**:
- **File system permissions (OS-level)**: Too coarse, doesn't allow agent-specific overrides. Rejected.
- **Git hooks**: Only catches commits, not in-progress edits. Rejected.
- **Agent-level instruction-only guard**: Relies on AI compliance, not enforceable. Rejected as sole mechanism; useful as supplementary.

---

### R9: Migration Numbering Convention

**Question**: What migration number should the new apps table use?

**Decision**: Use migration number `024` for the apps table schema.

**Rationale**: The existing consolidated schema is at `023_consolidated_schema.sql`. Following the established sequential pattern, the next available number is `024`. Note from repository memory: duplicate migration numbers (013, 014, 015, 021, 022) exist and are handled by the migration system. However, for clarity, using the next sequential number is preferred.

**Alternatives Considered**:
- **Adding to consolidated schema**: Would modify an existing migration, which is not the pattern. Rejected.
- **Higher number to leave room**: Unnecessary given the system handles sequential execution. Rejected.

---

### R10: Frontend Routing for Apps Page

**Question**: How should the Apps page integrate with the existing React Router setup?

**Decision**: Add a new route `/apps` to the existing React Router configuration, following the pattern of other pages (Projects, Agents, etc.).

**Rationale**: The frontend uses React Router v7.13 with routes defined in the main App component. Adding `/apps` follows the identical pattern to existing pages like `/projects`, `/agents`, `/tools`. The page component `AppsPage.tsx` goes in `frontend/src/pages/` and uses the same layout wrapper (`AppLayout`).

**Alternatives Considered**:
- **Nested routes under `/apps/:appName`**: Good for app detail views. The route structure should be `/apps` (list) and `/apps/:appName` (detail with preview). Selected.
- **Tab within existing page**: Doesn't give apps the prominence they deserve as a core feature. Rejected.
