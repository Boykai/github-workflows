# Research: Add Tools Page with MCP Configuration Upload and Agent Tool Selection

**Feature**: 027-mcp-tools-page | **Date**: 2026-03-07

## R1: GitHub MCP Configuration File Format and Placement

**Task**: Determine the official GitHub MCP configuration format, target file path within the repository, and the appropriate API for pushing configurations to enable GitHub Custom Agents to consume them.

**Decision**: MCP server configurations for GitHub Custom Agents are defined in the YAML frontmatter of agent definition files (`.github/agents/*.agent.md`) under the `mcp-servers` key. Each MCP server entry specifies `type` (http or stdio), `url` (for http) or `command`/`args` (for stdio), and optional `headers`/`env`. For shared project-level MCP config, `.copilot/mcp.json` stores a `mcpServers` object that the Copilot CLI and VS Code consume. The application will store MCP configurations locally and sync them by committing/pushing the config file to the connected GitHub repository via the GitHub Contents API (`PUT /repos/{owner}/{repo}/contents/{path}`).

**Rationale**: GitHub Custom Agents read MCP server definitions from `.github/agents/*.agent.md` YAML frontmatter. The `.copilot/mcp.json` format provides a complementary project-level config that tools like VS Code and the Copilot CLI pick up. Both formats use JSON-compatible structures. Using the Contents API for sync is the standard GitHub approach for programmatic file commits, already familiar from the existing agent service (`services/agents/service.py`) which creates PRs with file contents.

**Alternatives Considered**:
- **Direct GitHub API for Copilot Extensions**: Rejected — no stable public API exists for pushing MCP configs to Copilot directly; the file-in-repo approach is the documented integration path.
- **Storing configs only in `.github/agents/` frontmatter**: Rejected — the Tools page manages MCP configs as first-class entities; embedding them only in agent files couples tool management to agent management. Instead, store separately and reference by ID.
- **GitHub Copilot Extensions API**: Rejected — focuses on Copilot Extensions (chat plugins), not MCP server configurations.

---

## R2: MCP Configuration Validation Schema

**Task**: Define the validation rules for uploaded MCP configurations to ensure compatibility with GitHub Custom Agents.

**Decision**: Accept MCP configurations as JSON objects with the following schema:
```json
{
  "mcpServers": {
    "<server-name>": {
      "type": "http" | "stdio",
      "url": "<endpoint-url>",        // Required for type: http
      "command": "<command>",          // Required for type: stdio
      "args": ["<arg1>", ...],        // Optional, for stdio
      "headers": { "<key>": "<value>" }, // Optional, for http
      "env": { "<key>": "<value>" },    // Optional
      "tools": ["<tool-name>" | "*"]    // Optional
    }
  }
}
```
Validation rules: (1) Must be valid JSON, (2) Must contain a `mcpServers` object with at least one server entry, (3) Each server must have a `type` of `http` or `stdio`, (4) HTTP servers must have a `url`, (5) Stdio servers must have a `command`, (6) File size limit of 256 KB. The system extracts the server name as the MCP tool's display name and generates a description from the type and URL/command.

**Rationale**: This schema matches the documented `.copilot/mcp.json` format and the `mcp-servers` YAML frontmatter structure. Validating at upload time prevents broken configs from being synced to GitHub, satisfying FR-005 and FR-009. The 256 KB limit is generous for JSON config files while preventing abuse (FR-018).

**Alternatives Considered**:
- **Accept raw YAML from agent files**: Rejected — JSON is the standard interchange format for the API; YAML can be a future enhancement.
- **No schema validation (accept any JSON)**: Rejected — the spec mandates validation (FR-005) and specific error messages for invalid uploads.

---

## R3: Data Persistence Strategy for MCP Tools

**Task**: Determine how to extend the existing `mcp_configurations` table to support the Tools page requirements (description, raw config content, sync status, GitHub repo target).

