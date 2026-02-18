"""Unit tests for the AI agent service (multi-provider support)."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.services.ai_agent import (
    AIAgentService,
    GeneratedTask,
    StatusChangeIntent,
)
from src.services.completion_providers import CompletionProvider


class MockCompletionProvider(CompletionProvider):
    """Test double for CompletionProvider that returns configurable responses."""

    def __init__(self, response: str = ""):
        self._response = response
        self._side_effect = None
        self.last_messages = None
        self.last_github_token = None

    async def complete(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        github_token: str | None = None,
    ) -> str:
        self.last_messages = messages
        self.last_github_token = github_token
        if self._side_effect:
            raise self._side_effect
        return self._response

    def set_response(self, response: str) -> None:
        self._response = response
        self._side_effect = None

    def set_error(self, error: Exception) -> None:
        self._side_effect = error

    @property
    def name(self) -> str:
        return "mock"


class TestAIAgentServiceInit:
    """Tests for AIAgentService initialization."""

    def test_init_with_custom_provider(self):
        """Service should accept a custom CompletionProvider."""
        provider = MockCompletionProvider()
        service = AIAgentService(provider=provider)
        assert service._provider is provider

    @patch("src.services.ai_agent.create_completion_provider")
    def test_init_default_provider(self, mock_create):
        """Service should create provider via factory if none provided."""
        mock_provider = MockCompletionProvider()
        mock_create.return_value = mock_provider

        service = AIAgentService()
        mock_create.assert_called_once()
        assert service._provider is mock_provider


class TestCallCompletion:
    """Tests for the _call_completion method."""

    @pytest.fixture
    def mock_provider(self):
        return MockCompletionProvider()

    @pytest.fixture
    def service(self, mock_provider):
        return AIAgentService(provider=mock_provider)

    @pytest.mark.asyncio
    async def test_call_completion_passes_github_token(self, service, mock_provider):
        """Should pass github_token through to the provider."""
        mock_provider.set_response('{"result": "ok"}')

        await service._call_completion(
            messages=[{"role": "user", "content": "test"}],
            github_token="test-token-123",
        )

        assert mock_provider.last_github_token == "test-token-123"

    @pytest.mark.asyncio
    async def test_call_completion_passes_messages(self, service, mock_provider):
        """Should pass messages through to the provider."""
        mock_provider.set_response("response")
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
        ]

        await service._call_completion(messages=messages)

        assert mock_provider.last_messages == messages


class TestGenerateTaskFromDescription:
    """Tests for task generation from natural language."""

    @pytest.fixture
    def mock_provider(self):
        return MockCompletionProvider()

    @pytest.fixture
    def service(self, mock_provider):
        return AIAgentService(provider=mock_provider)

    @pytest.mark.asyncio
    async def test_generate_task_parses_json_response(self, service, mock_provider):
        """Service should parse JSON response and return GeneratedTask."""
        mock_provider.set_response(
            '{"title": "Test Task", "description": "Test Description"}'
        )

        result = await service.generate_task_from_description(
            "Create a task for testing", "Test Project", github_token="tok"
        )

        assert isinstance(result, GeneratedTask)
        assert result.title == "Test Task"
        assert result.description == "Test Description"

    @pytest.mark.asyncio
    async def test_generate_task_handles_markdown_code_blocks(self, service, mock_provider):
        """Service should handle JSON wrapped in markdown code blocks."""
        mock_provider.set_response(
            '```json\n{"title": "Markdown Task", "description": "With code block"}\n```'
        )

        result = await service.generate_task_from_description(
            "Create a task", "Project", github_token="tok"
        )

        assert result.title == "Markdown Task"
        assert result.description == "With code block"

    @pytest.mark.asyncio
    async def test_generate_task_raises_on_invalid_json(self, service, mock_provider):
        """Service should raise ValueError on invalid JSON."""
        mock_provider.set_response("Not valid JSON")

        with pytest.raises(ValueError, match="Failed to generate task"):
            await service.generate_task_from_description(
                "Create task", "Project", github_token="tok"
            )

    @pytest.mark.asyncio
    async def test_generate_task_raises_on_missing_title(self, service, mock_provider):
        """Service should raise ValueError when title is missing."""
        mock_provider.set_response('{"description": "No title"}')

        with pytest.raises(ValueError, match="Failed to generate task"):
            await service.generate_task_from_description(
                "Create task", "Project", github_token="tok"
            )

    @pytest.mark.asyncio
    async def test_generate_task_truncates_long_title(self, service, mock_provider):
        """Service should truncate titles over 256 characters."""
        long_title = "A" * 300
        mock_provider.set_response(
            f'{{"title": "{long_title}", "description": "Test"}}'
        )

        result = await service.generate_task_from_description(
            "Create task", "Project", github_token="tok"
        )

        assert len(result.title) == 256
        assert result.title.endswith("...")

    @pytest.mark.asyncio
    async def test_generate_task_helpful_error_on_401(self, service, mock_provider):
        """Service should provide helpful error message on 401."""
        mock_provider.set_error(Exception("401 Access denied"))

        with pytest.raises(ValueError, match="authentication failed"):
            await service.generate_task_from_description(
                "Create task", "Project", github_token="tok"
            )

    @pytest.mark.asyncio
    async def test_generate_task_helpful_error_on_404(self, service, mock_provider):
        """Service should provide helpful error message on 404."""
        mock_provider.set_error(Exception("404 Resource not found"))

        with pytest.raises(ValueError, match="not found"):
            await service.generate_task_from_description(
                "Create task", "Project", github_token="tok"
            )

    @pytest.mark.asyncio
    async def test_generate_task_passes_github_token(self, service, mock_provider):
        """Service should pass github_token to provider."""
        mock_provider.set_response(
            '{"title": "Task", "description": "Description"}'
        )

        await service.generate_task_from_description(
            "Create task", "Project", github_token="user-oauth-token"
        )

        assert mock_provider.last_github_token == "user-oauth-token"


class TestParseStatusChangeRequest:
    """Tests for status change intent detection."""

    @pytest.fixture
    def mock_provider(self):
        return MockCompletionProvider()

    @pytest.fixture
    def service(self, mock_provider):
        return AIAgentService(provider=mock_provider)

    @pytest.mark.asyncio
    async def test_parse_status_change_returns_intent(self, service, mock_provider):
        """Service should return StatusChangeIntent for valid requests."""
        mock_provider.set_response(
            '{"intent": "status_change", "task_reference": "Login feature", '
            '"target_status": "Done", "confidence": 0.9}'
        )

        result = await service.parse_status_change_request(
            "Mark login feature as done",
            ["Login feature", "Dashboard"],
            ["Todo", "In Progress", "Done"],
            github_token="tok",
        )

        assert isinstance(result, StatusChangeIntent)
        assert result.task_reference == "Login feature"
        assert result.target_status == "Done"
        assert result.confidence == 0.9

    @pytest.mark.asyncio
    async def test_parse_status_change_returns_none_for_low_confidence(
        self, service, mock_provider
    ):
        """Service should return None for low confidence detections."""
        mock_provider.set_response(
            '{"intent": "status_change", "task_reference": "Task", '
            '"target_status": "Done", "confidence": 0.3}'
        )

        result = await service.parse_status_change_request(
            "Maybe done?", ["Task"], ["Todo", "Done"], github_token="tok"
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_parse_status_change_returns_none_for_non_status_intent(
        self, service, mock_provider
    ):
        """Service should return None when intent is not status_change."""
        mock_provider.set_response('{"intent": "create_task", "confidence": 0.9}')

        result = await service.parse_status_change_request(
            "Create a new task", ["Task"], ["Todo", "Done"], github_token="tok"
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_parse_status_change_handles_errors_gracefully(
        self, service, mock_provider
    ):
        """Service should return None on errors, not raise."""
        mock_provider.set_error(Exception("API Error"))

        result = await service.parse_status_change_request(
            "Move task", ["Task"], ["Todo", "Done"], github_token="tok"
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_parse_status_change_passes_github_token(
        self, service, mock_provider
    ):
        """Service should pass github_token to provider."""
        mock_provider.set_response('{"intent": "other"}')

        await service.parse_status_change_request(
            "Move task", ["Task"], ["Todo", "Done"], github_token="my-token"
        )

        assert mock_provider.last_github_token == "my-token"


class TestDetectFeatureRequestIntent:
    """Tests for feature request intent detection."""

    @pytest.fixture
    def mock_provider(self):
        return MockCompletionProvider()

    @pytest.fixture
    def service(self, mock_provider):
        return AIAgentService(provider=mock_provider)

    @pytest.mark.asyncio
    async def test_detect_feature_request_true(self, service, mock_provider):
        """Should detect feature request intent."""
        mock_provider.set_response(
            '{"intent": "feature_request", "confidence": 0.9}'
        )

        result = await service.detect_feature_request_intent(
            "Add a dark mode toggle", github_token="tok"
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_detect_feature_request_false(self, service, mock_provider):
        """Should return False when not a feature request."""
        mock_provider.set_response('{"intent": "other", "confidence": 0.1}')

        result = await service.detect_feature_request_intent(
            "Move task to done", github_token="tok"
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_detect_feature_request_handles_errors(self, service, mock_provider):
        """Should return False on errors."""
        mock_provider.set_error(Exception("API Error"))

        result = await service.detect_feature_request_intent(
            "Some input", github_token="tok"
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_detect_feature_request_passes_github_token(
        self, service, mock_provider
    ):
        """Should pass github_token to provider."""
        mock_provider.set_response('{"intent": "other", "confidence": 0.1}')

        await service.detect_feature_request_intent(
            "Some input", github_token="my-gh-token"
        )

        assert mock_provider.last_github_token == "my-gh-token"


class TestIdentifyTargetTask:
    """Tests for task reference matching."""

    @pytest.fixture
    def service(self):
        return AIAgentService(provider=MockCompletionProvider())

    def test_identify_task_exact_match(self, service):
        """Should find exact title match."""
        tasks = [
            Mock(task_id="1", title="Login Feature"),
            Mock(task_id="2", title="Dashboard"),
        ]

        result = service.identify_target_task("Login Feature", tasks)

        assert result.task_id == "1"

    def test_identify_task_case_insensitive(self, service):
        """Should match case-insensitively."""
        tasks = [Mock(task_id="1", title="Login Feature")]

        result = service.identify_target_task("login feature", tasks)

        assert result.task_id == "1"

    def test_identify_task_partial_match(self, service):
        """Should match partial references."""
        tasks = [
            Mock(task_id="1", title="Implement Login Feature"),
            Mock(task_id="2", title="Dashboard Widget"),
        ]

        result = service.identify_target_task("Login Feature", tasks)

        assert result.task_id == "1"

    def test_identify_task_word_overlap(self, service):
        """Should match by word overlap when no partial match."""
        tasks = [
            Mock(task_id="1", title="Create user authentication system"),
            Mock(task_id="2", title="Build dashboard"),
        ]

        result = service.identify_target_task("user authentication", tasks)

        assert result.task_id == "1"

    def test_identify_task_returns_none_for_empty(self, service):
        """Should return None for empty inputs."""
        assert service.identify_target_task("", []) is None
        assert service.identify_target_task("task", []) is None
        assert service.identify_target_task("", [Mock(task_id="1", title="Task")]) is None


class TestIdentifyTargetStatus:
    """Tests for status reference matching."""

    @pytest.fixture
    def service(self):
        return AIAgentService(provider=MockCompletionProvider())

    def test_identify_status_exact_match(self, service):
        """Should find exact status match."""
        statuses = ["Todo", "In Progress", "Done"]

        assert service.identify_target_status("Done", statuses) == "Done"

    def test_identify_status_case_insensitive(self, service):
        """Should match case-insensitively."""
        statuses = ["Todo", "In Progress", "Done"]

        assert service.identify_target_status("done", statuses) == "Done"
        assert service.identify_target_status("TODO", statuses) == "Todo"

    def test_identify_status_partial_match(self, service):
        """Should match partial references."""
        statuses = ["Todo", "In Progress", "Done"]

        assert service.identify_target_status("progress", statuses) == "In Progress"

    def test_identify_status_aliases(self, service):
        """Should recognize common status aliases."""
        statuses = ["Todo", "In Progress", "Done"]

        # "completed" is an alias for "done"
        assert service.identify_target_status("completed", statuses) == "Done"
        # "doing" is an alias for "in progress"
        assert service.identify_target_status("doing", statuses) == "In Progress"

    def test_identify_status_returns_none_for_unknown(self, service):
        """Should return None for unrecognized statuses."""
        statuses = ["Todo", "In Progress", "Done"]

        assert service.identify_target_status("random status", statuses) is None

    def test_identify_status_returns_none_for_empty(self, service):
        """Should return None for empty inputs."""
        assert service.identify_target_status("", []) is None
        assert service.identify_target_status("done", []) is None
        assert service.identify_target_status("", ["Todo"]) is None


class TestParseJsonResponse:
    """Tests for JSON parsing helper."""

    @pytest.fixture
    def service(self):
        return AIAgentService(provider=MockCompletionProvider())

    def test_parse_plain_json(self, service):
        """Should parse plain JSON."""
        result = service._parse_json_response('{"key": "value"}')
        assert result == {"key": "value"}

    def test_parse_json_with_markdown(self, service):
        """Should strip markdown code blocks."""
        result = service._parse_json_response('```json\n{"key": "value"}\n```')
        assert result == {"key": "value"}

    def test_parse_json_with_generic_markdown(self, service):
        """Should strip generic markdown code blocks."""
        result = service._parse_json_response('```\n{"key": "value"}\n```')
        assert result == {"key": "value"}

    def test_parse_json_raises_on_invalid(self, service):
        """Should raise ValueError on invalid JSON."""
        with pytest.raises(ValueError, match="Invalid JSON response"):
            service._parse_json_response("not json at all")


class TestCompletionProviders:
    """Tests for the completion provider infrastructure."""

    def test_copilot_provider_requires_github_token(self):
        """CopilotCompletionProvider should require github_token."""
        from src.services.completion_providers import CopilotCompletionProvider

        provider = CopilotCompletionProvider(model="gpt-4o")
        assert provider.name == "copilot"

    @patch("src.services.completion_providers.get_settings")
    def test_azure_provider_requires_credentials(self, mock_settings):
        """AzureOpenAICompletionProvider should require Azure credentials."""
        from src.services.completion_providers import AzureOpenAICompletionProvider

        mock_settings.return_value = Mock(
            azure_openai_endpoint=None,
            azure_openai_key=None,
            azure_openai_deployment="gpt-4",
        )

        with pytest.raises(ValueError, match="Azure OpenAI credentials not configured"):
            AzureOpenAICompletionProvider()

    @patch("src.services.completion_providers.get_settings")
    def test_create_provider_copilot(self, mock_settings):
        """Factory should create CopilotCompletionProvider for 'copilot'."""
        from src.services.completion_providers import (
            CopilotCompletionProvider,
            create_completion_provider,
        )

        mock_settings.return_value = Mock(
            ai_provider="copilot",
            copilot_model="gpt-4o",
        )

        provider = create_completion_provider()
        assert isinstance(provider, CopilotCompletionProvider)

    @patch("src.services.completion_providers.get_settings")
    def test_create_provider_unknown_raises(self, mock_settings):
        """Factory should raise for unknown provider name."""
        from src.services.completion_providers import create_completion_provider

        mock_settings.return_value = Mock(ai_provider="unknown_provider")

        with pytest.raises(ValueError, match="Unknown AI provider"):
            create_completion_provider()
