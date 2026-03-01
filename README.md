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
│  👤 User describes feature        🤖 GitHub Copilot generates Issue          │
│  in chat interface          ───▶  with title, user story, requirements       │
│                                   (via Copilot SDK, or Azure OpenAI)         │
│                                                                              │
│  User clicks Confirm         ───▶  GitHub Issue created, added to Project    │
│                                    Sub-issues created for each agent         │
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
│     and posted as comments on the agent's SUB-ISSUE by the polling service   │
│                                                                              │
│  📌 SUB-ISSUE LIFECYCLE                                                      │
│     Sub-issues created upfront: [agent-name] Parent Title                    │
│     Copilot assigned to sub-issue (not parent)                               │
│     Agent outputs and Done! markers posted on sub-issue                      │
│     Sub-issue closed as completed when agent finishes                        │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Issue Status Flow

| Status | Agent(s) Assigned | What Happens | Transition Trigger |
|--------|-------------------|--------------|-------------------|
| 📋 **Backlog** | `speckit.specify` | Sub-issue created, agent assigned; creates first PR (establishes main branch) and writes `spec.md`; sub-issue closed on completion | `speckit.specify: Done!` on sub-issue |
| 📝 **Ready** | `speckit.plan` → `speckit.tasks` | Sequential pipeline: each agent assigned to its sub-issue, branches from main branch, child PR merged + branch deleted, sub-issue closed on completion | Both agents post `Done!` markers on their sub-issues |
| 🔄 **In Progress** | `speckit.implement` | Agent assigned to sub-issue, branches from main branch, implements code from `tasks.md`, child PR merged + branch deleted, main PR converted from draft to ready, sub-issue closed | Child PR completion detected (timeline events or not draft) |
| 👀 **In Review** | `copilot-review` | Main PR contains all agent work (child PRs already merged), Copilot code review requested; sub-issue closed when review completes | Manual merge |
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

- **Sub-Issue-Per-Agent Workflow**: When a feature issue is confirmed, the system creates sub-issues upfront for every agent in the pipeline. Each sub-issue is titled `[agent-name] Parent Title` and added to the same GitHub Project. Copilot is assigned to the sub-issue (not the parent), and agent markdown file comments (`.md` files) are posted **only on the sub-issue**. The `<agent>: Done!` marker is posted **only on the parent (main) issue**. When an agent completes, its sub-issue is automatically closed as completed (`state=closed`, `state_reason=completed`). This provides per-agent visibility and keeps the parent issue clean with only completion markers.
- **Hierarchical PR Branching**: The first PR created for an issue establishes the "main branch" for that issue. All subsequent agents branch FROM this main branch (using the branch name as `base_ref`) and create their own child PRs targeting it. When a child agent completes, their PR is automatically squash-merged into the main branch and the child branch is deleted. By the time the issue reaches In Review, the main PR contains all agent work consolidated into a single branch.
- **Main Branch Discovery**: The main branch is tracked per-issue in memory (including branch name, PR number, and latest HEAD SHA for audit purposes). If the server restarts, the system automatically discovers the main branch by scanning linked PRs for the issue before assigning the next agent.
- **System-Side Output Posting**: When an agent's PR work completes (for `speckit.specify`, `speckit.plan`, `speckit.tasks`), the polling service automatically extracts `.md` files from the PR branch, posts them as comments on the agent's sub-issue, and posts the `<agent>: Done!` marker on the parent issue to advance the pipeline.
- **speckit.implement Completion**: Unlike other agents, `speckit.implement` completion is detected via PR timeline events (`copilot_work_finished`, `review_requested`) or when the child PR is no longer a draft. When complete, its child PR is merged into the main branch, the main PR is converted from draft to ready for review, status is updated to "In Review", and Copilot code review is requested.
- **Sub-Issue Lifecycle**: Sub-issues are created open with `ai-generated` and `sub-issue` labels. When assigned, they receive an `in-progress` label. When the agent completes, the sub-issue is closed as completed with a `done` label added and `in-progress` removed, and the sub-issue's project board status is updated to "Done".
- **SQLite Workflow Config Persistence**: Workflow configuration (agent mappings, status columns) is persisted to SQLite alongside the in-memory cache. On server restart, the config is loaded from the `workflow_config` column in `project_settings`. A backfill mechanism migrates legacy `agent_pipeline_mappings` data to the full config format.
- **User-Specific Agent Pipeline Mappings**: When a user confirms a proposal (chat or Signal), the system loads their personal agent pipeline configuration from the `project_settings` table and applies it to the workflow. This ensures each user's customised agent assignments are respected. A 3-tier DB fallback (user → `__workflow__` canonical → any-user with backfill) guarantees configuration is always found.
- **Case-Insensitive Status Deduplication**: Both frontend and backend deduplicate agent_mappings keys by case-insensitive comparison before saving. When GitHub project column names (e.g., "In progress") differ in casing from backend defaults ("In Progress"), the non-empty mapping wins. The Settings UI syncs changes to the canonical `__workflow__` DB row and invalidates the in-memory config cache.
- **Pipeline Initialisation Safety**: When sub-issues are created upfront, the `PipelineState` is initialised with the actual agent list for the initial status and a `started_at` timestamp. This prevents the polling loop from seeing an empty agents list (`is_complete = 0 >= len([]) = True`) and prematurely advancing the pipeline.
- **Polling Auto-Start**: The background polling service automatically starts when a user confirms a proposal (chat) or recommendation (workflow), not only on explicit project selection. This ensures the pipeline runs immediately after issue creation.
- **Pipeline Reconstruction**: If the server restarts mid-pipeline, it reconstructs pipeline state from the durable tracking table in the issue body and from issue comments for `Done!` markers. Sub-issue mappings are reconstructed by parsing `[agent-name]` prefixes from sub-issue titles.
- **Automatic Branch Cleanup**: After a child PR is merged into the main branch, the child branch is automatically deleted from the repository to keep the branch list clean.
- **Copilot Status Acceptance**: When Copilot starts working, it naturally moves issues to "In Progress". The polling service accepts this status change and updates the internal pipeline state accordingly — it does NOT fight Copilot by reverting the status, which would re-trigger the agent.
- **Pipeline State Tracking**: Each issue with an active agent pipeline has its state tracked in memory, including which agents have completed and which is currently active. Pipeline states are initialised with actual agents and timestamps to prevent premature completion detection.
- **Case-Insensitive Status Matching**: All status name lookups use case-insensitive matching via a `_ci_get()` helper, accommodating variations between GitHub Project board column names (e.g., "In progress" vs "In Progress").
- **Case-Insensitive Status Deduplication**: Agent pipeline mappings are deduplicated by case-insensitive key comparison on save (backend) and load (frontend). When duplicates exist, the non-empty list wins.
- **Double-Assignment Prevention**: Pending agent assignment flags are set BEFORE the GitHub API call and cleared only on failure. A per-issue recovery cooldown (5 minutes) prevents rapid re-assignment.

