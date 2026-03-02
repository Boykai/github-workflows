# Feature Specification: Update Hashtag Agent Command to Use Chat AI Model with User Description and .github Examples

**Feature Branch**: `016-hashtag-agent-chat-ai`  
**Created**: 2026-03-02  
**Status**: Draft  
**Input**: User description: "Update the hashtag agent command, so that it uses the chat AI agent model to use the user's description as an input and the .github/agents/ and .github/prompts/ as examples of what to create for files and content of files based on the user's description. If you need to save a prompt for the chat agent to consistently generate the same level of detail for new agent file content."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate Agent Files from Natural Language Description (Priority: P1)

A developer types the `#agent` command with a natural language description (e.g., `#agent "Validates pull request titles against conventional commit format"`). The system invokes the chat AI model, passing the user's description along with representative examples from `.github/agents/` and `.github/prompts/` as few-shot context. The AI model generates agent and prompt file content that matches the structural patterns, naming conventions, and content depth of the existing examples. The generated files are committed to the repository at the appropriate paths.

**Why this priority**: This is the core value of the feature. Without AI-driven generation using real examples as context, the command cannot produce files that match established project patterns. Every other story depends on this generation capability.

**Independent Test**: Can be fully tested by issuing the `#agent` command with a description and verifying that the generated `.github/agents/<slug>.agent.md` and `.github/prompts/<slug>.prompt.md` files follow the same YAML frontmatter structure, content depth, and formatting as existing agent/prompt files.

**Acceptance Scenarios**:

1. **Given** a user provides a natural language description via the `#agent` command, **When** the system processes the command, **Then** the chat AI model is invoked with the user's description as the generation target.
2. **Given** the `.github/agents/` directory contains existing agent files, **When** the chat AI model generates a new agent file, **Then** the output uses the same YAML frontmatter schema (description, optional tools, optional handoffs) and markdown system prompt structure as the existing examples.
3. **Given** the `.github/prompts/` directory contains existing prompt files, **When** the chat AI model generates a new prompt file, **Then** the output follows the same routing file format as the existing prompt examples.
4. **Given** the user's description is processed, **When** the AI model returns generated content, **Then** the agent file content includes a meaningful system prompt with instructions appropriate to the described agent's purpose, at a detail level comparable to existing agent files.
5. **Given** the generation completes successfully, **When** the files are committed, **Then** the file paths follow the existing naming convention: `.github/agents/<slug>.agent.md` and `.github/prompts/<slug>.prompt.md`.

---

### User Story 2 - Persistent System Prompt for Consistent Generation Quality (Priority: P1)

A persistent system prompt (meta-prompt) is saved at a stable, well-known path (e.g., in `.github/prompts/`) that instructs the chat AI model on the expected schema, required sections, tone, and detail level for agent files. Every invocation of the `#agent` command includes this system prompt to ensure deterministic quality and consistent formatting across all generated agent files, regardless of who runs the command or when.

**Why this priority**: Without a persistent system prompt, each invocation may produce inconsistent output quality. The meta-prompt is the foundation for repeatability and is used by every generation request. It shares P1 priority because Story 1 depends on it for consistent results.

**Independent Test**: Can be tested by verifying that a system prompt file exists at the expected path, contains instructions about the expected agent file schema and quality standards, and is included in every AI generation request made by the `#agent` command.

**Acceptance Scenarios**:

1. **Given** the feature is deployed, **When** a maintainer inspects the repository, **Then** a persistent system prompt file exists at a stable, documented path within the repository.
2. **Given** the system prompt file exists, **When** the `#agent` command invokes the chat AI model, **Then** the system prompt is always included as part of the AI model's context alongside the user's description and examples.
3. **Given** the system prompt defines expected schema, required sections, tone, and detail level, **When** two different users run the `#agent` command with similar descriptions at different times, **Then** the generated files exhibit consistent structural patterns and comparable content depth.
4. **Given** the system prompt file is human-editable, **When** a maintainer updates the system prompt to adjust quality standards or formatting rules, **Then** subsequent `#agent` invocations reflect the updated standards without any code changes.

---

### User Story 3 - Example-Based Context from Existing Repository Files (Priority: P1)

When the `#agent` command is invoked, the system reads representative files from `.github/agents/` and `.github/prompts/` and passes them to the chat AI model as few-shot examples. The AI model uses these examples to infer the structural patterns, naming conventions, content depth, and formatting expected for new files. The system selects a manageable subset of examples (2–3 representative files) to stay within token limits.

