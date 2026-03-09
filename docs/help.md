# Help & Support

> A beginner-friendly guide for getting started, solving common problems, and finding help with Agent Projects.

**Last updated:** 2026-03-09 · Contributions welcome — open a PR to improve this guide.

---

## Getting Started

New to Agent Projects? Follow these steps to get up and running.

### 1. Clone and configure

```bash
git clone <repository-url>
cd github-workflows
cp .env.example .env
```

Edit `.env` and set the required variables:

- `GITHUB_CLIENT_ID` — from your [GitHub OAuth App](https://github.com/settings/developers)
- `GITHUB_CLIENT_SECRET` — from the same OAuth App
- `SESSION_SECRET_KEY` — generate with `openssl rand -hex 32`

### 2. Start the application

**Docker (recommended):**

```bash
docker compose up --build -d
```

**GitHub Codespaces:**

Click **Code → Codespaces → Create codespace on main**. The dev container installs everything automatically.

**Local development:**

See the full [Setup Guide](setup.md) for instructions without Docker.

### 3. Open the app

Navigate to **<http://localhost:5173>** and sign in with GitHub.

### 4. Create a project

Link a GitHub Project board with columns: **Backlog**, **Ready**, **In Progress**, **In Review**, **Done**. The app uses these columns to track work through the agent pipeline.

### 5. Start building

Type a feature description in the chat. The AI generates a structured GitHub Issue and the agent pipeline takes it from specification through implementation.

For the full setup walkthrough, see the [Setup Guide](setup.md).

---

## Frequently Asked Questions

### Setup

**How do I create a GitHub OAuth App?**

Go to [GitHub Developer Settings](https://github.com/settings/developers), click **New OAuth App**, and set the callback URL to `http://localhost:5173/api/v1/auth/github/callback`. Copy the Client ID and Client Secret into your `.env` file. See the [Configuration Guide](configuration.md) for details.

**What are the system requirements?**

You need Docker and Docker Compose (recommended), OR Node.js 22+ and Python 3.13+ for local development. A [GitHub Copilot subscription](https://github.com/features/copilot) is required for the agent pipeline and the default AI provider.

**Can I use GitHub Codespaces instead of Docker?**

Yes. Codespaces is the easiest way to get started. Click **Code → Codespaces → Create codespace on main** and the dev container handles all dependencies. See the [Setup Guide](setup.md) for details.

### Usage

**How do I create an issue with the chat?**

Type a natural language description of the feature you want in the chat input. The AI generates a structured GitHub Issue with title, body, labels, and priority. You can refine it before submitting.

**How do I configure which agents run on my issues?**

Go to the **Agents** page, browse the agent catalog, and drag agents into board column slots. Each column can have different agents assigned. Changes are saved per-project.

**What are chores and how do I use them?**

Chores are recurring maintenance tasks (like dependency updates or code cleanup) that can be scheduled and tracked. Go to the **Chores** page to create, edit, and manage chores for your project.

### Agent Pipeline

**What is the agent pipeline?**

The agent pipeline is an automated workflow that turns feature requests into working code. When an issue moves through your project board, agents run in sequence:

1. **speckit.specify** — generates a feature specification (`spec.md`)
2. **speckit.plan** — creates an implementation plan (`plan.md`, `research.md`, `data-model.md`)
3. **speckit.tasks** — breaks the plan into tasks (`tasks.md`)
4. **speckit.implement** — writes the code changes
5. **Code review** — Copilot reviews the pull request

Each agent gets a sub-issue and a child PR that merges back into the main feature branch.

**Why is my pipeline not advancing?**

Check that the polling service is running with `GET /api/v1/workflow/polling/status`. Verify your project has the required columns (Backlog, Ready, In Progress, In Review). See [Troubleshooting](troubleshooting.md) for more details.

### Contributing

**How do I contribute to this project?**

1. Fork the repository
2. Create a feature branch
3. Make your changes following existing code patterns
4. Run tests: `cd frontend && npm test` (frontend) or `cd backend && pytest tests/ -v` (backend)
5. Open a pull request

See the [Testing Guide](testing.md) for details on running the full test suite.

**How do I create a custom agent?**

Custom agents are defined as markdown files in `.github/agents/`. Each file describes the agent's role, instructions, and tools. See [Custom Agents Best Practices](custom-agents-best-practices.md) for a full guide.

---

## Support Channels

- **GitHub Issues** — [Report bugs or request features](https://github.com/Boykai/github-workflows/issues)
- **GitHub Discussions** — [Ask questions and share ideas](https://github.com/Boykai/github-workflows/discussions)
- **Documentation** — Browse the [full documentation](../README.md#documentation) for architecture, API reference, and configuration details

---

## Agent Pipeline Overview

```text
📋 Backlog     → speckit.specify     → spec.md
📝 Ready       → speckit.plan        → plan.md, research.md, data-model.md
                 speckit.tasks        → tasks.md
🔄 In Progress → speckit.implement   → Code changes on child PR
👀 In Review   → Copilot code review → Ready for human merge
✅ Done        → Merged
```

Each stage creates a sub-issue and a child branch. Child PRs are squash-merged back into the main feature branch automatically. The pipeline tracks progress with a durable markdown table in the issue body.

For the full agent pipeline documentation, see [Agent Pipeline](agent-pipeline.md).

---

## Further Reading

| Document | Description |
|----------|-------------|
| [Setup Guide](setup.md) | Installation for Docker, Codespaces, and local development |
| [Configuration](configuration.md) | Environment variables, database, workflow settings |
| [Architecture](architecture.md) | System design, frontend/backend modules, startup lifecycle |
| [Agent Pipeline](agent-pipeline.md) | Spec Kit agents, status flow, PR branching, polling service |
| [API Reference](api-reference.md) | All REST, WebSocket, and SSE endpoints |
| [Testing](testing.md) | Backend (pytest), frontend (Vitest, Playwright), code quality |
| [Troubleshooting](troubleshooting.md) | Common issues and solutions |
| [Custom Agents](custom-agents-best-practices.md) | Best practices for creating custom GitHub agents |