### Key Integrations

| Component | Role |
|-----------|------|
| **GitHub Copilot SDK** | Default AI provider for issue generation — authenticates via user's GitHub OAuth token |
| **Azure OpenAI** | Optional fallback AI provider for issue generation (requires separate API credentials) |
| **GitHub Projects V2** | Manages the kanban board with status columns (GraphQL API) |
| **GitHub Copilot** | Coding agent platform — custom Spec Kit agents run on it |
| **SQLite** | Persistent storage for workflow configuration, sessions, and settings (WAL mode, auto-migrated) |
| **Polling Service** | Background loop that detects agent completion, posts outputs to sub-issues, closes sub-issues, advances pipelines |
| **WebSocket** | Real-time UI updates for task changes and agent progress |
| **Signal (sidecar)** | Bidirectional Signal messaging via `bbernhard/signal-cli-rest-api` container |

---

## Features

- **GitHub OAuth Authentication**: Secure login with GitHub OAuth 2.0
- **Project Selection**: Browse and select from your GitHub Projects V2 boards
- **Natural Language Issue Creation**: Describe features in plain English; AI generates structured GitHub Issues with user stories, requirements, and metadata
- **Pluggable AI Provider**: GitHub Copilot (default, uses OAuth token) or Azure OpenAI (optional, uses API key) — configured via `AI_PROVIDER` env var
- **Automated Agent Pipeline**: Issues flow through Spec Kit agents automatically — specify → plan → tasks → implement → review
- **Sub-Issue-Per-Agent Workflow**: Each agent gets its own sub-issue created upfront, providing per-agent visibility. Sub-issues are closed as completed when their agent finishes.
- **Agent Configuration UI**: Drag-and-drop agent assignment per board column with presets (Spec Kit, GitHub Copilot, Custom) and custom agent support
- **Agent Discovery**: Agents are discovered from `.github/agents/*.agent.md` in the repository, combined with built-in agents
- **Hierarchical PR Branching**: First PR's branch becomes the "main" for the issue; subsequent agents branch from it, child PRs are squash-merged back, and child branches are automatically deleted
- **Automatic Branch Cleanup**: Child branches are deleted from the repository after their PRs are merged into the main branch
- **System-Side Output Posting**: Agent `.md` outputs are extracted from PRs and posted as sub-issue comments automatically
- **Main Branch Discovery**: If the server restarts, the main branch is rediscovered from linked PRs before assigning the next agent
- **SQLite Workflow Config Persistence**: Workflow configuration (agent mappings per status) is persisted to SQLite so it survives server restarts. Falls back to legacy data with automatic backfill migration.
- **User-Specific Agent Pipeline Mappings**: Each user's agent pipeline configuration (set via the Settings UI) is loaded and applied during workflow orchestration, with a 3-tier fallback: user-specific row → canonical `__workflow__` row → any-user fallback with automatic backfill.
- **Case-Insensitive Status Deduplication**: Agent pipeline mappings are deduplicated on both frontend and backend to prevent case-variant status keys (e.g., "In progress" vs "In Progress") from shadowing each other. The non-empty mapping always wins.
- **Custom Agent Creation via Chat (`#agent`)**: Create custom GitHub agents through a guided conversational flow — type `#agent <description> #<status>` in the chat or via Signal to generate an AI-powered agent with preview, iterative editing, and automated pipeline that saves config, creates a GitHub Issue, branch, commits configuration files, opens a PR, and moves the issue to "In Review"
  - Fuzzy status column matching with ambiguity detection (handles `#in-review`, `#InReview`, `#IN_REVIEW` variations)
  - AI-generated previews with natural language edit loop ("change the name to SecBot")
  - 8-step creation pipeline with best-effort execution and per-step status reporting
  - Works from both web chat and Signal messaging
