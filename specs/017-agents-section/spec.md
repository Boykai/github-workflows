# Feature Specification: Agents Section on Project Board

**Feature Branch**: `017-agents-section`  
**Created**: 2026-03-03  
**Status**: Draft  
**Input**: User description: "Add an Agents section under Chores on the project-board page to create Custom GitHub Agents with .agent.md and .prompt.md files, reusing existing agent creation code. Create docs for best practices."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Agents List on Project Board (Priority: P1)

As a user viewing the project board, I want to see an "Agents" section displayed below the existing "Chores" section in the right-side panel, so that I can see all Custom GitHub Agents configured for my repository at a glance.

**Why this priority**: Without the ability to view agents, no other agent management functionality is useful. This is the foundation of the feature.

**Independent Test**: Can be fully tested by navigating to the project board page with a selected project and verifying the "Agents" section renders below Chores with a list of existing agents (or an empty state with guidance).

**Acceptance Scenarios**:

1. **Given** a user is on the project board page with a project selected, **When** the page loads, **Then** an "Agents" section is displayed below the "Chores" section in the right-side panel.
2. **Given** the repository has no custom agents defined, **When** the Agents section loads, **Then** an empty state is shown with a brief explanation and a button to add an agent.
3. **Given** the repository has existing custom agents (`.github/agents/*.agent.md` files), **When** the Agents section loads, **Then** each agent is displayed as a card showing its name, description, and a status badge ("Pending PR" or "Active").
4. **Given** an agent has just been created (PR not yet merged), **When** the user views the Agent Pipeline settings, **Then** the new agent is immediately available for assignment to status-column mappings.

---

### User Story 2 - Create a New Custom GitHub Agent (Priority: P1)

As a user, I want to click "Add Agent" in the Agents section and provide a name and detailed content (description + prompt body) to create a new Custom GitHub Agent, so that the system generates and commits the `.github/agents/<name>.agent.md` and `.github/prompts/<name>.prompt.md` files to the repository.

**Why this priority**: This is the core value proposition — creating agents directly from the project board UI without needing to manually create files. Shares equal priority with US1 since the section must exist to create agents.

**Independent Test**: Can be fully tested by clicking "Add Agent", entering a name like "security-reviewer" and detailed content including a description and system prompt, submitting, and verifying that a branch is created with the two configuration files and a pull request is opened.

**Acceptance Scenarios**:

1. **Given** a user clicks "Add Agent" in the Agents section, **When** a modal or form opens, **Then** the user sees input fields for agent name and detailed text content (the agent prompt/instructions).
2. **Given** a user fills in a valid agent name and detailed content, **When** they submit the form, **Then** the system creates a branch, commits `.github/agents/<slug>.agent.md` and `.github/prompts/<slug>.prompt.md` files, and opens a pull request.
3. **Given** a user provides sparse input (brief description without structured content), **When** they submit, **Then** the system uses a chat-based refinement flow (similar to the Chores chat flow) to help the user expand their input into a complete agent configuration.
4. **Given** agent creation succeeds, **When** the result is returned, **Then** the user sees a success confirmation with a link to the created pull request.
5. **Given** an agent with the same name already exists, **When** the user attempts to create it, **Then** a validation error is shown indicating the name conflict.

---

### User Story 3 - AI-Assisted Agent Content Refinement (Priority: P2)

As a user who provides a brief or sparse description for an agent, I want the system to guide me through a conversational refinement flow to produce a complete and well-structured agent configuration, so that I can create high-quality agents without needing to know the exact markdown format.

**Why this priority**: Improves usability significantly but the core create-and-commit flow works without it. Users who provide detailed content can skip this step entirely.

**Independent Test**: Can be tested by entering a sparse description like "reviews code for security issues" and verifying the chat flow asks clarifying questions and produces a full agent configuration with a description, tools list, and system prompt.

**Acceptance Scenarios**:

1. **Given** a user enters sparse input (e.g., ≤15 words, no markdown structure), **When** they submit, **Then** the system transitions to a multi-turn chat refinement interface.
2. **Given** the chat flow is active, **When** the AI asks clarifying questions and the user responds, **Then** the system generates a complete agent preview showing name, description, tools, and system prompt.
3. **Given** a preview is displayed, **When** the user confirms, **Then** the agent files are generated and committed using the same pipeline as direct creation.

---

### User Story 4 - Delete an Existing Agent (Priority: P2)

As a user, I want to remove an agent from the Agents section, so that obsolete or incorrect agent configurations can be cleaned up.

**Why this priority**: Important for lifecycle management but not required for the initial value proposition of creating agents.

**Independent Test**: Can be tested by displaying a list of agents, clicking delete on one, confirming, and verifying the agent entry is removed from the UI.

