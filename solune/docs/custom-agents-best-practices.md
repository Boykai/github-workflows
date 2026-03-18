# Custom GitHub Agents — Best Practices Guide

One of Solune's most powerful features is the ability to create your own AI agents. Whether you need a security reviewer, a documentation writer, or a test specialist, this guide covers everything from file format to prompt engineering.

## Your First Custom Agent

Getting started takes four steps:

1. Create a file in `.github/agents/` named `my-agent.agent.md`
2. Add YAML frontmatter with `description` and `tools`
3. Write your system prompt in the body
4. The agent appears in the Pipeline Builder automatically

The sections below cover each step in detail.

## Overview

Custom GitHub Agents are specialized AI assistants that can be invoked within GitHub Copilot. Each agent is defined by two files in your repository:

1. **`.github/agents/<name>.agent.md`** — The agent definition (YAML frontmatter + system prompt)
2. **`.github/prompts/<name>.prompt.md`** — The prompt routing file (references the agent)

## Agent File Structure

### `.agent.md` — Agent Definition

```yaml
---
name: my-agent-name
description: A brief one-line description of what this agent does
tools: ["read", "edit", "search"]
---

Your system prompt goes here. This is the main instruction set
that defines the agent's behavior, expertise, and constraints.
```

### `.prompt.md` — Prompt Routing

````markdown
```prompt
---
agent: my-agent-name
---
```
````

## YAML Frontmatter Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `name` | string | No | Display name. Defaults to filename (without `.md` or `.agent.md`). |
| `description` | string | **Yes** | One-line summary of the agent's purpose and capabilities. |
| `tools` | list of strings | No | Tools the agent can use. Omit to enable all tools. |
| `target` | string | No | Target environment: `vscode` or `github-copilot`. Defaults to both. |
| `model` | string | No | AI model to use (IDE agents only). |
| `mcp-servers` | object | No | MCP server configurations. Auto-synced by the Agent MCP Sync service (see below). |
| `disable-model-invocation` | boolean | No | If `true`, agent must be manually selected (not auto-invoked). |
| `user-invocable` | boolean | No | If `false`, agent can only be accessed programmatically. |
| `metadata` | object | No | Key-value annotation data. |

## Tool Configuration

### Built-in Tool Aliases

| Alias | Alternatives | Description |
|-------|-------------|-------------|
| `execute` | `shell`, `bash`, `powershell` | Execute shell commands |
| `read` | `Read`, `NotebookRead` | Read file contents |
| `edit` | `Edit`, `MultiEdit`, `Write` | Edit files |
| `search` | `Grep`, `Glob` | Search for files or text |
| `agent` | `custom-agent`, `Task` | Invoke another custom agent |
| `web` | `WebSearch`, `WebFetch` | Fetch URLs and web search |

### MCP Server Tools

Reference MCP tools using the server name prefix:

```yaml
tools: ["read", "edit", "github/get_issue", "playwright/*"]
```

### Tool Configuration Strategies

- **All tools (enforced)**: `tools: ["*"]` — this is the only value permitted in this project. The Agent MCP Sync service automatically overwrites any other value.
- **Reference examples** (used in general GitHub Copilot docs, not in this project): `tools: ["read", "edit", "search"]` or `tools: []`