- **Schema Migrations**: Numbered SQL migrations run at startup (currently 001–007), tracked by a `schema_version` table
- **Polling Auto-Start**: Background polling automatically starts after confirming a proposal or recommendation, ensuring the pipeline runs without manual intervention
- **Case-Insensitive Status Matching**: Status name lookups accommodate variations between GitHub board column names (e.g., "In progress" vs "In Progress")
- **Project Board View**: Interactive Kanban board with columns, issue cards, detail modals, priority/size badges, assignee avatars, linked PR counts, and per-column agent configuration
- **Status Updates via Chat**: Update task status using natural language commands
- **Real-Time Sync**: Live updates via WebSocket with polling fallback
- **Pipeline State Tracking**: Monitor which agent is active, which have completed, and overall progress
- **Pipeline Reconstruction**: Server can reconstruct pipeline state from issue comments on restart
- **Self-Healing Recovery**: Background detection and automatic re-assignment of stalled agent pipelines with per-issue cooldowns
- **Double-Assignment Prevention**: Pending agent assignments are tracked to prevent race conditions in concurrent polling loops
- **Workflow Configuration**: Customize agent mappings, status columns, and assignees per project
- **Signal Messaging Integration**: Connect your Signal account to receive chat messages on your phone and reply directly from Signal
  - QR code linking flow in Settings (scan with Signal → Linked Devices)
  - Outbound delivery: assistant/system messages forwarded to Signal with styled formatting, emoji headers, and deep links
  - Inbound routing: reply from Signal → message appears in app chat and triggers AI workflow
  - `#project-name` prefix to route Signal messages to a specific project
  - Notification preferences: All Messages, Action Proposals Only, System Confirmations Only, or None
  - Conflict detection: if another account links the same phone number, the displaced user sees a dismissible banner
  - Retry with exponential backoff (4 attempts, 30s→8min) for delivery failures
  - Phone numbers Fernet-encrypted at rest with SHA-256 hash for lookup
- **Settings Management**: Unified settings UI for user preferences (AI, display, workflow defaults, notifications, Signal connection), global settings, and per-project configuration — all persisted to SQLite with optimistic updates
- **Responsive UI**: Modern React interface with dark/light mode, TanStack Query state management, and global error boundary

## Architecture

```
┌───────────────────────┐     ┌──────────────────────────────┐     ┌──────────────────┐
│      Frontend          │────▶│           Backend             │────▶│    GitHub API     │
│  React 18 + Vite 5     │◀────│           FastAPI             │◀────│  GraphQL + REST   │
│  TypeScript ~5.4        │ WS  │                              │     │                  │
│  TanStack Query v5      │     │  ┌────────────────────────┐  │     │  ┌────────────┐  │
│  dnd-kit (drag-drop)    │     │  │ Workflow Orchestrator   │  │     │  │ Projects   │  │
│  ErrorBoundary          │     │  │ (4 sub-modules)        │  │     │  │ V2 API     │  │
└───────────────────────┘     │  └────────────────────────┘  │     │  └────────────┘  │
                              │  ┌────────────────────────┐  │     │  ┌────────────┐  │
                              │  │ Copilot Polling        │  │     │  │ Copilot    │  │
                              │  │ Service (7 sub-modules)│  │     │  │ Assignment │  │
                              │  └────────────────────────┘  │     │  └────────────┘  │
                              │  ┌────────────────────────┐  │     └──────────────────┘
                              │  │ GitHub Projects        │  │
                              │  │ Service (2 sub-modules)│  │     ┌──────────────────┐
                              │  └────────────────────────┘  │     │ signal-cli-rest- │
                              │  ┌────────────────────────┐  │ HTTP │ api (sidecar)    │
                              │  │ Signal Bridge          │──│────▶│ ┌──────────────┐ │
                              │  │ + Delivery + WS Listener│◀│─WS──│ │ Signal Relay │ │
                              │  └────────────────────────┘  │     │ └──────────────┘ │
                              │  ┌────────────────────────┐  │     └──────────────────┘
                              │  │ AI Completion Providers │  │
                              │  │ ┌──────────────────┐   │  │
                              │  │ │ Copilot SDK      │   │  │  ◀── Default (OAuth)
                              │  │ ├──────────────────┤   │  │
                              │  │ │ Azure OpenAI     │   │  │  ◀── Optional (API key)
                              │  │ └──────────────────┘   │  │
                              │  └────────────────────────┘  │
                              │  ┌────────────────────────┐  │
                              │  │ SQLite (aiosqlite)     │  │
                              │  │ WAL mode, auto-migrate │  │  ◀── Workflow config,
                              │  │ data/settings.db       │  │      sessions, settings
                              │  └────────────────────────┘  │
                              │  ┌────────────────────────┐  │
                              │  │ FastAPI DI             │  │
                              │  │ (dependencies.py)      │  │  ◀── app.state singletons
                              │  └────────────────────────┘  │
                              └──────────────────────────────┘
```

