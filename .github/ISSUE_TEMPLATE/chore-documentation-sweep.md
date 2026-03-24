---
name: Documentation Sweep
about: Recurring chore — Deep documentation accuracy check and refresh
title: '[CHORE] Documentation Sweep'
labels: chore
assignees: ''
---

## Documentation Accuracy Sweep

### Objective

Perform a deep, codebase-driven documentation audit. Every claim in every doc file and in the custom instructions must be verified against the actual source code, configuration files, and dependency manifests — not memory or assumptions.

The codebase evolves continuously. Package versions, Python/Node targets, service ports, API routes, environment variables, directory layouts, and architectural patterns may have changed since docs were last updated. This chore exists to close that gap.

---

### Sources of Truth (read these first)

Before touching any doc, read and internalize the ground truth:

| File | What it governs |
|---|---|
| `backend/pyproject.toml` | Python version floor, all backend dependencies and version bounds, ruff/pyright/pytest config |
| `frontend/package.json` | All frontend dependencies and version bounds, npm scripts |
| `docker-compose.yml` | Service names, container ports, host port bindings, volumes, health checks, env vars passed to containers |
| `backend/src/config.py` | Every environment variable the backend accepts, types, defaults, required/optional, and validation rules |
| `backend/src/main.py` | Startup behavior, middleware order, lifespan hooks |
| `backend/src/migrations/` | Full schema history — tables, columns, constraints (newest migration = current schema) |
| `backend/src/api/` | Every route file = every endpoint that exists |
| `backend/src/services/` | Service module structure and responsibilities |
| `frontend/src/pages/` | Current page/route inventory |
| `frontend/src/components/` | Component domain breakdown |
| `.github/agents/copilot-instructions.md` | Custom AI instructions — must stay aligned with all of the above |

---

### Scope — What to Check and Fix

#### 1. Custom Instructions (`.github/agents/copilot-instructions.md`)

This file is the highest-priority target. An AI coding assistant reading stale instructions will make wrong decisions.

- [ ] **Stack versions** — compare every version pinned in this file against `pyproject.toml` and `package.json`. Update any that have drifted.
- [ ] **Python/Node targets** — confirm runtime targets (e.g. `python:3.14-slim`, `node:25-alpine`) match the actual Docker images and CI setup actions.
- [ ] **Backend dependencies** — verify listed packages and versions against `pyproject.toml` `[dependencies]` and `[optional-dependencies]`. Add missing packages; remove deleted ones.
- [ ] **Frontend dependencies** — verify listed packages and versions against `package.json` `dependencies` and `devDependencies`. Add missing; remove deleted.
- [ ] **Infrastructure section** — verify service names, port mappings, volume names, and health check paths against `docker-compose.yml`.
- [ ] **Architecture notes** — verify service module names/paths against the actual `backend/src/services/` tree.
- [ ] **Repo layout** — walk `backend/src/` and `frontend/src/` and reconcile the layout section against reality. Add new directories; remove deleted ones.
- [ ] **Migration count** — update the migration range (e.g. `001–017`) to match actual files in `backend/src/migrations/`.
- [ ] **Key tables list** — reconcile listed SQLite tables against actual migration SQL files.
- [ ] **Commands** — verify every listed command still works with the current toolchain.
- [ ] **"Do not recreate" list** — confirm deleted compatibility files are still absent and list is still accurate.

#### 2. `docs/configuration.md`

- [ ] Every env var in `backend/src/config.py` (`Settings` class fields) appears in the doc — including type, required/optional flag, default value, and description.
- [ ] No env var in the doc has been removed from `config.py`.
- [ ] Default values in the doc match the defaults in `config.py` exactly.
- [ ] Required-in-production flags match the `_validate_production_secrets` validator logic.

#### 3. `docs/api-reference.md`

- [ ] Every route file in `backend/src/api/` has matching entries. Walk each file and compare against the doc.
- [ ] Path prefixes, methods, path parameters, and auth requirements are accurate.
- [ ] Any endpoint that was removed or renamed is removed from the doc.
- [ ] Response shapes described match the Pydantic models in `backend/src/models/`.

#### 4. `docs/architecture.md`

- [ ] Service diagram reflects the current Docker Compose topology (3 services: backend, frontend, signal-api) with correct port numbers.
- [ ] All backend service modules listed match the actual `backend/src/services/` directory tree.
- [ ] AI provider section reflects current providers: Copilot SDK (default), OpenAI, Azure AI Inference.
- [ ] WebSocket and SSE flow descriptions match `backend/src/services/websocket.py` and actual usage in the projects API.
- [ ] Data persistence section lists all current SQLite tables and notes WAL mode.

