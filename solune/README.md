# Solune — Platform Core

Solune is an agent-driven development platform with a celestial-themed interface. Describe a feature in chat, design a pipeline of AI agents in a visual drag-and-drop builder, and watch them execute — branching, coding, and merging autonomously on your GitHub Project board. From idea to reviewed pull request, Solune orchestrates every step.

For the monorepo overview, see the [root README](../README.md).

## The Core Experience

### 1. Describe

Chat with Solune to describe what you want to build. Type or use voice input with real-time transcription. The AI generates structured GitHub Issues with labels, priorities, and acceptance criteria — ready for pipeline execution.

### 2. Design

Open the visual Pipeline Builder. Drag and drop agents into execution stages. Choose series or parallel execution for each group. Select AI models per agent and save pipelines as reusable workflow templates.

### 3. Execute

Launch the pipeline. Solune creates sub-issues, assigns agents, and tracks progress on your GitHub Project board. Each agent branches from the main PR, executes its task, and merges back automatically when complete.

### 4. Review

When all agents finish, Solune requests a Copilot code review on the consolidated PR. Get notified via Signal on your phone. Review, approve, and merge — your feature is done.

## Quick Start

### Docker (Recommended)

```bash
cp .env.example .env
# Edit .env — set GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET, SESSION_SECRET_KEY
cd .. && docker compose up --build -d
```

Open **<http://localhost:5173>**.

### GitHub Codespaces

Click **Code → Codespaces → Create codespace on main**. The dev container auto-installs everything. Copy `.env.example` to `.env`, add your OAuth credentials, and start the services.

### Local Development

See the [Setup Guide](docs/setup.md) for full instructions including local Python and Node.js setup.

## Architecture

Solune is a three-service Docker Compose application — a React frontend, a FastAPI backend, and a Signal messaging sidecar — orchestrated behind an nginx reverse proxy.

| Component | Stack |
|-----------|-------|
| **Frontend** | React 19, TypeScript 5.9, Vite 8, TanStack Query v5, Tailwind CSS 4 |
| **Backend** | Python 3.12+, FastAPI, Pydantic v2, aiosqlite (SQLite WAL), githubkit |
| **Signal** | signal-cli-rest-api (Docker sidecar) |
| **AI** | GitHub Copilot SDK (default, OAuth) or Azure OpenAI (optional) |
| **Infrastructure** | Docker Compose, nginx reverse proxy, SQLite with auto-migrations |

## Agent Pipeline

Agent Pipelines are the heart of Solune — the engine that turns a feature description into working code through a choreographed sequence of AI agents. Each pipeline is a customizable plan where you choose which agents run, in what order, and whether they execute in series or parallel.

```text
┌─────────────────── CUSTOMIZABLE AGENT PIPELINE ───────────────────┐
│                                                                   │
│  Stage 1 (series)   ── Agent A ──▶ output files                  │
│       │                                                           │
│       ▼                                                           │
│  Stage 2 (parallel) ─┬ Agent B ──▶ output files                  │
│                      └ Agent C ──▶ output files                  │
│       │                                                           │
│       ▼                                                           │
│  Stage 3 (series)   ── Agent D ──▶ code changes                  │
│       │                                                           │
│       ▼                                                           │
│  Review             ── Copilot code review ─▶ ready for merge    │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

The built-in **Spec Kit** preset (`specify` → `plan` → `tasks` → `implement` → `review`) ships as a default, but you can create your own pipelines with any custom agents.

Each agent branches from the issue's main PR branch. Child PRs are squash-merged back and branches deleted automatically. The pipeline is tracked with a durable markdown table in the issue body that survives server restarts.

See [Agent Pipeline](docs/agent-pipeline.md) for the full flow, sub-issue lifecycle, and polling details.

## Documentation

| Document | What you'll learn |
|----------|-------------------|
| [Setup Guide](docs/setup.md) | How to get Solune running — Docker, Codespaces, or local development |
| [Architecture](docs/architecture.md) | How the system is designed — services, data flow, and module structure |
| [Configuration](docs/configuration.md) | Every environment variable and how to customize your deployment |
| [Agent Pipeline](docs/agent-pipeline.md) | How pipelines orchestrate agents — stages, execution groups, and GitHub integration |
| [API Reference](docs/api-reference.md) | Explore all REST, WebSocket, and SSE endpoints with authentication details |
| [Signal Integration](docs/signal-integration.md) | Set up bidirectional Signal messaging for phone notifications |
| [Testing](docs/testing.md) | Run the test suite — pytest, Vitest, Playwright, and mutation testing |
| [Project Structure](docs/project-structure.md) | Navigate the complete directory layout with descriptions of every file and folder |
| [Troubleshooting](docs/troubleshooting.md) | Find solutions to common issues organized by component |
| [Custom Agents](docs/custom-agents-best-practices.md) | Create your own agents — file formats, prompt writing, and examples |

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