**Acceptance Scenarios**:

1. **Given** an agent card is displayed in the Agents section, **When** the user clicks the delete action, **Then** a confirmation prompt appears.
2. **Given** the user confirms deletion, **When** the deletion completes, **Then** the system creates a GitHub Issue and opens a PR to remove the agent's `.agent.md` and `.prompt.md` files from the repository, and the local SQLite record (if present) is removed.
3. **Given** the deletion PR is merged, **When** the Agents section reloads, **Then** the agent no longer appears in the merged list from either source.

---

### User Story 5 - Best Practices Documentation (Priority: P3)

As a developer or administrator, I want to reference documentation about best practices for writing Custom GitHub Agent markdown files, so that I can create effective, well-structured agent configurations.

**Why this priority**: Documentation supports the feature but is not required for core functionality. Users can create agents without reading documentation.

**Independent Test**: Can be tested by verifying the documentation file exists in the docs directory and contains actionable guidance about the `.agent.md` and `.prompt.md` file formats, YAML frontmatter properties, prompt writing tips, and examples.

**Acceptance Scenarios**:

1. **Given** a developer accesses the documentation, **When** they open the best practices guide, **Then** it contains sections on agent file structure, YAML frontmatter properties, prompt writing guidelines, tool configuration, and examples.
2. **Given** the documentation exists, **When** a user views the Agents section empty state, **Then** a link or reference to the documentation is provided.

---

### User Story 6 - Edit an Existing Agent (Priority: P3)

As a user, I want to edit an existing agent's configuration (name, description, tools, system prompt) from the Agents section, so that I can update agent behavior without deleting and recreating it.

**Why this priority**: Editing is a natural lifecycle extension but not required for the initial value proposition. Users can delete and recreate agents as a workaround.

**Independent Test**: Can be tested by clicking an edit action on an agent card, modifying the content, submitting, and verifying a PR is opened with the updated `.agent.md` and `.prompt.md` files.

**Acceptance Scenarios**:

1. **Given** an agent card is displayed in the Agents section, **When** the user clicks the edit action, **Then** a form opens pre-populated with the agent's current name, description, and system prompt.
2. **Given** the user modifies the agent content and submits, **When** the update completes, **Then** the system opens a PR with the modified `.agent.md` and `.prompt.md` files.
3. **Given** the edit PR is merged, **When** the Agents section reloads, **Then** the agent card reflects the updated content.

---

### Edge Cases

- What happens when the user enters a name containing invalid characters (spaces, special characters) that cannot be used as a filename?
  - The system slugifies the name (lowercase, hyphens for spaces, strip invalid characters) and shows the resulting slug in a preview before committing.
- What happens when the GitHub API fails during branch creation or file commit?
  - The system displays a clear error message indicating which step failed, consistent with the existing agent creation pipeline's per-step status reporting.
- What happens when the repository's default branch has been updated since the user started creating an agent?
  - The system fetches the latest HEAD OID at commit time, reducing the risk of conflicts.
- What happens when the user enters extremely long prompt text (>30,000 characters)?
  - The system validates against GitHub's 30,000 character limit for agent prompts and shows a validation error before attempting to commit.
- How does the system handle duplicate agent slugs that differ only in casing or special characters?
  - Slugification normalizes names to lowercase with hyphens, so "Security Bot" and "security-bot" resolve to the same slug. The duplicate check catches this.
- What happens when a pending agent (PR not merged) is assigned to the Agent Pipeline and the PR is later closed without merging?
  - The agent remains in SQLite with a "Pending PR" status. The pipeline mapping persists but the agent will not function until it is recreated or the PR is reopened and merged.

## Clarifications

### Session 2026-03-03

- Q: Who should be able to use the Agents section (view, create, delete)? → A: Same access level as Chores — any authenticated user with a valid session (no admin restriction).
- Q: Where should the Agents section read its agent list from? → A: Both SQLite and GitHub repo, deduplicated by slug. SQLite is the local representation until the PR is merged; GitHub repo is the source of truth post-merge.
- Q: What should "delete" do given agents exist in both SQLite and GitHub repo? → A: Deletion always opens a GitHub Issue and PR to remove the agent's `.agent.md` and `.prompt.md` files from the repo, applying the same PR-based source-of-truth pattern as creation. Local SQLite record is also removed.
- Q: Should users be able to edit existing agents from the Agents section? → A: Yes, at P3 priority. An edit action opens the agent content for modification and opens a PR with the updated files.
- Q: Should agent cards show lifecycle status, and when are agents available for the Agent Pipeline? → A: Yes, show a status badge ("Pending PR" vs. "Active"). Agents are immediately available to add to the Agent Pipeline (status-column mappings) upon creation, without waiting for PR merge.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display an "Agents" section below the "Chores" section in the right-side panel of the project board page.
- **FR-002**: System MUST list agents by merging data from the local SQLite database and the repository's `.github/agents/` directory, deduplicated by slug. SQLite provides the local representation for agents whose PRs have not yet been merged; the GitHub repo is the source of truth for merged agents. Each agent card shows its name and description.
- **FR-003**: System MUST provide an "Add Agent" action that opens a form for entering an agent name and detailed content (description + system prompt).
- **FR-004**: System MUST generate two files when creating a new agent:
  - `.github/agents/<slug>.agent.md` — YAML frontmatter (description, optional tools) and system prompt body
  - `.github/prompts/<slug>.prompt.md` — prompt routing file referencing the agent slug
