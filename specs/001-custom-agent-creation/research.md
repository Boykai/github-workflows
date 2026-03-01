# Research: Custom Agent Creation via Chat (#agent)

**Feature**: 001-custom-agent-creation  
**Date**: 2026-02-28  
**Status**: Complete

## Research Questions & Findings

### R-001: Agent Configuration Storage

**Question**: The spec assumes an `agent_configs` table exists. Does it?

**Finding**: **No `agent_configs` table exists.** Agent configurations are stored as JSON in `project_settings.agent_pipeline_mappings` — a JSON string mapping status column names to lists of agent slugs. Individual agents are represented by `ProjectAgentMapping(slug, display_name)` models. The system also discovers agents from `.github/agents/*.agent.md` files in the repository.

**Decision**: Create a new `agent_configs` table via migration `007_agent_configs.sql` to store custom agent definitions (name, description, system_prompt, status_column, tools JSON, created_by, project_id). This is separate from the pipeline mappings — `agent_configs` stores the agent's definition, while `agent_pipeline_mappings` stores which agents are assigned to which statuses. After creating the agent config, also update the relevant project's `agent_pipeline_mappings` to include the new agent.

**Rationale**: Embedding full agent definitions (with multi-line system prompts) into the existing JSON pipeline mappings would be fragile and violate single-responsibility. A dedicated table cleanly separates agent definitions from pipeline routing.

**Alternatives considered**: (1) Store in `agent_pipeline_mappings` JSON — rejected due to schema complexity and lack of queryability. (2) Store only in repo files (YAML) — rejected because the agent needs to be available to the system immediately without a PR merge.

---

### R-002: GitHub API Methods for Branch/Commit/PR Creation

**Question**: GitHubProjectsService lacks methods for creating branches, committing files, and creating PRs. What APIs are needed?

**Finding**: Three new GitHub GraphQL mutations are needed, plus one helper query:

1. **`createRef`** — Creates a branch. Requires `repositoryId` (node ID), `name` (fully qualified: `refs/heads/<name>`), and `oid` (SHA of commit to branch from).

2. **`createCommitOnBranch`** — Commits files without cloning. Requires `branch.repositoryNameWithOwner`, `branch.branchName` (bare name, NO `refs/heads/`), `expectedHeadOid` (optimistic concurrency), and `fileChanges.additions` (array of `{path, contents}` where contents is **Base64-encoded**).

3. **`createPullRequest`** — Creates a PR. Requires `repositoryId`, `title`, `headRefName` (bare name), `baseRefName` (bare name), optional `body` and `draft`.

4. **Helper query** — `repository(owner, name) { id, defaultBranchRef { name, target { ... on Commit { oid } } } }` — fetches repo node ID and default branch HEAD SHA in one call.

**Decision**: Add these four operations as new methods on `GitHubProjectsService` with corresponding GraphQL constants in `graphql.py`. Follow existing patterns (`_graphql` helper, `_request_with_retry`, constant naming like `CREATE_BRANCH_MUTATION`).

**Key gotchas to handle**:
- `createRef` requires `refs/heads/` prefix; `createCommitOnBranch` and `createPullRequest` use bare names
- `expectedHeadOid` mismatch on commit → retry with fresh SHA (up to 3 attempts)
- Branch already exists → handle gracefully (treat as success in idempotent pipeline)
- PR already exists for head→base → find and return existing
- File contents must be Base64-encoded for `createCommitOnBranch`

---

### R-003: Chat Command Routing Pattern

**Question**: How should the `#agent` command be intercepted in the chat and Signal flows?

**Finding**: There is **no existing `#` command pattern** in the codebase. Chat messages flow through a priority chain in `api/chat.py`: (1) detect feature request intent via AI, (2) parse status change via AI, (3) fallback to task generation via AI. Signal uses a similar flow after checking for confirm/reject keywords.

**Decision**: Add `#agent` detection as **Priority 0** — a simple `content.strip().startswith("#agent")` check before any AI calls. This avoids wasting LLM tokens on command parsing.

- **Web chat** (`api/chat.py`): After adding the user message to history, before `detect_feature_request_intent()`, check for `#agent` prefix and route to `AgentCreatorService`.
- **Signal** (`signal_chat.py`): In `process_signal_chat()`, after confirm/reject keyword check, before `_run_ai_pipeline()`.

**Rationale**: Simple string prefix detection is deterministic, fast, and doesn't require AI. This establishes a new pattern that future `#` commands can follow.

---

### R-004: Multi-Step Conversation State Management

**Question**: How should multi-step conversation state be managed for the guided `#agent` flow?

