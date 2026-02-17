# Agent Projects

> **A new way of working with DevOps** — leveraging AI in a conversational web app to create, manage, and execute GitHub Issues on a GitHub Project Board, with an automated **Spec Kit agent pipeline** that turns a feature request into a specification, plan, task breakdown, and implementation — all through GitHub Copilot custom agents.

This application transforms how development teams interact with their project management workflow. Instead of manually navigating GitHub's UI to create issues, update statuses, or track progress, users have a conversation with an AI-powered chat interface. The system then orchestrates a pipeline of custom Copilot agents that autonomously produce specification documents and implement the feature — each agent creates its own PR branch from the issue's main branch, and child PRs are automatically merged back when complete.

## The Vision

Traditional DevOps workflows require developers to context-switch between their IDE, GitHub Issues, Project Boards, and PR reviews. This application consolidates that experience into a single conversational interface where you can:

- **Describe what you want to build** in natural language
- **Watch AI generate structured GitHub Issues** with proper formatting, labels, and details
- **See the Spec Kit agent pipeline kick off automatically** — specification, planning, task breakdown, and implementation all happen autonomously
- **Monitor agent progress in real-time** as each agent completes its work and the pipeline advances
- **Review the main PR** containing all agent work — child branches are automatically merged into the main branch as each agent finishes

---

## Workflow: From Idea to Code Review

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        THE SPEC KIT AGENT PIPELINE                           │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  👤 User describes feature        🤖 Azure OpenAI generates Issue            │
│  in chat interface          ───▶  with title, user story, requirements       │
│                                                                              │
│  User clicks Confirm         ───▶  GitHub Issue created, added to Project    │
│                                    Status: 📋 Backlog                        │
│                                                                              │
│  ┌───────────────────── AUTOMATED AGENT PIPELINE ──────────────────────┐     │
│  │                                                                     │     │
│  │  📋 Backlog ─── speckit.specify ──▶ spec.md                         │     │
│  │       │         Creates first PR    (posted as issue comment)       │     │
│  │       │         (this branch = main branch for the issue)           │     │
│  │       ▼                                                             │     │
│  │  📝 Ready ─── speckit.plan ──▶ plan.md, research.md, data-model.md  │     │
│  │       │        Branches FROM        (posted as issue comments)      │     │
│  │       │        main branch,         Child PR merged + branch        │     │
│  │       │        child PR merged      deleted on completion           │     │
│  │       │                                                             │     │
│  │       ├─── speckit.tasks ──▶ tasks.md                               │     │
│  │       │     Branches FROM     (posted as issue comment)             │     │
│  │       │     main branch,      Child PR merged + branch              │     │
│  │       │     child PR merged   deleted on completion                 │     │
│  │       ▼                                                             │     │
│  │  🔄 In Progress ─── speckit.implement ──▶ Code changes              │     │
│  │       │               Branches FROM        Child PR merged +        │     │
│  │       │               main branch          branch deleted           │     │
│  │       ▼                                                             │     │
│  │  👀 In Review ─── Main PR ready for human review                    │     │
│  │                    Contains all merged agent work                   │     │
│  │                    Copilot code review requested                    │     │
│  │                                                                     │     │
│  └─────────────────────────────────────────────────────────────────────┘     │
│                                                                              │
│  🌿 HIERARCHICAL PR BRANCHING                                                │
│     First agent's PR branch = "main branch" for the issue                    │
│     All subsequent agents branch FROM and merge INTO this main branch        │
│     Child branches are automatically deleted after merge                     │
│                                                                              │
│  📄 Agent outputs (.md files) are automatically extracted from the PR        │
│     and posted as GitHub Issue comments by the polling service               │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Issue Status Flow

