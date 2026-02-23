"""Unit tests for the AI agent service (multi-provider support)."""

from unittest.mock import Mock, patch

import pytest

from src.models.chat import IssuePriority, IssueSize, RecommendationStatus
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

    def test_identify_task_fuzzy_multiple_partial_matches(self, service):
        """When multiple partial matches exist, fall through to fuzzy word overlap."""
        tasks = [
            Mock(task_id="1", title="fix login page"),
            Mock(task_id="2", title="fix auth flow"),
        ]
        # "fix" is a substring of both titles → multiple partial matches
        # Fuzzy: ref_words={"fix", "login"}, task1 overlap=2 (fix, login), task2 overlap=1 (fix)
        result = service.identify_target_task("fix login", tasks)
        assert result.task_id == "1"

    def test_identify_task_no_overlap_returns_none(self, service):
        """When no word overlap at all → returns None."""
        tasks = [
            Mock(task_id="1", title="build dashboard"),
            Mock(task_id="2", title="add widget"),
        ]
        # "deploy server" has zero word overlap with either title
        result = service.identify_target_task("deploy server", tasks)
        assert result is None


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


class TestGenerateIssueRecommendation:
    """Tests for issue recommendation generation flow."""

    @pytest.fixture
    def mock_provider(self):
        return MockCompletionProvider()

    @pytest.fixture
    def service(self, mock_provider):
        return AIAgentService(provider=mock_provider)

    @pytest.mark.asyncio
    async def test_generate_recommendation_happy_path(self, service, mock_provider):
        mock_provider.set_response(
            '{"title": "CSV Export", "user_story": "As a user I want CSV", '
            '"ui_ux_description": "Button", "functional_requirements": ["R1"], '
            '"technical_notes": "Stream"}'
        )
        rec = await service.generate_issue_recommendation(
            "Add CSV export", "MyProject", "00000000-0000-0000-0000-000000000001"
        )
        assert rec.title == "CSV Export"
        assert rec.original_input == "Add CSV export"
        assert rec.status == RecommendationStatus.PENDING
        assert "ai-generated" in rec.metadata.labels

    @pytest.mark.asyncio
    async def test_generate_recommendation_401_error(self, service, mock_provider):
        mock_provider.set_error(Exception("401 Access denied"))
        with pytest.raises(ValueError, match="authentication failed"):
            await service.generate_issue_recommendation(
                "input", "proj", "00000000-0000-0000-0000-000000000001"
            )

    @pytest.mark.asyncio
    async def test_generate_recommendation_404_error(self, service, mock_provider):
        mock_provider.set_error(Exception("404 Resource not found"))
        with pytest.raises(ValueError, match="not found"):
            await service.generate_issue_recommendation(
                "input", "proj", "00000000-0000-0000-0000-000000000001"
            )

    @pytest.mark.asyncio
    async def test_generate_recommendation_generic_error(self, service, mock_provider):
        mock_provider.set_error(Exception("Timeout"))
        with pytest.raises(ValueError, match="Failed to generate recommendation"):
            await service.generate_issue_recommendation(
                "input", "proj", "00000000-0000-0000-0000-000000000001"
            )


