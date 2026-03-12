# Research: Agent MCP Sync

**Feature**: 036-agent-mcp-sync | **Date**: 2026-03-11

## R1: GitHub Custom Agent Configuration Schema — `mcp` and `tools` Fields

**Decision**: Use the `mcp-servers` YAML frontmatter key for per-agent MCP server definitions, matching the existing codebase convention in `agent_creator.py`. Use `tools: ["*"]` to grant unrestricted tool access.

**Rationale**: The existing codebase uses `mcp-servers` as the YAML key in `agent_creator.py` (line 1019) for inline MCP server definitions within agent frontmatter. The repository also has a separate `.github/agents/mcp.json` file that serves as the central MCP configuration. The sync feature should populate the `mcp-servers` field in each agent's YAML frontmatter to match the existing pattern, while also updating the central `mcp.json`.

**Alternatives considered**:
- Using only the central `mcp.json` (rejected: per-agent configuration allows agent-specific MCP sets in the future)
- Using `mcp` as key name (rejected: would break existing agent file parsing that expects `mcp-servers`)
- Storing MCP references as IDs only (rejected: agent files must be self-contained for GitHub to process them)

## R2: YAML Frontmatter Parsing and Writing — Safe Round-Trip Editing

**Decision**: Use `yaml.safe_load()` to parse existing frontmatter and `yaml.dump(default_flow_style=False, sort_keys=False)` to serialize updated frontmatter, preserving existing key ordering. Separate the Markdown body from frontmatter using the existing `_FRONTMATTER_RE` regex pattern.

**Rationale**: The existing `agent_creator.py` already uses this pattern for initial file generation. For the sync utility, we need to round-trip edit existing files — parse the YAML frontmatter, modify the `tools` and `mcp-servers` fields, re-serialize, and concatenate with the original Markdown body. PyYAML's `sort_keys=False` preserves authorial key ordering, minimizing diffs.

**Alternatives considered**:
- Regex-based field replacement (rejected: brittle for multi-line YAML values, breaks on nested structures)
- Full file regeneration from templates (rejected: would lose manual edits to system prompts)
- Using `ruamel.yaml` for comment-preserving round-trips (rejected: adds dependency, existing code uses PyYAML)

## R3: Built-in MCP Registry — Single Source of Truth

**Decision**: Define `BUILTIN_MCPS` as a Python constant in the new `agent_mcp_sync.py` module, mirroring the frontend `BUILTIN_MCPS` constant in `buildGitHubMcpConfig.ts`. The backend constant is the authoritative source for sync operations; the frontend constant is used only for client-side config generation.

**Rationale**: The built-in MCPs (Context7, Code Graph Context) are currently defined only in the frontend (`buildGitHubMcpConfig.ts`) and in the static `.github/agents/mcp.json` file. The backend has no programmatic access to a built-in MCP registry. The sync utility needs a backend-accessible list to merge built-in MCPs into agent files. Keeping the constant aligned with the frontend ensures consistency.

**Alternatives considered**:
- Reading from `.github/agents/mcp.json` at runtime (rejected: requires GitHub API call, adds latency and failure mode)
- Sharing a JSON file between frontend and backend (rejected: adds coupling, the lists are small and stable)
- Database table for built-in MCPs (rejected: over-engineering — built-in MCPs change only with system updates)

## R4: Sync Trigger Points and Idempotency

**Decision**: The sync function is called at three trigger points: (1) after `sync_tool_to_github()` completes in the tools service, (2) after `create_agent()` / `update_agent()` in the agents service, and (3) on application startup via a background task. The function is fully idempotent — it reads the current truth (active MCPs + built-ins), computes the desired state for each agent file, and only writes files that differ from their current content.

**Rationale**: Idempotency is critical because multiple triggers can fire in rapid succession (e.g., user toggles several MCPs quickly). By comparing desired state vs. current file content, unnecessary writes are avoided, preventing git noise and respecting SC-004 (zero modifications on second run).

**Alternatives considered**:
- Event-driven sync with a queue (rejected: over-engineering for the current scale of ~15 agent files)
- Sync only on explicit user action (rejected: violates FR-009 startup reconciliation requirement)
- Debounced sync with a delay (rejected: adds complexity without clear benefit at current scale)

## R5: GitHub API Interaction Pattern for Batch File Updates

**Decision**: Use the GitHub Contents API (`GET /repos/{owner}/{repo}/contents/{path}` and `PUT /repos/{owner}/{repo}/contents/{path}`) for individual file reads/writes, matching the existing pattern in `sync_tool_to_github()`. For batch updates (multiple agent files), use sequential API calls within a single async function, with error handling per file so one failure doesn't block others.

**Rationale**: The existing `sync_tool_to_github()` method already establishes this pattern. Using the same approach ensures consistency and avoids introducing new API patterns. The Contents API handles file creation and update transparently (PUT creates if missing, updates if `sha` is provided).

**Alternatives considered**:
- Git Tree API for atomic batch commits (rejected: more complex, requires tree/blob/commit creation; the Contents API is simpler and already proven in the codebase)
- GraphQL `createCommitOnBranch` mutation (rejected: would require building file change sets, not worth the complexity for ~15 files)
- Local file system writes (rejected: the backend doesn't have direct filesystem access to the repo; all writes go through GitHub API)

## R6: Warning Surface for `tools` Field Override

**Decision**: Log warnings via Python's `logging` module when a non-`["*"]` `tools` value is overridden. Include the agent file path and the original `tools` value in the log message. The frontend does not display these warnings in the UI (out of scope per spec) but they are available in backend logs.

**Rationale**: FR-010 requires surfacing a warning when a restrictive `tools` value is overridden. The simplest implementation is structured logging, which integrates with existing monitoring. A UI notification would require a new API endpoint and frontend component — out of scope for this feature.

**Alternatives considered**:
- Toast notification in frontend (rejected: requires new API endpoint, UI component, and notification system changes)
- Annotation on the agent file in GitHub (rejected: adds GitHub API calls and complexity)
- Separate warnings log file (rejected: inconsistent with existing logging pattern)

## R7: Schema Validation After Sync

**Decision**: Perform lightweight validation after sync: verify that YAML frontmatter parses correctly, `tools` is `["*"]`, `mcp-servers` is a dict with valid server keys, and each server has required fields (`type`, and either `url` or `command`). Do not implement full JSON Schema validation against an external schema file.

**Rationale**: FR-011 says validation SHOULD (not MUST) be performed. The existing codebase validates MCP configs in `tools/service.py` using inline checks (not a schema file). Matching this lightweight approach keeps the implementation simple and consistent.

**Alternatives considered**:
- Full JSON Schema validation with `jsonschema` library (rejected: adds dependency, the schema is not published as a machine-readable file)
- No validation (rejected: violates the SHOULD requirement and risks persisting broken files)
- Validation only on new files (rejected: existing files could be corrupted by the sync itself)

## R8: Handling Agent Files Without YAML Frontmatter

**Decision**: Skip files that don't match the `_FRONTMATTER_RE` pattern (`^---\n...\n---\n`). Log a warning identifying the skipped file path. Do not attempt to add frontmatter to files that lack it.

**Rationale**: FR-012 explicitly requires skipping unparseable files. The existing `_FRONTMATTER_RE` regex in the agent discovery code already handles this detection. Files without frontmatter are likely not agent definition files (e.g., `copilot-instructions.md`, `mcp.json`).

**Alternatives considered**:
- Auto-add frontmatter to files without it (rejected: could corrupt non-agent files in the agents directory)
- Treat as error and halt sync (rejected: one bad file shouldn't block sync for all other files)