**Why this priority**: The examples are what make the AI model context-aware about this specific project's conventions. Without them, the AI would generate generic output that doesn't match the repository's established patterns.

**Independent Test**: Can be tested by verifying that the AI model request includes content from existing `.github/agents/` and `.github/prompts/` files, and that the generated output demonstrates awareness of the patterns found in those examples (e.g., uses the same YAML frontmatter fields, follows similar system prompt structure).

**Acceptance Scenarios**:

1. **Given** `.github/agents/` contains multiple agent files, **When** the `#agent` command prepares the AI request, **Then** the system selects 2–3 representative agent files and includes their content as few-shot examples.
2. **Given** `.github/prompts/` contains multiple prompt files, **When** the `#agent` command prepares the AI request, **Then** the system selects 2–3 representative prompt files and includes their content as few-shot examples.
3. **Given** the selected examples are passed to the AI model, **When** the model generates new content, **Then** the generated agent file uses the same YAML frontmatter fields and markdown structure observed in the examples.
4. **Given** the examples directory contains more files than the token budget allows, **When** the system selects examples, **Then** it chooses a diverse, representative subset rather than including all files.

---

### User Story 4 - User Feedback on Created File Paths (Priority: P2)

After the `#agent` command completes file generation and commit, the system surfaces the full file paths of all created files to the user. The feedback clearly lists each file that was created and where it lives in the repository, so the developer knows exactly what was produced and can navigate to review the files.

**Why this priority**: File path feedback is important for usability and trust, but the feature functions correctly without it. This is additive polish on top of the core generation flow.

**Independent Test**: Can be tested by running the `#agent` command and verifying the response message includes the file paths of all generated files.

**Acceptance Scenarios**:

1. **Given** the `#agent` command successfully generates and commits files, **When** the command response is displayed to the user, **Then** it includes the full file path for every created file (e.g., `.github/agents/security-reviewer.agent.md`, `.github/prompts/security-reviewer.prompt.md`).
2. **Given** the generation pipeline completes with a summary report, **When** the user reads the report, **Then** the created file paths are clearly distinguishable from other pipeline status information.

---

### User Story 5 - Graceful Handling of Empty Example Directories (Priority: P2)

A developer runs the `#agent` command on a fresh repository where `.github/agents/` or `.github/prompts/` directories are empty or do not yet exist. The system detects the absence of example files and falls back to the default structure and quality standards defined in the persistent system prompt, still producing well-formed agent files.

**Why this priority**: This is an important edge case for new repositories or first-time users, but most repositories using this feature will already have existing agent files. The persistent system prompt provides a reasonable fallback.

**Independent Test**: Can be tested by removing all files from `.github/agents/` and `.github/prompts/`, running the `#agent` command, and verifying the generated files are still well-formed and follow the schema defined in the persistent system prompt.

**Acceptance Scenarios**:

1. **Given** `.github/agents/` is empty or does not exist, **When** the `#agent` command is invoked, **Then** the system does not error and instead relies on the persistent system prompt's default structure to generate the agent file.
2. **Given** `.github/prompts/` is empty or does not exist, **When** the `#agent` command is invoked, **Then** the system does not error and instead relies on the persistent system prompt's default structure to generate the prompt file.
3. **Given** both example directories are empty, **When** the AI model generates files, **Then** the output still conforms to the schema and quality standards defined in the persistent system prompt.

---

### Edge Cases

