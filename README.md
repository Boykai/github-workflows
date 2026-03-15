# Solune

[![CI](https://github.com/Boykai/github-workflows/actions/workflows/ci.yml/badge.svg)](https://github.com/Boykai/github-workflows/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/github/license/Boykai/github-workflows?color=0f766e)](https://github.com/Boykai/github-workflows/blob/main/LICENSE)

> Agent-driven development platform. Design customizable Agent Pipelines via a visual GUI, compose AI Custom GitHub Agents to execute remote work in series or parallel, and track everything through GitHub Projects.

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

## Repository Structure

```text
solune/               # Platform core (frontend + backend + docs)
├── backend/          # FastAPI (Python 3.12+)
├── frontend/         # React 19 + TypeScript + Vite
├── docs/             # Documentation
├── scripts/          # Utility scripts
├── specs/            # Feature specifications
├── docker-compose.yml
└── mcp.json

apps/                 # Generated applications live here
├── .gitkeep
└── <app-name>/       # Scaffolded per-app directory

.github/              # Agents, workflows, prompts (serve whole repo)
README.md             # This file
docker-compose.yml    # Root compose orchestrating everything
```

## Quick Start

### Docker (Recommended)

```bash
git clone <repository-url>
cd <repository-name>
cp solune/.env.example solune/.env
# Edit solune/.env — set GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET, SESSION_SECRET_KEY
docker compose up --build -d
```

Open **<http://localhost:5173>**.

### GitHub Codespaces

Click **Code** → **Codespaces** → **Create codespace on main**. The dev container auto-installs everything. Copy `solune/.env.example` to `solune/.env`, add your OAuth credentials, and start the services.

See [solune/docs/setup.md](solune/docs/setup.md) for full instructions including local development without Docker.

## Architecture

| Component | Stack |
|-----------|-------|
| **Frontend** | React 19, TypeScript 5.9, Vite 7, TanStack Query v5, Tailwind CSS 4 |
| **Backend** | Python 3.12+, FastAPI, Pydantic v2, aiosqlite (SQLite WAL), githubkit |
| **Signal Sidecar** | `signal-cli-rest-api` (Docker) |

## License

[MIT](LICENSE)

---

<sub>This application was built with the assistance of AI.</sub>