**Finding**: The codebase uses two patterns for conversation state:
1. **Web chat**: Module-level plain dicts in `api/chat.py` — `_messages` (per session), `_proposals` (per proposal ID), `_recommendations` (per recommendation ID). No TTL or eviction.
2. **Signal**: Module-level `_signal_pending: dict[str, dict]` — one pending item per user (keyed by `github_user_id`). Overwrite semantics.

`BoundedDict` exists in `utils.py` (OrderedDict with max capacity, FIFO eviction) but is not used for chat state.

**Decision**: Use a module-level `BoundedDict` in `agent_creator.py` keyed by `session_id` (web chat) or `github_user_id` (Signal). Store an `AgentCreationState` dataclass with: current step, target project/repo info, parsed description, resolved status column, generated preview, pending edits. Use `BoundedDict(maxlen=100)` to prevent unbounded growth.

**Rationale**: Follows the existing in-memory state pattern but adds eviction via `BoundedDict` to satisfy the spec's requirement for cleanup. No timeout is needed for v1 — FIFO eviction handles the degenerate case of abandoned sessions.

---

### R-005: Admin Access Control

**Question**: How does `require_admin` work and can it be reused?

**Finding**: `require_admin` in `dependencies.py` checks `session.github_user_id` against `global_settings.admin_github_user_id`. Auto-promotes the first authenticated user if the admin field is NULL. Returns 403 if mismatch.

**Decision**: Reuse `require_admin` as a FastAPI dependency in the chat handler when `#agent` is detected. For Signal, check admin status using the same logic (query `global_settings.admin_github_user_id` and compare with the Signal user's `github_user_id`).

---

### R-006: Project Context Resolution

**Question**: How does the chat widget pass project context, and how should Signal handle multi-project selection?

**Finding**: 
- **Web chat**: `project_id` is NOT in the request body. It's resolved from `session.selected_project_id` stored in the DB session. The handler validates it's non-None.
- **Signal**: `project_id` is passed as a parameter to `process_signal_chat()`, resolved from the Signal user's associated session. The `#project-name` prefix syntax exists for routing.

**Decision**: 
- Web chat: Use `session.selected_project_id` (already available). Resolve `owner/repo` using the existing `resolve_repository()` utility.
- Signal: If `project_id` is available from the message context, use it. Otherwise, query the user's accessible projects and prompt for selection (numbered list). Store the selection in the conversation state.

---

### R-007: AI-Generated Agent Configuration

**Question**: How should the LLM be called to generate agent name, description, and system prompt?

**Finding**: `AIAgentService._call_completion()` is the internal method for LLM calls. It accepts a messages list, temperature, max_tokens, and github_token. It handles both Copilot SDK and Azure OpenAI providers transparently. Response is parsed via `_parse_json_response()` which handles markdown fences, truncation, etc.

**Decision**: Add a new method `generate_agent_config(description, status_column, available_tools, github_token)` to `AIAgentService` that:
1. Constructs a system prompt instructing the LLM to generate a JSON object with `name`, `description`, `system_prompt`, and `status_column` fields
2. Calls `_call_completion()` with the constructed messages
3. Parses the response via `_parse_json_response()`
4. Returns an `AgentPreview` model

For edit requests, a separate `edit_agent_config(current_preview, edit_instruction, github_token)` method re-calls the LLM with the current config + edit instruction.

---

### R-008: Status Column Matching Algorithm

**Question**: What normalization approach for matching status names?

**Decision**: Simple string normalization: `normalize(s) = s.lower().replace("-", "").replace("_", "").replace(" ", "")`. Compare normalized user input against normalized column names. If multiple columns produce the same normalized value (unlikely but possible), present all matches for user selection (FR-009).

**Rationale**: Spec explicitly requires "simple string normalization" without a fuzzy library. This approach handles the documented cases: `in-review` → `inreview`, `In Review` → `inreview`, `IN_REVIEW` → `inreview`, `InReview` → `inreview`.

---

### R-009: Repository Artifacts Format

**Question**: What should the committed YAML configuration files contain?

**Decision**: Three files committed in a single `createCommitOnBranch` call:

1. **`.github/agents/<slug>.yml`** — Agent metadata:
   ```yaml
   name: SecurityReviewer
   description: Reviews PRs for security vulnerabilities
   status_column: In Review
   tools: [list_projects, get_project_items, ...]
   ```

2. **`.github/agents/prompts/<slug>.md`** — Full system prompt as markdown (not YAML, for readability).

3. **`.github/agents/README.md`** — Create if missing, or append an entry:
   ```markdown
   ## SecurityReviewer
   Reviews PRs for security vulnerabilities. Assigned to: In Review.
   ```

**Rationale**: Separating the system prompt into its own `.md` file keeps it readable and editable. The main YAML config stays concise. README provides discoverability.