**Decision**: Create a new migration (`014_extend_mcp_tools.sql`) that adds columns to the existing `mcp_configurations` table: `description`, `config_content` (raw JSON), `sync_status` (enum: synced/pending/error), `sync_error`, `synced_at`, `github_repo_target`, and `project_id`. Also create a new `agent_tool_associations` junction table for the many-to-many relationship between agents and MCP tools.

**Rationale**: The existing `mcp_configurations` table (migration 006) has the core fields (`id`, `github_user_id`, `name`, `endpoint_url`, `is_active`, timestamps). The Tools page requires additional fields for sync tracking, raw config storage, and project scoping. Adding columns via ALTER TABLE in a new migration is the standard pattern (e.g., migration 002, 003). A separate junction table for agent-tool associations follows relational best practices and enables efficient queries for "which agents use this tool?" (needed for FR-016 delete warnings).

**Alternatives Considered**:
- **New separate table**: Rejected — the existing `mcp_configurations` table already serves MCP management; extending it avoids data duplication and maintains backward compatibility with the Settings page MCP list.
- **Store tool IDs as JSON array in `agent_configs.tools`**: Already partially exists (the `tools` column stores `'[]'`). The junction table is added in parallel to support relational queries (e.g., find all agents using a specific tool). The `tools` JSON column on agents can be updated on save for quick reads.

---

## R4: GitHub Sync Implementation Strategy

**Task**: Design the sync mechanism for pushing MCP configurations to the connected GitHub repository.

**Decision**: Implement an async sync operation that: (1) Reads the current `.copilot/mcp.json` from the repo via Contents API (`GET`), (2) Merges the new MCP server config into the existing object, (3) Writes the updated file back via Contents API (`PUT`) with the SHA for conflict detection, (4) Updates local sync status to "synced" on success or "error" with message on failure. Use optimistic UI updates — set status to "pending" immediately, then update on API response.

**Rationale**: The Contents API is the established pattern in this codebase for GitHub file operations (the agents service already uses it for `.github/agents/*.agent.md` files). Merging into a single `.copilot/mcp.json` file follows the documented project-level config pattern. Optimistic updates with error rollback provide responsive UX (FR-014, SC-002, SC-007). The SHA-based conflict detection prevents overwriting concurrent changes.

**Alternatives Considered**:
- **Creating individual files per MCP config**: Rejected — the `.copilot/mcp.json` format expects a single file with all servers; individual files would not be consumed by tooling.
- **Using the Git Data API (trees/blobs/commits)**: Rejected — more complex than Contents API for single-file operations; only beneficial for multi-file atomic commits.
- **PR-based sync (like agent creation)**: Rejected — MCP configs are infrastructure; direct commits to the default branch are appropriate and simpler. PRs add unnecessary workflow overhead for config files.

---

## R5: Tools Page Component Architecture

**Task**: Determine the optimal component architecture for the Tools page to maximize reuse of existing Agents page patterns.

**Decision**: Create a standalone `ToolsPage.tsx` that mirrors `AgentsPage.tsx` structure with: (1) A `CelestialCatalogHero` header section with Tools-specific copy, (2) A `ToolsPanel` component (mirroring `AgentsPanel`) containing the tool card grid, search, and upload action, (3) Individual `ToolCard` components showing name, description, sync status badge, and action buttons (re-sync, delete). Reuse existing UI primitives (`Card`, `Button`, `Input`, `Badge` from `components/ui/`). Do NOT abstract a generic "ResourcePage" wrapper — this follows Constitution Principle V (YAGNI, avoid premature abstraction).

**Rationale**: The spec explicitly requires the Tools page to "mirror the Agents page layout" (FR-002). Direct structural mirroring (same hero section pattern, same panel pattern, same card pattern) achieves visual consistency. The technical notes suggest "abstracting shared layout into a generic resource page wrapper," but with only two pages sharing this pattern, abstraction would be premature per Constitution Principle V. Each page has different data shapes, actions, and states; a wrapper would require extensive configuration that defeats the simplicity goal.

