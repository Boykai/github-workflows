"""Static MCP preset definitions for the Tools page."""

from __future__ import annotations

import json

from src.models.tools import McpPresetListResponse, McpPresetResponse


def _dump_config(config: dict[str, object]) -> str:
    return json.dumps(config, indent=2) + "\n"


_PRESETS: tuple[McpPresetResponse, ...] = (
    McpPresetResponse(
        id="github-readonly",
        name="GitHub MCP Server",
        description="Read-only GitHub MCP server with configurable toolsets for coding agents.",
        category="GitHub",
        icon="github",
        config_content=_dump_config(
            {
                "mcpServers": {
                    "github-readonly": {
                        "type": "http",
                        "url": "https://api.githubcopilot.com/mcp/readonly",
                        "tools": ["*"],
                        "headers": {"X-MCP-Toolsets": "repos,issues,users,pull_requests,actions"},
                    }
                }
            }
        ),
    ),
    McpPresetResponse(
        id="github-full",
        name="GitHub MCP Server (Full Access)",
        description="Full-access GitHub MCP server for broader repository automation.",
        category="GitHub",
        icon="github",
        config_content=_dump_config(
            {
                "mcpServers": {
                    "github-full-access": {
                        "type": "http",
                        "url": "https://api.githubcopilot.com/mcp/",
                        "tools": ["*"],
                        "headers": {
                            "X-MCP-Toolsets": "repos,issues,users,pull_requests,code_security,secret_protection,actions,web_search"
                        },
                    }
                }
            }
        ),
    ),
    McpPresetResponse(
        id="azure",
        name="Azure MCP",
        description="Local Azure MCP server for Azure-aware coding workflows.",
        category="Cloud",
        icon="cloud",
        config_content=_dump_config(
            {
                "mcpServers": {
                    "Azure": {
                        "type": "local",
                        "command": "npx",
                        "args": ["-y", "@azure/mcp@latest", "server", "start"],
                        "tools": ["*"],
                    }
                }
            }
        ),
    ),
    McpPresetResponse(
        id="sentry",
        name="Sentry MCP",
        description="Sentry MCP server for issue details and summaries.",
        category="Monitoring",
        icon="radar",
        config_content=_dump_config(
            {
                "mcpServers": {
                    "sentry": {
                        "type": "local",
                        "command": "npx",
                        "args": ["@sentry/mcp-server@latest", "--host=$SENTRY_HOST"],
                        "tools": ["get_issue_details", "get_issue_summary"],
                        "env": {
                            "SENTRY_HOST": "COPILOT_MCP_SENTRY_HOST",
                            "SENTRY_ACCESS_TOKEN": "COPILOT_MCP_SENTRY_ACCESS_TOKEN",  # nosec B105
                        },
                    }
                }
            }
        ),
    ),
    McpPresetResponse(
        id="cloudflare",
        name="Cloudflare MCP",
        description="SSE MCP endpoint for Cloudflare documentation and platform access.",
        category="Cloud",
        icon="globe",
        config_content=_dump_config(
            {
                "mcpServers": {
                    "cloudflare": {
                        "type": "sse",
                        "url": "https://docs.mcp.cloudflare.com/sse",
                        "tools": ["*"],
                    }
                }
            }
        ),
    ),
    McpPresetResponse(
        id="azure-devops",
        name="Azure DevOps MCP",
        description="Local MCP server for Azure DevOps work items and project access.",
        category="Cloud",
        icon="workflow",
        config_content=_dump_config(
            {
                "mcpServers": {
                    "ado": {
                        "type": "local",
                        "command": "npx",
                        "args": [
                            "-y",
                            "@azure-devops/mcp",
                            "<your-azure-devops-organization>",
                            "-a",
                            "azcli",
                        ],
                        "tools": ["*"],
                    }
                }
            }
        ),
    ),
    McpPresetResponse(
        id="context7",
        name="Context7",
        description="Up-to-date library documentation and code examples for AI-assisted development.",
        category="Documentation",
        icon="book-open",
        config_content=_dump_config(
            {
                "mcpServers": {
                    "context7": {
                        "type": "http",
                        "url": "https://mcp.context7.com/mcp",
                        "tools": ["resolve-library-id", "get-library-docs"],
                        "headers": {"CONTEXT7_API_KEY": "$COPILOT_MCP_CONTEXT7_API_KEY"},
                    }
                }
            }
        ),
    ),
    McpPresetResponse(
        id="codegraphcontext",
        name="Code Graph Context",
        description="Code indexing and graph analysis for call chains, dead code detection, and complexity metrics.",
        category="Code Analysis",
        icon="git-branch",
        config_content=_dump_config(
            {
                "mcpServers": {
                    "CodeGraphContext": {
                        "type": "local",
                        "command": "uvx",
                        "args": ["--from", "codegraphcontext", "cgc", "mcp", "start"],
                        "tools": ["*"],
                        "env": {
                            "IGNORE_TEST_FILES": "false",
                            "IGNORE_HIDDEN_FILES": "true",
                            "MAX_FILE_SIZE_MB": "10",
                        },
                    }
                }
            }
        ),
    ),
)


def list_mcp_presets() -> McpPresetListResponse:
    """Return the static preset catalog."""
    presets = list(_PRESETS)
    return McpPresetListResponse(presets=presets, count=len(presets))
