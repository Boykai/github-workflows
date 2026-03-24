# Agent Pipeline

Agent Pipelines are the heart of Solune — the engine that turns a feature description into working code through a choreographed sequence of AI agents. Each pipeline is a customizable plan where you choose which agents run, in what order, and whether they execute in series or parallel.

## Quick Concept

- A pipeline is a sequence of **stages**, each assigned to one or more AI agents
- Agents can run in **series** (one after another) or **parallel** (concurrently within a group)
- Each agent creates a **sub-issue**, branches from the main PR, and merges back when done
- The pipeline is tracked with a durable **markdown table** in the GitHub Issue body — visible directly on GitHub and survives server restarts

### Creating Your First Pipeline

Open the **Agents Pipelines** page in Solune, drag agents from the sidebar into execution stages, choose series or parallel mode for each group, and click **Launch**. The built-in **Spec Kit** preset is a great starting point — or create a blank pipeline and compose your own agent combinations.

## Overview

Agent Pipelines are customizable execution plans that orchestrate AI Custom GitHub Agents to perform remote work in series or parallel. Through the visual pipeline GUI, you compose any combination of agents into stages, assign AI models, and choose execution modes (series or parallel). When a pipeline is launched, the system creates a GitHub Issue, attaches it to a **GitHub Project** board, and executes each agent stage automatically — advancing the issue across board columns as agents complete their work.

Pipelines are not limited to any single agent set. The **Spec Kit** preset ships as a default (`specify` → `plan` → `tasks` → `implement` → `review`), but you can create pipelines with entirely custom agents, different stage counts, and mixed series/parallel execution groups.

## Pipeline Flow

```text
User describes feature     →   AI generates Issue (Copilot SDK or Azure OpenAI)
User clicks Confirm        →   GitHub Issue + sub-issues created, added to Project
                               Status: 📋 Backlog

  ┌───────────────── CUSTOMIZABLE AGENT PIPELINE ────────────────┐
  │                                                              │
  │  Stage 1 (series)   ── Agent A  ──▶ output files              │
  │       │              Creates first PR (= main branch)         │
  │       ▼                                                      │
  │  Stage 2 (parallel) ─┬ Agent B  ──▶ output files              │
  │                      └ Agent C  ──▶ output files              │
  │       │              Child PRs merged + branches deleted      │
  │       ▼                                                      │
  │  Stage 3 (series)   ── Agent D  ──▶ code changes             │
  │       │              Child PR merged + branch deleted         │
  │       ▼                                                      │
  │  Review             ── Copilot code review requested          │
  │                      Main PR ready for human review           │
  └──────────────────────────────────────────────────────────────┘
```

Agents in the diagram are placeholders — replace them with any agents from your repository’s `.github/agents/` directory or from preset configurations.

## Status Transitions

The pipeline advances issues through GitHub Project board columns. The exact agents in each status depend on your pipeline configuration. Using the default **Spec Kit** preset as an example:

| Status | Agent(s) | What Happens | Transition Trigger |
|--------|----------|--------------|-------------------|
| 📋 **Backlog** | First stage agent (e.g. `speckit.specify`) | Sub-issue created, agent assigned; creates first PR (establishes main branch); sub-issue closed on completion | `<agent>: Done!` on sub-issue |
| 📝 **Ready** | Middle stage agents (e.g. `speckit.plan` → `speckit.tasks`) | Sequential or parallel: each agent gets its sub-issue, branches from main branch, child PR merged + deleted, sub-issue closed | All agents in group post `Done!` markers |
| 🔄 **In Progress** | Implementation agent (e.g. `speckit.implement`) | Agent branches from main, implements code, child PR merged + deleted, main PR converted from draft to ready | Child PR completion detected via timeline events or PR no longer draft |
| 👀 **In Review** | `copilot-review` | **Not a coding agent.** The pipeline calls the GitHub API to request a Copilot code review directly on the parent issue's **main branch PR**. The `copilot-review` sub-issue is a tracking issue only — Copilot is **never** assigned to it as a coding agent. Sub-issue closed when review completes. | Manual merge |
| ✅ **Done** | — | Work merged | Manual or webhook on PR merge |

Custom pipelines can map any agents to any board column. The status names correspond to columns on your GitHub Project board.

## Built-in Agents (Spec Kit Preset)

The **Spec Kit** preset ships with these agents, defined in `.github/agents/*.agent.md`:

| Agent | Purpose | Output Files |
|-------|---------|-------------|
| `speckit.specify` | Feature specification from issue description | `spec.md`, `checklists/requirements.md` |
| `speckit.plan` | Implementation plan with research and data model | `plan.md`, `research.md`, `data-model.md`, `contracts/*`, `quickstart.md` |
| `speckit.tasks` | Actionable, dependency-ordered task breakdown | `tasks.md` |
| `speckit.implement` | Code implementation following `tasks.md` | Code files |
| `speckit.clarify` | Asks clarification questions, updates spec | Updates `spec.md` |
| `speckit.analyze` | Read-only cross-artifact consistency analysis | Analysis report in the agent response only (no committed files) |
| `speckit.checklist` | Quality checklists | `checklists/*.md` |
| `speckit.constitution` | Project constitution management | `.specify/memory/constitution.md` |
| `speckit.taskstoissues` | Converts `tasks.md` entries into GitHub Issues | GitHub Issues |

