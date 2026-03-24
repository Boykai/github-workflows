# Configuration

This is the authoritative reference for every environment variable Solune reads. Whether you're getting started with the three required variables or fine-tuning polling intervals and cache TTLs, you'll find the complete reference here.

> **Quick start — the only 3 variables you need:**
> `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, `SESSION_SECRET_KEY`

All configuration is managed through environment variables. Copy `.env.example` to `.env` and customize.

## Environment Variables

### Required

These variables are the minimum needed to get Solune running.

| Variable | Description |
|----------|-------------|
| `GITHUB_CLIENT_ID` | GitHub OAuth App Client ID |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth App Client Secret |
| `SESSION_SECRET_KEY` | Random hex string for session encryption (`openssl rand -hex 32`) |

### GitHub OAuth

These variables control the OAuth callback flow between Solune and GitHub.

| Variable | Default | Description |
|----------|---------|-------------|
| `GITHUB_REDIRECT_URI` | `http://localhost:8000/api/v1/auth/github/callback` | OAuth callback URL |
| `FRONTEND_URL` | `http://localhost:5173` | Frontend URL for OAuth redirects |

### AI Provider

The AI provider controls which LLM generates GitHub Issues from natural language input. Switch providers or models without changing any application code.

| Variable | Default | Description |
|----------|---------|-------------|
| `AI_PROVIDER` | `copilot` | Provider: `copilot` (GitHub Copilot via OAuth) or `azure_openai` |
| `COPILOT_MODEL` | `gpt-4o` | Model for Copilot completion provider |
| `AZURE_OPENAI_ENDPOINT` | — | Azure OpenAI endpoint URL (only when `azure_openai`) |
| `AZURE_OPENAI_KEY` | — | Azure OpenAI API key (only when `azure_openai`) |
| `AZURE_OPENAI_DEPLOYMENT` | `gpt-4` | Azure OpenAI deployment name |

### Webhook (Optional)

Webhooks provide faster detection when Copilot marks PRs as ready for review. The polling service handles this automatically, but webhooks reduce latency.

| Variable | Default | Description |
|----------|---------|-------------|
| `GITHUB_WEBHOOK_SECRET` | — | Secret for webhook signature verification |
| `GITHUB_WEBHOOK_TOKEN` | — | GitHub PAT (classic) with `repo` + `project` scopes |

### Polling

Controls how frequently Solune checks for agent activity on GitHub.

| Variable | Default | Description |
|----------|---------|-------------|
| `COPILOT_POLLING_INTERVAL` | `60` | Polling interval in seconds (0 to disable) |

### Defaults

| Variable | Default | Description |
|----------|---------|-------------|
| `DEFAULT_REPOSITORY` | — | Default repo for issue creation (`owner/repo`). Values missing either side of the slash are ignored. |
| `DEFAULT_PROJECT_ID` | — | Default GitHub Project V2 node ID for polling (e.g. `PVT_kwHOAIsXss4BOJmo`). Used as a direct project fallback when no `project_settings` row exists. |
| `DEFAULT_ASSIGNEE` | `""` | Default assignee for In Progress issues |

### Server

General server binding, debug mode, and CORS configuration.

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server bind host |
| `PORT` | `8000` | Server bind port |
| `DEBUG` | `false` | Development mode: enables dev-login endpoint, development logging/structured output, uvicorn reload, and disables strict production secret validation |
| `ENABLE_DOCS` | `false` | Serve interactive API docs at `/api/docs` and `/api/redoc` (independent of `DEBUG`) |
| `CORS_ORIGINS` | `http://localhost:5173` | Allowed CORS origins (comma-separated) |

### Session

| Variable | Default | Description |
|----------|---------|-------------|
| `SESSION_EXPIRE_HOURS` | `8` | Session TTL in hours |
| `SESSION_CLEANUP_INTERVAL` | `3600` | Interval for cleaning expired sessions (seconds) |

### Database

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_PATH` | `/var/lib/solune/data/settings.db` | SQLite database path (map to Docker volume for persistence) |

### Signal (Optional)

Connect Solune to Signal for bidirectional phone notifications. See the [Signal Integration](signal-integration.md) guide for full setup.

| Variable | Default | Description |
|----------|---------|-------------|
| `SIGNAL_API_URL` | `http://signal-api:8080` | URL of signal-cli-rest-api sidecar |
| `SIGNAL_PHONE_NUMBER` | — | Dedicated Signal phone number (E.164 format) |
| `SIGNAL_WEBHOOK_SECRET` | — | Secret for verifying inbound Signal webhook payloads |