### AI Completion Provider Architecture

The backend uses a pluggable completion provider architecture for AI-powered issue generation:

| Provider | Class | Default | Authentication |
|----------|-------|---------|----------------|
| **GitHub Copilot** | `CopilotCompletionProvider` | ✅ Yes | User's GitHub OAuth token (per-request) |
| **Azure OpenAI** | `AzureOpenAICompletionProvider` | No | Static API key from env vars |

Set `AI_PROVIDER=copilot` (default) or `AI_PROVIDER=azure_openai` in `.env` to select. The Copilot provider authenticates using the user's existing GitHub OAuth token — no additional API keys needed.

### Polling Service Cycle

The background polling service runs every 60 seconds (configurable) and executes these steps in order:

1. **Step 0 — Post Agent Outputs**: For issues with active pipelines (including reconstructed ones after restart), detect completed PRs. For each completed agent:
   - **Merge child PR first** into the main branch (before posting Done!)
   - Wait 2 seconds for GitHub to process the merge
   - Extract `.md` files from the PR branch and post them as comments on the agent's **sub-issue** (not the parent)
   - Post the `<agent>: Done!` marker on the sub-issue
   - **Close the sub-issue** as completed (`state=closed`, `state_reason=completed`)
   - Update the tracking table in the **parent issue** body (mark agent as ✅ Done)
   - Also captures the main branch when the first PR is detected
   - On server restart, reconstructs pipeline state from the durable tracking table in the issue body and sub-issue mappings from `[agent-name]` title prefixes
