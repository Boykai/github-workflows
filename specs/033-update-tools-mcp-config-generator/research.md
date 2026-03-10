# Research: Update Tools Page — GitHub.com MCP Configuration Generator

**Feature**: 033-update-tools-mcp-config-generator | **Date**: 2026-03-10

## Research Tasks

### R1: GitHub.com MCP Configuration Schema

**Task**: Verify the correct schema for GitHub.com remote Custom GitHub Agents MCP configuration.

**Decision**: Use the `mcpServers` JSON object format with typed server entries.

**Rationale**: The GitHub.com Custom Agents MCP configuration uses a top-level `mcpServers` key containing named server entries. Each server entry specifies a `type` (`http`, `sse`, `local`, `stdio`), connection details (`url` for HTTP/SSE, `command`/`args` for local/stdio), optional `tools` array (or `"*"` for all), optional `headers` object, and optional `env` object. This schema is already implemented in the existing `buildGitHubMcpConfig.ts` utility and validated by the backend `ToolsService.validate_mcp_config()` method. The allowed server types are: `http`, `stdio`, `local`, `sse`.

**Alternatives considered**:
- YAML output format: Rejected because GitHub.com expects JSON for MCP configuration and the existing codebase consistently uses JSON for MCP configs.
- Flat key-value format: Rejected as it doesn't support the nested server configuration structure required by the schema.

**Example output format**:

```json
{
  "mcpServers": {
    "context7": {
      "type": "http",
      "url": "https://mcp.context7.com/mcp",
      "tools": ["resolve-library-id", "get-library-docs"],
      "headers": {
        "CONTEXT7_API_KEY": "$COPILOT_MCP_CONTEXT7_API_KEY"
      }
    },
    "CodeGraphContext": {
      "type": "local",
      "command": "uvx",
      "args": ["--from", "codegraphcontext", "cgc", "mcp", "start"],
      "tools": ["*"]
    }
  }
}
```

---

### R2: Built-In MCP Identification and Management

**Task**: Determine which MCPs are "Built-In" and how they should be handled in the configuration.

**Decision**: Built-In MCPs are hardcoded in the `BUILTIN_MCPS` constant array in `buildGitHubMcpConfig.ts`. They are always included in the generated configuration regardless of user selections.

**Rationale**: The spec mandates that Built-In MCPs (Context7, Code Graph Context) are included unconditionally. Hardcoding them as a typed constant ensures they cannot be accidentally removed, are always present in the output, and can be extended by adding new entries to the array. The `builtin: true` flag on `McpServerEntry` enables UI differentiation (badges).

**Built-In MCPs**:

| Name | Server Key | Type | Purpose |
|------|-----------|------|---------|
| Context7 | `context7` | HTTP | Documentation search via `resolve-library-id` and `get-library-docs` tools |
| Code Graph Context | `CodeGraphContext` | Local | Code analysis via `uvx` command with `codegraphcontext` package |

**Alternatives considered**:
- Store built-ins in the database: Rejected — adds unnecessary backend complexity for a small, static list. Constitution Principle V (Simplicity) favors the hardcoded approach.
- Fetch built-ins from backend API: Rejected — no benefit since the list is static and the frontend is the only consumer.
- Make built-ins user-configurable: Rejected — the spec explicitly requires they be included automatically and unconditionally.

---

### R3: Clipboard API Best Practices

**Task**: Research clipboard copy patterns for modern web applications.

**Decision**: Use the `navigator.clipboard.writeText()` API as the primary method with a `document.execCommand('copy')` textarea fallback for insecure contexts.

**Rationale**: The Clipboard API (`navigator.clipboard`) is the modern standard supported by all current browsers. However, it requires a secure context (HTTPS) or localhost. A fallback using a temporary textarea and `execCommand('copy')` handles development environments and older browsers. The component provides visual feedback via a state toggle (check icon + "Copied!" text for 2 seconds).

