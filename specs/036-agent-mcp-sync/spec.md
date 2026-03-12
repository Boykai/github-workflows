# Feature Specification: Agent MCP Sync — Propagate Activated & Built-in MCPs to Agent Files

**Feature Branch**: `036-agent-mcp-sync`  
**Created**: 2026-03-11  
**Status**: Draft  
**Input**: User description: "Add activated/built-in MCPs to agent file mcp field and enforce tools: [*] in all agent definitions"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Enforce Full Tool Access Across All Agent Definitions (Priority: P1)

A developer managing agent configurations expects every agent to have unrestricted access to all available tools. Currently, some agent files may have restrictive or missing `tools` fields, meaning agents silently lack access to tools they need. With this feature, whenever agent files are created or updated, the system automatically sets `tools: ["*"]` on every agent definition. If an agent file already has a restrictive tools list (e.g., `tools: ["search", "edit"]`), the system replaces it with `tools: ["*"]` and surfaces a clear indication that the value was auto-corrected.

**Why this priority**: Without full tool access, agents cannot function correctly. A restrictive tools list is the most common misconfiguration causing agent failures. This is the foundation that all other stories depend on.

**Independent Test**: Can be tested by running the sync process on a set of agent files — some with `tools: ["*"]`, some with restrictive lists, and some with no `tools` field at all. Verify that all files end up with `tools: ["*"]` and that overwritten values are logged.

**Acceptance Scenarios**:

1. **Given** an agent file with no `tools` field, **When** the sync process runs, **Then** the agent file is updated to include `tools: ["*"]`.
2. **Given** an agent file with `tools: ["search", "edit"]`, **When** the sync process runs, **Then** the `tools` field is replaced with `tools: ["*"]` and a warning is surfaced indicating the previous value was overridden.
3. **Given** an agent file that already has `tools: ["*"]`, **When** the sync process runs, **Then** the file is unchanged (idempotent — no unnecessary writes).
4. **Given** a newly created agent file, **When** the agent creation process completes, **Then** the file includes `tools: ["*"]` from the start.

---

### User Story 2 - Propagate Activated MCPs to Agent Files on Toggle (Priority: P1)

A developer activates an MCP tool from the Tools page (e.g., a code search server). They expect this MCP to be immediately available to all agents without manually editing each agent file. The system reads the current list of activated MCPs and merges them into the `mcp-servers` field of every agent configuration file. When the developer later deactivates that MCP, the system removes it from all agent files on the next sync.

**Why this priority**: This is the core value proposition of the feature — keeping agent MCP configuration in sync with the Tools page without manual file edits. Manual edits are error-prone, especially when managing 10+ agent files.

**Independent Test**: Can be tested by activating an MCP on the Tools page, triggering the sync, and verifying that all agent files now list the newly activated MCP in their `mcp-servers` field. Then deactivate the MCP and verify it is removed from all agent files.

**Acceptance Scenarios**:

1. **Given** 3 active MCPs on the Tools page and 10 agent files with empty `mcp-servers` fields, **When** the sync process runs, **Then** all 10 agent files have their `mcp-servers` field populated with all 3 active MCPs.
2. **Given** an agent file already listing MCP "context7" in its `mcp-servers` field, **When** the sync process runs and "context7" is still active, **Then** no duplicate "context7" entry is created in the `mcp-servers` field.
3. **Given** 3 active MCPs and 1 MCP is deactivated from the Tools page, **When** the sync process runs, **Then** the deactivated MCP is removed from all agent files while the remaining 2 MCPs stay intact.
4. **Given** a Tools page with no active MCPs, **When** the sync process runs, **Then** the `mcp-servers` field in agent files contains only built-in MCPs (no user-activated MCPs).

---

### User Story 3 - Include Built-in MCPs in All Agent Files (Priority: P2)

The system ships with a set of built-in MCPs (e.g., Context7, Code Graph Context) that should always be available to every agent. When agent files are created or the sync process runs, these built-in MCPs are automatically included in each agent's `mcp-servers` field alongside any user-activated MCPs. Built-in MCPs cannot be removed by users — they are always present.

**Why this priority**: Built-in MCPs provide essential baseline capabilities. Without them, newly created agents lack core tool integrations. This is lower priority than Story 2 because built-in MCPs are a fixed set that can be manually configured once, whereas user-activated MCPs change frequently.

**Independent Test**: Can be tested by creating a new agent file and verifying that all built-in MCPs appear in its `mcp-servers` field without any user action on the Tools page.

**Acceptance Scenarios**:

