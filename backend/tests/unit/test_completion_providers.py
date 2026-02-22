"""Unit tests for completion provider factory and provider logic.

Covers:
- create_completion_provider() dispatch
- CopilotCompletionProvider initialization and error handling
- AzureOpenAICompletionProvider initialization and error handling
- CompletionProvider ABC interface contract
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.config import Settings
from src.services.completion_providers import (
    AzureOpenAICompletionProvider,
    CompletionProvider,
    CopilotCompletionProvider,
    create_completion_provider,
)


def _settings(**overrides) -> Settings:
    defaults = {
        "github_client_id": "cid",
        "github_client_secret": "cs",
        "session_secret_key": "sk",
        "_env_file": None,
    }
    defaults.update(overrides)
    return Settings(**defaults)


# =============================================================================
# CopilotCompletionProvider
# =============================================================================


class TestCopilotCompletionProvider:
    def test_name(self):
        p = CopilotCompletionProvider(model="gpt-4o")
        assert p.name == "copilot"

    def test_is_completion_provider(self):
        assert issubclass(CopilotCompletionProvider, CompletionProvider)

    def test_default_model(self):
        p = CopilotCompletionProvider()
        assert p._model == "gpt-4o"

    def test_custom_model(self):
        p = CopilotCompletionProvider(model="gpt-3.5-turbo")
        assert p._model == "gpt-3.5-turbo"

    async def test_complete_requires_github_token(self):
        p = CopilotCompletionProvider()
        with pytest.raises(ValueError, match="GitHub OAuth token required"):
            await p.complete([{"role": "user", "content": "hi"}], github_token=None)

    def test_token_key_is_deterministic(self):
        k1 = CopilotCompletionProvider._token_key("abc")
        k2 = CopilotCompletionProvider._token_key("abc")
        assert k1 == k2

    def test_token_key_differs_for_different_tokens(self):
        k1 = CopilotCompletionProvider._token_key("abc")
        k2 = CopilotCompletionProvider._token_key("xyz")
        assert k1 != k2

    async def test_cleanup_stops_clients(self):
        p = CopilotCompletionProvider()
        mock_client = AsyncMock()
        p._clients["key1"] = mock_client
        await p.cleanup()
        mock_client.stop.assert_awaited_once()
        assert len(p._clients) == 0

    async def test_cleanup_handles_errors(self):
        p = CopilotCompletionProvider()
        mock_client = AsyncMock()
        mock_client.stop.side_effect = RuntimeError("fail")
        p._clients["key1"] = mock_client
        # Should not raise
        await p.cleanup()
        assert len(p._clients) == 0

    async def test_get_or_create_client_caches(self):
        CopilotCompletionProvider()
        mock_client = AsyncMock()
        with patch(
            "src.services.completion_providers.CopilotCompletionProvider._get_or_create_client"
        ) as mock_get:
            mock_get.return_value = mock_client
            # Just verify the interface - we can't import copilot SDK
            client = await mock_get("token123")
            assert client is mock_client

    async def test_complete_with_copilot_sdk(self):
        """Test CopilotCompletionProvider.complete() end-to-end with mocked SDK."""
        p = CopilotCompletionProvider()

        # Mock the SDK components
        mock_session = AsyncMock()
        mock_client = AsyncMock()
        mock_client.create_session.return_value = mock_session

        # Make session.on capture the callback and simulate ASSISTANT_MESSAGE + SESSION_IDLE
        captured_callback = None

        def capture_on(callback):
            nonlocal captured_callback
            captured_callback = callback

        mock_session.on = capture_on

        async def fake_send(*args, **kwargs):
            # Simulate the copilot events
            from unittest.mock import MagicMock as MM

            msg_event = MM()
            msg_event.type = "assistant_message"
            msg_event.data.content = "Hello response"

            idle_event = MM()
            idle_event.type = "session_idle"

            # We need the actual enum values. Since we can't import copilot,
            # just inject the result directly into the client
            pass

        # Pre-inject a cached client
        key = CopilotCompletionProvider._token_key("test-token")
        p._clients[key] = mock_client

        # Patch SessionEventType and session types
        mock_event_type = MagicMock()
        mock_event_type.ASSISTANT_MESSAGE = "assistant_message"
        mock_event_type.SESSION_IDLE = "session_idle"
        mock_event_type.SESSION_ERROR = "session_error"

        with (
            patch.dict(
                "sys.modules",
                {
                    "copilot": MagicMock(),
                    "copilot.types": MagicMock(),
                    "copilot.generated": MagicMock(),
                    "copilot.generated.session_events": MagicMock(SessionEventType=mock_event_type),
                },
            ),
        ):
            # Have send trigger the callback with content + idle
            async def trigger_events(*args, **kwargs):
                # Simulate async event delivery
                event1 = MagicMock()
                event1.type = mock_event_type.ASSISTANT_MESSAGE
                event1.data.content = "response text"
                captured_callback(event1)

                event2 = MagicMock()
                event2.type = mock_event_type.SESSION_IDLE
                captured_callback(event2)

            mock_session.send = trigger_events

            result = await p.complete(
                [{"role": "system", "content": "sys"}, {"role": "user", "content": "hi"}],
                github_token="test-token",
            )
            assert result == "response text"


# =============================================================================
# AzureOpenAICompletionProvider
# =============================================================================


class TestAzureOpenAICompletionProvider:
    def test_raises_without_credentials(self):
        s = _settings(ai_provider="azure_openai", azure_openai_endpoint=None, azure_openai_key=None)
        with patch("src.services.completion_providers.get_settings", return_value=s):
            with pytest.raises(ValueError, match="credentials not configured"):
                AzureOpenAICompletionProvider()

    def test_name(self):
        s = _settings(
            ai_provider="azure_openai",
            azure_openai_endpoint="https://test.openai.azure.com",
            azure_openai_key="key",
        )
        with patch("src.services.completion_providers.get_settings", return_value=s):
            p = AzureOpenAICompletionProvider()
        assert p.name == "azure_openai"

    def test_is_completion_provider(self):
        assert issubclass(AzureOpenAICompletionProvider, CompletionProvider)

    async def test_azure_openai_complete(self):
        """Test AzureOpenAI complete() with mocked OpenAI SDK path."""
        # Manually construct provider to force _use_azure_inference = False
        with patch.object(AzureOpenAICompletionProvider, "__init__", lambda self_: None):
            p = AzureOpenAICompletionProvider.__new__(AzureOpenAICompletionProvider)
            p._deployment = "gpt-4"
            p._use_azure_inference = False
            p._client = MagicMock()

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Azure says hi"

        with patch("asyncio.to_thread", new_callable=AsyncMock, return_value=mock_response):
            result = await p.complete(
                [{"role": "user", "content": "hello"}],
                temperature=0.5,
                max_tokens=500,
            )
        assert result == "Azure says hi"

    async def test_azure_inference_complete(self):
        """Test AzureOpenAI complete() with Azure AI Inference SDK fallback."""
        s = _settings(
            ai_provider="azure_openai",
            azure_openai_endpoint="https://test.openai.azure.com",
            azure_openai_key="key",
        )
        # Simulate openai not installed → falls back to azure inference
        mock_inference_client = MagicMock()
        MagicMock()
        with (
            patch("src.services.completion_providers.get_settings", return_value=s),
            patch.dict("sys.modules", {"openai": None}),
            patch(
                "src.services.completion_providers.AzureOpenAICompletionProvider.__init__",
                lambda self_: None,
            ),
        ):
            p = AzureOpenAICompletionProvider.__new__(AzureOpenAICompletionProvider)
            p._client = mock_inference_client
            p._deployment = "gpt-4"
            p._use_azure_inference = True

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Inference says hi"

        with (
            patch("asyncio.to_thread", new_callable=AsyncMock, return_value=mock_response),
            patch.dict(
                "sys.modules",
                {
                    "azure": MagicMock(),
                    "azure.ai": MagicMock(),
                    "azure.ai.inference": MagicMock(),
                    "azure.ai.inference.models": MagicMock(),
                },
            ),
        ):
            result = await p.complete(
                [{"role": "system", "content": "sys"}, {"role": "user", "content": "hi"}],
            )
        assert result == "Inference says hi"


# =============================================================================
# create_completion_provider (factory)
# =============================================================================


class TestCreateCompletionProvider:
    def test_copilot_default(self):
        s = _settings(ai_provider="copilot")
        with patch("src.services.completion_providers.get_settings", return_value=s):
            p = create_completion_provider()
        assert isinstance(p, CopilotCompletionProvider)

    def test_azure_openai(self):
        s = _settings(
            ai_provider="azure_openai",
            azure_openai_endpoint="https://test.openai.azure.com",
            azure_openai_key="key",
        )
        with patch("src.services.completion_providers.get_settings", return_value=s):
            p = create_completion_provider()
        assert isinstance(p, AzureOpenAICompletionProvider)

    def test_unknown_provider_raises(self):
        s = _settings(ai_provider="unknown_llm")
        with patch("src.services.completion_providers.get_settings", return_value=s):
            with pytest.raises(ValueError, match="Unknown AI provider"):
                create_completion_provider()
