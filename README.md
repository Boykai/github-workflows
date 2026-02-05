# GitHub Projects Chat Interface

> **A new way of working with DevOps** — leveraging AI in a conversational web app to create, manage, and execute GitHub Issues on a GitHub Project Board.

This application transforms how development teams interact with their project management workflow. Instead of manually navigating GitHub's UI to create issues, update statuses, or track progress, users can simply have a conversation with an AI-powered chat interface that handles all the complexity behind the scenes.

## 🎯 The Vision

Traditional DevOps workflows require developers to context-switch between their IDE, GitHub Issues, Project Boards, and PR reviews. This application consolidates that experience into a single conversational interface where you can:

- **Describe what you want to build** in natural language
- **Watch AI generate structured GitHub Issues** with proper formatting, labels, and details  
- **Assign work to GitHub Copilot** with a single click
- **Monitor automated progress** as Copilot codes, creates PRs, and requests reviews
- **Track status changes** in real-time as work flows through your pipeline

---

## 🔄 Workflow: From Idea to Code Review

The application orchestrates a seamless flow between you, Azure OpenAI, GitHub Issues, and GitHub Copilot:

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                              THE CONVERSATIONAL DEVOPS FLOW                          │
├──────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  👤 USER                    🤖 AZURE OPENAI                   📋 GITHUB PROJECT     │
│  ─────                      ──────────────                    ───────────────        │
│    │                              │                                  │               │
│    │  "Create an issue to         │                                  │               │
│    │   add dark mode support"     │                                  │               │
│    │─────────────────────────────▶                                  │               │
│    │                              │                                  │               │
│    │                              │  Generates structured issue:     │               │
│    │                              │  • Title, description            │               │
│    │                              │  • Acceptance criteria           │               │
│    │                              │  • Technical approach            │               │
│    │                              │──────────────────────────────────▶               │
│    │                              │                                  │               │
│    │                              │                    Issue created │               │
│    │◀─────────────────────────────────────────────────── Status: 📝 Ready           │
│    │                                                                 │               │
│    │  "Assign to Copilot"                                            │               │
│    │────────────────────────────────────────────────────────────────▶               │
│    │                                                                 │               │
│    │                                                   Status: 🔄 In Progress       │
│    │                                                                 │               │
│    │                                                                 │               │
│    │                         🤖 GITHUB COPILOT                       │               │
│    │                         ─────────────────                       │               │
│    │                                │                                │               │
│    │                                │  • Reads issue context         │               │
│    │                                │  • Creates branch              │               │
│    │                                │  • Writes code                 │               │
│    │                                │  • Opens Draft PR              │               │
│    │                                │  • Commits changes             │               │
│    │                                │  • Marks PR ready              │               │
│    │                                │  • Requests your review        │               │
│    │                                │                                │               │
│    │                                ▼                                │               │
│    │                                                                 │               │
│    │  ┌──────────────────────────────────────────────────────────────┤               │
│    │  │  🔔 POLLING SERVICE DETECTS COMPLETION                       |              │
│    │  │  ─────────────────────────────────────────                   │               │
│    │  │  • Monitors "In Progress" issues every 15 seconds            │               │
│    │  │  • Detects timeline events:                                  │               │
│    │  │    - "copilot_work_finished"                                 │               │
│    │  │    - "review_requested" from Copilot                         │               │
│    │  │  • Converts Draft PR → Ready for Review                      │               │
│    │  │  • Updates issue status                                      │               │
│    │  │  • Requests Copilot code review on PR                        │               │
│    │  └──────────────────────────────────────────────────────────────┤               │
│    │                                                                 │               │
│    │◀──────────────────────────────────────────────── Status: 👀 In Review          │
│    │                                                                 │               │
│    │  Ready for your review! PR link available in chat.              │               │
│    │                                                                 │               │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

### Issue Status Flow

| Status | Description | Triggered By |
|--------|-------------|--------------|
| 📝 **Ready** | Issue created, waiting to be picked up | AI generates issue from chat |
| 🔄 **In Progress** | Work is actively being done | App assigns to Copilot or developer |
| 👀 **In Review** | PR created and ready for review | Polling detects Copilot code completion |
| ✅ **Done** | Work completed and merged | Manual or webhook on PR merge |

### Key Integrations

| Component | Role |
|-----------|------|
| **Azure OpenAI** | Generates structured GitHub Issues from natural language descriptions |
| **GitHub Projects V2** | Manages the kanban board with status columns |
| **GitHub Copilot** | Autonomous coding agent that implements issues |
| **Polling Service** | Monitors PRs for Copilot completion signals via timeline events |