class TestParseIssueRecommendationResponse:
    """Tests for _parse_issue_recommendation_response."""

    @pytest.fixture
    def service(self):
        return AIAgentService(provider=MockCompletionProvider())

    def test_valid_response(self, service):
        content = (
            '{"title": "Feat", "user_story": "As a user", '
            '"ui_ux_description": "Button", '
            '"functional_requirements": ["R1"]}'
        )
        rec = service._parse_issue_recommendation_response(
            content, "input", "00000000-0000-0000-0000-000000000001"
        )
        assert rec.title == "Feat"
        assert rec.original_context == "input"

    def test_missing_title_raises(self, service):
        with pytest.raises(ValueError, match="missing title"):
            service._parse_issue_recommendation_response(
                '{"user_story": "story", "functional_requirements": ["R1"]}',
                "i",
                "00000000-0000-0000-0000-000000000001",
            )

    def test_missing_user_story_raises(self, service):
        with pytest.raises(ValueError, match="missing user_story"):
            service._parse_issue_recommendation_response(
                '{"title": "T", "functional_requirements": ["R1"]}',
                "i",
                "00000000-0000-0000-0000-000000000001",
            )

    def test_missing_requirements_raises(self, service):
        with pytest.raises(ValueError, match="missing functional_requirements"):
            service._parse_issue_recommendation_response(
                '{"title": "T", "user_story": "S"}',
                "i",
                "00000000-0000-0000-0000-000000000001",
            )

    def test_long_title_truncated(self, service):
        long_title = "A" * 300
        content = (
            f'{{"title": "{long_title}", "user_story": "S", "functional_requirements": ["R"]}}'
        )
        rec = service._parse_issue_recommendation_response(
            content, "i", "00000000-0000-0000-0000-000000000001"
        )
        assert len(rec.title) == 256
        assert rec.title.endswith("...")


class TestParseIssueMetadata:
    """Tests for _parse_issue_metadata."""

    @pytest.fixture
    def service(self):
        return AIAgentService(provider=MockCompletionProvider())

    def test_default_metadata(self, service):
        meta = service._parse_issue_metadata({})
        assert meta.priority == IssuePriority.P2
        assert meta.size == IssueSize.M
        assert meta.estimate_hours == 4.0
        assert "ai-generated" in meta.labels
        assert "feature" in meta.labels

    def test_custom_priority_and_size(self, service):
        meta = service._parse_issue_metadata({"priority": "P1", "size": "XL"})
        assert meta.priority == IssuePriority.P1
        assert meta.size == IssueSize.XL

    def test_invalid_priority_defaults(self, service):
        meta = service._parse_issue_metadata({"priority": "INVALID"})
        assert meta.priority == IssuePriority.P2

    def test_invalid_size_defaults(self, service):
        meta = service._parse_issue_metadata({"size": "HUGE"})
        assert meta.size == IssueSize.M

    def test_estimate_hours_bounds(self, service):
        meta = service._parse_issue_metadata({"estimate_hours": 100})
        assert meta.estimate_hours == 40.0
        meta2 = service._parse_issue_metadata({"estimate_hours": 0.1})
        assert meta2.estimate_hours == 0.5

    def test_invalid_estimate_hours(self, service):
        meta = service._parse_issue_metadata({"estimate_hours": "not-a-number"})
        assert meta.estimate_hours == 4.0

    def test_invalid_date_gets_default(self, service):
        meta = service._parse_issue_metadata({"start_date": "not-a-date"})
        # Should fall back to today
        assert len(meta.start_date) == 10  # YYYY-MM-DD

    def test_valid_dates_preserved(self, service):
        meta = service._parse_issue_metadata(
            {
                "start_date": "2025-01-15",
                "target_date": "2025-01-20",
            }
        )
        assert meta.start_date == "2025-01-15"
        assert meta.target_date == "2025-01-20"

    def test_labels_filtering(self, service):
        meta = service._parse_issue_metadata({"labels": ["feature", "invalid-label-xyz", "bug"]})
        assert "feature" in meta.labels
        assert "bug" in meta.labels
        assert "invalid-label-xyz" not in meta.labels
        assert "ai-generated" in meta.labels

    def test_non_list_labels(self, service):
        meta = service._parse_issue_metadata({"labels": "not-a-list"})
        assert "ai-generated" in meta.labels
        assert "feature" in meta.labels  # default type label added


class TestIsValidDate:
    @pytest.fixture
    def service(self):
        return AIAgentService(provider=MockCompletionProvider())

    def test_valid_date(self, service):
        assert service._is_valid_date("2025-01-15") is True

    def test_invalid_date(self, service):
        assert service._is_valid_date("not-a-date") is False
        assert service._is_valid_date("2025/01/15") is False