| Status | Agent(s) Assigned | What Happens | Transition Trigger |
|--------|-------------------|--------------|-------------------|
| 📋 **Backlog** | `speckit.specify` | Agent creates first PR (establishes main branch) and writes `spec.md` | `speckit.specify: Done!` comment detected |
| 📝 **Ready** | `speckit.plan` → `speckit.tasks` | Sequential pipeline: each agent branches from main branch, child PR merged + branch deleted on completion | Both agents post `Done!` markers |
| 🔄 **In Progress** | `speckit.implement` | Agent branches from main branch, implements code from `tasks.md`, child PR merged + branch deleted, main PR converted from draft to ready | Child PR completion detected (timeline events or not draft) |
| 👀 **In Review** | — | Main PR contains all agent work (child PRs already merged), Copilot code review requested | Manual merge |
| ✅ **Done** | — | Work completed and merged | Manual or webhook on PR merge |

### Agent Pipeline Details

The **Spec Kit** agents are custom GitHub Copilot agents defined in `.github/agents/`:

| Agent | Purpose | Output Files |
|-------|---------|-------------|
| `speckit.specify` | Creates feature specification from the issue description | `spec.md`, `checklists/requirements.md` |
| `speckit.plan` | Generates implementation plan with research and data model | `plan.md`, `research.md`, `data-model.md`, `contracts/*`, `quickstart.md` |
| `speckit.tasks` | Produces actionable, dependency-ordered task breakdown | `tasks.md` |
| `speckit.implement` | Executes implementation following `tasks.md` | Code files |
| `speckit.clarify` | Asks clarification questions, updates spec | Updates `spec.md` |
| `speckit.analyze` | Read-only cross-artifact consistency analysis | Analysis report |
| `speckit.checklist` | Generates quality checklists | `checklists/*.md` |
| `speckit.constitution` | Creates/updates project constitution | `.specify/memory/constitution.md` |
| `speckit.taskstoissues` | Converts `tasks.md` entries into GitHub Issues | GitHub Issues |

### Key Behaviors

- **Hierarchical PR Branching**: The first PR created for an issue establishes the "main branch" for that issue. All subsequent agents branch FROM this main branch (using the branch name as `base_ref`) and create their own child PRs targeting it. When a child agent completes, their PR is automatically squash-merged into the main branch and the child branch is deleted. By the time the issue reaches In Review, the main PR contains all agent work consolidated into a single branch.
- **Main Branch Discovery**: The main branch is tracked per-issue in memory (including branch name, PR number, and latest HEAD SHA for audit purposes). If the server restarts, the system automatically discovers the main branch by scanning linked PRs for the issue before assigning the next agent.
- **System-Side Output Posting**: When an agent's PR work completes (for `speckit.specify`, `speckit.plan`, `speckit.tasks`), the polling service automatically extracts `.md` files from the PR branch, posts them as GitHub Issue comments, and posts the `<agent>: Done!` marker to advance the pipeline.
- **speckit.implement Completion**: Unlike other agents, `speckit.implement` completion is detected via PR timeline events (`copilot_work_finished`, `review_requested`) or when the child PR is no longer a draft. When complete, its child PR is merged into the main branch, the main PR is converted from draft to ready for review, status is updated to "In Review", and Copilot code review is requested.
- **Pipeline Reconstruction**: If the server restarts mid-pipeline, it reconstructs pipeline state by scanning issue comments for `Done!` markers.
- **Automatic Branch Cleanup**: After a child PR is merged into the main branch, the child branch is automatically deleted from the repository to keep the branch list clean.
- **Pipeline State Tracking**: Each issue with an active agent pipeline has its state tracked in memory, including which agents have completed and which is currently active. This prevents premature status transitions.

### Key Integrations

| Component | Role |
|-----------|------|
| **Azure OpenAI** | Generates structured GitHub Issues from natural language descriptions |
| **GitHub Projects V2** | Manages the kanban board with status columns (GraphQL API) |
| **GitHub Copilot** | Coding agent platform — custom Spec Kit agents run on it |
| **Polling Service** | Background loop that detects agent completion, posts outputs, advances pipelines |
| **WebSocket** | Real-time UI updates for task changes and agent progress |

---

## Features