### Security

Production hardening settings for authentication, encryption, and cookie security.

| Variable | Default | Description |
|----------|---------|-------------|
| `ADMIN_GITHUB_USER_ID` | — | Numeric GitHub user ID of the administrator. **Required in production mode**; in debug mode, the first authenticated user is auto-promoted with a warning. |
| `ENCRYPTION_KEY` | — | Fernet key for encrypting OAuth tokens at rest. Generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`. If unset, tokens are stored unencrypted. |
| `COOKIE_SECURE` | `false` | Set `true` in production (HTTPS) to add the `Secure` flag to session cookies. Auto-enabled when `FRONTEND_URL` starts with `https://`. |
| `COOKIE_MAX_AGE` | `28800` | Session cookie max-age in seconds (default: 8 hours) |

### Cache

Tune in-memory cache lifetimes for GitHub metadata and other frequently accessed data.

| Variable | Default | Description |
|----------|---------|-------------|
| `CACHE_TTL_SECONDS` | `300` | In-memory cache TTL in seconds |
| `METADATA_CACHE_TTL_SECONDS` | `3600` | TTL for cached GitHub metadata (labels, branches, milestones, collaborators) |

### Frontend (Vite)

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_BASE_URL` | `/api/v1` | API base URL for frontend |

## Database Schema

SQLite in WAL mode at `DATABASE_PATH`. Schema is auto-migrated at startup via numbered SQL files in `backend/src/migrations/` (currently `023` through `037`). Migrations are tracked by a `schema_version` table.

### Migration Files

| Migration | Purpose |
|-----------|---------|
| `023_consolidated_schema.sql` | Consolidated schema baseline (replaces 001–022) |
| `024_apps.sql` | Apps table and scaffolding |
| `025_fix_apps_fk.sql` | Fix foreign key constraint on apps |
| `026_performance_indexes.sql` | Indexes on `admin_github_user_id`, `selected_project_id`, and chat session columns |
| `027_done_items_cache.sql` | Cache for Done-status project items to reduce cold-start GitHub API calls |
| `028_new_repo_support.sql` | New-repo support columns for apps (GitHub repo/project URLs, project ID) |
| `029_pipeline_state_persistence.sql` | Durable pipeline run tracking, execution groups, and onboarding tour state |
| `030_app_parent_issue.sql` | Parent issue tracking columns on apps table |
| `031_queue_mode.sql` | Per-project pipeline queue mode toggle (`queue_mode` on `project_settings`) |
| `032_activity_events.sql` | Activity events table for unified audit trail |
| `033_copilot_review_requests.sql` | Durable storage for Copilot review request timestamps (restart-safe) |
| `034_auto_merge.sql` | Per-project auto-merge toggle (`auto_merge` on `project_settings`) |
| `034_phase8_pipeline_states_ext.sql` | Phase 8 — extend `pipeline_states` for concurrent execution tracking |
| `035_phase8_mcp_version.sql` | Phase 8 — add `version` column to `mcp_configurations` for optimistic concurrency |
| `036_phase8_collision_events.sql` | Phase 8 — `collision_events` table for MCP collision resolution auditing |
| `037_phase8_recovery_log.sql` | Phase 8 — `recovery_log` table for label-driven state recovery auditing |

## Workflow Settings

Agent pipeline mappings are fully customizable through the pipeline GUI, the Settings UI, or `PUT /api/v1/workflow/config`. The default **Spec Kit** preset ships with:

```json
{
  "agent_mappings": {
    "Backlog": ["speckit.specify"],
    "Ready": ["speckit.plan", "speckit.tasks"],
    "In Progress": ["speckit.implement"],
    "In Review": ["copilot-review"]
  }
}
```

Replace these with any custom agents from your `.github/agents/` directory. You can add or remove stages and configure series/parallel execution groups via the drag-and-drop pipeline GUI.

```text

Settings are stored per-user in SQLite with a 3-tier fallback:

1. User-specific row
2. Canonical `__workflow__` row
3. Any-user fallback with automatic backfill

Case-insensitive status deduplication is applied on both save (backend) and load (frontend).

---

## What's next?

- [Setup Guide](setup.md) — Installation instructions for Docker, Codespaces, and local development
- [Architecture](architecture.md) — How the services are designed and connected
- [Troubleshooting](troubleshooting.md) — Solutions to common issues