1. **Given** a newly created agent file, **When** the agent creation process completes, **Then** the `mcp-servers` field includes all built-in MCPs.
2. **Given** an existing agent file missing built-in MCPs from its `mcp-servers` field, **When** the sync process runs, **Then** the built-in MCPs are added to the `mcp-servers` field without removing any user-activated MCPs.
3. **Given** an agent file that already includes a built-in MCP, **When** the sync process runs, **Then** no duplicate entry is created for that built-in MCP.
4. **Given** a user attempts to remove a built-in MCP from an agent file, **When** the sync process runs, **Then** the built-in MCP is re-added to the `mcp-servers` field.

---

### User Story 4 - Real-Time Sync on MCP Activation Changes (Priority: P2)

When a developer toggles an MCP's activation state on the Tools page, the corresponding agent files are updated immediately (or on save) without requiring the developer to manually trigger a sync or restart the application. If the developer is viewing an agent file preview or editor, the `mcp-servers` field and `tools: ["*"]` setting are visibly reflected in the preview.

**Why this priority**: Real-time sync eliminates the gap between user intent (activating an MCP) and system state (agent files reflecting that activation). Without it, developers must remember to manually trigger syncs, which defeats the purpose of automation.

**Independent Test**: Can be tested by opening the Tools page, toggling an MCP on, and immediately checking agent file contents to verify the MCP appears in all agent `mcp-servers` fields.

**Acceptance Scenarios**:

1. **Given** a developer viewing the Tools page, **When** they activate a new MCP, **Then** all agent files are updated to include the MCP within the same save/sync operation.
2. **Given** a developer viewing the Tools page, **When** they deactivate an MCP, **Then** all agent files are updated to remove the MCP within the same save/sync operation.
3. **Given** multiple MCPs are toggled in rapid succession, **When** the sync completes, **Then** agent files reflect the final activation state accurately with no race conditions or partial updates.

---

### User Story 5 - Agent File Schema Validation After Sync (Priority: P3)

After the sync process updates agent files, the system validates each file against the custom agents configuration schema to catch structural errors before they are persisted. If validation fails (e.g., malformed YAML frontmatter, invalid `mcp-servers` entries), the system surfaces a clear error message and does not persist the invalid file.

**Why this priority**: Validation is a safety net that prevents broken agent files from being committed. While important, agents can function without strict schema validation as long as the sync logic itself is correct.

**Independent Test**: Can be tested by intentionally corrupting an agent file's structure and running the sync. Verify that the system detects the invalid structure, reports the error, and does not overwrite the file with invalid content.

**Acceptance Scenarios**:

1. **Given** a sync operation that would produce a valid agent file, **When** the sync completes, **Then** the file passes schema validation and is persisted.
2. **Given** a sync operation that encounters an agent file with malformed structure, **When** validation runs, **Then** the system reports a specific error (file path, field name, issue description) and skips persisting that file.
3. **Given** a sync operation on 10 agent files where 1 has a structural issue, **When** the sync completes, **Then** the 9 valid files are updated successfully and the 1 invalid file is reported with an error.

---

### Edge Cases

- What happens when an agent file does not yet have an `mcp-servers` field? The system initializes `mcp-servers` as an empty dict before appending entries.
- What happens when an agent file has no YAML frontmatter at all? The system treats it as a file that cannot be updated, logs a warning, and skips it.
- What happens when two sync operations run concurrently (e.g., user rapidly toggles MCPs)? The sync process must be idempotent — the final state reflects the current activation list regardless of how many times sync runs.
- What happens when a built-in MCP has the same server key as a user-activated MCP? The built-in MCP takes precedence; the user-activated entry is skipped to avoid conflicts, and a warning is surfaced.
- What happens when the MCP configuration content is invalid JSON? The system skips the invalid MCP, logs an error with the MCP name and validation failure, and continues syncing the remaining MCPs.
- What happens when there are no agent files in the repository? The sync completes successfully with no changes (no files to update).
- What happens when a user manually edits an agent file to add a restrictive `tools` list after sync? On the next sync trigger, the system re-enforces `tools: ["*"]` and surfaces a warning about the override.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST set `tools: ["*"]` on every agent file definition, replacing any pre-existing `tools` value.
- **FR-002**: System MUST add every MCP activated on the Tools page to the `mcp-servers` field of all agent configuration files.
- **FR-003**: System MUST add all built-in MCPs to the `mcp-servers` field of every agent file at creation time and on every sync.
- **FR-004**: System MUST remove an MCP from all agent files' `mcp-servers` fields when that MCP is deactivated on the Tools page.
- **FR-005**: System MUST NOT create duplicate MCP entries in an agent file's `mcp-servers` field if the MCP is already present.
- **FR-006**: System MUST initialize the `mcp-servers` field as an empty list when an agent file does not yet have one, before appending entries.
- **FR-007**: System MUST trigger agent file sync whenever an MCP activation state changes on the Tools page (activate or deactivate).
- **FR-008**: System MUST trigger agent file sync when a new agent file is created.
- **FR-009**: System MUST trigger agent file sync on application startup to reconcile any drift between Tools page state and agent files.
- **FR-010**: System MUST surface a warning when an existing `tools` field value other than `["*"]` is overwritten during sync.
- **FR-011**: System SHOULD validate updated agent files against the custom agents configuration schema before persisting changes.
- **FR-012**: System MUST skip agent files that lack parseable frontmatter and log a warning identifying the skipped file.
- **FR-013**: System MUST ensure built-in MCPs cannot be removed by user action — they are always re-added on sync.
- **FR-014**: System MUST handle server key conflicts between built-in and user-activated MCPs by giving precedence to built-in MCPs.
- **FR-015**: System MUST complete the sync operation idempotently — running the sync multiple times with the same input produces the same agent file output.

