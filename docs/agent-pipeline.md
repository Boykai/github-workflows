# Agent Pipeline

## Overview

The Spec Kit agent pipeline automates the journey from a feature idea to a code review. When a user confirms an issue proposal, the system creates a GitHub Issue, attaches it to a Project Board, and kicks off a sequential pipeline of custom GitHub Copilot agents.

## Pipeline Flow

```
User describes feature     →   AI generates Issue (Copilot SDK or Azure OpenAI)
User clicks Confirm        →   GitHub Issue + sub-issues created, added to Project
                               Status: 📋 Backlog

  ┌─────────────────── AUTOMATED AGENT PIPELINE ───────────────────┐
  │                                                                 │
  │  📋 Backlog ─── speckit.specify ──▶ spec.md                     │
  │       │         Creates first PR (= main branch for the issue)  │
  │       ▼                                                         │
  │  📝 Ready ─── speckit.plan ──▶ plan.md, research.md, data-model │
  │       │        Branches FROM main; child PR merged + deleted     │
  │       │                                                         │
  │       ├─── speckit.tasks ──▶ tasks.md                           │
  │       │     Branches FROM main; child PR merged + deleted        │
  │       ▼                                                         │
  │  🔄 In Progress ─── speckit.implement ──▶ Code changes          │
  │       │               Child PR merged + branch deleted           │
  │       ▼                                                         │
  │  👀 In Review ─── Main PR ready for human review                │
  │                    Copilot code review requested                 │
  └─────────────────────────────────────────────────────────────────┘
```

## Status Transitions

| Status | Agent(s) | What Happens | Transition Trigger |
|--------|----------|--------------|-------------------|
| 📋 **Backlog** | `speckit.specify` | Sub-issue created, agent assigned; creates first PR (establishes main branch) and writes `spec.md`; sub-issue closed on completion | `speckit.specify: Done!` on sub-issue |
| 📝 **Ready** | `speckit.plan` → `speckit.tasks` | Sequential: each agent gets its sub-issue, branches from main branch, child PR merged + deleted, sub-issue closed | Both agents post `Done!` markers |
| 🔄 **In Progress** | `speckit.implement` | Agent branches from main, implements code from `tasks.md`, child PR merged + deleted, main PR converted from draft to ready | Child PR completion detected via timeline events or PR no longer draft |
| 👀 **In Review** | `copilot-review` | **Not a coding agent.** The pipeline calls the GitHub API to request a Copilot code review directly on the parent issue's **main branch PR** (the branch established by `speckit.specify`). The `copilot-review` sub-issue is a tracking issue only — Copilot is **never** assigned to it as a coding agent. Sub-issue closed when review completes. | Manual merge |
| ✅ **Done** | — | Work merged | Manual or webhook on PR merge |

## Spec Kit Agents

Defined in `.github/agents/*.agent.md`:

| Agent | Purpose | Output Files |
|-------|---------|-------------|
| `speckit.specify` | Feature specification from issue description | `spec.md`, `checklists/requirements.md` |
| `speckit.plan` | Implementation plan with research and data model | `plan.md`, `research.md`, `data-model.md`, `contracts/*`, `quickstart.md` |
| `speckit.tasks` | Actionable, dependency-ordered task breakdown | `tasks.md` |
| `speckit.implement` | Code implementation following `tasks.md` | Code files |
| `speckit.clarify` | Asks clarification questions, updates spec | Updates `spec.md` |
| `speckit.analyze` | Read-only cross-artifact consistency analysis | Analysis report |
| `speckit.checklist` | Quality checklists | `checklists/*.md` |
| `speckit.constitution` | Project constitution management | `.specify/memory/constitution.md` |
| `speckit.taskstoissues` | Converts `tasks.md` entries into GitHub Issues | GitHub Issues |

## Sub-Issue-Per-Agent Workflow

When an issue is confirmed, the system creates **sub-issues upfront** for every agent in the pipeline:

- Each sub-issue is titled `[agent-name] Parent Title`
- Sub-issues are added to the same GitHub Project
- Copilot is assigned to the sub-issue (not the parent) — **except for `copilot-review`** (see below)
- Agent `.md` file outputs are posted as comments on the **sub-issue**
- The `<agent>: Done!` marker is posted on the **parent issue** to advance the pipeline
- When an agent completes, its sub-issue is closed as completed (`state=closed`, `state_reason=completed`)

