# Feature Specification: Tools Page — Fix MCP Bugs, Broken Link, Repo Name Display, Discover Button & Auto-populate MCP Name

**Feature Branch**: `028-mcp-tools-fixes`  
**Created**: 2026-03-07  
**Status**: Draft  
**Input**: User description: "On tools page, fix broken MCP docs link, display repo name instead of owner in Repository bubble, add Discover button linking to GitHub MCP Registry, auto-populate MCP name from uploaded definition JSON, and accept command/args-style MCP definitions without validation errors."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Accept Command/Args MCP Definitions Without Validation Error (Priority: P1)

As a developer creating a new MCP integration on the Tools page, I want to upload or paste a valid MCP definition that uses `command` and `args` fields (such as a Docker-based stdio server) and have the system accept it without throwing a validation error, so that I can configure legitimate MCP servers without being blocked by an incorrect type-enforcement check.

**Why this priority**: This is a blocking bug. Users cannot create valid MCP integrations when the definition uses the standard command/args format without an explicit `type` field. This directly prevents core functionality — configuring MCP servers — and generates confusing error messages for valid input.

**Independent Test**: Can be fully tested by pasting a command/args-style MCP definition JSON into the creation form and verifying no validation error appears and the server is created successfully.

**Acceptance Scenarios**:

1. **Given** a user is on the MCP creation form, **When** they upload or paste an MCP definition JSON containing `command` and `args` fields but no explicit `type` field (e.g., `{"mcpServers": {"markitdown": {"command": "docker", "args": ["run", "--rm", "-i", "markitdown-mcp:latest"]}}}`), **Then** the system accepts the definition without error and infers the transport type as `stdio`.
2. **Given** a user is on the MCP creation form, **When** they upload an MCP definition with an explicit `"type": "stdio"` alongside `command` and `args`, **Then** the system accepts the definition without error.
3. **Given** a user is on the MCP creation form, **When** they upload an MCP definition with `"type": "http"` and a `url` field, **Then** the system accepts the definition without error.
4. **Given** a user is on the MCP creation form, **When** they upload an MCP definition that has neither `type`, `command`, nor `url`, **Then** the system displays a clear, actionable error message indicating the definition is ambiguous or malformed.

---

### User Story 2 — Auto-populate MCP Name From Uploaded Definition (Priority: P1)

As a developer creating a new MCP integration, I want the MCP Name field to automatically populate with the server name extracted from my uploaded or pasted MCP definition JSON when the name field is empty, so that I can save time and avoid manually entering a name that already exists in the definition.

**Why this priority**: This is a high-value usability improvement that reduces friction in the MCP creation workflow. It directly addresses a common pain point where users must redundantly type a name that is already present in their definition file.

**Independent Test**: Can be fully tested by pasting an MCP definition JSON with the name field empty and verifying the name auto-populates from the first key under `mcpServers`.

**Acceptance Scenarios**:

1. **Given** the MCP Name field is empty on the creation form, **When** a user uploads or pastes an MCP definition JSON containing `{"mcpServers": {"context7": {...}}}`, **Then** the MCP Name field auto-populates with `context7`.
2. **Given** the MCP Name field already contains a user-entered value (e.g., `my-custom-name`), **When** a user uploads or pastes an MCP definition JSON containing `{"mcpServers": {"context7": {...}}}`, **Then** the MCP Name field retains `my-custom-name` and is not overwritten.
3. **Given** the MCP Name field is empty, **When** a user uploads or pastes an MCP definition JSON containing multiple servers under `mcpServers` (e.g., `{"mcpServers": {"server-a": {...}, "server-b": {...}}}`), **Then** the MCP Name field auto-populates with the first key (`server-a`) and the user is notified that multiple servers were detected.
4. **Given** the MCP Name field is empty, **When** a user uploads or pastes invalid JSON or JSON without an `mcpServers` key, **Then** no auto-population occurs and the name field remains empty.

---

### User Story 3 — Fix Broken MCP Documentation Link (Priority: P2)

As a developer seeking guidance on MCP integration, I want the MCP docs link on the Tools page to navigate to the correct GitHub Copilot MCP documentation, so that I can access relevant help without encountering a dead link.