- **FR-005**: System MUST create a feature branch, commit the agent files, and open a pull request for each new agent creation.
- **FR-006**: System MUST reuse the existing agent creation service logic (`agent_creator.py`) for file generation, slug creation, duplicate checking, GitHub commit workflows, and PR creation to ensure DRY code.
- **FR-007**: System MUST detect sparse input and route the user to an AI-assisted chat refinement flow to produce a complete agent configuration.
- **FR-008**: System MUST validate that the agent name does not conflict with existing agents before committing files.
- **FR-009**: System MUST display a success confirmation with a link to the created pull request upon successful agent creation.
- **FR-010**: System MUST allow users to delete an agent from the Agents section. Deletion MUST create a GitHub Issue and open a PR that removes the agent's `.agent.md` and `.prompt.md` files from the repository. The local SQLite record (if present) is also removed. This follows the same PR-based source-of-truth pattern as agent creation.
- **FR-011**: System MUST enforce the valid character set for agent filenames: `.`, `-`, `_`, `a-z`, `A-Z`, `0-9`.
- **FR-012**: System MUST validate that agent prompt content does not exceed the 30,000 character limit.
- **FR-013**: System MUST include best practices documentation for Custom GitHub Agents in the project's docs directory.
- **FR-014**: System MUST use the same access control as the Chores feature — any authenticated user with a valid session can view, create, and delete agents (no admin-only restriction).
- **FR-015**: System MUST allow users to edit an existing agent's configuration (name, description, tools, system prompt) from the Agents section. Editing opens the current content for modification and opens a PR with the updated files. This is a P3 priority feature.
- **FR-016**: System MUST display a status badge on each agent card indicating its lifecycle state: "Pending PR" (created but PR not yet merged) or "Active" (files exist in the repository's default branch).
- **FR-017**: System MUST make newly created agents immediately available for assignment to the Agent Pipeline (status-column mappings) upon creation, without waiting for the PR to be merged.

### Key Entities

- **Agent**: Represents a Custom GitHub Agent configuration. Key attributes: name (display name), slug (file-safe identifier), description (purpose summary), system prompt (behavioral instructions), tools (list of tool identifiers the agent can use).
- **Agent File Pair**: The two-file representation of an agent in the repository: the `.agent.md` definition file and the `.prompt.md` routing file.
- **Agent Record (local)**: The SQLite row representing an agent that has been created via the UI but whose PR has not yet merged. Tracks name, slug, description, branch, issue number, and PR number.
- **Agent Creation Session**: A stateful workflow tracking the user through name entry, content input, optional chat refinement, preview, and commit pipeline execution.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can create a new Custom GitHub Agent from the project board in under 3 minutes when providing detailed content directly.
- **SC-002**: Users who provide sparse input are guided through a refinement flow and produce a complete agent configuration within 5 conversational turns.
- **SC-003**: 100% of created agents result in valid `.agent.md` and `.prompt.md` files that conform to the GitHub Custom Agents format specification.
- **SC-004**: The Agents section loads and displays the agent list within the same time frame as the existing Chores section.
- **SC-005**: No code duplication exists between the Agents section creation pipeline and the existing `#agent` chat command — shared logic is extracted into reusable functions.
- **SC-006**: Best practices documentation covers all YAML frontmatter properties, prompt writing guidelines, tool configuration, and includes at least 3 example agent configurations.

## Assumptions

- The user has a GitHub repository connected to the project board with write access.
- The existing `agent_creator.py` service, GitHub Projects service, and AI agent service are functional and accessible.
- The frontend follows the same component patterns as the existing Chores section (panel → cards → modal/form → hooks → API service).
- The backend already supports the GitHub API operations needed (branch creation, file commit, PR creation) through the `github_projects_service`.
- Authentication follows the Chores pattern: any authenticated user with a valid session can use the Agents section (distinct from the `#agent` chat command which is admin-only).
- The sparse-to-rich input detection heuristic from the Chores feature is suitable for agent content as well.