**Alternatives considered**:
- `navigator.clipboard` only (no fallback): Rejected — breaks in HTTP-only development contexts.
- Third-party clipboard library (e.g., clipboard.js): Rejected — adds unnecessary dependency for a simple operation. Constitution Principle V favors using native APIs.

---

### R4: Real-Time Reactivity Pattern

**Task**: Research how MCP toggle changes propagate to the config generator.

**Decision**: Leverage existing TanStack Query cache invalidation. The `useToolsList` hook provides reactive `tools` array that automatically updates when tools are created, updated, or deleted via mutations. The `GitHubMcpConfigGenerator` component receives `tools` as a prop from `ToolsPanel` and uses `useMemo` to recompute the configuration when the tools array changes.

**Rationale**: The existing hook infrastructure already provides the reactivity needed. TanStack Query mutations in `useToolsList` invalidate the tools query cache on success, causing automatic re-fetch. The component's `useMemo` dependencies ensure the configuration JSON is recomputed only when the active tools list changes. No additional state management or subscriptions are needed.

**Alternatives considered**:
- WebSocket/SSE for real-time updates: Rejected — overkill for a single-user, single-page context. The user toggles MCPs on the same page, so mutation-based cache invalidation is sufficient.
- Global state store (Zustand/Redux): Rejected — TanStack Query already serves as the server state cache. Adding another store violates DRY.

---

### R5: Syntax Highlighting Approach

**Task**: Research syntax highlighting for JSON code blocks in React.

**Decision**: Implement a lightweight, custom JSON syntax highlighter using regex-based line parsing. The highlighter tokenizes JSON strings, keys, values, numbers, booleans, and null into styled spans with Tailwind CSS classes.

**Rationale**: The JSON output is well-structured and predictable (generated by `JSON.stringify`). A custom highlighter (~90 lines) avoids adding heavy dependencies like Prism.js (~30KB) or Shiki (~200KB) for a single code block. The custom approach provides full control over the color scheme to match the application's design system.

**Alternatives considered**:
- Prism.js / react-syntax-highlighter: Rejected — significant bundle size increase for a single use case. Constitution Principle V favors simplicity.
- No highlighting (plain `<pre>`): Rejected — the spec requires syntax highlighting for readability.
- Monaco Editor (read-only): Rejected — massive overkill for a non-editable display block.

---

### R6: Legacy Component Cleanup

**Task**: Research the impact of removing the legacy `GitHubToolsetSelector` component.

**Decision**: The `GitHubToolsetSelector` component can be safely removed. It is not imported or referenced in `ToolsPanel.tsx` or any other file — it has already been replaced by `GitHubMcpConfigGenerator` in the component tree.

**Rationale**: Searching the codebase confirms `GitHubToolsetSelector` is not imported anywhere except its own definition file. The `GitHubMcpConfigGenerator` component comment explicitly states it "Replaces the old GitHubToolsetSelector." Removing the dead code keeps the codebase clean per Constitution Principle V.

**Alternatives considered**:
- Keep as deprecated: Rejected — no consumers exist, and keeping dead code adds confusion.
- Gradual deprecation with warnings: Rejected — the component is internal, not a public API. No deprecation period needed.

---

## Summary of Decisions

| # | Topic | Decision | Key Rationale |
|---|-------|----------|---------------|
| R1 | Config schema | `mcpServers` JSON format | Matches GitHub.com spec; existing codebase pattern |
| R2 | Built-In MCPs | Hardcoded constant array with `builtin` flag | Static list; simple; frontend-only consumer |
| R3 | Clipboard | Clipboard API + execCommand fallback | Modern standard + insecure context support |
| R4 | Reactivity | TanStack Query mutation invalidation + useMemo | Existing infrastructure; zero new dependencies |
| R5 | Syntax highlighting | Custom lightweight JSON tokenizer | Small bundle; full design control; predictable input |
| R6 | Legacy cleanup | Remove GitHubToolsetSelector | Zero consumers; dead code removal |

All NEEDS CLARIFICATION items from Technical Context have been resolved. No blockers remain for Phase 1 design.