- **GitHub OAuth Authentication**: Secure login with GitHub OAuth 2.0
- **Project Selection**: Browse and select from your GitHub Projects V2 boards
- **Natural Language Issue Creation**: Describe features in plain English; AI generates structured GitHub Issues with user stories, requirements, and metadata
- **Automated Agent Pipeline**: Issues flow through Spec Kit agents automatically — specify → plan → tasks → implement
- **Hierarchical PR Branching**: First PR's branch becomes the "main" for the issue; subsequent agents branch from it, child PRs are squash-merged back, and child branches are automatically deleted
- **Automatic Branch Cleanup**: Child branches are deleted from the repository after their PRs are merged into the main branch
- **System-Side Output Posting**: Agent `.md` outputs are extracted from PRs and posted as issue comments automatically
- **Main Branch Discovery**: If the server restarts, the main branch is rediscovered from linked PRs before assigning the next agent
- **Project Board View**: Interactive Kanban board with columns, issue cards, detail modals, priority/size badges, assignee avatars, and linked PR counts
- **Status Updates via Chat**: Update task status using natural language commands
- **Real-Time Sync**: Live updates via WebSocket with polling fallback
- **Pipeline State Tracking**: Monitor which agent is active, which have completed, and overall progress
- **Pipeline Reconstruction**: Server can reconstruct pipeline state from issue comments on restart
- **Self-Healing Recovery**: Background detection and automatic re-assignment of stalled agent pipelines with per-issue cooldowns
- **Double-Assignment Prevention**: Pending agent assignments are tracked to prevent race conditions in concurrent polling loops
- **Workflow Configuration**: Customize agent mappings, status columns, and assignees per project
- **Responsive UI**: Modern React interface with dark/light mode and TanStack Query state management

## Architecture

```
┌─────────────────┐     ┌─────────────────────────┐     ┌──────────────────┐
│    Frontend      │────▶│       Backend            │────▶│  GitHub API      │
│  React + Vite    │◀────│       FastAPI            │◀────│  GraphQL + REST  │
│  TypeScript      │ WS  │                         │     │                  │
│  TanStack Query  │     │  ┌───────────────────┐  │     │  ┌────────────┐  │
└─────────────────┘     │  │ Workflow           │  │     │  │ Projects   │  │
                        │  │ Orchestrator       │  │     │  │ V2 API     │  │
                        │  └───────────────────┘  │     │  └────────────┘  │
                        │  ┌───────────────────┐  │     │  ┌────────────┐  │
                        │  │ Copilot Polling    │  │     │  │ Copilot    │  │
                        │  │ Service            │  │     │  │ Assignment │  │
                        │  └───────────────────┘  │     │  └────────────┘  │
                        │  ┌───────────────────┐  │     └──────────────────┘
                        │  │ AI Agent Service   │  │
                        │  │ (Azure OpenAI)     │  │
                        │  └───────────────────┘  │
                        └─────────────────────────┘
```

### Polling Service Cycle

The background polling service runs every 60 seconds (configurable) and executes these steps in order:

1. **Step 0 — Post Agent Outputs**: For issues with active pipelines, detect completed PRs. For each completed agent:
   - **Merge child PR first** into the main branch (before posting Done!)
   - Wait 2 seconds for GitHub to process the merge
   - Extract `.md` files from the PR branch and post them as issue comments
   - Post the `<agent>: Done!` marker
   - Update the tracking table in the issue body (mark agent as ✅ Done)
   - Also captures the main branch when the first PR is detected
2. **Step 1 — Check Backlog**: Scan Backlog issues for `speckit.specify: Done!` → transition to Ready, assign `speckit.plan` (branching from the main branch).
3. **Step 2 — Check Ready**: Scan Ready issues for `speckit.plan: Done!` / `speckit.tasks: Done!` → advance pipeline or transition to In Progress and assign `speckit.implement`.
4. **Step 3 — Check In Progress**: Detect `speckit.implement` child PR completion (timeline events: `copilot_work_finished`, `review_requested`, or PR not draft) → merge child PR into main branch, delete child branch, convert main PR from draft to ready for review, transition to In Review, request Copilot code review.
5. **Step 4 — Check In Review**: Ensure Copilot code review has been requested on In Review PRs.
6. **Step 5 — Self-Healing Recovery**: Detect stalled agent pipelines across all non-completed issues. If an issue has an active agent in its tracking table but no corresponding pending assignment or recent progress, the system re-assigns the agent. A per-issue cooldown (5 minutes) prevents rapid re-assignment. On restart, workflow configuration is auto-bootstrapped if missing.

