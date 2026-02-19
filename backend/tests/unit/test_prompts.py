"""Unit tests for prompt template modules."""

from src.prompts.issue_generation import (
    FEATURE_REQUEST_DETECTION_PROMPT,
    ISSUE_GENERATION_SYSTEM_PROMPT,
    PREDEFINED_LABELS,
    create_feature_request_detection_prompt,
    create_issue_generation_prompt,
)
from src.prompts.task_generation import (
    STATUS_CHANGE_SYSTEM_PROMPT,
    TASK_GENERATION_SYSTEM_PROMPT,
    TASK_GENERATION_USER_PROMPT_TEMPLATE,
    create_status_change_prompt,
    create_task_generation_prompt,
)


class TestIssueGenerationPrompts:
    """Tests for issue generation prompt templates."""

    def test_predefined_labels_contains_ai_generated(self):
        """Should always include ai-generated label."""
        assert "ai-generated" in PREDEFINED_LABELS

    def test_predefined_labels_contains_type_labels(self):
        """Should include core type labels."""
        for label in ["feature", "bug", "enhancement", "refactor"]:
            assert label in PREDEFINED_LABELS

    def test_predefined_labels_contains_scope_labels(self):
        """Should include scope labels."""
        for label in ["frontend", "backend", "database", "api"]:
            assert label in PREDEFINED_LABELS

    def test_issue_generation_system_prompt_not_empty(self):
        """Should have a non-empty system prompt."""
        assert len(ISSUE_GENERATION_SYSTEM_PROMPT) > 100

    def test_issue_generation_system_prompt_mentions_json(self):
        """Should instruct output as JSON."""
        assert "JSON" in ISSUE_GENERATION_SYSTEM_PROMPT

    def test_create_issue_generation_prompt_returns_two_messages(self):
        """Should return system and user messages."""
        messages = create_issue_generation_prompt("Add dark mode", "MyProject")

        assert len(messages) == 2

    def test_create_issue_generation_prompt_has_system_role(self):
        """Should have system role as first message."""
        messages = create_issue_generation_prompt("Add dark mode", "MyProject")

        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == ISSUE_GENERATION_SYSTEM_PROMPT

    def test_create_issue_generation_prompt_has_user_role(self):
        """Should have user role as second message."""
        messages = create_issue_generation_prompt("Add dark mode", "MyProject")

        assert messages[1]["role"] == "user"

    def test_create_issue_generation_prompt_includes_user_input(self):
        """Should include the user's feature request in user message."""
        messages = create_issue_generation_prompt("Add dark mode toggle", "MyProject")

        assert "Add dark mode toggle" in messages[1]["content"]

    def test_create_issue_generation_prompt_includes_project_name(self):
        """Should include project name in user message."""
        messages = create_issue_generation_prompt("Add feature", "TestProject")

        assert "TestProject" in messages[1]["content"]

    def test_create_issue_generation_prompt_includes_dates(self):
        """Should include date context in user message."""
        messages = create_issue_generation_prompt("Add feature", "Proj")

        assert "Today's Date" in messages[1]["content"]
        assert "Start Date" in messages[1]["content"]

    def test_feature_request_detection_prompt_not_empty(self):
        """Should have a non-empty detection prompt."""
        assert len(FEATURE_REQUEST_DETECTION_PROMPT) > 50

    def test_create_feature_request_detection_prompt_returns_two_messages(self):
        """Should return system and user messages."""
        messages = create_feature_request_detection_prompt("I want a new button")

        assert len(messages) == 2

    def test_create_feature_request_detection_prompt_system_role(self):
        """Should use the detection system prompt."""
        messages = create_feature_request_detection_prompt("I want a new button")

        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == FEATURE_REQUEST_DETECTION_PROMPT

    def test_create_feature_request_detection_prompt_user_role(self):
        """Should include user input in user message."""
        messages = create_feature_request_detection_prompt("Build a dashboard")

        assert messages[1]["role"] == "user"
        assert "Build a dashboard" in messages[1]["content"]

    def test_create_feature_request_detection_prompt_asks_for_json(self):
        """Should ask for JSON response."""
        messages = create_feature_request_detection_prompt("test")

        assert "JSON" in messages[1]["content"]


