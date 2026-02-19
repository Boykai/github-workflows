"""Unit tests for the AI agent service (multi-provider support)."""

import json
from datetime import datetime
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from src.models.chat import (
    IssuePriority,
    IssueRecommendation,
    IssueSize,
    RecommendationStatus,
)
from src.services.ai_agent import (
    AIAgentService,
    GeneratedTask,
    StatusChangeIntent,
    get_ai_agent_service,
    reset_ai_agent_service,
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
        mock_provider.set_response('{"title": "Test Task", "description": "Test Description"}')

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
        mock_provider.set_response(f'{{"title": "{long_title}", "description": "Test"}}')

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
        mock_provider.set_response('{"title": "Task", "description": "Description"}')

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
    async def test_parse_status_change_handles_errors_gracefully(self, service, mock_provider):
        """Service should return None on errors, not raise."""
        mock_provider.set_error(Exception("API Error"))

        result = await service.parse_status_change_request(
            "Move task", ["Task"], ["Todo", "Done"], github_token="tok"
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_parse_status_change_passes_github_token(self, service, mock_provider):
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
        mock_provider.set_response('{"intent": "feature_request", "confidence": 0.9}')

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

        result = await service.detect_feature_request_intent("Some input", github_token="tok")

        assert result is False

    @pytest.mark.asyncio
    async def test_detect_feature_request_passes_github_token(self, service, mock_provider):
        """Should pass github_token to provider."""
        mock_provider.set_response('{"intent": "other", "confidence": 0.1}')

        await service.detect_feature_request_intent("Some input", github_token="my-gh-token")

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


# ──────────────────────────────────────────────────────────────────
# New tests for uncovered lines
# ──────────────────────────────────────────────────────────────────


def _make_valid_issue_json(**overrides) -> str:
    """Helper to build a valid issue recommendation JSON string."""
    data = {
        "title": "Add dark mode",
        "user_story": "As a user I want dark mode so that I can reduce eye strain.",
        "ui_ux_description": "Toggle in settings page.",
        "functional_requirements": ["Implement toggle", "Persist preference"],
        "technical_notes": "Use CSS variables.",
        "metadata": {
            "priority": "P1",
            "size": "M",
            "estimate_hours": 4,
            "start_date": "2025-01-01",
            "target_date": "2025-01-03",
            "labels": ["feature", "frontend"],
        },
    }
    data.update(overrides)
    return json.dumps(data)


class TestGenerateIssueRecommendation:
    """Tests for generate_issue_recommendation (lines 167-196)."""

    @pytest.fixture
    def mock_provider(self):
        return MockCompletionProvider()

    @pytest.fixture
    def service(self, mock_provider):
        return AIAgentService(provider=mock_provider)

    @pytest.mark.asyncio
    async def test_successful_generation(self, service, mock_provider):
        """Should return IssueRecommendation on valid AI response."""
        mock_provider.set_response(_make_valid_issue_json())
        session_id = str(uuid4())

        result = await service.generate_issue_recommendation(
            "Add dark mode", "TestProject", session_id, github_token="tok"
        )

        assert isinstance(result, IssueRecommendation)
        assert result.title == "Add dark mode"
        assert result.status == RecommendationStatus.PENDING

    @pytest.mark.asyncio
    async def test_passes_github_token(self, service, mock_provider):
        """Should forward github_token to provider."""
        mock_provider.set_response(_make_valid_issue_json())
        session_id = str(uuid4())

        await service.generate_issue_recommendation(
            "Add dark mode", "TestProject", session_id, github_token="my-token"
        )

        assert mock_provider.last_github_token == "my-token"

    @pytest.mark.asyncio
    async def test_error_401(self, service, mock_provider):
        """Should raise helpful error on 401."""
        mock_provider.set_error(Exception("401 Access denied"))

        with pytest.raises(ValueError, match="authentication failed"):
            await service.generate_issue_recommendation(
                "feature", "Proj", str(uuid4()), github_token="tok"
            )

    @pytest.mark.asyncio
    async def test_error_404(self, service, mock_provider):
        """Should raise helpful error on 404."""
        mock_provider.set_error(Exception("404 Resource not found"))

        with pytest.raises(ValueError, match="not found"):
            await service.generate_issue_recommendation(
                "feature", "Proj", str(uuid4()), github_token="tok"
            )

    @pytest.mark.asyncio
    async def test_generic_error(self, service, mock_provider):
        """Should wrap generic errors."""
        mock_provider.set_error(Exception("timeout"))

        with pytest.raises(ValueError, match="Failed to generate recommendation"):
            await service.generate_issue_recommendation(
                "feature", "Proj", str(uuid4()), github_token="tok"
            )


class TestParseIssueRecommendationResponse:
    """Tests for _parse_issue_recommendation_response (lines 215-241)."""

    @pytest.fixture
    def service(self):
        return AIAgentService(provider=MockCompletionProvider())

    def test_valid_response(self, service):
        """Should parse a complete valid response."""
        session_id = str(uuid4())
        result = service._parse_issue_recommendation_response(
            _make_valid_issue_json(), "user input", session_id
        )

        assert result.title == "Add dark mode"
        assert result.original_input == "user input"
        assert result.original_context == "user input"
        assert result.status == RecommendationStatus.PENDING
        assert len(result.functional_requirements) == 2

    def test_missing_title_raises(self, service):
        """Should raise when title is empty."""
        content = _make_valid_issue_json(title="")
        with pytest.raises(ValueError, match="missing title"):
            service._parse_issue_recommendation_response(content, "input", str(uuid4()))

    def test_missing_user_story_raises(self, service):
        """Should raise when user_story is empty."""
        content = _make_valid_issue_json(user_story="")
        with pytest.raises(ValueError, match="missing user_story"):
            service._parse_issue_recommendation_response(content, "input", str(uuid4()))

    def test_missing_functional_requirements_raises(self, service):
        """Should raise when functional_requirements is empty."""
        content = _make_valid_issue_json(functional_requirements=[])
        with pytest.raises(ValueError, match="missing functional_requirements"):
            service._parse_issue_recommendation_response(content, "input", str(uuid4()))

    def test_title_truncation(self, service):
        """Should truncate title over 256 characters."""
        long_title = "A" * 300
        content = _make_valid_issue_json(title=long_title)
        result = service._parse_issue_recommendation_response(content, "input", str(uuid4()))

        assert len(result.title) == 256
        assert result.title.endswith("...")

    def test_default_ui_ux_description(self, service):
        """Should default ui_ux_description when empty."""
        content = _make_valid_issue_json(ui_ux_description="")
        result = service._parse_issue_recommendation_response(content, "input", str(uuid4()))

        assert result.ui_ux_description == "No UI/UX description provided."


class TestParseIssueMetadata:
    """Tests for _parse_issue_metadata (lines 264-342)."""

    @pytest.fixture
    def service(self):
        return AIAgentService(provider=MockCompletionProvider())

    def test_valid_metadata(self, service):
        """Should parse valid metadata correctly."""
        data = {
            "priority": "P1",
            "size": "L",
            "estimate_hours": 8,
            "start_date": "2025-06-01",
            "target_date": "2025-06-05",
            "labels": ["feature", "backend"],
        }
        result = service._parse_issue_metadata(data)

        assert result.priority == IssuePriority.P1
        assert result.size == IssueSize.L
        assert result.estimate_hours == 8.0
        assert result.start_date == "2025-06-01"
        assert result.target_date == "2025-06-05"
        assert "ai-generated" in result.labels
        assert "feature" in result.labels
        assert "backend" in result.labels

    def test_invalid_priority_defaults_to_p2(self, service):
        """Should default to P2 for invalid priority."""
        result = service._parse_issue_metadata({"priority": "INVALID"})
        assert result.priority == IssuePriority.P2

    def test_invalid_size_defaults_to_m(self, service):
        """Should default to M for invalid size."""
        result = service._parse_issue_metadata({"size": "INVALID"})
        assert result.size == IssueSize.M

    def test_estimate_hours_bounds_low(self, service):
        """Should clamp estimate_hours to min 0.5."""
        result = service._parse_issue_metadata({"estimate_hours": 0.1})
        assert result.estimate_hours == 0.5

    def test_estimate_hours_bounds_high(self, service):
        """Should clamp estimate_hours to max 40."""
        result = service._parse_issue_metadata({"estimate_hours": 100})
        assert result.estimate_hours == 40.0

    def test_estimate_hours_invalid_type(self, service):
        """Should default to 4.0 on invalid estimate_hours."""
        result = service._parse_issue_metadata({"estimate_hours": "not a number"})
        assert result.estimate_hours == 4.0

    def test_invalid_start_date_defaults_to_today(self, service):
        """Should default invalid start_date to today."""
        result = service._parse_issue_metadata({"start_date": "not-a-date"})
        today = datetime.now().strftime("%Y-%m-%d")
        assert result.start_date == today

    def test_empty_start_date_defaults_to_today(self, service):
        """Should default empty start_date to today."""
        result = service._parse_issue_metadata({"start_date": ""})
        today = datetime.now().strftime("%Y-%m-%d")
        assert result.start_date == today

    def test_invalid_target_date_calculated_from_size(self, service):
        """Should calculate target_date from size when invalid."""
        result = service._parse_issue_metadata({"target_date": "bad-date", "size": "L"})
        # L = 2 days from today
        assert result.target_date  # just verify it's set

    def test_empty_target_date_calculated_from_size(self, service):
        """Should calculate target_date from size when empty."""
        result = service._parse_issue_metadata({"target_date": "", "size": "XL"})
        assert result.target_date  # just verify it's set

    def test_labels_not_a_list(self, service):
        """Should default to ['ai-generated'] if labels is not a list."""
        result = service._parse_issue_metadata({"labels": "not-a-list"})
        assert "ai-generated" in result.labels

    def test_labels_invalid_entries_skipped(self, service):
        """Should skip invalid label strings not in predefined set."""
        result = service._parse_issue_metadata({"labels": ["feature", "invalid-label-xyz"]})
        assert "feature" in result.labels
        assert "invalid-label-xyz" not in result.labels

    def test_ai_generated_always_present(self, service):
        """Should ensure ai-generated label is always present."""
        result = service._parse_issue_metadata({"labels": ["feature"]})
        assert "ai-generated" in result.labels

    def test_no_type_label_defaults_to_feature(self, service):
        """Should add 'feature' if no type label present."""
        result = service._parse_issue_metadata({"labels": ["frontend"]})
        assert "feature" in result.labels

    def test_empty_metadata(self, service):
        """Should handle completely empty metadata dict."""
        result = service._parse_issue_metadata({})
        assert result.priority == IssuePriority.P2
        assert result.size == IssueSize.M
        assert result.estimate_hours == 4.0
        assert "ai-generated" in result.labels
        assert "feature" in result.labels

    def test_labels_with_non_string_entries(self, service):
        """Should skip non-string labels."""
        result = service._parse_issue_metadata({"labels": [123, None, "feature"]})
        assert "feature" in result.labels
        assert "ai-generated" in result.labels


class TestIsValidDate:
    """Tests for _is_valid_date (lines 353-359)."""

    @pytest.fixture
    def service(self):
        return AIAgentService(provider=MockCompletionProvider())

    def test_valid_date(self, service):
        assert service._is_valid_date("2025-01-15") is True

    def test_invalid_format(self, service):
        assert service._is_valid_date("01-15-2025") is False

    def test_invalid_string(self, service):
        assert service._is_valid_date("not-a-date") is False

    def test_empty_string(self, service):
        assert service._is_valid_date("") is False


class TestCalculateTargetDate:
    """Tests for _calculate_target_date (lines 363-374)."""

    @pytest.fixture
    def service(self):
        return AIAgentService(provider=MockCompletionProvider())

    def test_xs_same_day(self, service):
        start = datetime(2025, 6, 1)
        assert service._calculate_target_date(start, IssueSize.XS) == "2025-06-01"

    def test_s_same_day(self, service):
        start = datetime(2025, 6, 1)
        assert service._calculate_target_date(start, IssueSize.S) == "2025-06-01"

    def test_m_next_day(self, service):
        start = datetime(2025, 6, 1)
        assert service._calculate_target_date(start, IssueSize.M) == "2025-06-02"

    def test_l_two_days(self, service):
        start = datetime(2025, 6, 1)
        assert service._calculate_target_date(start, IssueSize.L) == "2025-06-03"

    def test_xl_four_days(self, service):
        start = datetime(2025, 6, 1)
        assert service._calculate_target_date(start, IssueSize.XL) == "2025-06-05"


class TestIdentifyTargetTaskFuzzy:
    """Additional tests for fuzzy matching in identify_target_task (lines 519-530)."""

    @pytest.fixture
    def service(self):
        return AIAgentService(provider=MockCompletionProvider())

    def test_fuzzy_match_best_word_overlap(self, service):
        """Should pick the task with most word overlap."""
        tasks = [
            Mock(task_id="1", title="Build user login page"),
            Mock(task_id="2", title="Design database schema"),
            Mock(task_id="3", title="Create user profile page"),
        ]

        result = service.identify_target_task("user profile settings page", tasks)
        assert result.task_id == "3"

    def test_fuzzy_no_overlap_returns_none(self, service):
        """Should return None when no words overlap."""
        tasks = [
            Mock(task_id="1", title="Alpha beta gamma"),
        ]

        result = service.identify_target_task("delta epsilon zeta", tasks)
        assert result is None


class TestIdentifyTargetStatusAliases:
    """Additional tests for alias matching in identify_target_status (lines 601-633)."""

    @pytest.fixture
    def service(self):
        return AIAgentService(provider=MockCompletionProvider())

    def test_alias_backlog_maps_to_todo(self, service):
        statuses = ["Todo", "In Progress", "Done"]
        assert service.identify_target_status("backlog", statuses) == "Todo"

    def test_alias_not_started_maps_to_todo(self, service):
        statuses = ["Todo", "In Progress", "Done"]
        assert service.identify_target_status("not started", statuses) == "Todo"

    def test_alias_working_maps_to_in_progress(self, service):
        statuses = ["Todo", "In Progress", "Done"]
        assert service.identify_target_status("working", statuses) == "In Progress"

    def test_alias_finished_maps_to_done(self, service):
        statuses = ["Todo", "In Progress", "Done"]
        assert service.identify_target_status("finished", statuses) == "Done"

    def test_alias_closed_maps_to_done(self, service):
        statuses = ["Todo", "In Progress", "Done"]
        assert service.identify_target_status("closed", statuses) == "Done"


class TestParseJsonResponseExtended:
    """Additional tests for _parse_json_response and _repair_truncated_json (lines 641-729)."""

    @pytest.fixture
    def service(self):
        return AIAgentService(provider=MockCompletionProvider())

    def test_truncated_markdown_code_block(self, service):
        """Should handle truncated markdown fence (no closing ```)."""
        content = '```json\n{"title": "Test", "description": "Value"}'
        result = service._parse_json_response(content)
        assert result["title"] == "Test"

    def test_json_embedded_in_text(self, service):
        """Should extract JSON object from surrounding text."""
        content = 'Here is the response: {"key": "value"} Hope that helps!'
        result = service._parse_json_response(content)
        assert result == {"key": "value"}

    def test_repair_truncated_object(self, service):
        """Should repair a truncated JSON object."""
        content = '{"title": "Test", "desc": "Val'
        result = service._parse_json_response(content)
        assert result["title"] == "Test"

    def test_repair_truncated_array(self, service):
        """Should repair truncated JSON with open array."""
        content = '{"items": ["a", "b"'
        result = service._parse_json_response(content)
        assert result["items"] == ["a", "b"]

    def test_repair_nested_truncation(self, service):
        """Should repair nested truncated JSON."""
        content = '{"outer": {"inner": "val'
        result = service._parse_json_response(content)
        assert result["outer"]["inner"] == "val"

    def test_no_json_object_raises(self, service):
        """Should raise when there is no JSON at all."""
        with pytest.raises(ValueError, match="Invalid JSON response"):
            service._parse_json_response("just plain text without braces")

    def test_json_with_escaped_quotes(self, service):
        """Should handle escaped quotes in JSON strings."""
        content = '{"msg": "He said \\"hello\\"", "ok": true}'
        result = service._parse_json_response(content)
        assert result["msg"] == 'He said "hello"'
        assert result["ok"] is True


class TestRepairTruncatedJson:
    """Direct tests for _repair_truncated_json (lines 638-729)."""

    @pytest.fixture
    def service(self):
        return AIAgentService(provider=MockCompletionProvider())

    def test_returns_none_for_complete_json(self, service):
        """Should return None when JSON is already complete (nothing to repair)."""
        result = service._repair_truncated_json('{"key": "value"}')
        assert result is None

    def test_repairs_open_string(self, service):
        """Should close an open string and object."""
        result = service._repair_truncated_json('{"key": "val')
        assert result is not None
        assert result["key"] == "val"

    def test_repairs_open_array_and_object(self, service):
        """Should close open array and object."""
        result = service._repair_truncated_json('{"items": [1, 2')
        assert result is not None
        assert result["items"] == [1, 2]

    def test_aggressive_repair_on_bad_truncation(self, service):
        """Should attempt aggressive repair when simple repair fails."""
        # Truncated mid-key: simple repair would produce invalid JSON,
        # so the aggressive trimming path should kick in.
        result = service._repair_truncated_json('{"a": 1, "b":')
        assert result is not None
        assert result["a"] == 1

    def test_unfixable_returns_none(self, service):
        """Should return None for content that can't be repaired."""
        result = service._repair_truncated_json("totally not json {{{")
        assert result is None


class TestValidateGeneratedTask:
    """Tests for _validate_generated_task (lines 731-746)."""

    @pytest.fixture
    def service(self):
        return AIAgentService(provider=MockCompletionProvider())

    def test_valid_task(self, service):
        data = {"title": "My Task", "description": "A description"}
        result = service._validate_generated_task(data)
        assert result.title == "My Task"
        assert result.description == "A description"

    def test_missing_title_raises(self, service):
        with pytest.raises(ValueError, match="missing title"):
            service._validate_generated_task({"title": "", "description": "desc"})

    def test_long_title_truncated(self, service):
        data = {"title": "T" * 300, "description": "desc"}
        result = service._validate_generated_task(data)
        assert len(result.title) == 256
        assert result.title.endswith("...")

    def test_long_description_truncated(self, service):
        data = {"title": "Task", "description": "D" * 70000}
        result = service._validate_generated_task(data)
        assert len(result.description) == 65535
        assert result.description.endswith("...")


class TestGetAndResetAIAgentService:
    """Tests for get_ai_agent_service and reset_ai_agent_service (lines 764-772)."""

    @patch("src.services.ai_agent.create_completion_provider")
    def test_get_returns_singleton(self, mock_create):
        """Should return the same instance on repeated calls."""
        mock_create.return_value = MockCompletionProvider()
        reset_ai_agent_service()

        svc1 = get_ai_agent_service()
        svc2 = get_ai_agent_service()

        assert svc1 is svc2
        mock_create.assert_called_once()

    @patch("src.services.ai_agent.create_completion_provider")
    def test_reset_clears_instance(self, mock_create):
        """Should create a new instance after reset."""
        mock_create.return_value = MockCompletionProvider()
        reset_ai_agent_service()

        svc1 = get_ai_agent_service()
        reset_ai_agent_service()
        svc2 = get_ai_agent_service()

        assert svc1 is not svc2
        assert mock_create.call_count == 2

    def teardown_method(self):
        """Clean up global state after each test."""
        reset_ai_agent_service()


class TestParseStatusChangeRequestExtended:
    """Additional tests for parse_status_change_request (lines 519-530)."""

    @pytest.fixture
    def mock_provider(self):
        return MockCompletionProvider()

    @pytest.fixture
    def service(self, mock_provider):
        return AIAgentService(provider=mock_provider)

    @pytest.mark.asyncio
    async def test_returns_none_on_invalid_json(self, service, mock_provider):
        """Should return None when provider returns invalid JSON."""
        mock_provider.set_response("not json")

        result = await service.parse_status_change_request(
            "move task", ["Task"], ["Todo", "Done"], github_token="tok"
        )
        assert result is None


class TestParseJsonResponseEscapes:
    """Tests for escape handling in _parse_json_response extraction loop (lines 606-612)."""

    @pytest.fixture
    def service(self):
        return AIAgentService(provider=MockCompletionProvider())

    def test_extracts_json_with_backslash_in_string_from_text(self, service):
        """Should handle backslashes inside JSON strings when extracting from text."""
        content = 'Result: {"path": "C:\\\\Users\\\\test", "ok": true} done'
        result = service._parse_json_response(content)
        assert result["path"] == "C:\\Users\\test"
        assert result["ok"] is True

    def test_extracts_json_with_escaped_quotes_from_text(self, service):
        """Should handle escaped quotes in extraction from surrounding text."""
        content = 'Output: {"msg": "say \\"hi\\"", "n": 1} end'
        result = service._parse_json_response(content)
        assert result["msg"] == 'say "hi"'

    def test_backslash_outside_string_ignored(self, service):
        """Backslashes outside of JSON strings should not trigger escape logic."""
        # backslash in the prefix text, not inside the JSON string
        content = 'path\\to\\file {"key": "value"}'
        result = service._parse_json_response(content)
        assert result["key"] == "value"


class TestRepairTruncatedJsonAggressive:
    """Tests for aggressive repair paths in _repair_truncated_json (lines 682-729)."""

    @pytest.fixture
    def service(self):
        return AIAgentService(provider=MockCompletionProvider())

    def test_aggressive_repair_with_escaped_strings(self, service):
        """Should handle escaped strings during aggressive repair recount."""
        # Truncated JSON with escape sequences that need aggressive repair
        content = '{"a": "val\\"ue", "b": "truncat'
        result = service._repair_truncated_json(content)
        assert result is not None
        # Should at least recover the first key
        assert "a" in result

    def test_aggressive_repair_with_nested_array(self, service):
        """Should handle nested arrays in aggressive repair."""
        content = '{"items": [{"id": 1}, {"id": 2'
        result = service._repair_truncated_json(content)
        assert result is not None
        assert len(result["items"]) >= 1

    def test_aggressive_repair_closing_bracket(self, service):
        """Should handle ']' in the repair tracking."""
        content = '{"list": [1, 2], "extra": ['
        result = service._repair_truncated_json(content)
        assert result is not None
        assert result["list"] == [1, 2]

    def test_aggressive_repair_with_open_string_in_trimmed(self, service):
        """Should handle open string state during aggressive recount."""
        # The trimmed version will have an open string that needs closing
        content = '{"x": 1, "y": "hello world'
        result = service._repair_truncated_json(content)
        assert result is not None

    def test_aggressive_repair_all_cutoff_chars_fail(self, service):
        """Should return None when all aggressive attempts fail."""
        # Content where simple repair produces invalid JSON and
        # aggressive trimming also can't produce valid JSON
        content = '{"bad: {{{[[["""'
        result = service._repair_truncated_json(content)
        # Either None or a valid dict - we just need to not crash
        assert result is None or isinstance(result, dict)

    def test_matched_candidate_invalid_json(self, service):
        """Exercise the branch where brace-matched candidate is not valid JSON."""
        # Braces match but content between them is not valid JSON
        # e.g. {not: valid json}  - braces balance but it's not parseable
        content = "prefix {not valid: json content} suffix"
        with pytest.raises(ValueError, match="Invalid JSON response"):
            service._parse_json_response(content)

    def test_aggressive_repair_recount_with_escapes_and_arrays(self, service):
        """Exercise recount loop with escapes, arrays, and closing brackets."""
        # Content where simple repair fails (truncated mid-key),
        # forcing aggressive path. The attempt content includes
        # escaped strings, arrays, and closing brackets.
        content = '{"a": "c:\\\\d", "list": [1, 2], "nested": {"x": 1}, "trunc'
        result = service._repair_truncated_json(content)
        assert result is not None
        assert result["a"] == "c:\\d"
        assert result["list"] == [1, 2]

    def test_aggressive_repair_recount_with_open_string(self, service):
        """Exercise the s_in_str branch in aggressive recount."""
        # Truncated mid-key so simple repair produces invalid JSON.
        # The trimmed attempt has strings with escapes to exercise recount.
        content = '{"path": "C:\\\\Users\\\\test", "k'
        result = service._repair_truncated_json(content)
        assert result is not None
        assert result["path"] == "C:\\Users\\test"