---

## Features

- **GitHub OAuth Authentication**: Secure login with GitHub OAuth 2.0
- **Project Selection**: Browse and select from your GitHub Projects V2 boards
- **Natural Language Task Creation**: Describe tasks in plain English; AI generates structured GitHub tasks
- **Status Updates via Chat**: Update task status using natural language commands
- **Real-Time Sync**: Live updates via WebSocket with polling fallback
- **Responsive UI**: Modern React interface with TanStack Query for state management
- **Automated Copilot Integration**: Automatically update issue status when GitHub Copilot completes PRs

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Frontend     │────▶│    Backend      │────▶│  GitHub API     │
│  React + Vite   │     │    FastAPI      │     │  GraphQL V2     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │  Azure OpenAI   │
                        │  (Task Gen AI)  │
                        └─────────────────┘
```

## Prerequisites
- ⚠️ [Fork repository](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo) before starting
- [Create GitHub Project](https://docs.github.com/en/issues/planning-and-tracking-with-projects/creating-projects/creating-a-project) and have a repository available
- [Visual Studio Code](https://code.visualstudio.com/download) or [GitHub Codespaces](https://github.com/features/codespaces)
- Docker and Docker Compose (recommended) OR:
  - Node.js 18+
  - Python 3.11+
- GitHub OAuth App credentials
- Azure OpenAI API credentials (optional, for AI features)

---

## Quick Start with GitHub Codespaces (Easiest)

The fastest way to get started! Launch a fully configured development environment in your browser.

### 1. Open in Codespaces

Click the button below or go to **Code** → **Codespaces** → **Create codespace on main**:

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/OWNER/REPO)

### 2. Wait for Setup

The dev container will automatically:
- Install Python 3.12 and Node.js 22
- Set up the backend virtual environment
- Install all dependencies (backend + frontend)
- Install Playwright browsers for testing

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add your credentials (see [.env.example](./.env.example) for details):
- `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` from your [GitHub OAuth App](https://github.com/settings/developers)
- [Azure OpenAI credentials](https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-models/how-to/deploy-foundry-models) (optional)

### 4. Update GitHub OAuth App

**Important**: Update your GitHub OAuth App callback URL to match your Codespaces URL:

1. The `post-start.sh` script will print your callback URL when the Codespace starts
2. Go to [GitHub Developer Settings](https://github.com/settings/developers) → OAuth Apps → Your App
3. Update **Authorization callback URL** to:
   ```
   https://YOUR-CODESPACE-NAME-8000.app.github.dev/api/v1/auth/github/callback
   ```

### 5. Start the Application

The ports will be automatically forwarded. Open the forwarded port 5173 to access the app.

To run services manually:
```bash
# Terminal 1: Backend
cd backend && source .venv/bin/activate && uvicorn src.main:app --reload

# Terminal 2: Frontend  
cd frontend && npm run dev
```

---

## Quick Start with Docker (Recommended)

### 1. Clone the Repository

```bash
git clone <repository-url>
cd github-workflows
```

### 2. Create Environment File

```bash
cp .env.example .env
```

### 3. Configure Required Environment Variables

Edit `.env` and fill in the required values:

#### GitHub OAuth Setup (Required)

1. Go to [GitHub Developer Settings](https://github.com/settings/developers)
2. Click **OAuth Apps** → **New OAuth App**
3. Fill in:
   - **Application name**: `Projects Chat` (or any name)
   - **Homepage URL**: `http://localhost:5173`
   - **Authorization callback URL**: `http://localhost:5173/api/v1/auth/github/callback`
4. Click **Register application**
5. Copy the **Client ID**
6. Click **Generate a new client secret** and copy it
7. Add to `.env`:
   ```env
   GITHUB_CLIENT_ID=your_client_id
   GITHUB_CLIENT_SECRET=your_client_secret
   ```

#### Session Secret (Optional)

Generate a secure session key:
```bash
openssl rand -hex 32
```

Add to `.env`:
```env
SESSION_SECRET_KEY=your_generated_key
```

#### Azure OpenAI (Optional - for AI features)

If you want AI-powered task generation:
```env
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_KEY=your_api_key
AZURE_OPENAI_DEPLOYMENT=gpt-5
```

### 4. Start the Application

```bash
docker compose up --build -d
```

### 5. Access the Application

