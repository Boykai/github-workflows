# Agent Projects

[![CI](https://github.com/Boykai/github-workflows/actions/workflows/ci.yml/badge.svg)](https://github.com/Boykai/github-workflows/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/github/license/Boykai/github-workflows?color=0f766e)](https://github.com/Boykai/github-workflows)
[![Last Commit](https://img.shields.io/github/last-commit/Boykai/github-workflows?color=2563eb&label=last%20commit)](https://github.com/Boykai/github-workflows/commits/main)
[![Open Issues](https://img.shields.io/github/issues/Boykai/github-workflows?color=f59e0b&label=issues)](https://github.com/Boykai/github-workflows/issues)
[![Open Pull Requests](https://img.shields.io/github/issues-pr/Boykai/github-workflows?color=dc2626&label=pull%20requests)](https://github.com/Boykai/github-workflows/pulls)
[![Repo Stars](https://img.shields.io/github/stars/Boykai/github-workflows?style=flat&color=facc15&label=stars)](https://github.com/Boykai/github-workflows/stargazers)
[![Repo Forks](https://img.shields.io/github/forks/Boykai/github-workflows?style=flat&color=7c3aed&label=forks)](https://github.com/Boykai/github-workflows/network/members)

> AI-powered conversational interface for creating, managing, and executing GitHub Issues on a Project Board — with an automated **Spec Kit agent pipeline** that turns feature requests into specifications, plans, tasks, and implementations through GitHub Copilot custom agents.

## What It Does

- **Describe features in natural language** → AI generates structured GitHub Issues
- **Automated agent pipeline** → `specify` → `plan` → `tasks` → `implement` → `review`
- **Each agent gets a sub-issue** for per-agent visibility, with child PRs merged into a single main branch
- **Real-time board** → Kanban view with drag-and-drop agent configuration
- **Voice input** → Dictate chat messages via microphone with real-time transcription (Firefox, Chrome, Edge, Safari)
- **Signal messaging** → Receive notifications and reply from your phone
- **Custom agent creation** → Type `#agent <description> #<status>` in chat to create agents
- **Import parent issues** → Paste or upload a GitHub Issue description on the Projects page and launch an agent pipeline directly

## Quick Start

### Docker (Recommended)

```bash
git clone <repository-url>
cd github-workflows
cp .env.example .env
# Edit .env — set GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET, SESSION_SECRET_KEY
docker compose up --build -d
```

Open **<http://localhost:5173>**.

### GitHub Codespaces

Click **Code** → **Codespaces** → **Create codespace on main**. The dev container auto-installs everything. Copy `.env.example` to `.env`, add your OAuth credentials, and start the services.

See [Setup Guide](docs/setup.md) for full instructions including local development without Docker.

## Architecture

| Component | Stack |
|-----------|-------|
| **Frontend** | React 19, TypeScript 5.9, Vite 7, TanStack Query v5, Tailwind CSS 4 |
| **Backend** | Python 3.13, FastAPI, Pydantic v2, aiosqlite (SQLite WAL), githubkit |
| **Signal Sidecar** | `signal-cli-rest-api` (Docker) |
| **AI Providers** | GitHub Copilot SDK (default, OAuth) or Azure OpenAI (optional, API key) |
| **Infrastructure** | Docker Compose (3 services), nginx reverse proxy, SQLite with auto-migrations |

## Agent Pipeline

```text
📋 Backlog → speckit.specify → spec.md
📝 Ready   → speckit.plan   → plan.md, research.md, data-model.md
             speckit.tasks   → tasks.md
🔄 In Prog → speckit.implement → Code changes
👀 Review  → Copilot code review → Ready for human merge
```

Each agent branches from the issue's main PR branch. Child PRs are squash-merged back and branches deleted automatically. The pipeline is tracked with a durable markdown table in the issue body that survives server restarts.

See [Agent Pipeline](docs/agent-pipeline.md) for the full flow, sub-issue lifecycle, and polling details.

## Documentation

| Document | Description |
|----------|-------------|
| [Setup Guide](docs/setup.md) | Installation for Docker, Codespaces, and local development |
| [Configuration](docs/configuration.md) | Environment variables, database, workflow settings |
| [Architecture](docs/architecture.md) | System design, frontend/backend modules, startup lifecycle |
| [Agent Pipeline](docs/agent-pipeline.md) | Spec Kit agents, status flow, PR branching, polling service |
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