### Agent Pipeline Tracking

Each issue maintains a **tracking table** in its body that shows the full agent pipeline and current progress:

```markdown
---

## 🤖 Agent Pipeline

| # | Status | Agent | State |
|---|--------|-------|-------|
| 1 | Backlog | `speckit.specify` | ✅ Done |
| 2 | Ready | `speckit.plan` | ✅ Done |
| 3 | Ready | `speckit.tasks` | 🔄 Active |
| 4 | In Progress | `speckit.implement` | ⏳ Pending |
```

**State values:**
- **⏳ Pending** — Agent not yet started
- **🔄 Active** — Currently assigned to GitHub Copilot
- **✅ Done** — `<agent>: Done!` comment posted

This durable tracking survives server restarts and provides visibility into pipeline progress directly on the GitHub Issue.

### Retry-with-Backoff

Agent assignments use exponential backoff to handle transient GitHub API errors (especially after PR merges):
- **3 attempts** with delays: 3s → 6s → 12s
- Logs warnings on retries, success/failure on completion

#### speckit.implement Completion Flow

When `speckit.implement` completes its work:
1. **Merge child PR** — The `speckit.implement` child PR is squash-merged into the issue's main branch
2. **Delete child branch** — The child branch is automatically deleted
3. **Convert main PR** — The main PR (first PR for the issue) is converted from draft to ready for review
4. **Update status** — Issue status is updated to "In Review"
5. **Request review** — Copilot code review is requested on the main PR

### GitHub Copilot Model

All custom Copilot agents use **Claude Opus 4.6** by default for reasoning and code generation tasks. The model is configured in both:
- GraphQL mutation: `assignCopilotToIssue`
- REST API fallback: `/repos/{owner}/{repo}/issues/{issue_number}/copilot`

---

## Prerequisites

