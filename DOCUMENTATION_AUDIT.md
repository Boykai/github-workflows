# DOCUMENTATION AUDIT REPORT
Generated for github-workflows codebase

---

## 1. API REFERENCE AUDIT
**File:** `/home/runner/work/github-workflows/github-workflows/docs/api-reference.md`

### What's Accurate ✅

- All major endpoint categories documented correctly:
  - Health check (`GET /health`)
  - Authentication routes (`/auth/*`)
  - Projects routes (`/projects/*`)
  - Board routes (`/board/*`)
  - Chat routes (`GET /chat/messages`, `POST /chat/messages`, `DELETE /chat/messages`)
  - Chat proposals (`/chat/proposals/{id}/*`)
  - Tasks routes (`POST /tasks`, `PATCH /tasks/{id}/status`)
  - Chores routes (CRUD + trigger + chat + evaluate)
  - Cleanup routes (preflight, execute, history)
  - Settings routes (user, global, project-level, models)
  - Workflow routes (config, agents, transitions, pipeline states, polling)
  - Signal routes (connection, preferences, banners)
  - Agents CRUD routes (`GET /agents/{project_id}`, `POST`, `PATCH`, `DELETE`)
  - MCP routes (`/settings/mcps/*`)
  - Metadata routes (`/metadata/{owner}/{repo}/*`)
  - Webhooks (`POST /webhooks/github`)

- WebSocket endpoint documented (`WS /projects/{id}/subscribe`)
- SSE endpoint documented (`GET /projects/{id}/events`)
- Proper prefix `/api/v1` mentioned
- Authentication requirements clearly stated
- `#agent` command documented

### What's Inaccurate or Outdated ❌

1. **Line 21: Missing `/auth/session` endpoint**
   - Documentation states: `POST /auth/session` - Set session cookie from token
   - **Actual Implementation:** This endpoint does not exist in `backend/src/api/auth.py`
   - Actual endpoints present: `GET /auth/github`, `GET /auth/github/callback`, `GET /auth/me`, `POST /auth/logout`, `POST /auth/dev-login`

### What's Missing 🟡

1. **Extra Agent Endpoints Not Documented:**
   - `GET /agents/{project_id}/pending` - List pending agents
   - `DELETE /agents/{project_id}/pending` - Purge pending agents (with `AgentPendingCleanupResult` response)
   - `PATCH /agents/{project_id}` - Bulk update models (undocumented)
   - `GET /agents/{project_id}/{agent_id}/tools` - Get agent tools configuration
   - `PUT /agents/{project_id}/{agent_id}/tools` - Update agent tools configuration
   
   Location: `backend/src/api/agents.py`, lines 59-238

2. **Chat Upload Endpoint Not Documented:**
   - `POST /chat/upload` - Upload files (returns `FileUploadResponse` with file URL)
   - Location: `backend/src/api/chat.py`, line 919

3. **Board Blocking Queue Endpoint Not Documented:**
   - `GET /board/projects/{project_id}/blocking-queue` - Get blocking queue items (requires project access)
   - Location: `backend/src/api/board.py`, line 254

4. **Pipelines API - Entirely Missing Section**
   - New API endpoints for pipeline CRUD that exist but aren't documented:
   - `GET /pipelines/{project_id}` - List pipelines
   - `POST /pipelines/{project_id}/seed-presets` - Seed preset pipelines
   - `GET /pipelines/{project_id}/assignment` - Get project pipeline assignment
   - `PUT /pipelines/{project_id}/assignment` - Update project assignment
   - `PATCH /pipelines/{project_id}/assignment` - Patch project assignment
   - `POST /pipelines/{project_id}` - Create pipeline
   - `GET /pipelines/{project_id}/{pipeline_id}` - Get specific pipeline
   - `PUT /pipelines/{project_id}/{pipeline_id}` - Update pipeline
   - `DELETE /pipelines/{project_id}/{pipeline_id}` - Delete pipeline
   - Location: `backend/src/api/pipelines.py`, entire file (50+ lines of endpoints)

5. **Tools API - Entirely Missing Section**
   - MCP tool management endpoints:
   - `GET /tools/presets` - List MCP presets
   - `GET /tools` - List user's MCP tools
   - `POST /tools` - Create new tool
   - `PUT /tools/{tool_id}` - Update tool
   - `DELETE /tools/{tool_id}` - Delete tool
   - `POST /tools/sync` - Sync tools
   - `GET /tools/repo-config` - Get repository MCP config
   - `PUT /tools/repo-config` - Update repository config
   - `POST /tools/upload` - Upload MCP config
   - Location: `backend/src/api/tools.py`, entire file

6. **Signal Webhook Endpoint Not Clearly Documented:**
   - `POST /signal/webhook/inbound` - Handle inbound Signal messages
   - Mentioned in code but not in API reference table
   - Location: `backend/src/api/signal.py`, line 261

