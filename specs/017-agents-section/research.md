# Research: Agents Section on Project Board

**Feature**: `017-agents-section` | **Date**: 2026-03-03

## Research Tasks

### R1: DRY Extraction Strategy for Agent Creation Logic

**Decision**: Extract shared pure functions from `agent_creator.py` into public module-level functions in the same file (make them non-private). Create a new shared `github_commit_workflow.py` module for the duplicated branch → commit → PR → issue workflow.

**Rationale**: The existing `agent_creator.py` contains 6 pure functions that are currently private (`_`-prefixed). The two highest-value candidates for reuse are `_generate_config_files()` and `_generate_issue_body()`. Rather than creating a separate helper file, making them public (removing the `_` prefix) is the simplest change and avoids import indirection. The GitHub commit workflow, duplicated between `agent_creator.py` (Steps 4-8, ~150 lines) and `chores/template_builder.py` (~65 lines), should be extracted into a shared module.

**Alternatives considered**:
- **New `agent_helpers.py` module**: Rejected — adds a new file when simply making functions public achieves the same result with less disruption.
- **Leave duplication in place**: Rejected — violates Constitution Principle V (Simplicity and DRY) and FR-006.
- **Full refactor of both callers to use shared workflow**: Keeps the scope bounded — only extract the workflow, don't refactor the Chores service in this feature.

### R2: Agent Listing — Merging SQLite and GitHub Repo Sources

**Decision**: The backend agents listing endpoint fetches from both sources in parallel and merges by slug. SQLite records include a `status` field derived from PR state. GitHub repo files (from the Contents API or tree endpoint) are marked as "Active". Deduplication: if a slug appears in both, the GitHub repo version takes precedence for content but SQLite metadata (issue/PR numbers) is preserved.

**Rationale**: SQLite is the local representation for agents whose PRs haven't merged yet. Once merged, the `.github/agents/` directory in the repo is the source of truth. Merging provides a complete view regardless of merge state.

**Alternatives considered**:
- **SQLite only**: Rejected — would miss agents created outside this app (manually, via `#agent` chat command on other machines, or by other team members).
- **GitHub repo only**: Rejected — wouldn't show agents with pending PRs.

### R3: Agent Deletion via PR

**Decision**: Deletion creates a branch that removes the two agent files (`.agent.md` and `.prompt.md`) and opens a PR. The commit uses the GitHub GraphQL `createCommitOnBranch` mutation with file deletions. A tracking issue is created for the deletion. The SQLite record is soft-removed (or marked for deletion) immediately.

**Rationale**: Following the same PR-based source-of-truth pattern as creation ensures all repository changes go through code review. The GitHub `createCommitOnBranch` mutation supports file deletions natively.

**Alternatives considered**:
- **Direct file deletion on default branch**: Rejected — bypasses code review workflow.
- **SQLite-only deletion**: Rejected per clarification — user explicitly requested PR-based deletion.

### R4: GitHub API for Reading Agent Files from Repository

**Decision**: Use the GitHub GraphQL API to read the repository tree and file contents for `.github/agents/*.agent.md`. The existing `github_projects_service` already has GraphQL infrastructure. A single `repository.object(expression: "HEAD:.github/agents")` query returns the directory listing, and individual file reads use `repository.object(expression: "HEAD:.github/agents/{name}")`.

**Rationale**: The GraphQL API is already used throughout the codebase. A tree query is efficient for listing files, and content queries are needed to parse YAML frontmatter for descriptions.

**Alternatives considered**:
- **REST Contents API**: Works but would be inconsistent with the codebase's GraphQL-first approach.
- **Git Trees API**: Lower-level, would require additional blob fetches for content.

### R5: Status Badge Logic

**Decision**: Agent status is determined by:
1. If the agent exists in the GitHub repo's default branch → "Active"
2. If the agent exists only in SQLite with a PR number → "Pending PR"
3. If merged agent has a pending deletion PR → "Pending Deletion"

**Rationale**: Three states cover the full lifecycle. The frontend displays a color-coded badge on each agent card.

**Alternatives considered**:
- **Two states only (Active/Pending)**: Simpler but doesn't distinguish deletion-in-progress.
- **PR state polling**: Too complex for initial implementation; status can be refreshed on page load.

### R6: Frontend Component Pattern

**Decision**: Mirror the exact Chores component structure:
- `AgentsPanel.tsx` — container (header, add button, list, empty/loading/error states)
- `AgentCard.tsx` — individual card (name, description, status badge, delete button)
- `AddAgentModal.tsx` — creation form (name input, content textarea, sparse detection → chat flow)
- `AgentChatFlow.tsx` — multi-turn AI refinement for sparse input

**Rationale**: Following the established Chores pattern ensures consistency, reduces learning curve, and leverages proven UI patterns.

**Alternatives considered**:
- **Inline form instead of modal**: Rejected — modal is the established pattern and handles focus management better.
- **Combined Chores+Agents panel**: Rejected — separate sections maintain clear separation of concerns.

### R7: Sparse Input Detection for Agent Content

**Decision**: Reuse the exact same `isSparseInput()` heuristic from `AddChoreModal.tsx`:
- Rich indicators: headings (`##`), list markers (`- *`), ≥4 lines
- ≤15 words → SPARSE
- ≤40 words on single line → SPARSE
- Otherwise → RICH

**Rationale**: The heuristic is already proven for the Chores feature and agent descriptions have similar characteristics to chore templates. The backend's `is_sparse_input()` function uses the same logic.

**Alternatives considered**:
- **Agent-specific heuristic**: Over-engineering; the generic heuristic works well enough.
- **Always show chat flow**: Adds friction for users who provide complete content.

### R8: Immediate Pipeline Availability

**Decision**: When an agent is created (saved to SQLite), it is immediately available in the `useAvailableAgents` hook that populates the Agent Pipeline settings. The existing `agent_configs` table already stores agents before PR merge. The `useAvailableAgents` hook already reads from this table.

**Rationale**: The existing infrastructure already supports this — the `agent_configs` table is populated during creation (Step 2 of the pipeline), and the pipeline mapping UI reads from this table. No additional work needed beyond ensuring the new REST endpoint also writes to `agent_configs`.

**Alternatives considered**:
- **Wait for PR merge**: Rejected per clarification — user explicitly requested immediate availability.

## Summary

All research tasks resolved. No NEEDS CLARIFICATION items remain. Key architectural decisions:
1. Make `_generate_config_files` and `_generate_issue_body` public in `agent_creator.py`
2. Create shared `github_commit_workflow.py` for branch → commit → PR → issue pipeline
3. Merge SQLite + GitHub repo sources for agent listing
4. Mirror Chores component patterns exactly for frontend
5. Three-state status badges (Active / Pending PR / Pending Deletion)
