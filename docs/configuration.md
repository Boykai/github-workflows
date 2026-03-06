# Configuration

All configuration is managed through environment variables. Copy `.env.example` to `.env` and customize.

## Environment Variables

### Required

| Variable | Description |
|----------|-------------|
| `GITHUB_CLIENT_ID` | GitHub OAuth App Client ID |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth App Client Secret |
| `SESSION_SECRET_KEY` | Random hex string for session encryption (`openssl rand -hex 32`) |

### GitHub OAuth

| Variable | Default | Description |
|----------|---------|-------------|
| `GITHUB_REDIRECT_URI` | `http://localhost:8000/api/v1/auth/github/callback` | OAuth callback URL |
| `FRONTEND_URL` | `http://localhost:5173` | Frontend URL for OAuth redirects |

### AI Provider

The AI provider controls which LLM generates GitHub Issues from natural language input.

| Variable | Default | Description |
|----------|---------|-------------|
| `AI_PROVIDER` | `copilot` | Provider: `copilot` (GitHub Copilot via OAuth) or `azure_openai` |
| `COPILOT_MODEL` | `gpt-4o` | Model for Copilot completion provider |
| `AZURE_OPENAI_ENDPOINT` | — | Azure OpenAI endpoint URL (only when `azure_openai`) |
| `AZURE_OPENAI_KEY` | — | Azure OpenAI API key (only when `azure_openai`) |
| `AZURE_OPENAI_DEPLOYMENT` | `gpt-4` | Azure OpenAI deployment name |

### Webhook (Optional)

| Variable | Default | Description |
|----------|---------|-------------|
| `GITHUB_WEBHOOK_SECRET` | — | Secret for webhook signature verification |
| `GITHUB_WEBHOOK_TOKEN` | — | GitHub PAT (classic) with `repo` + `project` scopes |

### Polling

| Variable | Default | Description |
|----------|---------|-------------|
| `COPILOT_POLLING_INTERVAL` | `60` | Polling interval in seconds (0 to disable) |

### Defaults

| Variable | Default | Description |
|----------|---------|-------------|
| `DEFAULT_REPOSITORY` | — | Default repo for issue creation (`owner/repo`) |
| `DEFAULT_ASSIGNEE` | `""` | Default assignee for In Progress issues |

### Server

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server bind host |
| `PORT` | `8000` | Server bind port |
| `DEBUG` | `false` | Enable API docs (`/api/docs`), dev-login endpoint |
| `CORS_ORIGINS` | `http://localhost:5173` | Allowed CORS origins (comma-separated) |

### Session

| Variable | Default | Description |
|----------|---------|-------------|
| `SESSION_EXPIRE_HOURS` | `8` | Session TTL in hours |
| `SESSION_CLEANUP_INTERVAL` | `3600` | Interval for cleaning expired sessions (seconds) |

### Database

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_PATH` | `/app/data/settings.db` | SQLite database path (map to Docker volume for persistence) |

### Signal (Optional)

| Variable | Default | Description |
|----------|---------|-------------|
| `SIGNAL_API_URL` | `http://signal-api:8080` | URL of signal-cli-rest-api sidecar |
| `SIGNAL_PHONE_NUMBER` | — | Dedicated Signal phone number (E.164 format) |

### Cache

| Variable | Default | Description |
|----------|---------|-------------|
| `CACHE_TTL_SECONDS` | `300` | In-memory cache TTL in seconds |

### Frontend (Vite)

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_BASE_URL` | `/api/v1` | API base URL for frontend |

## Database

SQLite in WAL mode at `DATABASE_PATH`. Schema is auto-migrated at startup via numbered SQL files in `backend/src/migrations/` (currently `001` through `012`). Migrations are tracked by a `schema_version` table.

### Migration Files

| Migration | Purpose |
|-----------|---------|
| `001_initial_schema.sql` | Sessions, project settings, global settings tables |
| `002_add_workflow_config_column.sql` | `workflow_config` column on `project_settings` |
| `003_add_admin_column.sql` | `admin_github_user_id` on `global_settings` |
| `004_add_signal_tables.sql` | Signal connection, messages, banners tables |
| `005_signal_phone_hash_unique.sql` | Unique constraint on phone hash |
| `006_add_mcp_configurations.sql` | MCP configurations table |
| `007_agent_configs.sql` | Agent configuration storage |
| `008_cleanup_audit_logs.sql` | Cleanup audit log table |
| `009_housekeeping.sql` | Housekeeping templates and schedules |
| `010_chores.sql` | Chores system (replaces housekeeping) |
| `011_metadata_cache.sql` | GitHub metadata cache (labels, branches, milestones) |
| `012_chat_persistence.sql` | Persistent chat messages, proposals, recommendations |

## Workflow Settings

Agent pipeline mappings are configurable through the Settings UI or `PUT /api/v1/workflow/config`:

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

Settings are stored per-user in SQLite with a 3-tier fallback:
1. User-specific row
2. Canonical `__workflow__` row
3. Any-user fallback with automatic backfill

Case-insensitive status deduplication is applied on both save (backend) and load (frontend).