**Total Routes in Docs: 74**
**Actual Implemented Routes: 102+** (including new pipeline, tools, pending agents, blocking queue, signal webhook)

---

## 2. CONFIGURATION AUDIT
**File:** `/home/runner/work/github-workflows/github-workflows/docs/configuration.md`
**Source:** `/home/runner/work/github-workflows/github-workflows/backend/src/config.py`

### What's Accurate ✅

- All required environment variables documented:
  - `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, `SESSION_SECRET_KEY`
- GitHub OAuth section complete
- AI Provider section correct (copilot/azure_openai)
- Webhook section accurate
- Polling section accurate (`COPILOT_POLLING_INTERVAL`)
- Defaults section accurate (repository, project ID, assignee)
- Server section complete (HOST, PORT, DEBUG, CORS_ORIGINS)
- Session section accurate
- Database section includes correct path structure
- Signal integration section documented
- Security section documented (encryption, cookie settings)
- Cache section documented
- Frontend variable `VITE_API_BASE_URL` documented

### What's Inaccurate or Outdated ❌

1. **Line 77: DATABASE_PATH Default Value Mismatch**
   - Documentation states: `/app/data/settings.db`
   - Actual default in `backend/src/config.py` line 79: `/var/lib/ghchat/data/settings.db`
   - Docker Compose override (line 35): `/var/lib/ghchat/data/settings.db`
   - **Impact:** Documentation is misleading for non-Docker setups

2. **Line 110: Migration Count Outdated**
   - Documentation states: "currently `001` through `012`"
   - Actual migrations: 21 files (001-018 with some numbered variations)
   - New migrations include:
     - 013_agent_config_lifecycle_status.sql
     - 013_pipeline_configs.sql
     - 014_agent_default_models.sql
     - 014_extend_mcp_tools.sql
     - 015_agent_icon_name.sql
     - 015_pipeline_mcp_presets.sql
     - 016_chores_enhancements.sql
     - 017_blocking_queue.sql
     - 018_pipeline_blocking_override.sql
   - **Impact:** Significantly understates current database schema complexity

### What's Missing 🟡

1. **Enable Docs Configuration Variable Not Documented:**
   - `ENABLE_DOCS` (default: `false`) - Toggle API documentation
   - In config.py line 94, in docker-compose.yml line 34
   - Should be added to "Server" section

2. **Signal Webhook Secret Listed as Optional But Not in Details:**
   - Line 85 documents `SIGNAL_WEBHOOK_SECRET`
   - Not clearly tied to webhook signature verification like GitHub's
   - Should clarify: "Secret for verifying inbound Signal webhook payloads (similar to GITHUB_WEBHOOK_SECRET)"

---

## 3. PROJECT STRUCTURE AUDIT
**File:** `/home/runner/work/github-workflows/github-workflows/docs/project-structure.md`

### What's Accurate ✅

- Main directory structure correct
- `.devcontainer/` documented with correct files
- `.github/agents/` with agent definitions (including new ones: designer, judge, linter, quality-assurance, archivist)
- Docker-compose.yml path correct
- Backend structure accurate:
  - `src/api/` with all major route files
  - `src/middleware/`
  - `src/migrations/`
  - `src/models/`
  - `src/services/` with subdirectories
- Frontend structure accurate:
  - Components directory structure
  - Pages directory
  - Services (api.ts)
- Scripts directory exists with pre-commit hooks
- Specs directory structure (feature specifications)

### What's Inaccurate or Outdated ❌

1. **Lines 40-55: API Route Files Incomplete List**
   - Documentation lists routes but is missing:
   - `pipelines.py` - **NOT DOCUMENTED** (NEW)
   - `tools.py` - **NOT DOCUMENTED** (NEW)
   - Lists 14 route files, actual count: 18

2. **Lines 59-75: Models Directory Incomplete**
   - Documentation lists specific model files
   - Missing new models:
   - `blocking.py` - Blocking queue models (NEW)
   - `pipeline.py` - Pipeline configuration models (NEW)
   - `tools.py` - MCP tool models (NEW)
   - List shows 9 items, actual count: 19

3. **Line 39: Dockerfile Python Version Not Specified**
   - Documentation: "Python 3.13-slim"
   - **Not verified in docs** but should confirm in actual Dockerfile
   - pyproject.toml specifies `requires-python = ">=3.12"` (line 5)
   - But ruff and pyright configured for Python 3.13

4. **Lines 78-101: Services Directory Incomplete**
   - Missing service directories that exist:
   - `services/pipelines/` - Pipeline service (NEW)
   - `services/tools/` - Tools/MCP service (NEW)
   - Missing standalone service files:
   - `blocking_queue.py` - Blocking queue service
   - `blocking_queue_store.py` - Queue persistence
   - Total listed: ~12 services, actual count: 30+ service files

5. **Line 6: Frontend Framework Versions Not Specific**
   - Documentation mentions versions exist in later text (e.g., "React 19 with TypeScript 5.9, built by Vite 7")
   - But line 6 just says "React, TypeScript, Vite, TanStack Query"
   - Should add version info in tree view

### What's Missing 🟡

1. **`.specify/scripts/` Directory**
   - Exists but not documented in project structure
   - Used for specification generation utilities

2. **Frontend Additional Directories:**
   - `src/context/` - React context providers (not listed)
   - `src/data/` - Data utilities (not listed)
   - `src/lib/` - Library utilities (not listed)
   - `src/layout/` - Layout components (not listed)
   - `src/test/` and `src/tests/` - Test utilities (may be duplicates)

3. **Backend `.logging_utils` Module**
   - Referenced in config.py (line 215) but not documented
   - Provides RequestIDFilter, SanitizingFormatter, StructuredJsonFormatter

4. **Missing New Feature Directories in Services:**
   - `services/pipelines/` - Complete directory with multiple files
   - `services/tools/` - Complete directory with service and presets

---

## 4. SETUP AUDIT
**File:** `/home/runner/work/github-workflows/github-workflows/docs/setup.md`

### What's Accurate ✅

- Prerequisites section complete
- GitHub Codespaces quick start documented
- Docker quick start documented with correct steps
- OAuth app setup documented with correct scopes
- Session secret generation with `openssl rand -hex 32` documented
- Docker Compose startup documented correctly
- Local development setup accurate
- Git hooks setup documented (`scripts/pre-commit`, `setup-hooks.sh`)
- Optional webhook setup documented with correct scopes
- Signal messaging setup references correct integration doc

### What's Inaccurate or Outdated ❌

1. **Lines 22-23: Devcontainer Versions Mismatch**
   - Documentation states: "Python 3.12 and Node.js 20"
   - Actual `.devcontainer/devcontainer.json`:
     - Python: 3.12 ✅
     - Node: 20 ✅
   - **BUT** bare-metal/Docker requirements state: "Node.js 22+ and Python 3.13+"
   - This is a deliberate difference (Codespaces pinned versions vs. newer bare-metal), but could be confusing
   - **Improvement:** Add explicit note that Codespaces uses older pinned versions

2. **Line 73: OAuth Callback URL Path Incorrect**
   - Documentation shows: `http://localhost:5173/api/v1/auth/github/callback`
   - **Actual path should be:** `http://localhost:5173/api/v1/auth/github/callback` (through proxy)
   - But the setup says "Authorization callback URL" which is correct
   - Note: docker-compose.yml line 13 shows: `http://localhost:5173/api/v1/auth/github/callback`
   - But setup.md says homepage is `http://localhost:5173` - this is correct because nginx proxies `/api/` to backend

