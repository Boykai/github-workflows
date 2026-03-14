# Quickstart: Solune Rebrand & App Builder Architecture

**Feature**: `041-solune-rebrand-app-builder` | **Date**: 2026-03-14
**Prerequisites**: Docker, Docker Compose, Node.js 20+, Python 3.12+

## Overview

This guide describes the implementation sequence for the Solune rebrand and app builder architecture. The feature spans 6 phases with clear dependencies.

## Phase Dependency Graph

```text
Phase 1 (Monorepo)
    │
    ├──► Phase 2 (Rebrand)     ← can start in parallel with Phase 1
    │
    └──► Phase 3 (App Backend) ← blocks Phases 4-6
              │
              ├──► Phase 4 (Apps Page Frontend)
              │
              ├──► Phase 5 (Slash Commands)
              │
              └──► Phase 6 (Admin Guard)
```

## Phase 1 — Monorepo Restructure

### Steps

1. **Archive current state**
   ```bash
   git tag pre-solune-archive
   git push origin pre-solune-archive
   ```

2. **Create directory structure**
   ```bash
   mkdir -p solune apps
   touch apps/.gitkeep
   ```

3. **Move files into `solune/`**
   ```bash
   # Move all top-level directories except .github, .git, solune, apps
   for dir in backend frontend docs scripts specs; do
     git mv "$dir" solune/
   done
   # Move top-level config files
   for file in docker-compose.yml CHANGELOG.md mcp.json .env.example \
               .pre-commit-config.yaml .markdownlint.json .markdown-link-check.json \
               .dockerignore .cgcignore tasks.md; do
     git mv "$file" solune/
   done
   ```

4. **Create root-level files**
   - `README.md` — Solune platform pitch
   - `docker-compose.yml` — Root orchestration (references `./solune/backend`, etc.)

5. **Update all internal paths**
   - `solune/docker-compose.yml`: Build contexts → `./backend` (relative to solune/)
   - `.github/workflows/ci.yml`: Working directories → `solune/backend`, `solune/frontend`
   - `.vscode/mcp.json`: Tool paths
   - `.devcontainer/`: Any container paths
   - `solune/mcp.json`: Tool references

6. **Verify**
   ```bash
   # From repo root
   cd solune && docker compose build
   cd solune/backend && python -m pytest tests/ -v
   cd solune/frontend && npm run build && npx vitest run
   ```

## Phase 2 — Rebrand

### Steps

1. **Run string replacement script** (see `research.md` R3 for full mapping)
   ```bash
   # Example replacements (from solune/ directory)
   find . -type f \( -name "*.py" -o -name "*.ts" -o -name "*.tsx" \
     -o -name "*.yml" -o -name "*.json" -o -name "*.md" \) \
     -exec sed -i 's/ghchat-backend/solune-backend/g' {} +
   # Repeat for each mapping...
   ```

2. **Rewrite README.md** — New Solune product pitch

3. **Rewrite copilot-instructions.md** — New repo structure and agent guidance

4. **Update frontend branding**
   - `AppPage.tsx`: Heading → "Solune"
   - `LoginPage.tsx`: Branding → "Solune"
   - `Sidebar.tsx`: Brand mark → "Solune"

5. **Verify zero old-brand remnants**
   ```bash
   # Should return no matches
   grep -ri "Agent Projects\|ghchat-\|GitHub Workflows Chat" solune/ --include="*.py" --include="*.ts" --include="*.tsx" --include="*.yml" --include="*.json" --include="*.md"
   ```

## Phase 3 — App Management Backend

### Steps

1. **Create migration** — `solune/backend/src/migrations/024_apps.sql`

2. **Create model** — `solune/backend/src/models/app.py`
   - See `data-model.md` for Pydantic models

3. **Create service** — `solune/backend/src/services/app_service.py`
   - CRUD operations, scaffold logic, lifecycle management
   - Path validation, name sanitization

4. **Create API routes** — `solune/backend/src/api/apps.py`
   - See `contracts/apps-api.md` for endpoint specifications

5. **Register router** in `solune/backend/src/main.py`
   ```python
   from src.api.apps import router as apps_router
   app.include_router(apps_router, prefix="/api/v1/apps", tags=["apps"])
   ```

6. **Verify**
   ```bash
   cd solune/backend
   python -m pytest tests/test_app_service.py -v
   python -m ruff check src/api/apps.py src/models/app.py src/services/app_service.py
   python -m pyright src/models/app.py src/services/app_service.py
   ```

## Phase 4 — Apps Page Frontend

### Steps

1. **Create types** — `solune/frontend/src/types/apps.ts`

2. **Create API client** — `solune/frontend/src/services/appsApi.ts`

3. **Create hooks** — `solune/frontend/src/hooks/useApps.ts`

4. **Create components**:
   - `AppCard.tsx` — App card with status badge
   - `AppDetailView.tsx` — Detail panel with preview and controls
   - `AppPreview.tsx` — Iframe wrapper for live preview

5. **Create page** — `solune/frontend/src/pages/AppsPage.tsx`

6. **Add route** in `App.tsx`:
   ```tsx
   <Route path="/apps" element={<AppsPage />} />
   <Route path="/apps/:appName" element={<AppDetailView />} />
   ```

7. **Add navigation** — Add "Apps" link to Sidebar

8. **Verify**
   ```bash
   cd solune/frontend
   npx vitest run
   npm run build
   npm run type-check
   ```

## Phase 5 — Slash Command Context Switching

### Steps

1. **Add context switch endpoint** — `POST /api/v1/chat/context`
2. **Extend session model** — Add `active_app_name` attribute
3. **Update chat command autocomplete** — Include app names
4. **Add context indicator** — Show active app in chat header
5. **Update agent operation routing** — Resolve working directory from context

## Phase 6 — Admin Guard

### Steps

1. **Create guard config** — `solune/guard-config.yml`
2. **Create guard service** — `solune/backend/src/services/guard_service.py`
3. **Create guard middleware** — `solune/backend/src/middleware/admin_guard.py`
4. **Integrate with agent operations** — Intercept file operations
5. **Verify**
   ```bash
   cd solune/backend
   python -m pytest tests/test_guard.py -v
   ```

## Verification Checklist

After all phases:

- [ ] `docker compose up` from repo root starts all services
- [ ] All backend tests pass: `cd solune/backend && python -m pytest tests/ -v`
- [ ] All frontend tests pass: `cd solune/frontend && npx vitest run`
- [ ] Zero old-brand strings in codebase
- [ ] Apps page accessible at `/apps`
- [ ] Can create, start, stop, delete an app
- [ ] `/<app-name>` command switches context
- [ ] Guard blocks `solune/` modifications, allows `apps/` modifications