#### 5. `docs/setup.md`

- [ ] Prerequisite versions (Python, Node, Docker) match `pyproject.toml` `requires-python`, `package.json` `engines` (if present), and Docker image tags.
- [ ] Docker Compose steps and service names match `docker-compose.yml`.
- [ ] Environment variable examples are consistent with `config.py` field names and defaults.
- [ ] Any env var in setup examples that no longer exists in `config.py` must be removed.

#### 6. `docs/agent-pipeline.md`

- [ ] Module paths for the workflow orchestrator, copilot polling, and GitHub projects service match actual file paths under `backend/src/services/`.
- [ ] Agent pipeline behavior descriptions are consistent with `backend/src/services/copilot_polling/` and `backend/src/services/workflow_orchestrator/`.
- [ ] Blocking queue behavior is documented (added in migration 017).

#### 7. `docs/project-structure.md`

- [ ] Directory tree matches the actual repo layout. Walk the repo and reconcile.
- [ ] New top-level service directories, component domains, and test subdirectories are included.
- [ ] Deleted directories/files are removed from the tree.

#### 8. `docs/testing.md`

- [ ] Test commands match the scripts defined in `package.json` and the pytest configuration in `pyproject.toml`.
- [ ] CI behavior description matches `.github/workflows/ci.yml` (Python version used in CI, Node version used in CI, jobs defined).
- [ ] Coverage targets and Playwright setup reflect current config files (`vitest.config.ts`, `playwright.config.ts`).

#### 9. `docs/signal-integration.md`

- [ ] Signal sidecar image name and configuration match `docker-compose.yml` (`signal-api` service).
- [ ] Webhook flow description matches `backend/src/services/signal_bridge.py` and `signal_delivery.py`.

#### 10. `docs/troubleshooting.md`

- [ ] Remove any troubleshooting entries for issues that are no longer applicable (e.g. fixed bugs, removed features, outdated setup steps).
- [ ] Confirm that Docker Compose service names and port numbers referenced in troubleshooting steps still match `docker-compose.yml`.

#### 11. `README.md`

- [ ] Links to `docs/` files are valid and point to existing files.
- [ ] Tech stack badges or version callouts match `pyproject.toml` and `package.json`.
- [ ] Quick-start commands match the current toolchain.

#### 12. `frontend/docs/` (if present)

- [ ] Component pattern docs reflect the current component directory structure under `frontend/src/components/`.
- [ ] Any hook or API pattern docs reflect hooks in `frontend/src/hooks/`.

---

### Actions Required

**For clear inaccuracies** (wrong version, deleted env var, renamed path, wrong port):

- Fix the doc directly.
- No test needed, but re-read the source of truth after the edit to confirm the fix is precise.

**For ambiguous or potentially breaking changes** (behavior descriptions that might conflict with undocumented design intent):

- Do **not** guess. Add a `<!-- TODO(doc-sweep): ... -->` comment in the doc explaining the uncertainty.
- Include these in the summary output.

**For missing documentation** (a feature/module exists in code but has no doc coverage):

- Add a concise, accurate entry. Match the existing format and tone of the surrounding doc.
- Do not over-document — one accurate paragraph beats three inaccurate sections.

---

### Validation

After all edits:

1. Run `npx markdownlint-cli docs/ README.md .github/agents/copilot-instructions.md` (if available) and fix any lint errors.
2. Verify all internal cross-links in the changed files resolve to existing headings.
3. Confirm no code block in a doc references a path, command, or variable that no longer exists.

---

### Output

Provide a single summary table at the end:

| # | File | Section | Change type | Description |
|---|---|---|---|---|
| 1 | `.github/agents/copilot-instructions.md` | Backend stack | Updated | `fastapi` version corrected to `>=0.135.0` |
| 2 | `docs/configuration.md` | Env vars | Added | `BLOCKING_QUEUE_ENABLED` was missing |
| 3 | `docs/api-reference.md` | Chores | Removed | `/api/v1/chores/{id}/run` no longer exists |
| 4 | `docs/architecture.md` | Services | Flagged | Description of caching layer may be outdated — left TODO |

Change types: **Updated** · **Added** · **Removed** · **Flagged**

---

### Constraints

- Do not change source code. This chore is documentation-only.
- Do not add aspirational or future-looking content — document only what the code currently does.
- Do not consolidate or restructure doc files unless a file is genuinely broken (e.g. duplicate headings causing link failures).
- Preserve existing doc tone and formatting style within each file.
- Each edit must be traceable to a specific source-of-truth file.
