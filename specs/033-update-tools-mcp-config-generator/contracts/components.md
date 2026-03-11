# Component Contracts: Update Tools Page — GitHub.com MCP Configuration Generator

**Feature**: 033-update-tools-mcp-config-generator | **Date**: 2026-03-10

## New Components

### GitHubMcpConfigGenerator

**File**: `frontend/src/components/tools/GitHubMcpConfigGenerator.tsx`
**Role**: Replaces `GitHubToolsetSelector`. Generates and displays a ready-to-copy GitHub.com MCP configuration block.

#### Props Interface

```typescript
interface GitHubMcpConfigGeneratorProps {
  tools: McpToolConfig[];  // All project tools (active + inactive)
}
```

#### Behavior Contract

| Behavior | Description |
|----------|-------------|
| **Active tool filtering** | Filters `tools` to `is_active === true` before generating config |
| **Config generation** | Calls `buildGitHubMcpConfig(activeTools)` via `useMemo` |
| **Built-In inclusion** | Always includes Context7 and Code Graph Context in output |
| **Built-In badges** | Renders "Built-In" badge on entries where `entry.builtin === true` |
| **Copy to clipboard** | Copies `configJson` via Clipboard API with execCommand fallback |
| **Copy feedback** | Shows check icon + "Copied!" text for 2 seconds after successful copy |
| **Empty state** | When no user tools are active, shows guidance message with Sparkles icon |
| **Real-time updates** | Re-renders automatically when `tools` prop changes (via TanStack Query) |
| **Syntax highlighting** | Renders JSON with color-coded keys (sky), strings (emerald), numbers (amber), booleans (violet) |
| **Statistics display** | Shows count of active project MCPs and count of Built-In MCPs |

#### Visual Sections (top to bottom)

1. **Header**: Title "MCP Configuration for GitHub Agents" + description
2. **Info callout**: Contextual help about the configuration purpose
3. **Stats grid**: Two cards — active project MCPs count + always-included Built-In count
4. **MCP entry list**: Pill badges for each server, with "Built-In" label on built-in entries
5. **Empty state** (conditional): Guidance when no user tools are active
6. **Code block**: Syntax-highlighted JSON with line numbers + "Copy to Clipboard" button

#### Accessibility

- Copy button uses `aria-live="polite"` for screen reader feedback
- Code block uses monospace font with adequate contrast
- Line numbers are `select-none` to prevent accidental selection

---

### buildGitHubMcpConfig (Utility Function)

**File**: `frontend/src/lib/buildGitHubMcpConfig.ts`
**Role**: Pure function that merges user tools + built-in MCPs into a GitHub.com MCP configuration.

#### Function Signature

```typescript
export function buildGitHubMcpConfig(tools: McpToolConfig[]): {
  configJson: string;
  entries: McpServerEntry[];
}
```

#### Contract

| Input | Output |
|-------|--------|
| Empty array | Built-In MCPs only (Context7 + CodeGraphContext) |
| Array with active tools | User servers + Built-In MCPs (deduped by key) |
| Tools with malformed JSON | Skipped silently; valid tools + built-ins still included |
| Tool with key collision on built-in | User version wins; built-in is not included |
| Multiple tools with same key | First tool wins |

#### Helper: extractServersFromTool

```typescript
export function extractServersFromTool(tool: McpToolConfig): McpServerEntry[]
```

- Parses `tool.config_content` as JSON
- Returns `McpServerEntry[]` from `mcpServers` object
- Returns empty array for malformed JSON or missing `mcpServers`

---

## Modified Components

### ToolsPanel

**File**: `frontend/src/components/tools/ToolsPanel.tsx`
**Change**: Imports and renders `GitHubMcpConfigGenerator` instead of `GitHubToolsetSelector`.

```typescript
// Line 19: Import
import { GitHubMcpConfigGenerator } from './GitHubMcpConfigGenerator';

// Line 217: Render
<GitHubMcpConfigGenerator tools={tools} />
```

**No other changes** to ToolsPanel logic, state, or props.

---

## Removed Components

### GitHubToolsetSelector (Legacy)

**File**: `frontend/src/components/tools/GitHubToolsetSelector.tsx`
**Status**: To be deleted. Not imported anywhere in the codebase.
**Reason**: Fully replaced by `GitHubMcpConfigGenerator`.

---

## Component Hierarchy

```text
ToolsPage
└── ToolsPanel (projectId)
    ├── RepoConfigPanel
    ├── Grid
    │   ├── McpPresetsGallery
    │   └── GitHubMcpConfigGenerator (tools) ← NEW (replaces GitHubToolsetSelector)
    ├── Tool Archive Section
    │   ├── Search Input
    │   └── ToolCard[] (filtered)
    ├── UploadMcpModal
    └── EditRepoMcpModal
```

## Test Contracts

### Unit Tests: buildGitHubMcpConfig.test.ts

| Test | Assertion |
|------|-----------|
| Built-in MCPs with no tools | Returns BUILTIN_MCPS.length entries, all `builtin: true` |
| Merge user + built-in | Returns user entries + built-in entries |
| User overrides built-in key | User version used, `builtin: false` |
| Deduplicate across tools | First tool's server key wins |
| Valid JSON output | `JSON.parse(configJson)` does not throw |
| Malformed config skipped | Only valid tools + built-ins in output |

### Component Tests: ToolsEnhancements.test.tsx

| Test | Assertion |
|------|-----------|
| Renders built-in badges | "Built-In" text appears for Context7 and CodeGraphContext |
| Shows user tools | User tool server keys appear in entry list |
| Copy button exists | "Copy to Clipboard" button is rendered |
| Empty state shows guidance | When no active user tools, guidance message is displayed |
| Active-only filtering | Inactive tools excluded from configuration |