> **`copilot-review` is a special-case agent.** It does NOT assign Copilot to the sub-issue as a coding task. Instead, the pipeline directly requests a Copilot code review on the **parent issue's main branch PR** (the branch created by `speckit.specify` and merged into by all subsequent agents) via the GitHub GraphQL API. The sub-issue is a tracking issue only — it is marked active when the review is requested and closed when the review completes.

Label lifecycle: created with `ai-generated` + `sub-issue` → `in-progress` added on assignment → `done` added + `in-progress` removed on completion.

## Hierarchical PR Branching

```
main (repo default)
  └── feature/issue-42-my-feature        ← speckit.specify creates this (= main branch)
       ├── copilot/issue-42-plan         ← speckit.plan branches from main branch
       │     └── (squash-merged back, branch deleted)
       ├── copilot/issue-42-tasks        ← speckit.tasks branches from main branch
       │     └── (squash-merged back, branch deleted)
       └── copilot/issue-42-implement    ← speckit.implement branches from main branch
             └── (squash-merged back, branch deleted)
```

- The **first PR** created for an issue establishes the "main branch" for that issue
- All subsequent agents branch FROM and merge INTO this main branch
- Child branches are automatically deleted after their PRs are squash-merged
- By the time the issue reaches In Review, the main PR contains all agent work consolidated

## Pipeline Tracking

Each issue maintains a durable **tracking table** in its body:

```markdown
## 🤖 Agent Pipeline

| # | Status | Agent | State |
|---|--------|-------|-------|
| 1 | Backlog | `speckit.specify` | ✅ Done |
| 2 | Ready | `speckit.plan` | ✅ Done |
| 3 | Ready | `speckit.tasks` | 🔄 Active |
| 4 | In Progress | `speckit.implement` | ⏳ Pending |
| 5 | In Review | `copilot-review` | ⏳ Pending |
```

States: **⏳ Pending** (not started), **🔄 Active** (assigned to Copilot), **✅ Done** (completed).

This table survives server restarts and provides visibility directly on the GitHub Issue.

## Polling Service

The background polling service runs every 60 seconds (configurable via `COPILOT_POLLING_INTERVAL`) and executes in order:

1. **Post Agent Outputs** — Detect completed PRs, merge child PRs, extract `.md` files, post to sub-issues, close sub-issues, update tracking table
2. **Check Backlog** — Scan for `speckit.specify: Done!` → transition to Ready, assign `speckit.plan`
3. **Check Ready** — Scan for `speckit.plan: Done!` / `speckit.tasks: Done!` → advance or transition to In Progress
4. **Check In Progress** — Detect `speckit.implement` completion (timeline events or PR not draft) → merge, convert main PR, transition to In Review
5. **Check In Review** — Ensure Copilot code review has been requested
6. **Self-Healing Recovery** — Detect stalled pipelines, re-assign agents with per-issue cooldown (5 minutes)

### Agent Assignment

- Uses **retry with exponential backoff** (3 attempts: 3s → 6s → 12s) for transient GitHub API errors
- **Double-assignment prevention**: pending flags set BEFORE the API call, cleared only on failure
- **Copilot status acceptance**: when Copilot naturally moves issues to "In Progress", the polling service accepts it rather than reverting (which would re-trigger the agent)

### speckit.implement Completion Flow

1. Child PR squash-merged into main branch
2. Child branch deleted
3. Main PR converted from draft to ready for review
4. Issue status updated to "In Review"
5. Copilot code review requested on the main PR

### copilot-review Step

The `copilot-review` step is a **non-coding** agent. It does NOT assign Copilot
to the sub-issue as a coding agent. Instead the pipeline:

1. Resolves the main PR for the parent issue (branch created by `speckit.specify`)
2. **Converts draft → ready for review** — GitHub does not allow requesting reviews
   on draft PRs, so the pipeline ensures the PR is marked ready first
3. Calls the GitHub GraphQL `requestReviewsByLogin` mutation with `botLogins: ["copilot"]`
   (and the `GraphQL-Features: copilot_code_review` header) to request a Copilot code review
4. Marks the `[copilot-review]` sub-issue as "in-progress" (tracking only)
5. Sub-issue is closed when the review completes

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

Agent-to-status mappings are configurable per user via the Settings UI:

| Status | Default Agents |
|--------|---------------|
| Backlog | `speckit.specify` |
| Ready | `speckit.plan`, `speckit.tasks` |
| In Progress | `speckit.implement` |
| In Review | `copilot-review` |

Mappings are persisted to SQLite with a 3-tier fallback: user-specific → canonical `__workflow__` row → any-user with automatic backfill. The Settings UI syncs changes to the canonical row and invalidates the in-memory config cache.