### Key Entities

- **Agent Configuration File**: A file defining an agent's identity, capabilities, and tool access. Contains a name, description, optional handoffs, a `tools` field controlling tool access, and an `mcp-servers` field listing available MCP servers. Lives in the repository's agents directory.
- **MCP Entry**: A reference to an MCP server within an agent file's `mcp-servers` field. Contains a server key (unique identifier) and server configuration (type, endpoint, authentication). Can originate from user activation on the Tools page or from the built-in MCP registry.
- **Built-in MCP**: An MCP server that ships with the system and is always included in every agent file. Cannot be deactivated by users. Examples include documentation search and code graph analysis tools.
- **Activated MCP**: An MCP server that a user has explicitly enabled via the Tools page. Can be activated or deactivated at any time. When activated, it is added to all agent files; when deactivated, it is removed.
- **Sync Operation**: The process of reconciling the current MCP activation state (built-in + user-activated) with the contents of all agent configuration files. Produces updated agent files with correct `mcp-servers` and `tools` fields.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After sync, 100% of agent files in the repository contain `tools: ["*"]` — verified by scanning all agent files.
- **SC-002**: After activating an MCP on the Tools page, the MCP appears in the `mcp-servers` field of every agent file within the same save/sync operation.
- **SC-003**: After deactivating an MCP on the Tools page, the MCP is absent from the `mcp-servers` field of every agent file within the same save/sync operation.
- **SC-004**: Running the sync process twice in succession on an unchanged activation state produces zero file modifications on the second run (idempotency).
- **SC-005**: Built-in MCPs are present in 100% of agent files after every sync, regardless of user actions.
- **SC-006**: No agent file contains duplicate MCP entries after sync — each MCP server key appears at most once per file.
- **SC-007**: The sync process completes for 25 agent files with 10 active MCPs in under 5 seconds.
- **SC-008**: When a restrictive `tools` value is overridden, a warning is surfaced or logged for every affected file, enabling developers to audit changes.

### Assumptions

- Agent configuration files use YAML frontmatter for structured fields (`tools`, `mcp-servers`) and a Markdown body for the system prompt. Files without parseable frontmatter are skipped.
- The built-in MCP registry is a fixed, known list maintained by the system. Adding or removing built-in MCPs requires a system update, not user action.
- The `mcp-servers` field in agent files follows the schema documented in the custom agents configuration reference — an array of server configuration objects with unique server keys.
- The Tools page maintains a source-of-truth list of user-activated MCPs with their full configuration (server key, type, endpoint, authentication).
- The sync process operates on all agent files in the repository's agents directory. Files outside this directory are not affected.
- The `tools: ["*"]` enforcement is unconditional — there is no use case where an agent should have restricted tool access. If such a use case arises in the future, it would be handled by a separate opt-out mechanism.
- Concurrent sync operations are resolved by last-write-wins semantics. The sync is idempotent, so the final state is always consistent regardless of execution order.

### Dependencies

- Existing MCP activation state management on the Tools page (the source of truth for which MCPs are active).
- Existing agent file creation pipeline (the entry point for initial `tools` and `mcp-servers` field population).
- Existing built-in MCP registry (the authoritative list of MCPs that ship with the system).
- Custom agents configuration schema reference for validation.

### Scope Boundaries

**In scope:**

- Syncing `mcp-servers` field contents across all agent files based on Tools page activation state and built-in MCP registry
- Enforcing `tools: ["*"]` on all agent file definitions
- Triggering sync on MCP activation/deactivation, agent file creation, and application startup
- Deduplication of MCP entries within agent files
- Warning/logging when `tools` values are overridden
- Schema validation of updated agent files (best-effort)

**Out of scope:**

- Changes to the Tools page UI itself (activation/deactivation flow remains as-is)
- Changes to the MCP configuration schema or format
- Per-agent MCP customization (all agents receive the same MCP set)
- Selective `tools` restrictions for specific agents (all agents get `tools: ["*"]`)
- Migration of MCP configs between `.copilot/mcp.json` and agent file `mcp-servers` fields (these remain separate sync targets)
- Changes to the built-in MCP registry itself (adding/removing built-in MCPs is out of scope)
