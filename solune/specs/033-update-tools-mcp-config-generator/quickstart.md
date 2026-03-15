# Quickstart: Update Tools Page — GitHub.com MCP Configuration Generator

**Feature**: 033-update-tools-mcp-config-generator | **Date**: 2026-03-10

## Prerequisites

- Node.js 18+ and npm
- Repository cloned and frontend dependencies installed
- A project with at least one MCP tool configured (optional — built-in MCPs are always shown)

## Setup

```bash
cd frontend
npm install
```

## Development

Start the development server:

```bash
npm run dev
```

Navigate to the Tools page in the application. The "MCP Configuration for GitHub Agents" section displays the generated configuration.

## Key Files

| File | Purpose |
|------|---------|
| `frontend/src/lib/buildGitHubMcpConfig.ts` | Core config generation utility |
| `frontend/src/lib/buildGitHubMcpConfig.test.ts` | Unit tests for the utility |
| `frontend/src/components/tools/GitHubMcpConfigGenerator.tsx` | Config generator UI component |
| `frontend/src/components/tools/ToolsPanel.tsx` | Parent container (renders the generator) |
| `frontend/src/components/tools/ToolsEnhancements.test.tsx` | Component integration tests |

## Running Tests

```bash
# Unit tests for the config builder
cd frontend
npm run test -- src/lib/buildGitHubMcpConfig.test.ts

# Component tests
npm run test -- src/components/tools/ToolsEnhancements.test.tsx

# All frontend tests
npm run test

# Linting
npm run lint

# Type checking
npm run type-check
```

## How It Works

1. **ToolsPanel** loads the user's MCP tools via `useToolsList(projectId)` (TanStack Query)
2. **GitHubMcpConfigGenerator** receives the full `tools[]` array as a prop
3. The component filters for active tools (`is_active === true`)
4. **buildGitHubMcpConfig** merges active tool servers with Built-In MCPs (Context7, Code Graph Context)
5. The merged configuration is displayed as syntax-highlighted JSON in a read-only code block
6. Users click "Copy to Clipboard" to copy the JSON for pasting into GitHub.com

## Using the Generated Configuration

1. Open the Tools page in the application
2. Ensure your desired MCP tools are active (toggle them on)
3. Review the generated JSON configuration in the code block
4. Click "Copy to Clipboard"
5. Navigate to your GitHub.com repository or organization settings
6. Paste the configuration into the Custom GitHub Agents MCP configuration field
7. Save the settings — your remote agents will now have access to the configured MCP servers

## Adding a New Built-In MCP

To add a new Built-In MCP, edit the `BUILTIN_MCPS` array in `frontend/src/lib/buildGitHubMcpConfig.ts`:

```typescript
export const BUILTIN_MCPS: readonly BuiltInMcp[] = [
  // ... existing entries ...
  {
    name: 'New Built-In',
    serverKey: 'new-builtin',
    config: {
      type: 'http',
      url: 'https://example.com/mcp',
      tools: ['*'],
    },
  },
] as const;
```

The new entry will automatically appear in all generated configurations with a "Built-In" badge.