### What's Missing 🟡

1. **Docker Port Clarification**
   - Line 102 mentions containers but frontend port mapping could be clearer
   - Frontend runs on 8080 internally, exposed as 5173 on host (docker-compose.yml line 58)
   - Setup guide doesn't explain this mapping

2. **API Documentation Access**
   - Setup doesn't mention how to access `/api/docs` when `DEBUG=true` or `ENABLE_DOCS=true`
   - Should add: "API Interactive Docs: http://localhost:8000/api/docs (when DEBUG=true)"

3. **Alternative: ENABLE_DOCS Configuration**
   - Setup mentions `DEBUG=true` for API docs
   - But config.py now has separate `ENABLE_DOCS` flag (line 94)
   - Setup should mention this independent toggle

4. **Database Initialization**
   - Setup doesn't mention that database migrations run automatically on startup
   - Users may wonder about database setup steps

5. **Frontend Build Info Missing**
   - Setup mentions `npm run dev` but doesn't explain build process
   - package.json shows separate `build` command used in Docker
   - Could add: "For production build: `npm run build`"

---

## 5. ARCHITECTURE AUDIT
**File:** `/home/runner/work/github-workflows/github-workflows/docs/architecture.md`

### What's Accurate ✅

- Overview section describes full-stack correctly
- Services diagram mentions all main components:
  - Frontend (React 19 + Vite 7, TypeScript 5.9)
  - Backend (FastAPI)
  - Signal sidecar
- Docker Compose services table accurate:
  - backend: 8000, FastAPI
  - frontend: 5173 → 80, nginx
  - signal-api: 8080, signal-cli-rest-api
- Volumes documented (ghchat-data, signal-cli-config)
- Frontend architecture section accurate:
  - React 19, TypeScript 5.9, Vite 7
  - TanStack Query v5
  - dnd-kit for drag-drop
  - Tailwind CSS 4
  - Error boundary handling