**Why this priority**: A broken documentation link creates a dead-end for users seeking help. While not a functional blocker, it significantly degrades the user experience and erodes trust in the platform. This is a quick fix with high impact.

**Independent Test**: Can be fully tested by clicking the MCP docs link and verifying it navigates to the official GitHub Copilot MCP documentation page with a valid HTTP 200 response.

**Acceptance Scenarios**:

1. **Given** a user is on the Tools page MCP section, **When** they click the MCP documentation link, **Then** they are navigated to the official GitHub Copilot MCP documentation page (a valid, accessible URL).
2. **Given** a user is on the Tools page MCP section, **When** they inspect the MCP documentation link, **Then** the URL points to the correct GitHub Copilot MCP documentation resource.

---

### User Story 4 — Display Repository Name Instead of Owner (Priority: P2)

As a developer viewing the Tools page, I want the Repository field/bubble to display the repository name (not the repository owner), so that I can correctly identify which repository a tool belongs to.

**Why this priority**: Displaying the wrong information (owner instead of repo name) is misleading and causes confusion when users manage tools across multiple repositories. The bubble must also dynamically resize to fit varying repository name lengths.

**Independent Test**: Can be fully tested by viewing the Tools page with repositories of varying name lengths and verifying the correct repository name is displayed within a properly sized bubble.

**Acceptance Scenarios**:

1. **Given** a user is viewing the Tools page with a repository named `github-workflows` owned by `Boykai`, **When** they look at the Repository display bubble, **Then** the bubble shows `github-workflows` (not `Boykai`).
2. **Given** a repository with a short name (e.g., `api`), **When** the user views the Repository bubble, **Then** the bubble resizes to fit the short text without excessive whitespace.
3. **Given** a repository with a long name (e.g., `my-very-long-repository-name-for-testing`), **When** the user views the Repository bubble, **Then** the bubble expands to accommodate the full name or gracefully truncates with an ellipsis and provides the full name via a tooltip.

---

### User Story 5 — Add Discover Button for MCP Registry (Priority: P3)

As a developer exploring available MCP integrations, I want a "Discover" button on the Tools page that links to the GitHub MCP Registry, so that I can easily find and browse available MCP servers to integrate with my project.

**Why this priority**: This is an enhancement that improves discoverability. While not fixing a bug, it provides significant value by connecting users to the broader MCP ecosystem directly from the Tools page.

**Independent Test**: Can be fully tested by verifying the Discover button renders on the Tools page, is keyboard-navigable, and opens the GitHub MCP Registry in a new tab when clicked.

**Acceptance Scenarios**:

1. **Given** a user is on the Tools page MCP section, **When** they see the Discover button, **Then** the button is visually consistent with other buttons on the page and is clearly labeled.
2. **Given** a user is on the Tools page MCP section, **When** they click the Discover button, **Then** a new browser tab opens navigating to `https://github.com/mcp`.
3. **Given** a user navigates the Tools page using only a keyboard, **When** they tab to the Discover button, **Then** the button receives visible focus and can be activated with Enter or Space.
4. **Given** a screen reader user navigates the Tools page, **When** the Discover button is focused, **Then** the screen reader announces an accessible label describing the button's purpose (e.g., "Discover MCP integrations on GitHub").

---

### Edge Cases