Custom agents can be added to `.github/agents/` and will appear in the pipeline GUI for drag-and-drop composition. See [Custom Agents Best Practices](custom-agents-best-practices.md) for guidance on creating your own.

## Sub-Issue-Per-Agent Workflow

When an issue is confirmed, the system creates **sub-issues upfront** for every agent in the pipeline:

- Each sub-issue is titled `[agent-name] Parent Title`
- Sub-issues are added to the same GitHub Project
- Copilot is assigned to the sub-issue (not the parent) — **except for `copilot-review`** (see below)
- Agent `.md` file outputs are posted as comments on the **sub-issue**; read-only agents such as `speckit.analyze` return their analysis in the agent response instead and do not commit branch changes
- The `<agent>: Done!` marker is posted on the **parent issue** to advance the pipeline
- When an agent completes, its sub-issue is closed as completed (`state=closed`, `state_reason=completed`)

> **`copilot-review` is a special-case agent.** It does NOT assign Copilot to the sub-issue as a coding task. Instead, the pipeline directly requests a Copilot code review on the **parent issue’s main branch PR** (the branch created by the first agent and merged into by all subsequent agents) via the GitHub GraphQL API. The sub-issue is a tracking issue only — it is marked active when the review is requested and closed when the review completes.

Label lifecycle: created with `ai-generated` + `sub-issue` → `in-progress` added on assignment → `done` added + `in-progress` removed on completion.

## Hierarchical PR Branching

```text
main (repo default)
  └── feature/issue-42-my-feature        ← first agent creates this (= main branch)
       ├── copilot/issue-42-<agent-b>      ← second agent branches from main branch
       │     └── (squash-merged back, branch deleted)
       ├── copilot/issue-42-<agent-c>      ← third agent branches from main branch
       │     └── (squash-merged back, branch deleted)
       └── copilot/issue-42-<agent-d>      ← fourth agent branches from main branch
             └── (squash-merged back, branch deleted)
```

- The **first PR** created for an issue establishes the "main branch" for that issue
- All subsequent agents branch FROM and merge INTO this main branch
- Child branches are automatically deleted after their PRs are squash-merged
- By the time the issue reaches In Review, the main PR contains all agent work consolidated

## Launch from Imported Issue

In addition to the chat-driven flow ("describe feature → confirm proposal"), the **Projects page** offers a direct launch path:

1. **Paste or upload** a GitHub Parent Issue description (Markdown or `.md`/`.txt` file) into the `ProjectIssueLaunchPanel`.
2. **Select an Agent Pipeline Config** from the saved pipelines dropdown.
3. Click **Launch pipeline**.

The backend `POST /api/v1/pipelines/{project_id}/launch` endpoint then:

- Derives an issue title from the first Markdown heading or opening line.
- Creates a new GitHub Issue with the uploaded body (plus the agent tracking table).
- Adds the issue to the project board and applies the `ai-generated` label.
- Creates sub-issues for each agent in the selected pipeline.
- Activates the first agent automatically.

This flow reuses the same sub-issue-per-agent workflow, polling service, and hierarchical PR branching described above — the only difference is that issue text is imported directly rather than generated by the AI completion provider.

## Pipeline Tracking

Each issue maintains a durable **tracking table** in its body, visible directly on the GitHub Issue:

```markdown
## 🤖 Agent Pipeline

| # | Status | Agent | State |
|---|--------|-------|-------|
| 1 | Backlog | `agent-a` | ✅ Done |
| 2 | Ready | `agent-b` | ✅ Done |
| 3 | Ready | `agent-c` | 🔄 Active |
| 4 | In Progress | `agent-d` | ⏳ Pending |
| 5 | In Review | `copilot-review` | ⏳ Pending |
```

States: **⏳ Pending** (not started), **🔄 Active** (assigned to Copilot), **✅ Done** (completed).

This table survives server restarts and provides visibility into pipeline progress directly on GitHub.

### Group-Aware Tracking Table

Pipelines that use **execution groups** display a 6-column tracking table with an additional `Group` column:

```markdown
## 🤖 Agent Pipeline

| # | Group | Status | Agent | Model | State |
|---|-------|--------|-------|-------|-------|
| 1 | G1 (series) | Backlog | `agent-a` | gpt-4o | ✅ Done |
| 2 | G2 (parallel) | Ready | `agent-b` | gpt-4o | 🔄 Active |
| 3 | G2 (parallel) | Ready | `agent-c` | gpt-4o | 🔄 Active |
| 4 | G3 (series) | In Progress | `agent-d` | gpt-4o | ⏳ Pending |
| 5 | G4 (series) | In Review | `copilot-review` | gpt-4o | ⏳ Pending |
```