- [Fork this repository](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo) before starting
- [Create a GitHub Project (Kanban)](https://docs.github.com/en/issues/planning-and-tracking-with-projects/creating-projects/creating-a-project) with status columns: **Backlog**, **Ready**, **In Progress**, **In Review**, **Done**
- Sign up for [GitHub Copilot](https://github.com/features/copilot) (required for the agent pipeline)
- [Visual Studio Code](https://code.visualstudio.com/download) or [GitHub Codespaces](https://github.com/features/codespaces)
- Docker and Docker Compose (recommended) OR:
  - Node.js 18+
  - Python 3.12+
- GitHub OAuth App credentials
- Azure OpenAI API credentials (optional, for AI issue generation)

---

## Quick Start with GitHub Codespaces (Easiest)

The fastest way to get started! Launch a fully configured development environment in your browser.

### 1. Open in Codespaces

Click the button below or go to **Code** → **Codespaces** → **Create codespace on main**:

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/OWNER/REPO)

### 2. Wait for Setup

The dev container will automatically:
- Install Python 3.12 and Node.js 20
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

#### Azure OpenAI (Optional — for AI issue generation)

If you want AI-powered issue generation from natural language:
```env
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_KEY=your_api_key
AZURE_OPENAI_DEPLOYMENT=gpt-4
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
- `ghchat-backend` — Backend API (healthy)
- `ghchat-frontend` — Frontend UI

---

## GitHub Webhook Setup (Optional)

Enable real-time status updates when GitHub Copilot marks PRs as ready for review. The polling service handles this automatically, but webhooks provide faster detection.

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

> **Important**: Use **Tokens (classic)**, not Fine-grained tokens. Projects V2 API requires the `project` scope which is only available in classic tokens.

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
- API Docs: http://localhost:8000/api/docs (when `DEBUG=true`)

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GITHUB_CLIENT_ID` | Yes | — | GitHub OAuth App Client ID |
| `GITHUB_CLIENT_SECRET` | Yes | — | GitHub OAuth App Client Secret |
| `GITHUB_REDIRECT_URI` | No | `http://localhost:8000/api/v1/auth/github/callback` | OAuth callback URL |
| `SESSION_SECRET_KEY` | Yes | — | Random hex string for session encryption |
| `SESSION_EXPIRE_HOURS` | No | `8` | Session TTL in hours |
| `AZURE_OPENAI_ENDPOINT` | No | — | Azure OpenAI endpoint URL |
| `AZURE_OPENAI_KEY` | No | — | Azure OpenAI API key |
| `AZURE_OPENAI_DEPLOYMENT` | No | `gpt-4` | Azure OpenAI deployment name |
| `GITHUB_WEBHOOK_SECRET` | No | — | Secret for webhook signature verification |
| `GITHUB_WEBHOOK_TOKEN` | No | — | GitHub PAT (classic) for webhook operations |
| `DEFAULT_REPOSITORY` | No | — | Default repo for issue creation (`owner/repo`) |
| `DEFAULT_ASSIGNEE` | No | `""` | Default assignee for In Progress issues |
| `COPILOT_POLLING_INTERVAL` | No | `60` | Polling interval in seconds |
| `FRONTEND_URL` | No | `http://localhost:5173` | Frontend URL for OAuth redirects |
| `CORS_ORIGINS` | No | `http://localhost:5173` | Allowed CORS origins (comma-separated) |
| `DEBUG` | No | `false` | Enable debug mode (API docs, dev-login) |
| `CACHE_TTL_SECONDS` | No | `300` | In-memory cache TTL in seconds |
| `HOST` | No | `0.0.0.0` | Server host |
| `PORT` | No | `8000` | Server port |

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
npm test                  # Unit tests (Vitest)
npm run test:e2e          # E2E tests (Playwright)
npm run test:e2e:headed   # E2E with browser visible
```

---

## API Endpoints

### Health
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Health check |

### Authentication
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/auth/github` | Initiate GitHub OAuth flow |
| GET | `/api/v1/auth/github/callback` | OAuth callback handler |
| POST | `/api/v1/auth/session` | Set session cookie from token |
| GET | `/api/v1/auth/me` | Get current authenticated user |
| POST | `/api/v1/auth/logout` | Logout and clear session |
| POST | `/api/v1/auth/dev-login` | Dev-only PAT login (debug mode) |

### Projects
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/projects` | List user's GitHub Projects |
| GET | `/api/v1/projects/{id}` | Get project details |
| GET | `/api/v1/projects/{id}/tasks` | Get project tasks |
| POST | `/api/v1/projects/{id}/select` | Select active project (starts polling) |
| WS | `/api/v1/projects/{id}/subscribe` | WebSocket for real-time updates |
| GET | `/api/v1/projects/{id}/events` | SSE fallback for real-time updates |

### Board
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/board/projects` | List projects with status field configuration |
| GET | `/api/v1/board/{project_id}` | Get board data (columns + items) |

### Chat
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/chat/messages` | Get chat messages for session |
| POST | `/api/v1/chat/messages` | Send message, get AI response |
| DELETE | `/api/v1/chat/messages` | Clear chat history |
| POST | `/api/v1/chat/proposals/{id}/confirm` | Confirm task proposal |
| DELETE | `/api/v1/chat/proposals/{id}` | Cancel task proposal |

### Tasks
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/tasks` | Create a task (GitHub Issue + project attachment) |
| PATCH | `/api/v1/tasks/{id}/status` | Update task status |

### Workflow & Pipeline
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/workflow/recommendations/{id}/confirm` | Confirm issue recommendation → full workflow |
| POST | `/api/v1/workflow/recommendations/{id}/reject` | Reject recommendation |
| GET | `/api/v1/workflow/config` | Get workflow configuration |
| PUT | `/api/v1/workflow/config` | Update workflow configuration |
| GET | `/api/v1/workflow/transitions` | Get transition audit log |
| GET | `/api/v1/workflow/pipeline-states` | Get all active pipeline states |
| GET | `/api/v1/workflow/pipeline-states/{issue_number}` | Get pipeline state for specific issue |
| POST | `/api/v1/workflow/notify/in-review` | Send In Review notification |
| GET | `/api/v1/workflow/polling/status` | Get polling service status |
| POST | `/api/v1/workflow/polling/start` | Start background polling |
| POST | `/api/v1/workflow/polling/stop` | Stop background polling |
| POST | `/api/v1/workflow/polling/check-issue/{issue_number}` | Manually check a specific issue |
| POST | `/api/v1/workflow/polling/check-all` | Check all In Progress issues |

### Webhooks
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/webhooks/github` | Handle GitHub webhook events (PR ready_for_review) |

API documentation available at http://localhost:8000/api/docs when `DEBUG=true`.

---

## Project Structure

```
github-workflows/
├── .env.example              # Environment template
├── docker-compose.yml        # Docker orchestration (backend + frontend)
├── README.md
├── .github/
│   └── agents/               # Spec Kit custom Copilot agent definitions
│       ├── speckit.specify.agent.md
│       ├── speckit.plan.agent.md
│       ├── speckit.tasks.agent.md
│       ├── speckit.implement.agent.md
│       ├── speckit.clarify.agent.md
│       ├── speckit.analyze.agent.md
│       ├── speckit.checklist.agent.md
│       ├── speckit.constitution.agent.md
│       ├── speckit.taskstoissues.agent.md
│       └── copilot-instructions.md
├── backend/
│   ├── src/
│   │   ├── api/              # API endpoints
│   │   │   ├── auth.py       #   Authentication (OAuth)
│   │   │   ├── board.py      #   Project board (Kanban columns + items)
│   │   │   ├── chat.py       #   Chat interface
│   │   │   ├── projects.py   #   Project management
│   │   │   ├── tasks.py      #   Task CRUD
│   │   │   ├── workflow.py   #   Workflow & pipeline management
│   │   │   └── webhooks.py   #   GitHub webhook handler
│   │   ├── models/           # Pydantic data models
│   │   │   ├── board.py      #   Board columns, items, custom fields
│   │   │   ├── chat.py       #   Chat, workflow config, agent mappings
│   │   │   ├── project.py    #   Projects, status columns
│   │   │   ├── task.py       #   Tasks / project items
│   │   │   └── user.py       #   User / session
│   │   ├── services/         # Business logic
│   │   │   ├── ai_agent.py           # Azure OpenAI integration
│   │   │   ├── agent_tracking.py     # Agent pipeline tracking (issue body markdown)
│   │   │   ├── cache.py              # In-memory TTL cache
│   │   │   ├── copilot_polling.py    # Background polling + agent output posting
│   │   │   ├── github_auth.py        # OAuth token exchange
│   │   │   ├── github_projects.py    # GitHub API (GraphQL + REST)
│   │   │   ├── websocket.py          # WebSocket connection manager
│   │   │   └── workflow_orchestrator.py  # Pipeline state + agent assignment
│   │   ├── prompts/          # AI prompt templates
│   │   ├── config.py         # Environment configuration
│   │   ├── constants.py      # API constants
│   │   ├── exceptions.py     # Custom exceptions
│   │   └── main.py           # FastAPI app entry point
│   ├── tests/
│   │   ├── unit/             # Unit tests
│   │   ├── integration/      # Integration tests
│   │   ├── test_api_e2e.py   # API end-to-end tests
│   │   └── conftest.py       # Test fixtures
│   └── pyproject.toml        # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── auth/         # LoginButton
│   │   │   ├── board/        # ProjectBoard, BoardColumn, IssueCard,
│   │   │   │                 # IssueDetailModal, colorUtils
│   │   │   ├── chat/         # ChatInterface, MessageBubble, TaskPreview,
│   │   │   │                 # StatusChangePreview, IssueRecommendationPreview
│   │   │   ├── common/       # ErrorDisplay, RateLimitIndicator
│   │   │   └── sidebar/      # ProjectSidebar, ProjectSelector, TaskCard
│   │   ├── hooks/            # useAuth, useChat, useProjects, useWorkflow,
│   │   │                     # useRealTimeSync, useProjectBoard, useAppTheme
│   │   ├── pages/            # ProjectBoardPage
│   │   ├── services/         # API client (api.ts)
│   │   └── types/            # TypeScript type definitions
│   ├── e2e/                  # Playwright E2E tests
│   ├── package.json
│   ├── vite.config.ts
│   ├── vitest.config.ts
│   └── playwright.config.ts
└── specs/                    # Feature specifications
    ├── 001-app-title-update/
    ├── 001-github-project-board/
    ├── 001-github-project-chat/
    ├── 001-github-project-workflow/
    └── 002-speckit-agent-assignment/
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
- Azure OpenAI is optional — the app works without it (AI features disabled)

**Agent pipeline not advancing:**
- Verify the polling service is running: `GET /api/v1/workflow/polling/status`
- Check that your GitHub Project has the required status columns: Backlog, Ready, In Progress, In Review
- Review backend logs for agent assignment errors: `docker compose logs -f backend`
- Manually trigger a check: `POST /api/v1/workflow/polling/check-all`
- Check pipeline state for a specific issue: `GET /api/v1/workflow/pipeline-states/{issue_number}`

**speckit.implement not starting or completing:**
- Ensure the `speckit.tasks: Done!` marker was posted on the issue
- Check that the issue transitioned to "In Progress" status
- Verify the pipeline state shows `speckit.implement` as the current agent
- Review logs for child PR detection: the system waits for a child PR targeting the main branch
- If Copilot hasn't created a PR yet, this may be a GitHub Copilot delay — the backend correctly assigned the agent

**Issue stuck in "In Progress":**
- The system waits for `speckit.implement` to create a child PR that targets the issue's main branch
- Check if a new child PR exists by looking at linked PRs for the issue
- The system looks for `copilot_work_finished` timeline events or the PR no longer being a draft
- Once detected, the child PR will be merged, main PR converted to ready, and status updated to "In Review"

**Multiple PRs created for one issue:**
- This is expected behavior with hierarchical branching. The first PR's branch becomes the "main branch" for the issue. Each subsequent agent (speckit.plan, speckit.tasks, speckit.implement) creates its own child branch from the main branch and opens a child PR targeting it. When each agent completes, the system automatically squash-merges the child PR into the main branch and deletes the child branch. By the time the issue reaches In Review, the main PR contains all consolidated work.

**Webhook not triggering:**
- Verify `GITHUB_WEBHOOK_SECRET` matches the secret in GitHub webhook settings
- Check `GITHUB_WEBHOOK_TOKEN` has `repo` and `project` scopes
- Ensure webhook is configured for "Pull requests" events
- Check webhook delivery logs in GitHub: Repo → Settings → Webhooks → Recent Deliveries

**Projects not showing:**
- Ensure your GitHub token has `project` scope
- Projects V2 requires the user to have access to the project
- Organization projects need `read:org` scope

**GitHub Copilot agent fails to start / Repository ruleset violation:**
If you see the error:
> "The agent encountered an error and was unable to start working on this issue: This may be caused by a repository ruleset violation."

This occurs when GitHub Copilot doesn't have permission to bypass branch protection rules. To fix:

1. Go to your repository → **Settings** → **Rules** → **Rulesets**
2. Click on the ruleset protecting your default branch
3. Under **Bypass list**, click **Add bypass**
4. Search for and add **Copilot** (the GitHub Copilot app)
5. Set bypass mode to **Always Allow**
6. Set target branches to **Include all branches**
7. Save the ruleset

**Rate limiting:**
- GitHub API has rate limits (5000 requests/hour for authenticated users)
- The app tracks remaining calls; wait for reset if limits are hit

**Port already in use:**
```bash
lsof -ti:8000 | xargs kill -9   # Backend
lsof -ti:5173 | xargs kill -9   # Frontend
```

### Viewing Logs

```bash
docker compose logs -f            # All containers
docker compose logs -f backend    # Backend only
docker compose logs -f frontend   # Frontend only
```

---

## License

MIT License — see LICENSE file for details.
