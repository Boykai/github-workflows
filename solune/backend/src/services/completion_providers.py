"""LLM completion providers for AI agent operations.

Provides a unified interface for different AI backends:
- CopilotCompletionProvider: Default. Uses GitHub Copilot SDK with user's OAuth token.
- AzureOpenAICompletionProvider: Optional. Uses Azure OpenAI with static API keys.
"""

import asyncio
import hashlib
from abc import ABC, abstractmethod
from typing import Any

from src.config import get_settings
from src.logging_utils import get_logger
from src.utils import BoundedDict

logger = get_logger(__name__)

_copilot_client_pool: "CopilotClientPool | None" = None


class CopilotClientPool:
    """Shared, bounded cache of CopilotClient instances keyed by token hash.

    Used by both CopilotCompletionProvider and GitHubCopilotModelFetcher to avoid
    duplicate client creation. Each unique GitHub token maps to exactly one
    CopilotClient, regardless of which service requests it.

    Thread-safe via asyncio.Lock for concurrent get_or_create calls.
    Memory-safe via BoundedDict with FIFO eviction when capacity is reached.
    """

    def __init__(self, maxlen: int = 50) -> None:
        self._clients: BoundedDict[str, Any] = BoundedDict(maxlen=maxlen)
        self._lock: asyncio.Lock | None = None

    def _get_lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    @staticmethod
    def _token_key(github_token: str) -> str:
        """Return a stable hash of the token for use as a cache key.

        Avoids keeping raw tokens as dict keys where they could be
        exposed by debug tooling or log dumps.
        """
        return hashlib.sha256(github_token.encode()).hexdigest()[:16]

    async def get_or_create(self, github_token: str) -> Any:
        """Get cached or create new CopilotClient for a given token."""
        key = self._token_key(github_token)
        if key in self._clients:
            return self._clients[key]

        async with self._get_lock():
            # Double-check after acquiring lock
            if key in self._clients:
                return self._clients[key]

            from copilot import CopilotClient  # type: ignore[reportMissingImports]
            from copilot.types import CopilotClientOptions

            options = CopilotClientOptions(github_token=github_token, auto_start=False)
            client = CopilotClient(options=options)
            await client.start()
            self._clients[key] = client
            logger.info(
                "Created new CopilotClient (pool size: %d/%d)",
                len(self._clients),
                self._clients._maxlen,
            )
            return client

    async def cleanup(self) -> None:
        """Stop all cached CopilotClient instances. Call on app shutdown."""
        for _token_hash, client in list(self._clients.items()):
            try:
                await client.stop()
            except Exception as e:
                logger.warning("Error stopping CopilotClient: %s", e)
        self._clients.clear()
        logger.info("Cleaned up all CopilotClient instances")

    async def remove(self, github_token: str) -> None:
        """Stop and remove a single client by token."""
        key = self._token_key(github_token)
        client = self._clients.pop(key, None)
        if client:
            try:
                await client.stop()
            except Exception as e:
                logger.warning("Error stopping CopilotClient: %s", e)


def get_copilot_client_pool() -> CopilotClientPool:
    """Return the shared Copilot client pool, creating it on first use."""
    global _copilot_client_pool
    if _copilot_client_pool is None:
        _copilot_client_pool = CopilotClientPool()
    return _copilot_client_pool


