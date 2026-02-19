"""Unit tests for completion providers."""

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.completion_providers import (
    AzureOpenAICompletionProvider,
    CopilotCompletionProvider,
    create_completion_provider,
)


class TestCopilotCompletionProvider:
    """Tests for CopilotCompletionProvider."""

    def test_name_returns_copilot(self):
        """Should return 'copilot' as provider name."""
        provider = CopilotCompletionProvider()

        assert provider.name == "copilot"

    def test_default_model_is_gpt4o(self):
        """Should use gpt-4o as default model."""
        provider = CopilotCompletionProvider()

        assert provider._model == "gpt-4o"

    def test_custom_model(self):
        """Should accept custom model name."""
        provider = CopilotCompletionProvider(model="gpt-3.5-turbo")

        assert provider._model == "gpt-3.5-turbo"

    def test_token_key_returns_stable_hash(self):
        """Should return consistent hash for same token."""
        key1 = CopilotCompletionProvider._token_key("my_token_123")
        key2 = CopilotCompletionProvider._token_key("my_token_123")

        assert key1 == key2
        assert len(key1) == 16

    def test_token_key_differs_for_different_tokens(self):
        """Should return different hashes for different tokens."""
        key1 = CopilotCompletionProvider._token_key("token_a")
        key2 = CopilotCompletionProvider._token_key("token_b")

        assert key1 != key2

    def test_token_key_does_not_contain_raw_token(self):
        """Should not expose raw token in key."""
        token = "ghp_super_secret_token_12345"
        key = CopilotCompletionProvider._token_key(token)

        assert token not in key
        assert "ghp_" not in key

    @pytest.mark.asyncio
    async def test_complete_without_token_raises_error(self):
        """Should raise ValueError when no GitHub token provided."""
        provider = CopilotCompletionProvider()
        messages = [{"role": "user", "content": "Hello"}]

        with pytest.raises(ValueError, match="GitHub OAuth token required"):
            await provider.complete(messages)

    @pytest.mark.asyncio
    async def test_complete_with_none_token_raises_error(self):
        """Should raise ValueError when token is explicitly None."""
        provider = CopilotCompletionProvider()
        messages = [{"role": "user", "content": "Hello"}]

        with pytest.raises(ValueError, match="GitHub OAuth token required"):
            await provider.complete(messages, github_token=None)

    @pytest.mark.asyncio
    async def test_complete_with_empty_token_raises_error(self):
        """Should raise ValueError when token is empty string."""
        provider = CopilotCompletionProvider()
        messages = [{"role": "user", "content": "Hello"}]

        with pytest.raises(ValueError, match="GitHub OAuth token required"):
            await provider.complete(messages, github_token="")

    def test_clients_cache_initially_empty(self):
        """Should start with empty clients cache."""
        provider = CopilotCompletionProvider()

        assert len(provider._clients) == 0

    @pytest.mark.asyncio
    async def test_get_or_create_client_creates_and_caches(self):
        """Should create a CopilotClient and cache it by token hash."""
        provider = CopilotCompletionProvider()
        mock_client = AsyncMock()

        mock_options_cls = MagicMock()
        mock_client_cls = MagicMock(return_value=mock_client)

        with (
            patch.dict(
                sys.modules,
                {
                    "copilot": MagicMock(CopilotClient=mock_client_cls),
                    "copilot.types": MagicMock(CopilotClientOptions=mock_options_cls),
                },
            ),
        ):
            client = await provider._get_or_create_client("ghp_test_token")

        assert client is mock_client
        mock_client.start.assert_awaited_once()
        assert len(provider._clients) == 1

    @pytest.mark.asyncio
    async def test_get_or_create_client_returns_cached(self):
        """Should return cached client for same token."""
        provider = CopilotCompletionProvider()
        mock_client = AsyncMock()
        key = CopilotCompletionProvider._token_key("ghp_test_token")
        provider._clients[key] = mock_client

        with patch.dict(sys.modules, {"copilot": MagicMock(), "copilot.types": MagicMock()}):
            client = await provider._get_or_create_client("ghp_test_token")

        assert client is mock_client
        assert len(provider._clients) == 1

    @pytest.mark.asyncio
    async def test_complete_returns_assistant_message(self):
        """Should return concatenated assistant message content."""
        provider = CopilotCompletionProvider()

        # Pre-populate a cached mock client
        mock_session = AsyncMock()
        mock_client = AsyncMock()
        mock_client.create_session = AsyncMock(return_value=mock_session)

        key = CopilotCompletionProvider._token_key("ghp_token")
        provider._clients[key] = mock_client

        # Build mock event types
        mock_session_event_type = MagicMock()
        mock_session_event_type.ASSISTANT_MESSAGE = "assistant_message"
        mock_session_event_type.SESSION_IDLE = "session_idle"
        mock_session_event_type.SESSION_ERROR = "session_error"

        mock_session_config = MagicMock()
        mock_message_options = MagicMock()

        def fake_on(callback):
            # Simulate events: one assistant message then idle
            msg_event = MagicMock()
            msg_event.type = "assistant_message"
            msg_event.data.content = "Hello world"
            callback(msg_event)

            idle_event = MagicMock()
            idle_event.type = "session_idle"
            callback(idle_event)

        mock_session.on = fake_on

        with patch.dict(
            sys.modules,
            {
                "copilot": MagicMock(),
                "copilot.generated.session_events": MagicMock(
                    SessionEventType=mock_session_event_type
                ),
                "copilot.types": MagicMock(
                    SessionConfig=mock_session_config,
                    MessageOptions=mock_message_options,
                ),
            },
        ):
            result = await provider.complete(
                messages=[
                    {"role": "system", "content": "You are helpful"},
                    {"role": "user", "content": "Hi"},
                ],
                github_token="ghp_token",
            )

        assert result == "Hello world"
        mock_session.destroy.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_complete_raises_on_session_error(self):
        """Should raise ValueError when Copilot session returns an error."""
        provider = CopilotCompletionProvider()

        mock_session = AsyncMock()
        mock_client = AsyncMock()
        mock_client.create_session = AsyncMock(return_value=mock_session)

        key = CopilotCompletionProvider._token_key("ghp_token")
        provider._clients[key] = mock_client

        mock_session_event_type = MagicMock()
        mock_session_event_type.ASSISTANT_MESSAGE = "assistant_message"
        mock_session_event_type.SESSION_IDLE = "session_idle"
        mock_session_event_type.SESSION_ERROR = "session_error"

        def fake_on(callback):
            error_event = MagicMock()
            error_event.type = "session_error"
            error_event.data.message = "Rate limit exceeded"
            callback(error_event)

        mock_session.on = fake_on

        with patch.dict(
            sys.modules,
            {
                "copilot": MagicMock(),
                "copilot.generated.session_events": MagicMock(
                    SessionEventType=mock_session_event_type
                ),
                "copilot.types": MagicMock(),
            },
        ):
            with pytest.raises(ValueError, match="Copilot API error: Rate limit exceeded"):
                await provider.complete(
                    messages=[{"role": "user", "content": "Hi"}],
                    github_token="ghp_token",
                )

    @pytest.mark.asyncio
    async def test_complete_returns_empty_on_no_content(self):
        """Should return empty string when no assistant content received."""
        provider = CopilotCompletionProvider()

        mock_session = AsyncMock()
        mock_client = AsyncMock()
        mock_client.create_session = AsyncMock(return_value=mock_session)

        key = CopilotCompletionProvider._token_key("ghp_token")
        provider._clients[key] = mock_client

        mock_session_event_type = MagicMock()
        mock_session_event_type.ASSISTANT_MESSAGE = "assistant_message"
        mock_session_event_type.SESSION_IDLE = "session_idle"
        mock_session_event_type.SESSION_ERROR = "session_error"

        def fake_on(callback):
            idle_event = MagicMock()
            idle_event.type = "session_idle"
            callback(idle_event)

        mock_session.on = fake_on

        with patch.dict(
            sys.modules,
            {
                "copilot": MagicMock(),
                "copilot.generated.session_events": MagicMock(
                    SessionEventType=mock_session_event_type
                ),
                "copilot.types": MagicMock(),
            },
        ):
            result = await provider.complete(
                messages=[{"role": "user", "content": "Hi"}],
                github_token="ghp_token",
            )

        assert result == ""

    @pytest.mark.asyncio
    async def test_complete_handles_timeout(self):
        """Should handle timeout gracefully and return empty string."""
        provider = CopilotCompletionProvider()

        mock_session = AsyncMock()
        mock_client = AsyncMock()
        mock_client.create_session = AsyncMock(return_value=mock_session)

        key = CopilotCompletionProvider._token_key("ghp_token")
        provider._clients[key] = mock_client

        mock_session_event_type = MagicMock()
        mock_session_event_type.ASSISTANT_MESSAGE = "assistant_message"
        mock_session_event_type.SESSION_IDLE = "session_idle"
        mock_session_event_type.SESSION_ERROR = "session_error"

        # Never call callback -> event never set -> timeout
        mock_session.on = MagicMock()

        with (
            patch.dict(
                sys.modules,
                {
                    "copilot": MagicMock(),
                    "copilot.generated.session_events": MagicMock(
                        SessionEventType=mock_session_event_type
                    ),
                    "copilot.types": MagicMock(),
                },
            ),
            patch("src.services.completion_providers.asyncio.wait_for", side_effect=TimeoutError),
        ):
            result = await provider.complete(
                messages=[{"role": "user", "content": "Hi"}],
                github_token="ghp_token",
            )

        assert result == ""
        mock_session.destroy.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_complete_handles_session_destroy_error(self):
        """Should handle error during session destroy gracefully."""
        provider = CopilotCompletionProvider()

        mock_session = AsyncMock()
        mock_session.destroy = AsyncMock(side_effect=RuntimeError("destroy failed"))
        mock_client = AsyncMock()
        mock_client.create_session = AsyncMock(return_value=mock_session)

        key = CopilotCompletionProvider._token_key("ghp_token")
        provider._clients[key] = mock_client

        mock_session_event_type = MagicMock()
        mock_session_event_type.ASSISTANT_MESSAGE = "assistant_message"
        mock_session_event_type.SESSION_IDLE = "session_idle"
        mock_session_event_type.SESSION_ERROR = "session_error"

        def fake_on(callback):
            idle_event = MagicMock()
            idle_event.type = "session_idle"
            callback(idle_event)

        mock_session.on = fake_on

        with patch.dict(
            sys.modules,
            {
                "copilot": MagicMock(),
                "copilot.generated.session_events": MagicMock(
                    SessionEventType=mock_session_event_type
                ),
                "copilot.types": MagicMock(),
            },
        ):
            # Should not raise despite destroy error
            result = await provider.complete(
                messages=[{"role": "user", "content": "Hi"}],
                github_token="ghp_token",
            )

        assert result == ""

    @pytest.mark.asyncio
    async def test_complete_event_callback_handles_exception(self):
        """Should handle exception in event callback gracefully."""
        provider = CopilotCompletionProvider()

        mock_session = AsyncMock()
        mock_client = AsyncMock()
        mock_client.create_session = AsyncMock(return_value=mock_session)

        key = CopilotCompletionProvider._token_key("ghp_token")
        provider._clients[key] = mock_client

        mock_session_event_type = MagicMock()
        mock_session_event_type.ASSISTANT_MESSAGE = "assistant_message"
        mock_session_event_type.SESSION_IDLE = "session_idle"
        mock_session_event_type.SESSION_ERROR = "session_error"

        def fake_on(callback):
            # Event with no .type attribute -> triggers exception in callback
            bad_event = MagicMock()
            bad_event.type = property(lambda s: (_ for _ in ()).throw(AttributeError("no type")))
            del bad_event.type
            callback(bad_event)

        mock_session.on = fake_on

        with patch.dict(
            sys.modules,
            {
                "copilot": MagicMock(),
                "copilot.generated.session_events": MagicMock(
                    SessionEventType=mock_session_event_type
                ),
                "copilot.types": MagicMock(),
            },
        ):
            # The exception in callback sets done, returns empty
            result = await provider.complete(
                messages=[{"role": "user", "content": "Hi"}],
                github_token="ghp_token",
            )

        assert result == ""

    @pytest.mark.asyncio
    async def test_cleanup_stops_all_clients(self):
        """Should stop all cached clients and clear the cache."""
        provider = CopilotCompletionProvider()
        mock_client_1 = AsyncMock()
        mock_client_2 = AsyncMock()
        provider._clients["key1"] = mock_client_1
        provider._clients["key2"] = mock_client_2

        await provider.cleanup()

        mock_client_1.stop.assert_awaited_once()
        mock_client_2.stop.assert_awaited_once()
        assert len(provider._clients) == 0

    @pytest.mark.asyncio
    async def test_cleanup_handles_stop_error(self):
        """Should continue cleanup even if a client.stop() fails."""
        provider = CopilotCompletionProvider()
        mock_client_ok = AsyncMock()
        mock_client_bad = AsyncMock()
        mock_client_bad.stop = AsyncMock(side_effect=RuntimeError("stop failed"))
        provider._clients["ok"] = mock_client_ok
        provider._clients["bad"] = mock_client_bad

        await provider.cleanup()  # Should not raise

        assert len(provider._clients) == 0

    @pytest.mark.asyncio
    async def test_cleanup_on_empty_cache(self):
        """Should handle cleanup with no cached clients."""
        provider = CopilotCompletionProvider()

        await provider.cleanup()

        assert len(provider._clients) == 0