Open **http://localhost:5173** in your browser.

### 6. Verify It's Running

```bash
docker ps
```

You should see:
- `ghchat-backend` - Backend API (healthy)
- `ghchat-frontend` - Frontend UI

---

## GitHub Webhook Setup (Optional - for Copilot Integration)

Enable automatic status updates when GitHub Copilot finishes work on PRs.

### How It Works

1. GitHub Copilot creates a draft PR for an issue
2. When Copilot marks the PR as ready for review
3. The webhook automatically updates the linked issue status to "In Review"

### Setup Steps

#### 1. Generate Webhook Secret

```bash
openssl rand -hex 32
```

Add to `.env`:
```env
GITHUB_WEBHOOK_SECRET=your_generated_secret
```

#### 2. Create GitHub Personal Access Token (Classic)

1. Go to [GitHub Tokens](https://github.com/settings/tokens)
2. Click **Generate new token** → **Generate new token (classic)**
3. Select scopes:
   - ✅ `repo` (Full control of private repositories)
   - ✅ `project` (Full control of projects)
   - ✅ `read:org` (if using organization projects)
4. Click **Generate token** and copy it
5. Add to `.env`:
   ```env
   GITHUB_WEBHOOK_TOKEN=ghp_your_token_here
   ```

> ⚠️ **Important**: Use **Tokens (classic)**, not Fine-grained tokens. Projects V2 API requires the `project` scope which is only available in classic tokens.

#### 3. Configure GitHub Webhook

1. Go to your repository → **Settings** → **Webhooks** → **Add webhook**
2. Configure:
   - **Payload URL**: `https://your-domain/api/v1/webhooks/github`
   - **Content type**: `application/json`
   - **Secret**: Same value as `GITHUB_WEBHOOK_SECRET`
3. Under "Which events would you like to trigger this webhook?":
   - Select **Let me select individual events**
   - Check **Pull requests**
4. Click **Add webhook**

#### 4. Restart the Application

```bash
docker compose down
docker compose up --build -d
```

---

## Local Development Setup (Without Docker)

### Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# Configure environment in root .env (backend loads from ../.env)
# See root .env.example for all available options

# Run the server
uvicorn src.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install

# Run the dev server
npm run dev
```

### Access

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/api/docs (when DEBUG=true)

### Updating Task Status
1. Type a status change command, e.g.:
   - "Move the login bug task to In Progress"
   - "Mark 'Implement dark mode' as Done"
2. Confirm the status change proposal

---

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_CLIENT_ID` | ✅ Yes | GitHub OAuth App Client ID |
| `GITHUB_CLIENT_SECRET` | ✅ Yes | GitHub OAuth App Client Secret |
| `GITHUB_REDIRECT_URI` | ✅ Yes | OAuth callback URL (default: `http://localhost:5173/api/v1/auth/github/callback`) |
| `SESSION_SECRET_KEY` | ❌ No | Random hex string for session encryption (generate with `openssl rand -hex 32`) |
| `AZURE_OPENAI_ENDPOINT` | ❌ No | Azure OpenAI endpoint URL |
| `AZURE_OPENAI_KEY` | ❌ No | Azure OpenAI API key |
| `AZURE_OPENAI_DEPLOYMENT` | ❌ No | Azure OpenAI deployment name (default: `gpt-4`) |
| `GITHUB_WEBHOOK_SECRET` | ❌ No | Secret for webhook signature verification |
| `GITHUB_WEBHOOK_TOKEN` | ❌ No | GitHub PAT (classic) for webhook operations |
| `DEFAULT_REPOSITORY` | ❌ No | Default repo for issue creation (`owner/repo`) |
| `DEFAULT_ASSIGNEE` | ❌ No | Default assignee for "In Progress" issues |
| `FRONTEND_URL` | ❌ No | Frontend URL (default: `http://localhost:5173`) |
| `CORS_ORIGINS` | ❌ No | Allowed CORS origins (comma-separated) |
| `DEBUG` | ❌ No | Enable debug mode (default: `false`) |
| `CACHE_TTL_SECONDS` | ❌ No | Cache TTL in seconds (default: `300`) |

---

## Running Tests

### Backend Tests
```bash
cd backend
source .venv/bin/activate
pytest tests/ -v
```

### Frontend Tests
```bash
cd frontend
npm test                  # Unit tests
npm run test:e2e          # E2E tests
npm run test:e2e:headed   # E2E with browser visible
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/health` | GET | Health check |
| `/api/v1/auth/github` | GET | Start OAuth flow |
| `/api/v1/auth/me` | GET | Get current user |
| `/api/v1/projects` | GET | List user's projects |
| `/api/v1/projects/{id}/select` | POST | Select active project |
| `/api/v1/chat/messages` | GET | Get chat history |
| `/api/v1/chat/messages` | POST | Send chat message |
| `/api/v1/chat/messages` | DELETE | Clear chat history |
| `/api/v1/webhooks/github` | POST | GitHub webhook endpoint |

API documentation available at http://localhost:8000/api/docs when `DEBUG=true`.

---

## Project Structure

```
github-workflows/
├── .env.example          # Environment template
├── docker-compose.yml    # Docker orchestration
├── README.md
├── backend/
│   ├── src/
│   │   ├── api/          # API endpoints (auth, chat, projects, webhooks)
│   │   ├── models/       # Pydantic models
│   │   ├── services/     # Business logic (GitHub, AI, cache)
│   │   ├── prompts/      # AI prompt templates
│   │   ├── config.py     # Configuration
│   │   └── main.py       # FastAPI app
│   ├── tests/            # Backend tests
│   └── pyproject.toml    # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── hooks/        # Custom React hooks
│   │   ├── services/     # API client
│   │   └── types/        # TypeScript types
│   ├── package.json      # NPM dependencies
│   └── vite.config.ts    # Vite configuration
└── specs/                # Feature specifications
```

---

## Troubleshooting

### Common Issues

**OAuth callback fails / Login doesn't work:**
- Verify you created a GitHub OAuth App (not a GitHub App)
- Ensure `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` are correctly set
- Verify the callback URL matches exactly: `http://localhost:5173/api/v1/auth/github/callback`
- Check that `FRONTEND_URL` is set to `http://localhost:5173`
- Restart containers after updating `.env`: `docker compose down && docker compose up -d`

**"401 Unauthorized" after GitHub login:**
- Check browser dev tools → Application → Cookies for `session_id`
- Ensure `CORS_ORIGINS` includes your frontend URL
- Verify `SESSION_SECRET_KEY` is set

**Azure OpenAI errors:**
- Verify `AZURE_OPENAI_ENDPOINT` format: `https://your-resource.openai.azure.com`
- Check `AZURE_OPENAI_KEY` is correct
- Ensure the deployment name matches your Azure configuration
- Azure OpenAI is optional - the app works without it (AI features disabled)

**Webhook not triggering:**
- Verify `GITHUB_WEBHOOK_SECRET` matches the secret in GitHub webhook settings
- Check `GITHUB_WEBHOOK_TOKEN` has `repo` and `project` scopes
- Ensure webhook is configured for "Pull requests" events
- Check webhook delivery logs in GitHub: Repo → Settings → Webhooks → Recent Deliveries

**Projects not showing:**
- Ensure your GitHub token has `project` scope
- Projects V2 requires the user to have access to the project
- Organization projects need `read:org` scope

**Rate limiting:**
- GitHub API has rate limits (5000 requests/hour for authenticated users)
- The app tracks remaining calls; wait for reset if limits are hit

**GitHub Copilot agent fails to start / Repository ruleset violation:**
If you see the error:
> "The agent encountered an error and was unable to start working on this issue: This may be caused by a repository ruleset violation."

This occurs when GitHub Copilot doesn't have permission to bypass branch protection rules. To fix:

1. Go to your repository → **Settings** → **Rules** → **Rulesets**
2. Click on the ruleset protecting your default branch
3. Provide the ruleset a name if it doesn't have one
4. **Active** enforcement status
5. Under **Bypass list**, click **Add bypass**
6. Search for and add **Copilot** (the GitHub Copilot app)
7. Set bypass mode to **Always Allow** (or **Pull requests only** if preferred)
8. Set target branches to **Include all branches**
9. Save the ruleset

Alternatively, if using legacy branch protection rules:
1. Go to **Settings** → **Branches** → Edit the protection rule
2. Under "Allow specified actors to bypass required pull requests", add the Copilot app

**Port already in use:**
```bash
# Kill process on port 8000 (backend)
lsof -ti:8000 | xargs kill -9

# Kill process on port 5173 (frontend)
lsof -ti:5173 | xargs kill -9
```

### Viewing Logs

```bash
# All containers
docker compose logs -f

# Backend only
docker compose logs -f backend

# Frontend only
docker compose logs -f frontend
```

---

## License

MIT License - see LICENSE file for details.
