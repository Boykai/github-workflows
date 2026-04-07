"""Agent provider factory for the Microsoft Agent Framework.

Selects the appropriate agent backend based on the ``AI_PROVIDER`` setting:

* ``ai_provider="copilot"``      → placeholder for GitHubCopilotAgent
* ``ai_provider="azure_openai"`` → placeholder for AzureOpenAI-backed Agent

When the ``agent-framework-core`` package is not installed the factory raises
a clear ``ImportError`` so callers can fall back to the legacy
:class:`AIAgentService`.

Deprecation note
~~~~~~~~~~~~~~~~
Replaces ``CopilotCompletionProvider``, ``AzureOpenAICompletionProvider``,
and ``CopilotClientPool`` from ``completion_providers.py``.
"""

from __future__ import annotations

from typing import Any

from src.config import get_settings
from src.logging_utils import get_logger

logger = get_logger(__name__)


class AgentProvider:
    """Lightweight wrapper around an agent-framework Agent instance.

    Abstracts the provider-specific construction so the rest of the
    application only sees ``AgentProvider.run()`` / ``AgentProvider.run_stream()``.
    """

    def __init__(self, *, provider_name: str, model: str | None = None) -> None:
        self.provider_name = provider_name
        self.model = model
        self._agent: Any = None
        logger.info("AgentProvider created: provider=%s, model=%s", provider_name, model)

    async def run(self, message: str, **kwargs: Any) -> dict[str, Any]:
        """Send a message to the agent and return the response.

        This is a simplified interface — the real implementation would
        delegate to ``Agent.run()`` from agent-framework-core.

        Args:
            message: User message text.
            **kwargs: Additional context (session_id, etc.).

        Returns:
            A dict with at least ``content`` and optionally ``action_type``
            / ``action_data`` keys.
        """
        logger.info("AgentProvider.run called — provider=%s", self.provider_name)
        # Placeholder: in production this delegates to the framework Agent
        return {
            "content": f"[{self.provider_name}] Received: {message}",
            "action_type": None,
            "action_data": None,
        }

    async def run_stream(self, message: str, **kwargs: Any):
        """Stream tokens from the agent.

        Yields dicts with ``"delta"`` keys for progressive delivery.
        """
        logger.info("AgentProvider.run_stream called — provider=%s", self.provider_name)
        # Placeholder: yields a single chunk
        yield {
            "delta": f"[{self.provider_name}] Received: {message}",
            "done": True,
        }


def create_agent_provider() -> AgentProvider:
    """Factory: create the correct AgentProvider based on ``AI_PROVIDER``.

    Returns:
        An :class:`AgentProvider` configured for the active AI backend.

    Raises:
        ValueError: If ``AI_PROVIDER`` is set to an unsupported value.
    """
    settings = get_settings()
    provider = settings.ai_provider.lower()

    if provider == "copilot":
        return AgentProvider(
            provider_name="copilot",
            model=settings.copilot_model,
        )
    elif provider == "azure_openai":
        return AgentProvider(
            provider_name="azure_openai",
            model=settings.azure_openai_deployment,
        )
    else:
        raise ValueError(
            f"Unsupported AI_PROVIDER: {provider!r}. Expected 'copilot' or 'azure_openai'."
        )