class TestTaskGenerationPrompts:
    """Tests for task generation prompt templates."""

    def test_task_generation_system_prompt_not_empty(self):
        """Should have a non-empty system prompt."""
        assert len(TASK_GENERATION_SYSTEM_PROMPT) > 100

    def test_task_generation_system_prompt_mentions_json(self):
        """Should instruct output as JSON."""
        assert "JSON" in TASK_GENERATION_SYSTEM_PROMPT

    def test_task_generation_system_prompt_mentions_title(self):
        """Should mention title field."""
        assert "title" in TASK_GENERATION_SYSTEM_PROMPT

    def test_task_generation_system_prompt_mentions_description(self):
        """Should mention description field."""
        assert "description" in TASK_GENERATION_SYSTEM_PROMPT

    def test_status_change_system_prompt_not_empty(self):
        """Should have a non-empty status change prompt."""
        assert len(STATUS_CHANGE_SYSTEM_PROMPT) > 50

    def test_status_change_system_prompt_mentions_json(self):
        """Should instruct output as JSON."""
        assert "JSON" in STATUS_CHANGE_SYSTEM_PROMPT

    def test_user_prompt_template_has_placeholders(self):
        """Should contain format placeholders."""
        assert "{user_input}" in TASK_GENERATION_USER_PROMPT_TEMPLATE
        assert "{project_name}" in TASK_GENERATION_USER_PROMPT_TEMPLATE

    def test_create_task_generation_prompt_returns_two_messages(self):
        """Should return system and user messages."""
        messages = create_task_generation_prompt("Fix login bug", "MyProject")

        assert len(messages) == 2

    def test_create_task_generation_prompt_system_role(self):
        """Should have system role as first message."""
        messages = create_task_generation_prompt("Fix login bug", "MyProject")

        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == TASK_GENERATION_SYSTEM_PROMPT

    def test_create_task_generation_prompt_user_role_includes_input(self):
        """Should include user input and project name in user message."""
        messages = create_task_generation_prompt("Fix login bug", "TestProj")

        assert messages[1]["role"] == "user"
        assert "Fix login bug" in messages[1]["content"]
        assert "TestProj" in messages[1]["content"]

    def test_create_status_change_prompt_returns_two_messages(self):
        """Should return system and user messages."""
        messages = create_status_change_prompt(
            "Move auth task to done",
            ["auth task", "login feature"],
            ["Todo", "In Progress", "Done"],
        )

        assert len(messages) == 2

    def test_create_status_change_prompt_system_role(self):
        """Should use the status change system prompt."""
        messages = create_status_change_prompt("Move task to done", ["task1"], ["Todo", "Done"])

        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == STATUS_CHANGE_SYSTEM_PROMPT

    def test_create_status_change_prompt_includes_tasks(self):
        """Should list available tasks in user message."""
        messages = create_status_change_prompt(
            "Move auth to done",
            ["auth task", "login feature"],
            ["Todo", "Done"],
        )

        assert "auth task" in messages[1]["content"]
        assert "login feature" in messages[1]["content"]

    def test_create_status_change_prompt_includes_statuses(self):
        """Should list available statuses in user message."""
        messages = create_status_change_prompt(
            "Move task", ["task1"], ["Todo", "In Progress", "Done"]
        )

        assert "Todo" in messages[1]["content"]
        assert "In Progress" in messages[1]["content"]
        assert "Done" in messages[1]["content"]

    def test_create_status_change_prompt_includes_user_input(self):
        """Should include user request in message."""
        messages = create_status_change_prompt("Mark login as complete", ["login"], ["Done"])

        assert "Mark login as complete" in messages[1]["content"]

    def test_create_status_change_prompt_limits_tasks_to_20(self):
        """Should only include first 20 tasks."""
        many_tasks = [f"task_{i}" for i in range(30)]
        messages = create_status_change_prompt("move task", many_tasks, ["Done"])

        content = messages[1]["content"]
        assert "task_19" in content
        assert "task_20" not in content
