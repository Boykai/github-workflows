# Agent Creator Service Contract

**Feature**: 001-custom-agent-creation  
**Date**: 2026-02-28

This document defines the internal service interfaces for the `#agent` command. These are not HTTP APIs exposed to external clients — they are internal Python async method signatures used between services.

## AgentCreatorService

Module: `backend/src/services/agent_creator.py`

### parse_command

Parses the `#agent` command text, extracting the description and optional status name.

**Input**: `command_text: str` — Full message text starting with `#agent`
**Output**: `tuple[str, str | None]` — `(description, status_name_or_none)`

**Behavior**:
- Strips `#agent` prefix
- Extracts trailing `#<status-name>` if present (last `#` token)
- Returns cleaned description and optional raw status name
- Raises `ValueError` if description is empty after parsing

**Examples**:
```
"#agent Reviews PRs for security #in-review"  → ("Reviews PRs for security", "in-review")
"#agent Triages new issues"                    → ("Triages new issues", None)
"#agent #backlog"                              → ValueError (empty description)
```

---

### fuzzy_match_status

Resolves a user-provided status name against existing project columns.

**Input**: 
- `raw_status: str` — User's status name (e.g., "in-review")
- `columns: list[str]` — Existing project column names

**Output**: `tuple[str | None, bool]` — `(resolved_column_name, is_ambiguous)`
- If exact/normalized match: `("In Review", False)`
- If multiple matches: `(None, True)` — caller should present options
- If no match: `(None, False)` — caller should offer to create new column

**Normalization**: `s.lower().replace("-", "").replace("_", "").replace(" ", "")`

---

### generate_preview

Uses AI to generate an agent configuration from a natural language description.

**Input**:
- `description: str` — User's description of the agent
- `status_column: str` — Resolved status column name
- `available_tools: list[str]` — All tool identifiers to include
- `github_token: str` — For LLM API auth

**Output**: `AgentPreview` — Generated agent configuration

---

### apply_edit

Applies a user's edit request to an existing preview.

**Input**:
- `current_preview: AgentPreview` — Current preview state
- `edit_instruction: str` — User's edit request in natural language
- `github_token: str` — For LLM API auth

**Output**: `AgentPreview` — Updated agent configuration

---

### execute_pipeline

Executes the creation pipeline with best-effort semantics.

**Input**:
- `preview: AgentPreview` — Confirmed agent configuration
- `project_id: str` — Target project node ID
- `owner: str` — Repo owner
- `repo: str` — Repo name
- `created_by: str` — Admin user's GitHub user ID
- `access_token: str` — GitHub OAuth token
- `db: aiosqlite.Connection` — Database connection

**Output**: `list[PipelineStepResult]` — Per-step results

**Pipeline steps** (executed in order, best-effort):
1. Save agent config to database
2. Create/verify project column
3. Create GitHub Issue
4. Create branch from default branch
5. Commit configuration files
6. Open Pull Request
7. Move issue to "In Review" on project board

Each step catches exceptions, logs them, and records success/failure. Subsequent steps proceed regardless (unless they depend on a failed step's output, e.g., can't commit files if branch creation failed).

---

### handle_message

Main entry point for processing a message in an active `#agent` conversation.

**Input**:
- `state: AgentCreationState` — Current conversation state
- `message: str` — User's message
- `session_id: str` — Session identifier
- `github_token: str` — OAuth token
- `db: aiosqlite.Connection` — Database connection

**Output**: `tuple[str, AgentCreationState]` — `(response_markdown, updated_state)`

**Behavior**: Routes to the appropriate handler based on `state.step`:
- `RESOLVE_PROJECT` — Parse project selection from message
- `RESOLVE_STATUS` — Parse status column selection
- `PREVIEW` / `EDIT_LOOP` — Check for confirmation or edit request
- `EXECUTING` — Should not receive messages (pipeline is running)

---

## GitHubProjectsService Extensions

Module: `backend/src/services/github_projects/service.py`

### get_repository_info

**Input**: `access_token: str, owner: str, repo: str`
**Output**: `dict` — `{"repository_id": str, "default_branch": str, "head_oid": str}`

### create_branch

**Input**: `access_token: str, repository_id: str, branch_name: str, from_oid: str`
**Output**: `str | None` — Branch ref ID on success, None on failure

### commit_files

**Input**: `access_token: str, owner: str, repo: str, branch_name: str, head_oid: str, files: list[dict], message: str`
**Output**: `str | None` — Commit OID on success, None on failure

Files format: `[{"path": "relative/path", "content": "text content"}]` — Base64 encoding handled internally.

### create_pull_request

**Input**: `access_token: str, repository_id: str, title: str, body: str, head_branch: str, base_branch: str, draft: bool = False`
**Output**: `dict | None` — `{"id": str, "number": int, "url": str}` on success, None on failure

---

## AIAgentService Extensions

Module: `backend/src/services/ai_agent.py`

### generate_agent_config

**Input**: `description: str, status_column: str, github_token: str`
**Output**: `dict` — `{"name": str, "description": str, "system_prompt": str}`

Calls `_call_completion()` with a structured prompt. Parses response via `_parse_json_response()`.

### edit_agent_config

**Input**: `current_config: dict, edit_instruction: str, github_token: str`
**Output**: `dict` — Updated config with same structure

Sends current config + edit instruction to LLM for targeted modification.

---

## Chat API Integration

Module: `backend/src/api/chat.py`

### Modified `send_message` flow

```
POST /chat/messages {"content": "#agent Reviews PRs #in-review"}

1. Add user message to history
2. NEW: Check if content starts with "#agent"
   a. Yes → Check admin status (require_admin equivalent)
   b. Route to AgentCreatorService.handle_message()
   c. Return assistant message with preview/status
3. Existing: detect_feature_request_intent() ...
```

### Response format for #agent messages

Uses existing `ChatMessage` model:
- `sender_type`: `SenderType.ASSISTANT`
- `content`: Markdown-formatted preview or status report
- `action_type`: `None` (no confirm/reject buttons — confirmation is via natural language)
- `action_data`: `{"agent_creation": True, "step": "preview"}` (metadata for frontend)
