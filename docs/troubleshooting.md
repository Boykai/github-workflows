# Troubleshooting

## Authentication

**OAuth callback fails / Login doesn't work:**
- Verify you created a **GitHub OAuth App** (not a GitHub App)
- Ensure `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` are correctly set
- Verify the callback URL in your OAuth App matches your setup:
  - **Docker**: `http://localhost:5173/api/v1/auth/github/callback`
  - **Local dev (no Docker)**: `http://localhost:8000/api/v1/auth/github/callback`
- Check that `FRONTEND_URL` is set to `http://localhost:5173` (Docker) or `http://localhost:8000` (local dev)
- Restart containers after updating `.env`: `docker compose down && docker compose up -d`

**"401 Unauthorized" after GitHub login:**
- Check browser devtools → Application → Cookies for `session_id`
- Ensure `CORS_ORIGINS` includes your frontend URL
- Verify `SESSION_SECRET_KEY` is set

## AI Issue Generation

**Copilot provider fails:**
- Ensure you're logged in (Copilot uses your GitHub OAuth token)
- Verify you have an active [GitHub Copilot subscription](https://github.com/features/copilot)
- Partial JSON responses are automatically repaired
- Check logs for `CopilotClient` errors

**Azure OpenAI provider fails:**
- Set `AI_PROVIDER=azure_openai`
- Verify `AZURE_OPENAI_ENDPOINT` format: `https://your-resource.openai.azure.com`
- Check `AZURE_OPENAI_KEY` is correct
- Ensure deployment name matches your Azure configuration

## Agent Pipeline

**Pipeline not advancing:**
- Check polling is running: `GET /api/v1/workflow/polling/status`
- Verify project has required columns: Backlog, Ready, In Progress, In Review (case-insensitive)
- Review logs: `docker compose logs -f backend`
- Manual trigger: `POST /api/v1/workflow/polling/check-all`
- Check per-issue state: `GET /api/v1/workflow/pipeline-states/{issue_number}`

**Pipeline advances too quickly (multiple agents simultaneously):**
- Ensure `PipelineState` is initialized with actual agents and a timestamp — empty agent lists are seen as immediately complete

**Workflow configuration lost after restart:**
- Verify Docker volume `ghchat-data` is mounted
- Check `DATABASE_PATH` points to a persistent location (default: `data/settings.db`)
- Auto-backfill migrates legacy `agent_pipeline_mappings` data on startup

**Agent configuration not saving / wrong agents:**
- Config is per-user in `project_settings`. Settings UI syncs to canonical `__workflow__` row
- Case-variant status keys are deduplicated automatically on save
- Verify with `GET /api/v1/workflow/config`

**speckit.implement not starting or completing:**
- Check that `speckit.tasks: Done!` was posted
- Verify issue transitioned to "In Progress"
- System waits for child PR targeting the main branch
- Check for Copilot delay — agent was correctly assigned

**Issue stuck in "In Progress":**
- System waits for `speckit.implement` child PR
- Detects `copilot_work_finished` timeline events or PR no longer draft
- Once detected: child PR merged → main PR ready → status "In Review"

**Duplicate PRs for one issue:**
- Previously caused by the system fighting Copilot's natural status changes
- System now accepts Copilot's "In Progress" status change instead of reverting

**Copilot agent fails to start / Repository ruleset violation:**
1. Repository → **Settings** → **Rules** → **Rulesets**
2. Under **Bypass list**, add **Copilot** (GitHub Copilot app)
3. Set bypass mode to **Always Allow**
4. Set target branches to **Include all branches**

## Signal

**QR code not appearing / connection fails:**
- Verify `signal-api` container is healthy: `docker compose ps`
- Check number is registered: `docker compose exec signal-api curl http://localhost:8080/v1/accounts`
- Check logs: `docker compose logs -f backend | grep signal`

**Messages not delivered:**
- Check Settings → Signal Connection shows "Connected"
- Check notification preferences aren't "None"
- Check `signal_messages` table for `failed` entries
- Check for retry warnings: `docker compose logs -f backend | grep delivery`

**Inbound messages not appearing:**
- Verify WS listener started (check startup logs for `Signal WS listener started`)
- Ensure sender's phone is linked to an account (unlinked numbers get auto-reply)
- Check user has an active project selected (routes to `last_active_project_id`)
- Media/attachment messages are unsupported (sender gets auto-reply)

## Webhooks

**Not triggering:**
- Verify `GITHUB_WEBHOOK_SECRET` matches GitHub webhook settings
- Check `GITHUB_WEBHOOK_TOKEN` has `repo` and `project` scopes
- Ensure webhook is configured for "Pull requests" events
- Check delivery logs: Repository → Settings → Webhooks → Recent Deliveries

## General

**Projects not showing:**
- Ensure GitHub token has `project` scope
- Organization projects need `read:org` scope

**Rate limiting:**
- GitHub API limit: 5,000 requests/hour for authenticated users
- App tracks remaining calls; wait for reset if limits are hit

**Port already in use:**

```bash
lsof -ti:8000 | xargs kill -9   # Backend
lsof -ti:5173 | xargs kill -9   # Frontend
```

## Viewing Logs

```bash
docker compose logs -f            # All containers
docker compose logs -f backend    # Backend only
docker compose logs -f frontend   # Frontend only
```