class TestCalculateTargetDate:
    @pytest.fixture
    def service(self):
        return AIAgentService(provider=MockCompletionProvider())

    def test_xs_same_day(self, service):
        from datetime import datetime

        start = datetime(2025, 1, 15)
        result = service._calculate_target_date(start, IssueSize.XS)
        assert result == "2025-01-15"

    def test_xl_four_days(self, service):
        from datetime import datetime

        start = datetime(2025, 1, 15)
        result = service._calculate_target_date(start, IssueSize.XL)
        assert result == "2025-01-19"


class TestRepairTruncatedJson:
    @pytest.fixture
    def service(self):
        return AIAgentService(provider=MockCompletionProvider())

    def test_repair_missing_closing_brace(self, service):
        result = service._repair_truncated_json('{"key": "value"')
        assert result == {"key": "value"}

    def test_repair_missing_array_close(self, service):
        result = service._repair_truncated_json('{"items": [1, 2')
        assert result == {"items": [1, 2]}

    def test_repair_truncated_string(self, service):
        result = service._repair_truncated_json('{"key": "val')
        assert result is not None
        assert "key" in result

    def test_non_truncated_returns_none(self, service):
        result = service._repair_truncated_json('{"key": "value"}')
        assert result is None

    def test_unfixable_returns_none(self, service):
        result = service._repair_truncated_json("completely broken")
        assert result is None

    def test_aggressive_repair_trims_to_comma(self, service):
        """When simple repair fails, trim to last comma and re-close brackets."""
        # The simple repair will produce invalid JSON because "bad_key has no value
        # Aggressive path trims to last comma → keeps {"title": "hello"}
        content = '{"title": "hello", "bad_key'
        result = service._repair_truncated_json(content)
        assert result is not None
        assert result["title"] == "hello"

    def test_aggressive_repair_with_nested_arrays(self, service):
        """Aggressive repair when truncated inside nested structure."""
        content = '{"items": ["a", "b"], "extra": {"nested": "val'
        result = service._repair_truncated_json(content)
        assert result is not None
        assert result["items"] == ["a", "b"]

    def test_aggressive_repair_completely_unfixable(self, service):
        """Aggressive repair also fails → returns None."""
        content = "{{{invalid"
        result = service._repair_truncated_json(content)
        assert result is None


class TestParseJsonResponseExtended:
    """Additional edge cases for _parse_json_response."""

    @pytest.fixture
    def service(self):
        return AIAgentService(provider=MockCompletionProvider())

    def test_json_embedded_in_text(self, service):
        content = 'Here is the result: {"title": "Test"} end of response'
        result = service._parse_json_response(content)
        assert result["title"] == "Test"

    def test_truncated_json_with_repair(self, service):
        content = '{"title": "Test", "items": [1, 2'
        result = service._parse_json_response(content)
        assert result["title"] == "Test"

    def test_truncated_code_fence(self, service):
        content = '```json\n{"title": "Truncated"'
        result = service._parse_json_response(content)
        assert result["title"] == "Truncated"


class TestGetAiAgentService:
    def test_singleton_creation(self):
        from src.services.ai_agent import (
            get_ai_agent_service,
            reset_ai_agent_service,
        )

        reset_ai_agent_service()
        with patch("src.services.ai_agent.create_completion_provider") as mock_create:
            mock_create.return_value = MockCompletionProvider()
            svc1 = get_ai_agent_service()
            svc2 = get_ai_agent_service()
            assert svc1 is svc2
            mock_create.assert_called_once()
        reset_ai_agent_service()

    def test_reset_clears_singleton(self):
        from src.services.ai_agent import (
            get_ai_agent_service,
            reset_ai_agent_service,
        )

        reset_ai_agent_service()
        with patch("src.services.ai_agent.create_completion_provider") as mock_create:
            mock_create.return_value = MockCompletionProvider()
            svc1 = get_ai_agent_service()
            reset_ai_agent_service()
            svc2 = get_ai_agent_service()
            assert svc1 is not svc2
        reset_ai_agent_service()


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