2. **Step 1 — Check Backlog**: Scan Backlog issues for `speckit.specify: Done!` → transition to Ready, assign `speckit.plan` (branching from the main branch).
3. **Step 2 — Check Ready**: Scan Ready issues for `speckit.plan: Done!` / `speckit.tasks: Done!` → advance pipeline or transition to In Progress and assign `speckit.implement`.
4. **Step 3 — Check In Progress**: Detect `speckit.implement` child PR completion (timeline events: `copilot_work_finished`, `review_requested`, or PR not draft) → merge child PR into main branch, delete child branch, convert main PR from draft to ready for review, transition to In Review, request Copilot code review. If Copilot moves an issue to "In Progress" before the pipeline expects it, the polling service **accepts the status change** and updates the pipeline state — it does NOT restore the old status (which would re-trigger the agent).
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
| 5 | In Review | `copilot-review` | ⏳ Pending |
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
- Sign up for [GitHub Copilot](https://github.com/features/copilot) (required for the agent pipeline and default AI provider)
- [Visual Studio Code](https://code.visualstudio.com/download) or [GitHub Codespaces](https://github.com/features/codespaces)
- Docker and Docker Compose (recommended) OR:
  - Node.js 18+
  - Python 3.11+
- GitHub OAuth App credentials
- Azure OpenAI API credentials (optional — only needed if using `AI_PROVIDER=azure_openai`)

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
- AI provider is GitHub Copilot by default (uses your OAuth token — no extra credentials needed)
- [Azure OpenAI credentials](https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-models/how-to/deploy-foundry-models) (only if using `AI_PROVIDER=azure_openai`)

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

#### AI Provider (Optional — defaults to GitHub Copilot)

By default, AI issue generation uses **GitHub Copilot** via the user's OAuth token. No extra credentials needed.

To use Azure OpenAI instead:
```env
AI_PROVIDER=azure_openai
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
- `ghchat-signal-api` — Signal messaging sidecar (healthy)

---

## GitHub Webhook Setup (Optional)

Enable real-time status updates when GitHub Copilot marks PRs as ready for review. The polling service handles this automatically, but webhooks provide faster detection.

---

## Signal Messaging Integration (Optional)

Enable bidirectional Signal messaging so users receive chat notifications on Signal and can reply directly.

### How It Works

- **Backend** communicates with a `signal-cli-rest-api` sidecar via HTTP (send messages, generate QR codes) and WebSocket (receive inbound messages)
- **Frontend** only talks to the Backend — never directly to the Signal sidecar
- Phone numbers are Fernet-encrypted at rest in SQLite with SHA-256 hashes for lookup

### Signal Setup Steps

#### 1. Environment Variables

The Signal sidecar and environment variables are already configured in `docker-compose.yml`. Add the phone number to `.env`:

```env
SIGNAL_PHONE_NUMBER=+1234567890
```

#### 2. Start Services

```bash
docker compose up -d
```

The `signal-api` sidecar will start with a health check. The backend waits for it to be healthy before starting.

#### 3. Register the App's Signal Number

Before users can link, register the app's dedicated Signal number:

```bash
# Register (replace +1234567890 with your dedicated number)
docker compose exec signal-api curl -s -X POST "http://localhost:8080/v1/register/+1234567890"

# Complete verification with the SMS code you receive
docker compose exec signal-api curl -s -X POST "http://localhost:8080/v1/register/+1234567890/verify/123456"
```

#### 4. Link Your Signal Account

1. Open the app → **Settings** → **Signal Connection**
2. Click **Connect Signal** — a QR code appears
3. On your phone: **Signal → Settings → Linked Devices → "+" → Scan QR code**
4. The status updates to "Connected" with your masked phone number

#### 5. Test the Integration

- **Outbound**: Send a message in app chat → receive it on Signal within 30 seconds
- **Inbound**: Reply from Signal → message appears in app chat and AI responds
- **Project routing**: Prefix a Signal message with `#project-name` to route to a specific project
- **Preferences**: In Settings, choose which messages to receive (All, Actions Only, Confirmations Only, None)
- **Disconnect**: Click Disconnect in Settings → no more Signal messages

---

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
python3 -m venv .venv
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
| `DATABASE_PATH` | No | `/app/data/settings.db` | SQLite database file path (map to Docker volume for persistence) |
| `AI_PROVIDER` | No | `copilot` | AI provider: `copilot` (GitHub Copilot via OAuth) or `azure_openai` |
| `COPILOT_MODEL` | No | `gpt-4o` | Model for Copilot completion provider |
| `AZURE_OPENAI_ENDPOINT` | No | — | Azure OpenAI endpoint URL (only when `AI_PROVIDER=azure_openai`) |
| `AZURE_OPENAI_KEY` | No | — | Azure OpenAI API key (only when `AI_PROVIDER=azure_openai`) |
| `AZURE_OPENAI_DEPLOYMENT` | No | `gpt-4` | Azure OpenAI deployment name |
| `GITHUB_WEBHOOK_SECRET` | No | — | Secret for webhook signature verification |
| `GITHUB_WEBHOOK_TOKEN` | No | — | GitHub PAT (classic) for webhook operations |
| `DEFAULT_REPOSITORY` | No | — | Default repo for issue creation (`owner/repo`) |
| `DEFAULT_ASSIGNEE` | No | `""` | Default assignee for In Progress issues |
| `COPILOT_POLLING_INTERVAL` | No | `60` | Polling interval in seconds |
| `FRONTEND_URL` | No | `http://localhost:5173` | Frontend URL for OAuth redirects |
| `CORS_ORIGINS` | No | `http://localhost:5173` | Allowed CORS origins (comma-separated) |
| `SIGNAL_API_URL` | No | `http://signal-api:8080` | URL of the signal-cli-rest-api sidecar |
| `SIGNAL_PHONE_NUMBER` | No | — | Dedicated Signal phone number (E.164 format, e.g. `+1234567890`) |
| `DEBUG` | No | `false` | Enable debug mode (API docs, dev-login) |
| `CACHE_TTL_SECONDS` | No | `300` | In-memory cache TTL in seconds |
| `HOST` | No | `0.0.0.0` | Server host |
| `PORT` | No | `8000` | Server port |
| `SESSION_CLEANUP_INTERVAL` | No | `3600` | Interval in seconds for cleaning up expired sessions |

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
| GET | `/api/v1/board/projects/{project_id}` | Get board data (columns + items) |

### Chat
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/chat/messages` | Get chat messages for session |
| POST | `/api/v1/chat/messages` | Send message, get AI response (supports `#agent` command) |
| DELETE | `/api/v1/chat/messages` | Clear chat history |
| POST | `/api/v1/chat/proposals/{id}/confirm` | Confirm task proposal |
| DELETE | `/api/v1/chat/proposals/{id}` | Cancel task proposal |

> **`#agent` command:** Send `#agent <description> #<status-name>` via chat or Signal to start the guided agent creation flow. The system parses the command, resolves the status column (fuzzy matching), generates an AI preview, and on confirmation executes an 8-step pipeline (save config → create column → create issue → create branch → commit files → open PR → move to In Review → update pipeline mappings).

### Tasks
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/tasks` | Create a task (GitHub Issue + project attachment) |
| PATCH | `/api/v1/tasks/{id}/status` | Update task status |

### Settings
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/settings/user` | Get effective user settings (preferences + defaults) |
| PUT | `/api/v1/settings/user` | Update user preferences |
| GET | `/api/v1/settings/global` | Get global settings |
| PUT | `/api/v1/settings/global` | Update global settings |
| GET | `/api/v1/settings/project/{project_id}` | Get effective project settings |
| PUT | `/api/v1/settings/project/{project_id}` | Update project-specific settings |

### Workflow & Pipeline
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/workflow/recommendations/{id}/confirm` | Confirm issue recommendation → full workflow |
| POST | `/api/v1/workflow/recommendations/{id}/reject` | Reject recommendation |
| POST | `/api/v1/workflow/pipeline/{issue_number}/retry` | Retry a failed/stalled agent assignment |
| GET | `/api/v1/workflow/config` | Get workflow configuration |
| PUT | `/api/v1/workflow/config` | Update workflow configuration |
| GET | `/api/v1/workflow/agents` | List available agents (discovered from repo + built-in) |
| GET | `/api/v1/workflow/transitions` | Get transition audit log |
| GET | `/api/v1/workflow/pipeline-states` | Get all active pipeline states |
| GET | `/api/v1/workflow/pipeline-states/{issue_number}` | Get pipeline state for specific issue |
| POST | `/api/v1/workflow/notify/in-review` | Send In Review notification |
| GET | `/api/v1/workflow/polling/status` | Get polling service status |
| POST | `/api/v1/workflow/polling/start` | Start background polling |
| POST | `/api/v1/workflow/polling/stop` | Stop background polling |
| POST | `/api/v1/workflow/polling/check-issue/{issue_number}` | Manually check a specific issue |
| POST | `/api/v1/workflow/polling/check-all` | Check all In Progress issues |

### Signal
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/signal/connection` | Get Signal connection status |
| POST | `/api/v1/signal/connection/link` | Generate QR code for linking |
| GET | `/api/v1/signal/connection/link/status` | Poll link completion status |
| DELETE | `/api/v1/signal/connection` | Disconnect Signal account |
| GET | `/api/v1/signal/preferences` | Get notification preferences |
| PUT | `/api/v1/signal/preferences` | Update notification preferences |
| GET | `/api/v1/signal/banners` | Get active conflict banners |
| POST | `/api/v1/signal/banners/{id}/dismiss` | Dismiss a conflict banner |

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
│   │   ├── api/              # API route handlers (9 modules)
│   │   │   ├── auth.py       #   OAuth flow, sessions, dev-login
│   │   │   ├── board.py      #   Project board (Kanban columns + items)
│   │   │   ├── chat.py       #   Chat messages, proposals, confirm/reject
│   │   │   ├── projects.py   #   Project selection, tasks, WebSocket, SSE
│   │   │   ├── settings.py   #   User, global, and project settings
│   │   │   ├── signal.py     #   Signal connection, preferences, banners
│   │   │   ├── tasks.py      #   Task CRUD
│   │   │   ├── workflow.py   #   Workflow config, pipeline, polling control
│   │   │   └── webhooks.py   #   GitHub webhook handler
│   │   ├── migrations/       # SQL schema migrations (auto-run at startup)
│   │   │   ├── 001_initial_schema.sql
│   │   │   ├── 002_add_workflow_config_column.sql
│   │   │   ├── 003_add_admin_column.sql
│   │   │   ├── 004_add_signal_tables.sql
│   │   │   ├── 005_signal_phone_hash_unique.sql
│   │   │   ├── 006_add_mcp_configurations.sql
│   │   │   └── 007_agent_configs.sql
│   │   ├── models/           # Pydantic v2 data models (9 modules)
│   │   │   ├── agent.py      #   AgentSource, AgentAssignment, AvailableAgent
│   │   │   ├── agent_creator.py  # CreationStep, AgentPreview, AgentCreationState
│   │   │   ├── board.py      #   Board columns, items, custom fields
│   │   │   ├── chat.py       #   ChatMessage, SenderType, ActionType
│   │   │   ├── project.py    #   GitHubProject, StatusColumn
│   │   │   ├── recommendation.py  # AITaskProposal, IssueRecommendation, labels
│   │   │   ├── settings.py   #   User preferences, global/project settings
│   │   │   ├── signal.py     #   Signal connection, message, banner models
│   │   │   ├── task.py       #   Task / project item
│   │   │   ├── user.py       #   UserSession
│   │   │   └── workflow.py   #   WorkflowConfiguration, WorkflowTransition
│   │   ├── services/         # Business logic layer
│   │   │   ├── github_projects/         # GitHub API package (decomposed)
│   │   │   │   ├── service.py           #   GitHubProjectsService, shared httpx.AsyncClient
│   │   │   │   └── graphql.py           #   GraphQL queries and mutations
│   │   │   ├── copilot_polling/         # Background polling package (decomposed)
│   │   │   │   ├── state.py             #   Module-level mutable state
│   │   │   │   ├── helpers.py           #   Sub-issue lookup, tracking helpers
│   │   │   │   ├── polling_loop.py      #   Start/stop/tick scheduling
│   │   │   │   ├── agent_output.py      #   Agent output extraction and posting
│   │   │   │   ├── pipeline.py          #   Pipeline advancement and transitions
│   │   │   │   ├── recovery.py          #   Stalled issue recovery, cooldowns
│   │   │   │   └── completion.py        #   PR completion detection (main + child)
│   │   │   ├── workflow_orchestrator/   # Pipeline orchestration package (decomposed)
│   │   │   │   ├── models.py            #   WorkflowContext, PipelineState, WorkflowState
│   │   │   │   ├── config.py            #   Async config load/persist/defaults/dedup
│   │   │   │   ├── transitions.py       #   Status transitions, branch tracking
│   │   │   │   └── orchestrator.py      #   WorkflowOrchestrator class
│   │   │   ├── agent_creator.py         #   #agent command: guided agent creation flow
│   │   │   ├── ai_agent.py             #   AI issue generation (via CompletionProvider)
│   │   │   ├── agent_tracking.py       #   Agent pipeline tracking (issue body markdown)
│   │   │   ├── cache.py                #   In-memory TTL cache
│   │   │   ├── completion_providers.py #   Pluggable LLM providers (Copilot / Azure)
│   │   │   ├── database.py            #   aiosqlite connection, WAL mode, migrations
│   │   │   ├── github_auth.py         #   OAuth token exchange
│   │   │   ├── session_store.py       #   Session CRUD (async SQLite)
│   │   │   ├── settings_store.py      #   Settings persistence (async SQLite)
│   │   │   ├── signal_bridge.py       #   Signal HTTP client, DB helpers, WS listener
│   │   │   ├── signal_delivery.py     #   Outbound Signal formatting & retry delivery
│   │   │   └── websocket.py           #   WebSocket connection manager
│   │   ├── prompts/          # AI prompt templates
│   │   │   ├── issue_generation.py    #   System/user prompts for issue creation
│   │   │   └── task_generation.py     #   Task generation prompts
│   │   ├── config.py         # Pydantic Settings from env / .env
│   │   ├── constants.py      # Status names, agent mappings, display names
│   │   ├── dependencies.py   # FastAPI DI helpers (app.state singletons)
│   │   ├── exceptions.py     # Custom exception classes (AppException tree)
│   │   ├── main.py           # FastAPI app factory, lifespan, CORS
│   │   └── utils.py          # Shared helpers (utcnow, resolve_repository)
│   ├── tests/
│   │   ├── unit/             # 42 unit test files
│   │   ├── integration/      # Integration tests
│   │   ├── test_api_e2e.py   # API end-to-end tests
│   │   └── conftest.py       # Test fixtures
│   └── pyproject.toml        # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── auth/         # LoginButton
│   │   │   ├── board/        # ProjectBoard, BoardColumn, IssueCard,
│   │   │   │                 # IssueDetailModal, AgentPresetSelector,
│   │   │   │                 # AgentConfigRow, AgentColumnCell, AgentTile,
│   │   │   │                 # AgentSaveBar, AddAgentPopover, colorUtils
│   │   │   ├── chat/         # ChatInterface, MessageBubble, TaskPreview,
│   │   │   │                 # StatusChangePreview, IssueRecommendationPreview
│   │   │   ├── common/       # ErrorBoundary (React class + TanStack integration)
│   │   │   ├── settings/     # AIPreferences, DisplayPreferences,
│   │   │   │                 # WorkflowDefaults, NotificationPreferences,
│   │   │   │                 # ProjectSettings, GlobalSettings, SettingsSection,
│   │   │   │                 # SignalConnection
│   │   │   └── sidebar/      # ProjectSidebar, ProjectSelector, TaskCard
│   │   ├── hooks/            # useAuth, useChat, useProjects, useWorkflow,
│   │   │                     # useRealTimeSync, useProjectBoard, useAppTheme,
│   │   │                     # useAgentConfig, useSettings, useSettingsForm
│   │   ├── pages/            # ProjectBoardPage, SettingsPage
│   │   ├── services/         # API client (api.ts)
│   │   ├── utils/            # generateId, formatTime
│   │   ├── types/            # TypeScript type definitions (index.ts)
│   │   └── constants.ts      # Named timing/polling/cache constants
│   ├── e2e/                  # Playwright E2E tests
│   ├── package.json
│   ├── vite.config.ts
│   ├── vitest.config.ts
│   └── playwright.config.ts
├── scripts/                  # Development tooling
│   ├── pre-commit            # Git pre-commit hook (ruff, pyright, eslint, tsc, vitest, build)
│   └── setup-hooks.sh        # Install git hooks
└── specs/                    # Feature specifications (Spec Kit output)
    ├── 001-custom-agent-creation/
    ├── 001-codebase-cleanup-refactor/
    ├── 007-codebase-cleanup-refactor/
    ├── 008-test-coverage-bug-fixes/
    ├── 009-codebase-cleanup-refactor/
    └── 011-signal-chat-integration/
```

---

## Tech Stack

### Backend
| Technology | Version | Purpose |
|---|---|---|
| Python | ≥ 3.11 | Runtime |
| FastAPI | ≥ 0.109 | Web framework |
| Pydantic | ≥ 2.5 | Data validation (v2 with `model_config`) |
| pydantic-settings | ≥ 2.1 | Environment configuration |
| httpx | ≥ 0.26 | Shared async HTTP client (GitHub API) |
| aiosqlite | — | Fully async SQLite (WAL mode) |
| uvicorn | ≥ 0.27 | ASGI server |

### Frontend
| Technology | Version | Purpose |
|---|---|---|
| React | 18.x | UI framework |
| TypeScript | ~5.4 | Type safety |
| Vite | 5.x | Build tool & dev server |
| TanStack Query | v5 | Server state management |
| dnd-kit | 6.x / 9.x / 10.x | Drag-and-drop (agent config) |
| socket.io-client | 4.x | WebSocket real-time sync |

### Testing
| Tool | Scope | Tests |
|---|---|---|
| pytest + pytest-asyncio | Backend unit/integration/e2e | 1086+ tests across 42 files |
| Vitest + React Testing Library | Frontend unit | 75+ tests across 9 files |
| Playwright | Frontend E2E | 3 spec files |

### Infrastructure
| Component | Details |
|---|---|
| Docker Compose | 3 services: `ghchat-backend` (port 8000) + `ghchat-frontend` (nginx, port 5173 → 80) + `ghchat-signal-api` (signal-cli sidecar) |
| SQLite | WAL mode, auto-migrated schema (7 migrations), `ghchat-data` Docker volume |
| nginx | Frontend static serving + reverse proxy to backend `/api` |
| signal-cli-rest-api | Sidecar for Signal protocol, json-rpc mode, `signal-cli-config` Docker volume |

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

**AI issue generation fails (Copilot provider):**
- The Copilot provider uses your GitHub OAuth token — ensure you're logged in
- Verify you have an active [GitHub Copilot subscription](https://github.com/features/copilot)
- If response is truncated, the system automatically repairs partial JSON
- Check backend logs for `CopilotClient` errors

**AI issue generation fails (Azure OpenAI provider):**
- Ensure `AI_PROVIDER=azure_openai` is set
- Verify `AZURE_OPENAI_ENDPOINT` format: `https://your-resource.openai.azure.com`
- Check `AZURE_OPENAI_KEY` is correct
- Ensure the deployment name matches your Azure configuration

**Agent pipeline not advancing:**
- Verify the polling service is running: `GET /api/v1/workflow/polling/status`
- Check that your GitHub Project has the required status columns: Backlog, Ready, In Progress, In Review
- Note: status names are matched case-insensitively, so "In progress" and "In Progress" both work
- Review backend logs for agent assignment errors: `docker compose logs -f backend`
- Manually trigger a check: `POST /api/v1/workflow/polling/check-all`
- Check pipeline state for a specific issue: `GET /api/v1/workflow/pipeline-states/{issue_number}`
- If the pipeline advances too quickly (multiple agents assigned simultaneously), ensure you're on the latest version — an earlier bug caused `PipelineState(agents=[])` to be seen as complete immediately

**Workflow configuration lost after restart:**
- Workflow config is persisted to SQLite. Verify the database volume is mounted: check `docker-compose.yml` for the `data/` volume
- Check that `DATABASE_PATH` env var points to a persistent location (default: `data/settings.db`)
- If migrating from an older version, the system auto-backfills the `workflow_config` column from legacy `agent_pipeline_mappings` data
- Check logs for `Loaded workflow config from DB` or `Failed to load workflow config from DB` messages

**Agent pipeline configuration not saving / wrong agents used:**
- Pipeline mappings are stored per-user in the `project_settings` table. The Settings UI writes to the user's own row and syncs to the canonical `__workflow__` row.
- If you see duplicate or empty status entries (e.g., both "In Progress" and "In progress"), the backend now deduplicates case-variant keys automatically on save.
- Verify the pipeline config via `GET /api/v1/workflow/config` and check the `agent_mappings` field.
- Check that the frontend hook (`useAgentConfig`) is deduplicating on load — clear browser cache if you see stale data.

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

**Multiple PRs created for one issue (duplicate agent trigger):**
- This was caused by the polling service fighting Copilot's natural status changes. When Copilot starts working, it moves issues to "In Progress". The system now **accepts this status change** and updates the pipeline state rather than reverting it. Ensure you're on the latest version.
- The first PR's branch becomes the "main branch" for the issue — subsequent child PRs from other agents are expected behavior.

**Webhook not triggering:**
- Verify `GITHUB_WEBHOOK_SECRET` matches the secret in GitHub webhook settings
- Check `GITHUB_WEBHOOK_TOKEN` has `repo` and `project` scopes
- Ensure webhook is configured for "Pull requests" events
- Check webhook delivery logs in GitHub: Repo → Settings → Webhooks → Recent Deliveries

**Signal QR code not appearing / connection fails:**
- Ensure the `signal-api` container is healthy: `docker compose ps` should show `healthy`
- Verify `SIGNAL_PHONE_NUMBER` is set and registered: `docker compose exec signal-api curl http://localhost:8080/v1/accounts`
- Check backend logs for signal_bridge errors: `docker compose logs -f backend | grep signal`
- If the number isn't registered yet, follow the registration steps in the Signal setup section

**Signal messages not being delivered:**
- Verify the user has an active connection: check Settings → Signal Connection shows "Connected"
- Check notification preferences aren't set to "None"
- Review the `signal_messages` table for delivery status: `failed` entries indicate retry exhaustion
- Check backend logs for tenacity retry warnings: `docker compose logs -f backend | grep delivery`
- Ensure the signal-api sidecar can reach Signal servers (not blocked by firewall)

**Signal inbound messages not appearing in chat:**
- Verify the WebSocket listener started: check backend startup logs for `Signal WS listener started`
- Ensure the sender's phone number is linked to an account (unlinked numbers get an auto-reply)
- Check that the user has an active project selected (the message routes to `last_active_project_id`)
- Media/attachment messages are not supported — sender receives an auto-reply

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
