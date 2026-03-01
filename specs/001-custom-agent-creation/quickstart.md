# Quickstart: Custom Agent Creation via Chat (#agent)

**Feature**: 001-custom-agent-creation  
**Date**: 2026-02-28

## What This Feature Does

Allows admin users to create custom GitHub agents through a guided chat conversation. Type `#agent <description> #<status-name>` in either the in-app chat or Signal, and the system walks you through generating, previewing, and confirming an agent — then creates all the required artifacts automatically.

## Prerequisites

- An admin account (first authenticated user is auto-promoted)
- A selected GitHub project in the app (or specify via Signal)
- GitHub OAuth token with `repo` scope (existing auth flow provides this)

## Usage

### In-App Chat

1. Open the chat widget while viewing a project
2. Type: `#agent Reviews PRs for security vulnerabilities #in-review`
3. Review the generated preview (name, description, system prompt, tools)
4. Request edits if needed: "change the name to SecBot"
5. Confirm: "looks good" or "create"
6. Watch the status report as artifacts are created

### Via Signal

1. Send: `#agent Triages new issues #backlog`
2. If you have multiple projects, select from the numbered list
3. Same guided flow as in-app chat

## What Gets Created

Upon confirmation, the system creates (best-effort):

| Step | Artifact |
|------|----------|
| 1 | Agent configuration saved to database |
| 2 | GitHub Project column (if new status) |
| 3 | GitHub Issue with agent spec (labeled `agent-config`) |
| 4 | Branch: `agent/<agent-slug>` |
| 5 | Files: agent config YAML, prompt markdown, README entry |
| 6 | Pull Request referencing the issue |
| 7 | Issue moved to "In Review" on project board |

## Command Syntax

```
#agent <description> [#<status-name>]
```

- `<description>` — Natural language description of the agent's purpose (required)
- `#<status-name>` — Optional status column assignment (fuzzy-matched)

## Examples

```
#agent Reviews PRs for security vulnerabilities #in-review
#agent Triages new issues and adds labels #backlog
#agent Monitors CI failures and reports daily #in-progress
#agent Generates release notes from merged PRs
```

## Development Setup

### Backend

```bash
cd backend && source .venv/bin/activate

# Run tests for this feature
pytest tests/test_agent_creator.py -v

# Run all tests
pytest tests/ -q
```

### Key Files

| File | Action | Purpose |
|------|--------|---------|
| `backend/src/services/agent_creator.py` | New | Core orchestration service |
| `backend/src/models/agent_creator.py` | New | Pydantic models for state/preview/results |
| `backend/src/migrations/007_agent_configs.sql` | New | Database table for agent configs |
| `backend/src/services/ai_agent.py` | Modified | New `generate_agent_config()` method |
| `backend/src/services/github_projects/service.py` | Modified | New `create_branch()`, `commit_files()`, `create_pull_request()` |
| `backend/src/services/github_projects/graphql.py` | Modified | New GraphQL mutation constants |
| `backend/src/api/chat.py` | Modified | `#agent` command routing |
| `backend/src/services/signal_chat.py` | Modified | `#agent` command routing |
| `backend/tests/unit/test_agent_creator.py` | New | Unit tests |