- What happens when the uploaded MCP definition JSON is syntactically invalid (malformed JSON)? The system should display a clear JSON parse error and not crash or auto-populate the name field.
- What happens when an MCP definition contains `mcpServers` as an empty object (`{}`)? No auto-population should occur, and the system should display an appropriate validation message.
- What happens when the MCP definition has a `command` field but the value is an empty string? The system should treat this as malformed and display a validation error rather than silently inferring `stdio`.
- What happens when the Repository name contains special characters (e.g., dots, underscores)? The bubble should display the full name correctly without breaking layout.
- What happens when the MCP definition uses `url` without `type`? The system should infer `http` as the transport type, similar to how `command` infers `stdio`.
- What happens when the Discover button link (`https://github.com/mcp`) is temporarily unavailable? The button should still open the link in a new tab — availability of the external resource is not the system's responsibility.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept MCP definitions that use `command` and `args` fields without an explicit `type` field, inferring `stdio` as the implicit transport type when `command` is present.
- **FR-002**: System MUST accept MCP definitions with an explicit `type` field set to `http` or `stdio` without error.
- **FR-003**: System MUST display a clear, actionable error message when an MCP definition has neither an explicit `type`, a `command` field, nor a `url` field — indicating the definition is genuinely ambiguous or malformed.
- **FR-004**: System MUST auto-populate the MCP Name field with the first key found under `mcpServers` in an uploaded or pasted MCP definition JSON when the name field is currently empty.
- **FR-005**: System MUST NOT overwrite a user-entered MCP Name when an MCP definition is uploaded or pasted — auto-population applies only when the name field is empty.
- **FR-006**: System SHOULD notify the user when an uploaded MCP definition contains multiple servers under `mcpServers`, while still using the first key for auto-population.
- **FR-007**: System MUST update the MCP documentation link on the Tools page to point to the official GitHub Copilot MCP documentation URL.
- **FR-008**: System MUST display the repository name (not the repository owner) in the Repository field/bubble on the Tools page.
- **FR-009**: System MUST dynamically size the Repository display bubble to fit the repository name text, preventing overflow or truncation for names of varying lengths.
- **FR-010**: System MUST render a "Discover" button in the MCP section of the Tools page that opens `https://github.com/mcp` in a new browser tab.
- **FR-011**: System MUST ensure the Discover button opens the link securely (using `rel="noopener noreferrer"` or equivalent).
- **FR-012**: System MUST ensure the Discover button is accessible — keyboard-navigable, has an appropriate accessible label, and is consistent with the existing Tools page button styling.
- **FR-013**: System MUST infer `http` as the transport type when a server entry contains a `url` field but no explicit `type`.

### Key Entities

- **MCP Definition**: A JSON object containing server configurations under `mcpServers`. Each server entry is keyed by name and contains transport-related fields (`type`, `command`, `args`, `url`, `headers`). The first key under `mcpServers` is used for name auto-population.
- **MCP Server Entry**: An individual server configuration within an MCP Definition. Contains fields that determine transport type: `type` (explicit), `command`/`args` (implies `stdio`), or `url` (implies `http`).
- **Repository Bubble**: A UI element on the Tools page that displays the repository identifier. Should show the repository name portion, dynamically sized to fit the text.

### Assumptions

- The correct GitHub Copilot MCP documentation URL is a stable, publicly accessible URL maintained by GitHub. The implementation team will confirm the exact URL during development.
- The MCP spec convention that `command`-based servers are inherently `stdio` transports is an industry-standard assumption that will not change in the near term.
- When `url` is present without `type`, inferring `http` follows the same convention pattern as `command` implying `stdio`.
- The "first key" under `mcpServers` for auto-population is taken as the first property name returned by `Object.keys(parsed.mcpServers)` in the JavaScript runtime, relying on ECMAScript property enumeration behavior rather than any ordering guarantee from the JSON standard.
- The Discover button target URL (`https://github.com/mcp`) is the official GitHub MCP Registry and will remain stable.
- The Repository bubble currently receives the full repository identifier (e.g., `owner/repo-name`), and the fix involves extracting and displaying only the repo name portion.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of valid MCP definitions using `command`/`args` format (without explicit `type`) are accepted by the creation form without error.
- **SC-002**: Users can create a new MCP integration using a Docker-based command/args definition in under 2 minutes without encountering validation errors.
- **SC-003**: When an MCP definition is pasted with the name field empty, the name field auto-populates correctly within 1 second in 100% of cases.
- **SC-004**: The MCP documentation link resolves to a valid, accessible documentation page with zero broken link reports.
- **SC-005**: The Repository bubble displays the correct repository name (not owner) for 100% of repositories on the Tools page.
- **SC-006**: The Repository bubble accommodates repository names up to 100 characters without overflow or layout breakage.
- **SC-007**: The Discover button is reachable and activatable via keyboard navigation in 100% of tested scenarios.
- **SC-008**: The Discover button successfully opens the GitHub MCP Registry in a new tab when clicked.
- **SC-009**: Zero validation errors are reported for legitimately valid MCP definitions after the fix is deployed.
- **SC-010**: User-entered MCP names are preserved in 100% of cases when an MCP definition is subsequently uploaded or pasted.