class CompletionProvider(ABC):
    """Abstract interface for LLM completion providers."""

    @abstractmethod
    async def complete(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        github_token: str | None = None,
    ) -> str:
        """Generate a chat completion from messages.

        Args:
            messages: List of {"role": "system"|"user", "content": "..."} dicts
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens in response
            github_token: GitHub OAuth token (required for Copilot provider)

        Returns:
            The assistant's response content
        """
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name for logging and diagnostics."""
        ...


class CopilotCompletionProvider(CompletionProvider):
    """Completion provider using GitHub Copilot SDK.

    Authenticates using the user's GitHub OAuth token. Client instances are
    managed by the shared CopilotClientPool to avoid duplication with the
    model fetcher service.

    Requires:
        uv add github-copilot-sdk
    """

    def __init__(self, model: str = "gpt-4o", pool: CopilotClientPool | None = None):
        self._model = model
        self._pool = pool or get_copilot_client_pool()
        logger.info("Initialized Copilot completion provider (model: %s)", model)

    async def complete(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        github_token: str | None = None,
    ) -> str:
        if not github_token:
            raise ValueError(
                "GitHub OAuth token required for Copilot provider. "
                "Ensure user is authenticated via GitHub OAuth."
            )

        client = await self._pool.get_or_create(github_token)

        from copilot.generated.session_events import (  # type: ignore[reportMissingImports]
            SessionEventType,
        )
        from copilot.session import PermissionHandler  # type: ignore[reportMissingImports]

        # Extract system message for session config, user message for prompt
        system_content = ""
        user_content = ""
        for msg in messages:
            if msg["role"] == "system":
                system_content = msg["content"]
            elif msg["role"] == "user":
                user_content = msg["content"]

        # Build create_session kwargs (SessionConfig was removed in SDK 0.1.0)
        session_kwargs: dict[str, Any] = {
            "model": self._model,
            "on_permission_request": PermissionHandler.approve_all,  # pyright: ignore[reportAttributeAccessIssue]
        }
        if system_content:
            session_kwargs["system_message"] = {"mode": "replace", "content": system_content}

        # Create session, send prompt, wait for response
        session = await client.create_session(**session_kwargs)
        done = asyncio.Event()
        result_content: list[str] = []
        error_content: list[str] = []

        def on_event(event: Any) -> None:
            try:
                etype = event.type
                if etype == SessionEventType.ASSISTANT_MESSAGE:
                    content = getattr(event.data, "content", None)
                    if content:
                        result_content.append(content)
                elif etype == SessionEventType.SESSION_IDLE:
                    done.set()
                elif etype == SessionEventType.SESSION_ERROR:
                    error_msg = getattr(event.data, "message", str(event.data))
                    error_content.append(error_msg)
                    done.set()
            except Exception as e:
                logger.warning("Error processing Copilot event: %s", e)
                done.set()

        session.on(on_event)
        await session.send(user_content)

        try:
            await asyncio.wait_for(done.wait(), timeout=120)
        except TimeoutError:
            logger.warning("Copilot completion timed out after 120s")
        finally:
            try:
                await session.destroy()
            except Exception as e:
                logger.warning("Error destroying Copilot session: %s", e)

        if error_content:
            raise ValueError(f"Copilot API error: {error_content[0]}")

        return "".join(result_content) if result_content else ""

    async def cleanup(self) -> None:
        """Stop all cached CopilotClient instances. Delegates to the shared pool."""
        await self._pool.cleanup()

    @property
    def name(self) -> str:
        return "copilot"


class AzureOpenAICompletionProvider(CompletionProvider):
    """Completion provider using Azure OpenAI or Azure AI Inference.

    Uses static API key credentials from environment configuration.
    Does not require a per-user GitHub token.
    """

    AZURE_API_VERSION = "2024-02-15-preview"

    def __init__(self) -> None:
        settings = get_settings()
        self._deployment = settings.azure_openai_deployment
        self._client: Any = None
        self._use_azure_inference = False

        if not settings.azure_openai_endpoint or not settings.azure_openai_key:
            raise ValueError(
                "Azure OpenAI credentials not configured. "
                "Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY in .env"
            )

        # Try Azure OpenAI SDK first (openai package)
        try:
            from openai import AzureOpenAI  # type: ignore[reportMissingImports]

            self._client = AzureOpenAI(
                azure_endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_key,
                api_version=self.AZURE_API_VERSION,
            )
            self._use_azure_inference = False
            logger.info(
                "Initialized Azure OpenAI client for deployment: %s",
                self._deployment,
            )
        except ImportError:
            # Fall back to Azure AI Inference SDK
            from azure.ai.inference import ChatCompletionsClient
            from azure.core.credentials import AzureKeyCredential

            self._client = ChatCompletionsClient(
                endpoint=settings.azure_openai_endpoint,  # type: ignore[arg-type]
                credential=AzureKeyCredential(settings.azure_openai_key),  # type: ignore[arg-type]
            )
            self._use_azure_inference = True
            logger.info(
                "Initialized Azure AI Inference client for model: %s",
                self._deployment,
            )

    async def complete(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        github_token: str | None = None,
    ) -> str:
        # github_token is ignored for Azure OpenAI (uses static API key)
        if self._use_azure_inference:
            from azure.ai.inference.models import SystemMessage, UserMessage

            inference_messages = [
                (
                    SystemMessage(content=m["content"])
                    if m["role"] == "system"
                    else UserMessage(content=m["content"])
                )
                for m in messages
            ]
            response = await asyncio.to_thread(
                self._client.complete,
                model=self._deployment,
                messages=inference_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        else:
            response = await asyncio.to_thread(
                self._client.chat.completions.create,
                model=self._deployment,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        if not response.choices:
            return ""
        return response.choices[0].message.content or ""

    @property
    def name(self) -> str:
        return "azure_openai"


def create_completion_provider() -> CompletionProvider:
    """Factory: create the configured completion provider.

    Reads AI_PROVIDER from settings:
      - "copilot" (default): GitHub Copilot via user's OAuth token
      - "azure_openai": Azure OpenAI with static API keys

    Returns:
        Configured CompletionProvider instance
    """
    settings = get_settings()
    provider_name = settings.ai_provider

    if provider_name == "azure_openai":
        logger.info("Using Azure OpenAI completion provider")
        return AzureOpenAICompletionProvider()
    elif provider_name == "copilot":
        model = settings.copilot_model
        logger.info("Using GitHub Copilot completion provider (model: %s)", model)
        return CopilotCompletionProvider(model=model)
    else:
        raise ValueError(
            f"Unknown AI provider: '{provider_name}'. "
            "Set AI_PROVIDER to 'copilot' or 'azure_openai'."
        )