class TestAzureOpenAICompletionProvider:
    """Tests for AzureOpenAICompletionProvider."""

    @patch("src.services.completion_providers.get_settings")
    def test_init_with_openai_sdk(self, mock_settings):
        """Should initialize with Azure OpenAI SDK when available."""
        mock_settings.return_value = MagicMock(
            azure_openai_endpoint="https://test.openai.azure.com",
            azure_openai_key="test-key",
            azure_openai_deployment="gpt-4",
        )

        with patch(
            "src.services.completion_providers.AzureOpenAI",
            create=True,
        ) as mock_cls:
            # Simulate successful import by injecting in the openai module path
            with patch.dict(sys.modules, {"openai": MagicMock(AzureOpenAI=mock_cls)}):
                provider = AzureOpenAICompletionProvider()

        assert provider._use_azure_inference is False
        assert provider.name == "azure_openai"

    @patch("src.services.completion_providers.get_settings")
    def test_init_missing_credentials_raises(self, mock_settings):
        """Should raise ValueError when endpoint or key is missing."""
        mock_settings.return_value = MagicMock(
            azure_openai_endpoint=None,
            azure_openai_key=None,
            azure_openai_deployment="gpt-4",
        )

        with pytest.raises(ValueError, match="Azure OpenAI credentials not configured"):
            AzureOpenAICompletionProvider()

    @patch("src.services.completion_providers.get_settings")
    def test_init_missing_key_only_raises(self, mock_settings):
        """Should raise ValueError when only key is missing."""
        mock_settings.return_value = MagicMock(
            azure_openai_endpoint="https://test.openai.azure.com",
            azure_openai_key=None,
            azure_openai_deployment="gpt-4",
        )

        with pytest.raises(ValueError, match="Azure OpenAI credentials not configured"):
            AzureOpenAICompletionProvider()

    @patch("src.services.completion_providers.get_settings")
    def test_init_fallback_to_azure_inference(self, mock_settings):
        """Should fall back to Azure AI Inference when openai package unavailable."""
        mock_settings.return_value = MagicMock(
            azure_openai_endpoint="https://test.openai.azure.com",
            azure_openai_key="test-key",
            azure_openai_deployment="gpt-4",
        )

        mock_inference_client = MagicMock()
        mock_credential = MagicMock()

        # Make the openai import fail
        with patch.dict(
            sys.modules,
            {
                "openai": None,
                "azure.ai.inference": MagicMock(
                    ChatCompletionsClient=MagicMock(return_value=mock_inference_client)
                ),
                "azure.core.credentials": MagicMock(
                    AzureKeyCredential=MagicMock(return_value=mock_credential)
                ),
            },
        ):
            provider = AzureOpenAICompletionProvider()

        assert provider._use_azure_inference is True
        assert provider.name == "azure_openai"

    @pytest.mark.asyncio
    @patch("src.services.completion_providers.get_settings")
    async def test_complete_openai_sdk_path(self, mock_settings):
        """Should call chat.completions.create for OpenAI SDK path."""
        mock_settings.return_value = MagicMock(
            azure_openai_endpoint="https://test.openai.azure.com",
            azure_openai_key="test-key",
            azure_openai_deployment="gpt-4",
        )

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Azure response"

        mock_client = MagicMock()
        mock_client.chat.completions.create = MagicMock(return_value=mock_response)

        mock_azure_cls = MagicMock(return_value=mock_client)

        with patch.dict(sys.modules, {"openai": MagicMock(AzureOpenAI=mock_azure_cls)}):
            provider = AzureOpenAICompletionProvider()

        messages = [
            {"role": "system", "content": "Be helpful"},
            {"role": "user", "content": "Hello"},
        ]

        async def fake_to_thread(func, *args, **kwargs):
            return func(*args, **kwargs)

        with patch(
            "src.services.completion_providers.asyncio.to_thread", side_effect=fake_to_thread
        ):
            result = await provider.complete(messages, temperature=0.5, max_tokens=500)

        assert result == "Azure response"

    @pytest.mark.asyncio
    @patch("src.services.completion_providers.get_settings")
    async def test_complete_azure_inference_path(self, mock_settings):
        """Should call client.complete for Azure Inference SDK path."""
        mock_settings.return_value = MagicMock(
            azure_openai_endpoint="https://test.openai.azure.com",
            azure_openai_key="test-key",
            azure_openai_deployment="gpt-4",
        )

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Inference response"

        mock_inference_client = MagicMock()
        mock_inference_client.complete = MagicMock(return_value=mock_response)

        with patch.dict(
            sys.modules,
            {
                "openai": None,
                "azure.ai.inference": MagicMock(
                    ChatCompletionsClient=MagicMock(return_value=mock_inference_client)
                ),
                "azure.core.credentials": MagicMock(),
            },
        ):
            provider = AzureOpenAICompletionProvider()

        messages = [
            {"role": "system", "content": "Be helpful"},
            {"role": "user", "content": "Hello"},
        ]

        async def fake_to_thread(func, *args, **kwargs):
            return func(*args, **kwargs)

        with (
            patch.dict(
                sys.modules,
                {
                    "azure.ai.inference.models": MagicMock(
                        SystemMessage=MagicMock(return_value=MagicMock()),
                        UserMessage=MagicMock(return_value=MagicMock()),
                    ),
                },
            ),
            patch(
                "src.services.completion_providers.asyncio.to_thread", side_effect=fake_to_thread
            ),
        ):
            result = await provider.complete(messages, temperature=0.5, max_tokens=500)

        assert result == "Inference response"

    @pytest.mark.asyncio
    @patch("src.services.completion_providers.get_settings")
    async def test_complete_returns_empty_on_none_content(self, mock_settings):
        """Should return empty string when response content is None."""
        mock_settings.return_value = MagicMock(
            azure_openai_endpoint="https://test.openai.azure.com",
            azure_openai_key="test-key",
            azure_openai_deployment="gpt-4",
        )

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None

        mock_client = MagicMock()
        mock_client.chat.completions.create = MagicMock(return_value=mock_response)
        mock_azure_cls = MagicMock(return_value=mock_client)

        with patch.dict(sys.modules, {"openai": MagicMock(AzureOpenAI=mock_azure_cls)}):
            provider = AzureOpenAICompletionProvider()

        async def fake_to_thread(func, *args, **kwargs):
            return func(*args, **kwargs)

        with patch(
            "src.services.completion_providers.asyncio.to_thread", side_effect=fake_to_thread
        ):
            result = await provider.complete([{"role": "user", "content": "Hi"}])

        assert result == ""

    def test_name_returns_azure_openai(self):
        """Should return 'azure_openai' as provider name."""
        with patch("src.services.completion_providers.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                azure_openai_endpoint="https://test.openai.azure.com",
                azure_openai_key="test-key",
                azure_openai_deployment="gpt-4",
            )
            mock_azure_cls = MagicMock()
            with patch.dict(sys.modules, {"openai": MagicMock(AzureOpenAI=mock_azure_cls)}):
                provider = AzureOpenAICompletionProvider()

        assert provider.name == "azure_openai"


