# Tools

The Tools page lets you manage MCP (Model Context Protocol) tool configurations that extend what your AI agents can do. By uploading MCP definitions, you give agents access to additional capabilities during pipeline execution.

## What You See

- **Stats bar** — total number of tools configured for the current project
- **Tools list** — all uploaded MCP configurations, each shown as a card
- **Upload control** — button or area to upload new MCP tool definitions
- **MCP documentation link** — quick reference to the MCP specification

If no tools have been configured yet, you will see an empty state with guidance on getting started.

## How to Use It

### Adding a Tool

1. Click the upload button
2. Select or drag in your MCP configuration file
3. The tool appears in the list once uploaded

### Removing a Tool

Click the delete action on a tool card to remove it. Agents will no longer have access to that tool in future pipeline runs.

### Understanding MCP Tools

MCP tools are extensions that let agents interact with external services, databases, APIs, or other systems. For example, an MCP tool might let an agent query a documentation search engine, create a pull request, or send a notification.

Each tool you upload here becomes available to any agent assigned in your [Pipeline](pipeline.md).

## Tips

- Tools are scoped to your current project. If you switch projects, you will see a different set of tools.
- Check the linked MCP documentation for the format and options available when creating tool definitions.
