# Setup Guide

Whether you're trying Solune for the first time or setting up a new development environment, this guide walks you through every option — from a one-click Codespaces launch to a full local development setup.

## Which path is right for you?

| Path | Best For | Time | Prerequisites |
|------|----------|------|---------------|
| **Codespaces** | Fastest start, no local setup | ~2 min | GitHub account |
| **Docker** | Production-like environment | ~5 min | Docker Desktop |
| **Local** | Full development control | ~10 min | Python 3.12+, Node.js 20+ |

## Prerequisites

- [Fork the repository](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo)
- [Create a GitHub Project (Kanban)](https://docs.github.com/en/issues/planning-and-tracking-with-projects/creating-projects/creating-a-project) with columns: **Backlog**, **Ready**, **In Progress**, **In Review**, **Done**
- [GitHub Copilot subscription](https://github.com/features/copilot) (required for agent pipeline and default AI provider)
- Docker and Docker Compose (recommended), OR Node.js 22+ and Python 3.12+ for bare-metal/local installs
- GitHub OAuth App credentials

## Quick Start: GitHub Codespaces (Easiest)

### 1. Open in Codespaces

Click **Code** → **Codespaces** → **Create codespace on main**, or use:

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/OWNER/REPO)

### 2. Wait for Setup

The dev container currently installs Python 3.13 and Node.js 25 (see `.devcontainer/devcontainer.json` for exact versions), plus the backend virtual environment, all dependencies, and Playwright browsers.

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` — minimum required:

- `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` ([GitHub OAuth App](https://github.com/settings/developers))
- `SESSION_SECRET_KEY` — generate with `openssl rand -hex 32`

### 4. Update OAuth Callback URL

Update your GitHub OAuth App's **Authorization callback URL** to match Codespaces:

```text
https://YOUR-CODESPACE-NAME-5173.app.github.dev/api/v1/auth/github/callback
```

The `post-start.sh` script prints the exact URL on startup.

### 5. Start the Application

```bash
# Terminal 1: Backend
cd backend && source .venv/bin/activate && uvicorn src.main:app --reload

# Terminal 2: Frontend
cd frontend && npm run dev
```

---

## Quick Start: Docker (Recommended)

### 1. Clone and Configure

```bash
git clone <repository-url>
cd <repository-name>
cp solune/.env.example solune/.env
```

### 2. Create GitHub OAuth App

1. Go to [GitHub Developer Settings](https://github.com/settings/developers) → **OAuth Apps** → **New OAuth App**
2. Set:
   - **Homepage URL**: `http://localhost:5173`
   - **Authorization callback URL**: `http://localhost:5173/api/v1/auth/github/callback`
3. Copy **Client ID** and generate a **Client Secret**
4. Add to `.env`:

   ```env
   GITHUB_CLIENT_ID=your_client_id
   GITHUB_CLIENT_SECRET=your_client_secret
   ```

### 3. Generate Session Secret

```bash
openssl rand -hex 32
```

Add to `.env`:

```env
SESSION_SECRET_KEY=your_generated_key
```

### 4. Start

```bash
docker compose up --build -d
```

### 5. Access

Open **<http://localhost:5173>**. Verify containers are running:

```bash
docker ps
# solune-backend    (healthy)
# solune-frontend
# solune-signal-api (healthy)
```

---

## Local Development (Without Docker)

### Backend

```bash
cd backend
uv sync --extra dev
uvicorn src.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Access Points

| URL | Service |
|-----|---------|
| <http://localhost:5173> | Frontend |
| <http://localhost:8000> | Backend API |
| <http://localhost:8000/api/docs> | API docs (when `ENABLE_DOCS=true`) |

---

## Optional: GitHub Webhooks

Enable faster detection when Copilot marks PRs as ready for review (the polling service handles this automatically, but webhooks are faster).

### 1. Generate Webhook Secret

```bash
openssl rand -hex 32
```

Add to `.env`:

```env
GITHUB_WEBHOOK_SECRET=your_secret
```

### 2. Create Personal Access Token (Classic)

Go to [GitHub Tokens](https://github.com/settings/tokens) → **Generate new token (classic)**:

- ✅ `repo` — Full control of private repositories
- ✅ `project` — Full control of projects
- ✅ `read:org` — If using organization projects

> **Important**: Use **Tokens (classic)**, not Fine-grained tokens. The `project` scope is only available in classic tokens.

Add to `.env`:

```env
GITHUB_WEBHOOK_TOKEN=ghp_your_token_here
```

### 3. Configure in GitHub

1. Repository → **Settings** → **Webhooks** → **Add webhook**
2. **Payload URL**: `https://your-domain/api/v1/webhooks/github`
3. **Content type**: `application/json`
4. **Secret**: Same value as `GITHUB_WEBHOOK_SECRET`
5. Events: Select **Pull requests**

### 4. Restart

```bash
docker compose down && docker compose up --build -d
```

---

## Optional: Signal Messaging

See [Signal Integration](signal-integration.md) for full setup instructions.

---

## What's next?

- [Configuration](configuration.md) — Customize environment variables for your deployment
- [Architecture](architecture.md) — Understand how the services fit together
- [Agent Pipeline](agent-pipeline.md) — Learn how to build and launch your first pipeline
