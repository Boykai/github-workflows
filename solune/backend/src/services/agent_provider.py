"""Agent provider factory — creates Agent Framework agents for each AI backend.

Replaces the ``CompletionProvider`` abstraction with native Agent Framework
providers:

- ``ai_provider="copilot"``      → ``GitHubCopilotAgent``
- ``ai_provider="azure_openai"`` → ``Agent`` with ``OpenAIChatCompletionClient``
                                   (Azure endpoint mode)

The factory returns a fully configured ``Agent`` (or subclass) ready for
``agent.run()`` calls.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from agent_framework import Agent, AgentMiddleware

from src.config import get_settings
from src.logging_utils import get_logger

logger = get_logger(__name__)


def create_agent(
    instructions: str,
    tools: Sequence[Any] | None = None,
    middleware: Sequence[AgentMiddleware] | None = None,
) -> Agent:
    """Create an Agent instance based on the configured AI provider.

    Args:
        instructions: System instructions for the agent.
        tools: List of ``@tool``-decorated functions.
        middleware: Optional agent middleware (logging, security, etc.).

    Returns:
        A configured ``Agent`` ready for ``.run()`` calls.

    Raises:
        ValueError: If the configured ``ai_provider`` is not supported.
    """
    settings = get_settings()
    provider = settings.ai_provider.lower()

    if provider == "copilot":
        return _create_copilot_agent(instructions, tools, middleware)
    elif provider == "azure_openai":
        return _create_azure_openai_agent(instructions, tools, middleware)
    else:
        raise ValueError(
            f"Unsupported AI provider: {provider!r}. Supported values: 'copilot', 'azure_openai'."
        )


# ── Copilot provider ───────────────────────────────────────────────────────


def _create_copilot_agent(
    instructions: str,
    tools: Sequence[Any] | None,
    middleware: Sequence[AgentMiddleware] | None,
) -> Agent:
    """Create a GitHubCopilotAgent.

    The Copilot agent uses the GitHub Copilot SDK under the hood.  Per-user
    token passing is handled at run-time via ``function_invocation_kwargs``
    in ``ChatAgentService.run()``.
    """
    from agent_framework.github import GitHubCopilotAgent

    settings = get_settings()
    model = settings.copilot_model or "gpt-4o"

    agent = GitHubCopilotAgent(
        instructions=instructions,
        name="solune-chat-agent",
        description="Solune project management assistant",
        tools=list(tools) if tools else None,
        middleware=list(middleware) if middleware else None,
        default_options={"model": model},
    )
    logger.info("Created GitHubCopilotAgent (model=%s)", model)
    return agent


# ── Azure OpenAI provider ──────────────────────────────────────────────────


def _create_azure_openai_agent(
    instructions: str,
    tools: Sequence[Any] | None,
    middleware: Sequence[AgentMiddleware] | None,
) -> Agent:
    """Create an Agent with ``OpenAIChatCompletionClient`` pointed at Azure.

    Uses the ``azure_endpoint`` parameter of the OpenAI SDK so that the same
    ``Agent`` class works for both OpenAI and Azure OpenAI.
    """
    from agent_framework.openai import OpenAIChatCompletionClient

    settings = get_settings()

    if not settings.azure_openai_endpoint:
        raise ValueError("AZURE_OPENAI_ENDPOINT is required for azure_openai provider")
    if not settings.azure_openai_key:
        raise ValueError("AZURE_OPENAI_KEY is required for azure_openai provider")

    client = OpenAIChatCompletionClient(
        model=settings.azure_openai_deployment or "gpt-4",
        api_key=settings.azure_openai_key,
        azure_endpoint=settings.azure_openai_endpoint,
        api_version="2024-02-15-preview",
    )

    agent = Agent(
        client=client,
        instructions=instructions,
        name="solune-chat-agent",
        description="Solune project management assistant",
        tools=list(tools) if tools else None,
        middleware=list(middleware) if middleware else None,
    )
    logger.info(
        "Created Agent with AzureOpenAI (deployment=%s)",
        settings.azure_openai_deployment,
    )
    return agent
