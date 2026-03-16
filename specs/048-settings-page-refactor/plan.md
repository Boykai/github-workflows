# Implementation Plan: Settings Page Refactor with Secrets

**Feature Branch**: `048-settings-page-refactor`
**Created**: 2026-03-16
**Status**: Ready for Implementation
**Input**: spec.md (7 user stories, 35 FRs), parent issue #4152

## Overview

Refactor the Settings page from a monolithic form dump (18 components, 5 sections behind a collapsible) into a clean tabbed layout showing only essentials by default, with a new GitHub Repository Environment Secrets feature for MCP API keys (e.g. `COPILOT_MCP_CONTEXT7_API_KEY`).

**Approach**: Tab-based layout (Essential / Secrets / Preferences / Admin), new backend `secrets_service.py` using `githubkit` environment secrets API, new frontend `SecretsManager` component, and consolidation of redundant components.

## Tech Stack

- **Backend**: Python 3.13, FastAPI 0.135+, Pydantic 2.12+, githubkit 0.14.6+, pynacl (NEW)
- **Frontend**: TypeScript, React, Shadcn UI (Tabs), TanStack React Query, Zod, react-hook-form
- **Infrastructure**: aiosqlite, NaCl sealed-box encryption for GitHub secrets API

## Project Structure

```
solune/
├── backend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── secrets.py                 # CREATE — REST router for secrets
│   │   │   └── settings.py               # KEEP — existing settings router
│   │   ├── models/
│   │   │   └── tools.py                   # EDIT — add required_secrets to McpPresetResponse
│   │   ├── services/
│   │   │   ├── secrets_service.py         # CREATE — NaCl encrypted secrets CRUD
│   │   │   ├── tools/
│   │   │   │   └── presets.py             # EDIT — add required_secrets field to presets
│   │   │   └── github_projects/
│   │   │       └── __init__.py            # KEEP — GitHubClientFactory pattern to reuse
│   │   └── main.py                        # EDIT — register secrets router
│   ├── pyproject.toml                     # EDIT — add pynacl dependency
│   └── tests/
│       ├── unit/
│       │   └── test_secrets_service.py    # CREATE — mock-verified encrypt/list/set/delete
│       └── integration/
│           └── test_secrets_api.py        # CREATE — endpoint auth, routing, name validation
├── frontend/
│   └── src/
│       ├── pages/
│       │   └── SettingsPage.tsx            # REWRITE — 4-tab layout
│       ├── components/
│       │   └── settings/
│       │       ├── PrimarySettings.tsx     # RENAME → EssentialSettings.tsx
│       │       ├── AdvancedSettings.tsx    # DELETE — replaced by tabs
│       │       ├── PreferencesTab.tsx      # CREATE — consolidated prefs
│       │       ├── AdminTab.tsx            # CREATE — global + project
│       │       ├── SecretsManager.tsx      # CREATE — secrets CRUD UI
│       │       ├── SettingsSection.tsx     # KEEP — reuse as card wrapper
│       │       ├── DynamicDropdown.tsx     # KEEP — reuse in EssentialSettings
│       │       ├── globalSettingsSchema.ts # KEEP — reuse in AdminTab
│       │       ├── AIPreferences.tsx       # DELETE — consolidated
│       │       ├── AISettingsSection.tsx   # DELETE — consolidated
│       │       ├── DisplaySettings.tsx     # DELETE — consolidated
│       │       ├── WorkflowSettings.tsx    # DELETE — consolidated
│       │       └── NotificationSettings.tsx# DELETE — consolidated
│       ├── hooks/
│       │   ├── useSecrets.ts              # CREATE — TanStack Query hooks
│       │   └── useSettings.ts             # KEEP — existing settings hooks
│       ├── services/
│       │   └── api.ts                     # EDIT — add secretsApi group
│       └── types/
│           └── index.ts                   # EDIT — add SecretListItem types
```

## Phase Overview

### Phase 1: Backend — GitHub Environment Secrets Service

1. Add `pynacl` to `solune/backend/pyproject.toml`
2. Create `solune/backend/src/services/secrets_service.py` — NaCl encrypted secrets CRUD using `GitHubClientFactory.get_client()` pattern
3. Create `solune/backend/src/api/secrets.py` — REST router under `/api/v1/secrets` with authentication and validation
4. Register secrets router in `solune/backend/src/main.py`

### Phase 2: Frontend — Tab-Based Settings Layout

5. Restructure `solune/frontend/src/pages/SettingsPage.tsx` into 4 Shadcn `Tabs`
6. Rename `PrimarySettings.tsx` → `EssentialSettings.tsx`
7. Create `PreferencesTab.tsx` consolidating display, workflow, notification, and Signal settings
8. Create `AdminTab.tsx` consolidating global and project settings
9. Delete `AdvancedSettings.tsx`

### Phase 3: Frontend — Secrets Manager Component

10. Create `solune/frontend/src/hooks/useSecrets.ts` — TanStack Query hooks
11. Create `solune/frontend/src/components/settings/SecretsManager.tsx` — secrets CRUD UI
12. Add types to `solune/frontend/src/types/index.ts`
13. Add `secretsApi` group to `solune/frontend/src/services/api.ts`

### Phase 4: Integration — Wire Secrets to MCP Presets

14. Add `required_secrets` field to `McpPresetResponse` in models/tools.py and presets.py
15. Add secrets check endpoint to `solune/backend/src/api/secrets.py`
16. Optional deep-link toast on Tools page

### Phase 5: Cleanup & Polish

17. Delete redundant components
18. URL hash routing for tabs
19. Accessibility improvements
20. Tests (backend + frontend)

## Decisions

- **Tabs over accordion**: Direct access without scrolling. Current collapsed "Advanced" hides too much.
- **Environment secrets, not repo secrets**: GitHub's `$COPILOT_MCP_*` convention uses environment secrets (environment: `copilot`), not repository-level Actions secrets.
- **`pynacl` for encryption**: Required by GitHub API for NaCl sealed-box encryption of secret values before upload.
- **Known secrets constant**: Hardcoded `KNOWN_SECRETS` list driven by MCP preset `required_secrets` — avoids over-engineering.
- **Per-section save preserved**: Each card keeps its own save button — matches current UX contract.
- **Signal moves to Preferences**: Optional integration, not essential for most users.
- **Admin tab**: Controlled by `github_user_id === admin_github_user_id`; backend PUT endpoint already enforces admin-only server-side.

## Libraries

| Library | Version | Purpose |
|---------|---------|---------|
| pynacl | latest | NaCl sealed-box encryption for GitHub secrets API |
| githubkit | 0.14.6+ | Already installed — environment secrets endpoints |
| @radix-ui/react-tabs | via Shadcn | Already installed — tab UI component |