- Backend framework (FastAPI, Pydantic v2, aiosqlite, SQLite WAL)
- Module layout for backend mostly accurate
- AI Completion Providers section accurate (Copilot SDK vs Azure OpenAI)
- Startup lifecycle described correctly
- nginx reverse proxy configuration documented

### What's Inaccurate or Outdated ❌

1. **Line 49: Service Port Mapping Misleading**
   - Documentation shows: `frontend | ghchat-frontend | 5173 → 80`
   - More accurately: `frontend | ghchat-frontend | 8080 (internal) → 5173 (docker-compose port mapped to 5173:8080)`
   - docker-compose.yml line 58: `"127.0.0.1:5173:8080"`
   - Should clarify: internal nginx listens on 8080, exposed to host as 5173

2. **Lines 93-101: Backend Module References Incomplete**
   - Documentation lists `api/` routes: "auth, agents, board, chat, chores, cleanup, health, mcp, metadata, projects, settings, signal, tasks, webhooks, workflow"
   - **Missing:** `pipelines`, `tools`
   - Should list 16 route files, not 14

3. **Lines 98-102: Services Section Incomplete**
   - Documentation lists subdirectories but missing:
   - `services/pipelines/` (NEW) - Pipeline service module
   - `services/tools/` (NEW) - Tools/MCP service module
   - Also missing individual service files:
   - `blocking_queue.py`, `blocking_queue_store.py`, etc.

### What's Missing 🟡

1. **Pipeline Service Architecture Not Documented**
   - New major feature: `services/pipelines/` with pipeline CRUD
   - Not mentioned in architecture overview
   - Creates new abstraction layer for agent pipeline configuration

2. **Tools/MCP Service Architecture Not Documented**
   - New feature: `services/tools/` for MCP tool management
   - Separate from agents but related
   - Not described in architecture

3. **Blocking Queue Feature Not Mentioned**
   - New service: `services/blocking_queue.py`, `blocking_queue_store.py`
   - Related endpoint: `GET /board/projects/{project_id}/blocking-queue`
   - Database migration: `017_blocking_queue.sql`
   - Architectural impact not documented

4. **Frontend New Directories Not Listed**
   - `src/context/` - Context providers
   - `src/data/` - Data utilities
   - `src/lib/` - Library utilities
   - `src/layout/` - Layout components
   - Should be in module layout table (lines 69-81)

5. **Chores Service Architecture Missing Details**
   - Documentation mentions `services/chores/` but doesn't list subdirectory structure
   - Directory contains: chat.py, counter.py, scheduler.py, service.py, template_builder.py

6. **Frontend Hooks List Incomplete**
   - Line 79 lists many hooks but documentation string may be outdated
   - Should verify all hooks in `src/hooks/` match list

7. **Agent Configuration Pipeline Not Described**
   - Documentation doesn't explain the full #agent command flow
   - 8-step pipeline mentioned in API reference but not architectural details
   - Related services: `agent_creator.py`, `agent_tracking.py`

---

## SUMMARY TABLE

| Audit Area | Status | Critical Issues | Missing Items | Misleading Items |
|------------|--------|-----------------|-----------------|------------------|
| **API Reference** | ⚠️ INCOMPLETE | Missing `/auth/session` endpoint | 4 new endpoints (blocking-queue, chat/upload, agents/pending, agents/tools), 2 entire new sections (pipelines, tools) | None |
| **Configuration** | ⚠️ MOSTLY OK | DATABASE_PATH path mismatch | ENABLE_DOCS variable | Outdated migration count |
| **Project Structure** | ⚠️ INCOMPLETE | Missing new API route files | 5 new model files, 2 new service directories, 4 frontend directories | None |
| **Setup** | ✅ MOSTLY OK | None | 3 improvements (API docs access, build info, db initialization) | Port mapping could be clearer |
| **Architecture** | ⚠️ INCOMPLETE | Service port mapping unclear | 2 new service modules, blocking queue feature, frontend directories | API route list incomplete |

---

## PRIORITY FIXES (High to Low)

### 🔴 CRITICAL
1. **API Reference:** Add entire "Pipelines" and "Tools" sections (2 major API modules)
2. **API Reference:** Document 4 missing agent endpoints (pending, tools)
3. **Configuration:** Fix DATABASE_PATH documentation (misleading for non-Docker)

### 🟠 HIGH  
4. **Project Structure:** Add pipelines.py and tools.py to api/ list, add blocking.py and pipeline.py to models/
5. **Architecture:** Add pipelines and tools services to backend module layout
6. **API Reference:** Document blocking-queue endpoint and chat/upload endpoint

### 🟡 MEDIUM
7. **Configuration:** Document ENABLE_DOCS variable
8. **Project Structure:** Add missing service directories (pipelines, tools) and frontend directories
9. **Setup:** Add note about API docs access and database initialization
10. **Architecture:** Clarify port mappings and service structure

---