> **Note:** The Agent MCP Sync service enforces `tools: ["*"]` on every agent file. See [Automatic MCP Sync](#automatic-mcp-sync) below.

## Automatic MCP Sync

The backend `agent_mcp_sync` service keeps every `.github/agents/*.agent.md` file's `mcp-servers` field and `tools` value in sync automatically. This means:

- **Built-in MCPs** (defined in `.github/agents/mcp.json` and mirrored in `backend/src/services/agents/agent_mcp_sync.py`) are merged into every agent file's `mcp-servers` field.
- **User-activated MCPs** from the Tools page are added to agent files when activated and removed when deactivated.
- **`tools: ["*"]`** is unconditionally enforced on every agent definition — any pre-existing restrictive `tools` list is overwritten.
- Duplicate MCP entries are prevented; the sync is idempotent.

### Sync Triggers

The sync runs automatically on:

1. **Application startup** — reconciles drift for the most recent active session.
2. **MCP activation/deactivation** — when a tool is toggled or deleted on the Tools page.
3. **Agent file creation/update** — when an agent is created or updated via the Agents service.

### Built-in MCPs

The following MCP servers are built-in and always present in every agent file:

| Server | Type | Purpose |
|--------|------|---------|
| `context7` | HTTP | Library resolution and documentation lookup |
| `CodeGraphContext` | Local (uvx) | Code graph analysis and navigation |

These are defined in `.github/agents/mcp.json` and must stay in sync with the `BUILTIN_MCPS` constants in both `backend/src/services/agents/agent_mcp_sync.py` and `frontend/src/lib/buildGitHubMcpConfig.ts`. The backend test suite (`test_agent_mcp_sync.py`) validates the shape and contents of `BUILTIN_MCPS` — if you add or change a built-in MCP, update all three locations and run the tests to catch drift.

## Prompt Writing Guidelines

### Structure Your System Prompt

1. **Start with a role statement**: "You are a [role] focused on [domain]."
2. **Define responsibilities**: Use a bulleted list of specific tasks.
3. **Set boundaries**: Specify what the agent should and should NOT do.
4. **Include output format**: Describe how responses should be structured.
5. **Add examples**: Show expected input/output patterns when helpful.

### Best Practices

- **Be specific**: "Review Python files for SQL injection vulnerabilities" is better than "Review code for security."
- **Set constraints**: "Only modify test files" or "Never change production code."
- **Define scope**: Tell the agent exactly which file types, patterns, or areas to focus on.
- **Keep prompts focused**: Each agent should have ONE clear purpose.
- **Use markdown formatting**: Headings, lists, and code blocks make prompts clearer.
- **Stay under 30,000 characters**: This is the GitHub-enforced limit.

### Anti-Patterns to Avoid

- **Vague instructions**: "Be helpful" doesn't guide behavior.
- **Conflicting rules**: "Always add tests" + "Never modify existing files" creates confusion.
- **Overly broad scope**: An agent that does everything does nothing well.
- **Missing context**: Don't assume the agent knows your project structure.

## Example Agent Configurations

### 1. Testing Specialist

```yaml
---
name: test-specialist
description: Focuses on test coverage, quality, and testing best practices without modifying production code
---

You are a testing specialist focused on improving code quality through comprehensive testing. Your responsibilities:

- Analyze existing tests and identify coverage gaps
- Write unit tests, integration tests, and end-to-end tests following best practices
- Review test quality and suggest improvements for maintainability
- Ensure tests are isolated, deterministic, and well-documented
- Focus only on test files and avoid modifying production code unless specifically requested

Always include clear test descriptions and use appropriate testing patterns for the language and framework.
```

### 2. Security Reviewer

```yaml
---
name: security-reviewer
description: Reviews code for security vulnerabilities, insecure patterns, and compliance issues
tools: ["read", "search"]
---

You are a security-focused code reviewer. Your responsibilities:

- Scan code for common vulnerability patterns (OWASP Top 10)
- Identify insecure dependencies and suggest updates
- Review authentication and authorization implementations
- Check for sensitive data exposure (API keys, credentials, PII)
- Validate input sanitization and output encoding
- Review cryptographic implementations for correctness

When reporting issues:
1. Classify severity (Critical, High, Medium, Low)
2. Explain the vulnerability with a concrete attack scenario
3. Provide a specific fix with code example
4. Reference relevant CWE or OWASP identifiers

Never modify production code directly. Only create reports and recommendations.
```

### 3. Implementation Planner

```yaml
---
name: implementation-planner
description: Creates detailed implementation plans and technical specifications in markdown format
tools: ["read", "search", "edit"]
---

You are a technical planning specialist focused on creating comprehensive implementation plans. Your responsibilities:

- Analyze requirements and break them down into actionable tasks
- Create detailed technical specifications and architecture documentation
- Generate implementation plans with clear steps, dependencies, and timelines
- Document API designs, data models, and system interactions
- Create markdown files with structured plans that development teams can follow

Always structure your plans with clear headings, task breakdowns, and acceptance criteria. Include considerations for testing, deployment, and potential risks. Focus on creating thorough documentation rather than implementing code.
```

### 4. Documentation Writer

```yaml
---
name: docs-writer
description: Creates and maintains project documentation including READMEs, API docs, and guides
tools: ["read", "edit", "search"]
---

You are a technical documentation specialist. Your responsibilities:

- Write clear, concise README files and getting-started guides
- Document API endpoints with request/response examples
- Create architecture decision records (ADRs)
- Maintain changelog entries following Keep a Changelog format
- Write inline code documentation and JSDoc/docstrings

Documentation style guidelines:
- Use active voice and present tense
- Include practical examples for every concept
- Structure with clear headings and table of contents for longer docs
- Keep paragraphs short (3-5 sentences max)
- Use code blocks with language identifiers for syntax highlighting
```

## File Naming Conventions

- Agent names may only contain: `.`, `-`, `_`, `a-z`, `A-Z`, `0-9`
- Use kebab-case for multi-word names: `security-reviewer`, `test-specialist`
- Keep names descriptive but concise (2-4 words)
- The filename (without `.agent.md`) becomes the agent identifier

## Organization-Level Agents

- **Repository-level**: Place in `.github/agents/` for single-repo agents
- **Organization-level**: Place in `.github-private` repository's `agents/` directory
- Repository-level agents override organization-level agents with the same name

## Further Reading

- [GitHub Custom Agents Configuration Reference](https://docs.github.com/en/copilot/reference/custom-agents-configuration)
- [Creating Custom Agents for Copilot](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent/create-custom-agents)
- [Custom Agents Customization Library](https://docs.github.com/en/copilot/tutorials/customization-library/custom-agents)

---

## What's Next?

- [Learn about agent pipelines](agent-pipeline.md) — orchestrate agents into workflows
- [Explore the architecture](architecture.md) — understand how agents fit into the system
- [Troubleshoot common issues](troubleshooting.md) — when agents don't behave as expected