**Alternatives Considered**:
- **Generic ResourcePage wrapper**: Rejected — premature abstraction for only two consumers (Agents, Tools). Would require complex prop drilling for actions, states, and card rendering. Can be extracted later if a third page needs the same pattern.
- **Embedding Tools in the existing Settings/MCP section**: Rejected — the spec explicitly requires a standalone Tools page in the sidebar (FR-001), not a settings subsection.

---

## R6: Tool Selector Modal for Agent Forms

**Task**: Design the MCP tool selector modal that appears on the Agent creation/edit form.

**Decision**: Create a `ToolSelectorModal` component rendered as a full overlay dialog with: (1) Header with title and close button, (2) Optional search/filter input, (3) Responsive tile grid (CSS Grid: 1 column on mobile, 2 on tablet, 3 on desktop), (4) Each tile showing MCP icon placeholder, name, description, and selected state (checkmark overlay + highlighted border), (5) Multi-select managed via local `Set<string>` state, (6) Footer with Cancel and Confirm buttons. Selected tools are committed to the agent form only on Confirm. The modal is triggered from an "Add Tools" section in `AddAgentModal.tsx`.

**Rationale**: The spec requires a "full overlay modal displaying all available MCPs in a responsive tile grid" with multi-select (FR-011). Managing selection state locally (not persisted until Confirm) follows the principle of least surprise and matches how modal forms typically work. CSS Grid with responsive breakpoints ensures the tile layout adapts to viewport width (SC-011). This mirrors the model selection UX pattern described in the spec's UI/UX section.

**Alternatives Considered**:
- **Inline multi-select dropdown**: Rejected — the spec explicitly requires a tile grid modal, not a dropdown.
- **Side panel / drawer**: Rejected — the spec says "full overlay modal."
- **Immediate selection (no confirm step)**: Rejected — the spec describes a confirm flow (open modal → select → confirm → chips appear).

---

## R7: Agent-Tool Association Persistence

**Task**: Determine how to persist and retrieve the association between agents and MCP tools.

**Decision**: Use a dual approach: (1) The `agent_configs.tools` JSON column stores an array of MCP tool IDs for quick reads when loading agent details, (2) A new `agent_tool_associations` junction table stores the normalized relationship for relational queries (e.g., "find all agents using tool X" for delete warnings). On agent create/update, both are written in a transaction. The frontend sends tool IDs in the agent create/update payload.

**Rationale**: The `tools` column already exists on `agent_configs` (migration 007) as a JSON array defaulting to `'[]'`. Storing tool IDs there enables efficient single-query agent loads without JOINs. The junction table adds relational integrity for reverse lookups needed by FR-016 (warn on tool deletion). This dual approach trades slight write complexity for optimal read performance in both directions.

**Alternatives Considered**:
- **Junction table only**: Rejected — would require JOINs for every agent load, adding complexity to the existing agent list/detail queries.
- **JSON column only**: Rejected — reverse lookups ("which agents use this tool?") would require scanning all agents and parsing JSON, which is inefficient.

---

## R8: Navigation and Routing

**Task**: Determine how to add the Tools page to the navigation and routing.

**Decision**: Add a new entry to `NAV_ROUTES` in `frontend/src/constants.ts` after the Agents entry: `{ path: '/tools', label: 'Tools', icon: Wrench }` (using `Wrench` from lucide-react). Add a corresponding route in the router configuration. The sidebar automatically renders all `NAV_ROUTES` via `map()`, so no sidebar component changes are needed.

**Rationale**: The existing navigation system is data-driven — the `NAV_ROUTES` array in `constants.ts` is the single source of truth for sidebar items, and `Sidebar.tsx` renders them via `map()`. Adding a new entry is the minimal change needed (FR-001). `Wrench` is the standard lucide-react icon for tools/settings, consistent with the icon pattern used by other nav items.

**Alternatives Considered**:
- **Custom sidebar modification**: Rejected — the data-driven approach requires no sidebar code changes.
- **Placing Tools under Settings**: Rejected — the spec requires a top-level nav item (FR-001).
