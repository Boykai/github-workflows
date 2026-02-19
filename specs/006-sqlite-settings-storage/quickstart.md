# Quickstart: SQLite-Backed Settings Storage

**Feature**: 006-sqlite-settings-storage
**Date**: 2026-02-19

## Prerequisites

- Docker and Docker Compose installed
- Existing `.env` file with GitHub OAuth credentials (`GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, `SESSION_SECRET_KEY`)
- Repository cloned and on branch `006-sqlite-settings-storage`

## What Changes

| Component | Change |
|-----------|--------|
| Backend | New dependency: `aiosqlite`. New files: `database.py`, `session_store.py`, `settings_store.py`, `api/settings.py`, `models/settings.py`, `migrations/001_initial_schema.sql`. Modified: `main.py`, `github_auth.py`, `config.py`, `constants.py`, `api/__init__.py` |
| Frontend | New files: `pages/SettingsPage.tsx`, `hooks/useSettings.ts`, `components/settings/*.tsx`. Modified: `App.tsx`, `useAppTheme.ts`, `api.ts`, `types/index.ts` |
| Docker | `docker-compose.yml` adds a named volume `ghchat-data` mounted at `/app/data` in the backend container |

## Getting Started

### 1. Start the application

```bash
docker compose up --build -d
```

On first startup, the backend automatically:
1. Creates the SQLite database at `/app/data/settings.db`
2. Creates the `schema_version` table
3. Runs migration `001_initial_schema.sql` (creates all tables)
4. Seeds `global_settings` from environment variables (if no global settings exist)
5. Logs: `INFO - Database initialized at /app/data/settings.db (schema version: 1)`

### 2. Verify database initialization

```bash
docker compose logs backend | grep -i "database\|migration\|schema"
```

Expected output:
```
INFO - Database initialized at /app/data/settings.db (schema version: 1)
INFO - Applied migration 001_initial_schema (0 → 1)
INFO - Global settings seeded from environment variables
```

### 3. Log in via GitHub OAuth

Navigate to `http://localhost:5173`. Click "Login with GitHub" and complete the OAuth flow. Your session is now persisted to SQLite.

### 4. Verify session persistence

```bash
# Restart only the backend
docker compose restart backend

# Reload the browser — you should still be logged in
```

### 5. Access the Settings page

After logging in, click "Settings" in the header navigation (next to "Chat" and "Project Board"). You'll see sections for:

- **AI Preferences**: Provider, model, temperature
- **Display Preferences**: Theme, default view, sidebar state
- **Workflow Defaults**: Default repository, assignee, polling interval
- **Notification Preferences**: Toggle each event type
- **Global Settings**: Instance-wide defaults (visible to all users)

### 6. Test the Settings API directly

```bash
# Get effective user settings (merged with global defaults)
curl -s -b "session_id=YOUR_SESSION_ID" \
  http://localhost:8000/api/v1/settings/user | python -m json.tool

# Update user AI preferences
curl -s -b "session_id=YOUR_SESSION_ID" \
  -X PUT http://localhost:8000/api/v1/settings/user \
  -H "Content-Type: application/json" \
  -d '{"ai": {"provider": "azure_openai", "model": "gpt-4", "temperature": 0.5}}' | python -m json.tool

# Get global settings
curl -s -b "session_id=YOUR_SESSION_ID" \
  http://localhost:8000/api/v1/settings/global | python -m json.tool

# Get project-specific settings
curl -s -b "session_id=YOUR_SESSION_ID" \
  http://localhost:8000/api/v1/settings/project/PVT_kwDOABCD1234 | python -m json.tool
```

### 7. Verify data survives container recreation

```bash
# Stop and remove containers (volume persists)
docker compose down

# Recreate containers
docker compose up --build -d

# Log in again — previous settings should be preserved
# Check logs for "Database initialized" (no re-seeding)
docker compose logs backend | grep "Global settings"
# Should NOT show "seeded from environment variables" on subsequent startups
```

## Database Location

- **Container path**: `/app/data/settings.db`
- **Docker volume**: `ghchat-data` (named volume, persists across `docker compose down`)
- **Manual inspection**:
  ```bash
  docker compose exec backend sqlite3 /app/data/settings.db ".tables"
  # Output: global_settings  project_settings  schema_version  user_preferences  user_sessions
  ```

## Configuration

New environment variable (optional):

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_PATH` | `/app/data/settings.db` | Path to SQLite database file |

The directory is automatically created if it doesn't exist.

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| "Schema version mismatch" error on startup | Database was upgraded by a newer version of the app, then rolled back | Delete the database file or upgrade the app |
| Sessions lost after restart | Docker volume not mounted | Verify `ghchat-data` volume in `docker compose config` |
| "Database is locked" errors | Multiple backend instances | Only run one backend instance (SQLite single-writer) |
| Settings not persisting | Browser not sending session cookie | Check cookies in DevTools; ensure `credentials: 'include'` in fetch |