- What happens when the user's description is ambiguous about whether to create an agent file, a prompt file, or both? The system should default to creating both files (agent + prompt) as this is the established pattern, and let the user edit or remove files during the preview/edit step.
- What happens when the existing example files in `.github/agents/` have varying structures (e.g., some have handoffs, some don't)? The system should select diverse examples that demonstrate both simple and complex patterns, and the AI model should match the complexity level appropriate to the user's description.
- What happens when the total content of example files exceeds the AI model's token limit? The system should prioritize the persistent system prompt and user description, then include as many representative examples as fit within the remaining token budget, truncating or omitting examples as needed.
- What happens when the persistent system prompt file is missing or corrupted? The system should log a warning and fall back to a hardcoded minimal prompt that defines the basic agent file schema, then proceed with generation.
- What happens when the AI model returns content that doesn't match the expected file format (e.g., missing YAML frontmatter)? The system should validate the generated content against the expected schema and either retry the generation or surface an error to the user.
- What happens when the user provides an extremely long description? The system should truncate the description to fit within the AI model's input constraints while preserving the most meaningful content, and inform the user if truncation occurred.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST invoke the chat AI agent model (not a static template engine) to process the user's natural language description and generate agent file content.
- **FR-002**: System MUST include the user's description as the primary generation target in the AI model request.
- **FR-003**: System MUST read existing files from the `.github/agents/` directory and pass a representative subset (2–3 files) as few-shot examples to the chat AI model.
- **FR-004**: System MUST read existing files from the `.github/prompts/` directory and pass a representative subset (2–3 files) as few-shot examples to the chat AI model.
- **FR-005**: System MUST generate output files whose structure, YAML frontmatter schema, and content depth match the patterns observed in existing `.github/agents/` and `.github/prompts/` files.
- **FR-006**: System MUST maintain a persistent system prompt file at a stable, documented path within the repository that defines the expected schema, required sections, tone, and detail level for generated agent files.
- **FR-007**: System MUST include the persistent system prompt as context in every AI generation request made by the `#agent` command.
- **FR-008**: System MUST write generated agent files to `.github/agents/<slug>.agent.md` following the established naming convention.
- **FR-009**: System MUST write generated prompt files to `.github/prompts/<slug>.prompt.md` following the established naming convention.
- **FR-010**: System SHOULD display the file path(s) of all created files to the user upon successful generation.
- **FR-011**: System MUST handle the case where `.github/agents/` or `.github/prompts/` directories are empty or absent by falling back to default structure defined in the persistent system prompt.
- **FR-012**: System MUST select example files that stay within the AI model's token budget, prioritizing the persistent system prompt and user description over example volume.
- **FR-013**: System MUST preserve the existing multi-step creation workflow (preview, edit, confirm) while updating the AI generation step to use the chat AI model with examples.

### Key Entities *(include if feature involves data)*

- **Persistent System Prompt**: A human-editable markdown file stored at a stable repository path that defines the quality standards, expected schema (YAML frontmatter fields, required sections), tone, and formatting rules for generated agent files. Serves as the AI model's instruction set for consistent output.
- **Agent File**: A markdown file with YAML frontmatter (description, optional tools, optional handoffs) and a markdown body containing the agent's system prompt. Stored in `.github/agents/`.
- **Prompt File**: A minimal routing/discovery file with YAML frontmatter referencing an agent slug. Stored in `.github/prompts/`.
- **Example Context**: A curated subset of existing agent and prompt files selected from the repository to serve as few-shot examples for the AI model. Composed of 2–3 representative files from each directory.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Generated agent files match the structural patterns of existing repository agent files at least 90% of the time (same YAML frontmatter fields, same markdown body structure), as validated by manual review of 10 consecutive generation attempts.
- **SC-002**: Users can generate a new agent from a natural language description in under 2 minutes (from typing the command to seeing the preview), comparable to the current command experience.
- **SC-003**: Two different users generating agents with similar descriptions produce files with consistent structure and comparable content depth at least 80% of the time, demonstrating the persistent system prompt's effectiveness.
- **SC-004**: The system successfully generates well-formed agent files when example directories are empty, with no errors or degraded formatting, for 100% of attempts.
- **SC-005**: Generated files are created at the correct repository paths and follow the established naming conventions for 100% of successful generation attempts.
- **SC-006**: The user receives clear feedback listing all created file paths after every successful generation.

## Assumptions

- The existing multi-step creation workflow (parse → resolve project → resolve status → preview → edit → confirm → pipeline) will be preserved; only the AI generation step within this workflow is being updated.
- The chat AI agent model interface already exists and is accessible from the backend; this feature leverages the existing AI service rather than introducing a new AI provider.
- Token limits for the AI model are sufficient to include the persistent system prompt, 2–3 example files from each directory, and the user's description in a single request. If not, examples will be truncated to fit.
- The persistent system prompt will be version-controlled alongside the repository, allowing teams to evolve their quality standards over time.
- The admin-only access restriction for the `#agent` command remains unchanged.
- The existing pipeline steps (database save, branch creation, issue creation, PR creation, project board assignment) are not modified by this feature; only the content generation step is updated.