class TestCreateCompletionProvider:
    """Tests for create_completion_provider factory function."""

    @patch("src.services.completion_providers.get_settings")
    def test_creates_copilot_provider_by_default(self, mock_settings):
        """Should create CopilotCompletionProvider for 'copilot' setting."""
        mock_settings.return_value = MagicMock(ai_provider="copilot", copilot_model="gpt-4o")

        provider = create_completion_provider()

        assert isinstance(provider, CopilotCompletionProvider)
        assert provider.name == "copilot"

    @patch("src.services.completion_providers.get_settings")
    def test_creates_copilot_provider_with_custom_model(self, mock_settings):
        """Should pass model from settings to CopilotCompletionProvider."""
        mock_settings.return_value = MagicMock(ai_provider="copilot", copilot_model="gpt-3.5-turbo")

        provider = create_completion_provider()

        assert isinstance(provider, CopilotCompletionProvider)
        assert provider._model == "gpt-3.5-turbo"

    @patch("src.services.completion_providers.get_settings")
    def test_unknown_provider_raises_error(self, mock_settings):
        """Should raise ValueError for unknown provider."""
        mock_settings.return_value = MagicMock(ai_provider="unknown_provider")

        with pytest.raises(ValueError, match="Unknown AI provider"):
            create_completion_provider()

    @patch("src.services.completion_providers.get_settings")
    def test_azure_provider_without_credentials_raises_error(self, mock_settings):
        """Should raise ValueError when Azure credentials missing."""
        mock_settings.return_value = MagicMock(
            ai_provider="azure_openai",
            azure_openai_endpoint=None,
            azure_openai_key=None,
            azure_openai_deployment="gpt-4",
        )

        with pytest.raises(ValueError, match="Azure OpenAI credentials not configured"):
            create_completion_provider()

    @patch("src.services.completion_providers.get_settings")
    def test_creates_azure_provider_with_credentials(self, mock_settings):
        """Should create AzureOpenAICompletionProvider when credentials configured."""
        mock_settings.return_value = MagicMock(
            ai_provider="azure_openai",
            azure_openai_endpoint="https://test.openai.azure.com",
            azure_openai_key="test-key",
            azure_openai_deployment="gpt-4",
        )

        mock_azure_cls = MagicMock()
        with patch.dict(sys.modules, {"openai": MagicMock(AzureOpenAI=mock_azure_cls)}):
            provider = create_completion_provider()

        assert isinstance(provider, AzureOpenAICompletionProvider)