Groups numbered G1, G2, etc. execute sequentially (one group finishes before the next starts). Agents within a **parallel** group run concurrently. The `(series)` / `(parallel)` label indicates the execution mode.

## Pipeline Analytics

The **Pipeline Analytics** dashboard replaces the former Recent Activity section on the Agents Pipelines page. It provides four metrics:

1. **Agent Frequency** — How often each agent is used across pipeline runs
2. **Model Distribution** — Breakdown of AI models assigned to agents
3. **Execution Mode Breakdown** — Ratio of series vs. parallel execution groups
4. **Complexity Spotlight** — Highlights pipelines with the most stages or longest durations

## Polling Service

The background polling service runs every 60 seconds (configurable via `COPILOT_POLLING_INTERVAL`) and executes in order:

1. **Post Agent Outputs** — Detect completed PRs, merge child PRs, extract `.md` files, post to sub-issues, close sub-issues, update tracking table
2. **Check Backlog** — Scan for first-stage agent `Done!` markers → transition to next status, assign next agent(s)
3. **Check Ready** — Scan for middle-stage agent `Done!` markers → advance pipeline or transition to In Progress
4. **Check In Progress** — Detect implementation agent completion (timeline events or PR not draft) → merge, convert main PR, transition to In Review
5. **Check In Review** — Ensure Copilot code review has been requested
6. **Self-Healing Recovery** — Detect stalled pipelines, re-assign agents with per-issue cooldown (5 minutes)

### Agent Assignment

- Uses **retry with exponential backoff** (3 attempts: 3s → 6s → 12s) for transient GitHub API errors
- **Double-assignment prevention**: pending flags set BEFORE the API call, cleared only on failure
- **Copilot status acceptance**: when Copilot naturally moves issues to "In Progress", the polling service accepts it rather than reverting (which would re-trigger the agent)

### Implementation Agent Completion Flow

1. Child PR squash-merged into main branch
2. Child branch deleted
3. Main PR converted from draft to ready for review
4. Issue status updated to "In Review"
5. Copilot code review requested on the main PR

### copilot-review Step

The `copilot-review` step is a **non-coding** agent. It does NOT assign Copilot
to the sub-issue as a coding agent. Instead the pipeline:

1. Resolves the main PR for the parent issue (branch created by the first pipeline agent)
2. **Converts draft → ready for review** — GitHub does not allow requesting reviews
   on draft PRs, so the pipeline ensures the PR is marked ready first
3. Uses the GitHub REST API `POST /repos/{owner}/{repo}/pulls/{pr_number}/requested_reviewers`
   to add `copilot-pull-request-reviewer[bot]` as a requested reviewer (preferred path —
   does not consume the GraphQL rate limit)
4. If the REST call is unavailable or fails, falls back to the GitHub GraphQL
   `requestReviews` mutation with `botLogins: ["copilot-pull-request-reviewer"]`
   and the `GraphQL-Features: copilot_code_review` header
5. Marks the `[copilot-review]` sub-issue as "in-progress" (tracking only)
6. Sub-issue is closed when the review completes

The polling service's "Check In Review" step acts as a safety net: on each cycle
it verifies that Copilot has been requested as a reviewer for every "In Review"
issue, converting draft PRs and requesting reviews as needed.

## Pipeline Reconstruction

On server restart, the system reconstructs state from:

- The durable tracking table in issue bodies
- `Done!` markers from issue comments
- Sub-issue mappings from `[agent-name]` title prefixes
- Main branch discovery by scanning linked PRs

## Configuration

Agent-to-status mappings are fully customizable through the **pipeline GUI**, the Settings UI, or `PUT /api/v1/workflow/config`. The default **Spec Kit** preset ships with:

| Status | Default Agents |
|--------|---------------|
| Backlog | `speckit.specify` |
| Ready | `speckit.plan`, `speckit.tasks` |
| In Progress | `speckit.implement` |
| In Review | `copilot-review` |

You can replace these with any custom agents, add or remove stages, and configure execution groups (series or parallel) for each stage. Pipeline configurations are saved and reusable — select a saved pipeline when launching from the Projects page.

Mappings are persisted to SQLite with a 3-tier fallback: user-specific → canonical `__workflow__` row → any-user with automatic backfill. The Settings UI syncs changes to the canonical row and invalidates the in-memory config cache.

## GitHub Projects Integration

Agent Pipelines are fully integrated with **GitHub Projects**:

- Issues are automatically added to the selected GitHub Project board on pipeline launch
- Issue status (board column) advances as agents complete their stages
- Sub-issues appear on the same project board with `ai-generated` + `sub-issue` labels
- The durable tracking table is embedded directly in the GitHub Issue body, providing visibility without needing the Solune UI
- Pipeline progress is reflected in real-time on the Solune Kanban board, synced bidirectionally with GitHub Project columns

---

## What's next?

- [Custom Agents Best Practices](custom-agents-best-practices.md) — Create your own agents with custom prompts and tools
- [Architecture](architecture.md) — Understand how the pipeline engine fits into the overall system
- [Troubleshooting](troubleshooting.md) — Solutions to common pipeline issues
