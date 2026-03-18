# Solune — Platform Core

> Agent-driven development platform. Design customizable Agent Pipelines via a visual GUI, compose AI Custom GitHub Agents to execute remote work in series or parallel, and track everything through GitHub Projects.

This directory contains the Solune platform core: backend, frontend, documentation, scripts, and feature specifications. For the monorepo overview, see the [root README](../README.md).

## What It Does

- **Build apps from conversation** — Describe what you want, Solune scaffolds the project, creates GitHub Issues, and wires up an agent pipeline
- **Customizable Agent Pipelines** — Visual drag-and-drop GUI to compose any combination of AI agents into execution stages, with series and parallel execution groups, integrated with GitHub Projects for real-time tracking
- **Multi-app management** — Create, preview, start/stop applications from a unified dashboard
- **Live preview** — Embedded iframe preview for running applications with start/stop controls
- **Real-time board** — Kanban view with drag-and-drop agent configuration
- **Voice input** — Dictate chat messages via microphone with real-time transcription
- **Signal messaging** — Receive notifications and reply from your phone
- **Context switching** — `/<app-name>` slash command to switch agent focus between applications
- **Self-editing protection** — `@admin`/`@adminlock` guards prevent agents from modifying platform core

## Quick Start

From the repository root:

### Docker (Recommended)

```bash
cp solune/.env.example solune/.env
# Edit solune/.env — set GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET, SESSION_SECRET_KEY
docker compose up --build -d
```

Open **<http://localhost:5173>**.

### GitHub Codespaces

Click **Code** → **Codespaces** → **Create codespace on main**. The dev container auto-installs everything. Copy `solune/.env.example` to `solune/.env`, add your OAuth credentials, and start the services.

See [Setup Guide](docs/setup.md) for full instructions including local development without Docker.

## Architecture

| Component | Stack |
|-----------|-------|
| **Frontend** | React 19, TypeScript 5.9, Vite 8, TanStack Query v5, Tailwind CSS 4 |
| **Backend** | Python 3.14, FastAPI, Pydantic v2, aiosqlite (SQLite WAL), githubkit |
| **Signal Sidecar** | `signal-cli-rest-api` (Docker) |
| **AI Providers** | GitHub Copilot SDK (default, OAuth) or Azure OpenAI (optional, API key) |
| **Infrastructure** | Docker Compose (3 services), nginx reverse proxy, SQLite with auto-migrations |

## Agent Pipeline

Agent Pipelines are customizable execution plans for AI Custom GitHub Agents. Each pipeline is a sequence of stages with agents that can run in **series** (one after another) or **parallel** (concurrently within a group). Pipelines are fully integrated with **GitHub Projects** — issues move across board columns as agents complete their work.

```text
┌─────────────────── CUSTOMIZABLE AGENT PIPELINE ───────────────────┐
│                                                                │
│  Stage 1 (series)   ── Agent A ──▶ output files                │
│       │                                                        │
│       ▼                                                        │
│  Stage 2 (parallel) ─┬ Agent B ──▶ output files                │
│                      └ Agent C ──▶ output files                │
│       │                                                        │
│       ▼                                                        │
│  Stage 3 (series)   ── Agent D ──▶ code changes               │
│       │                                                        │
│       ▼                                                        │
│  Review             ── Copilot code review ─▶ ready for merge  │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

The built-in **Spec Kit** preset (`specify` → `plan` → `tasks` → `implement` → `review`) ships as a default, but you can create your own pipelines with any custom agents.

Each agent branches from the issue's main PR branch. Child PRs are squash-merged back and branches deleted automatically. The pipeline is tracked with a durable markdown table in the issue body that survives server restarts.

See [Agent Pipeline](docs/agent-pipeline.md) for the full flow, sub-issue lifecycle, and polling details.

## Documentation

| Document | Description |
|----------|-------------|
| [Setup Guide](docs/setup.md) | Installation for Docker, Codespaces, and local development |
| [Configuration](docs/configuration.md) | Environment variables, database, workflow settings |
| [Architecture](docs/architecture.md) | System design, frontend/backend modules, startup lifecycle |
| [Agent Pipeline](docs/agent-pipeline.md) | Customizable agent pipelines, execution groups, GitHub Projects integration, PR branching, polling service |
| [API Reference](docs/api-reference.md) | All REST, WebSocket, and SSE endpoints |
| [Signal Integration](docs/signal-integration.md) | Signal messaging setup and features |
| [Testing](docs/testing.md) | Backend (pytest), frontend (Vitest, Playwright), code quality |
| [Project Structure](docs/project-structure.md) | Complete file/directory tree with descriptions |
| [Troubleshooting](docs/troubleshooting.md) | Common issues and solutions |
| [Custom Agents](docs/custom-agents-best-practices.md) | Best practices for creating custom GitHub agents |
| [Documentation Maintenance](docs/checklists/) | Weekly sweep, monthly review, quarterly audit checklists |

## Running Tests

```bash
# Backend
cd backend && source .venv/bin/activate && pytest tests/ -v

# Frontend unit
cd frontend && npm test

# Frontend E2E
cd frontend && npm run test:e2e
```

## Environment Variables (Key)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GITHUB_CLIENT_ID` | Yes | — | GitHub OAuth App Client ID |
| `GITHUB_CLIENT_SECRET` | Yes | — | GitHub OAuth App Client Secret |
| `SESSION_SECRET_KEY` | Yes | — | Session encryption key (`openssl rand -hex 32`) |
| `AI_PROVIDER` | No | `copilot` | `copilot` or `azure_openai` |
| `COPILOT_POLLING_INTERVAL` | No | `60` | Polling interval in seconds |
| `DEBUG` | No | `false` | Enable API docs at `/api/docs` |

See [Configuration](docs/configuration.md) for the complete reference.

## License

MIT License.
