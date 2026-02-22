"""Unit tests for prompt construction functions.

Covers:
- create_issue_generation_prompt()
- create_feature_request_detection_prompt()
- create_task_generation_prompt()
- create_status_change_prompt()
"""

from datetime import datetime, timedelta

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
    create_status_change_prompt,
    create_task_generation_prompt,
)

# =============================================================================
# Issue generation prompt
# =============================================================================


class TestCreateIssueGenerationPrompt:
    """Tests for create_issue_generation_prompt()."""

    def test_returns_two_messages(self):
        msgs = create_issue_generation_prompt("Add dark mode", "My Project")
        assert len(msgs) == 2

    def test_system_message_first(self):
        msgs = create_issue_generation_prompt("Add dark mode", "My Project")
        assert msgs[0]["role"] == "system"
        assert msgs[0]["content"] == ISSUE_GENERATION_SYSTEM_PROMPT

    def test_user_message_contains_input_and_project(self):
        msgs = create_issue_generation_prompt("Add dark mode", "My Project")
        user_content = msgs[1]["content"]
        assert "Add dark mode" in user_content
        assert "My Project" in user_content

    def test_user_message_contains_dates(self):
        msgs = create_issue_generation_prompt("feature", "proj")
        user_content = msgs[1]["content"]
        today = datetime.now().strftime("%Y-%m-%d")
        assert today in user_content

    def test_user_message_contains_target_date(self):
        msgs = create_issue_generation_prompt("feature", "proj")
        user_content = msgs[1]["content"]
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        assert tomorrow in user_content

    def test_user_message_role(self):
        msgs = create_issue_generation_prompt("x", "y")
        assert msgs[1]["role"] == "user"


# =============================================================================
# Feature request detection prompt
# =============================================================================


class TestCreateFeatureRequestDetectionPrompt:
    """Tests for create_feature_request_detection_prompt()."""

    def test_returns_two_messages(self):
        msgs = create_feature_request_detection_prompt("I need a button")
        assert len(msgs) == 2

    def test_system_message_first(self):
        msgs = create_feature_request_detection_prompt("I need a button")
        assert msgs[0]["role"] == "system"
        assert msgs[0]["content"] == FEATURE_REQUEST_DETECTION_PROMPT

    def test_user_input_in_user_message(self):
        msgs = create_feature_request_detection_prompt("I need a button")
        assert "I need a button" in msgs[1]["content"]

    def test_user_message_role(self):
        msgs = create_feature_request_detection_prompt("anything")
        assert msgs[1]["role"] == "user"


# =============================================================================
# Task generation prompt
# =============================================================================


class TestCreateTaskGenerationPrompt:
    """Tests for create_task_generation_prompt()."""

    def test_returns_two_messages(self):
        msgs = create_task_generation_prompt("Fix login bug", "Backend")
        assert len(msgs) == 2

    def test_system_message_first(self):
        msgs = create_task_generation_prompt("Fix login bug", "Backend")
        assert msgs[0]["role"] == "system"
        assert msgs[0]["content"] == TASK_GENERATION_SYSTEM_PROMPT

    def test_user_message_contains_input_and_project(self):
        msgs = create_task_generation_prompt("Fix login bug", "Backend")
        assert "Fix login bug" in msgs[1]["content"]
        assert "Backend" in msgs[1]["content"]

    def test_user_message_role(self):
        msgs = create_task_generation_prompt("x", "y")
        assert msgs[1]["role"] == "user"


# =============================================================================
# Status change prompt
# =============================================================================


class TestCreateStatusChangePrompt:
    """Tests for create_status_change_prompt()."""

    def test_returns_two_messages(self):
        msgs = create_status_change_prompt(
            "Move login to done", ["Fix login", "Add test"], ["Todo", "Done"]
        )
        assert len(msgs) == 2

    def test_system_message_first(self):
        msgs = create_status_change_prompt("x", [], [])
        assert msgs[0]["role"] == "system"
        assert msgs[0]["content"] == STATUS_CHANGE_SYSTEM_PROMPT

    def test_user_message_contains_tasks_and_statuses(self):
        tasks = ["Fix login", "Add test"]
        statuses = ["Todo", "Done"]
        msgs = create_status_change_prompt("move login to done", tasks, statuses)
        content = msgs[1]["content"]
        assert "Fix login" in content
        assert "Add test" in content
        assert "Todo" in content
        assert "Done" in content
        assert "move login to done" in content

    def test_user_message_role(self):
        msgs = create_status_change_prompt("x", [], [])
        assert msgs[1]["role"] == "user"

    def test_truncates_long_task_list(self):
        """Tasks list is truncated at 20 items."""
        tasks = [f"Task {i}" for i in range(30)]
        msgs = create_status_change_prompt("x", tasks, ["Todo"])
        content = msgs[1]["content"]
        assert "Task 19" in content
        assert "Task 20" not in content


# =============================================================================
# Module-level constants sanity checks
# =============================================================================


class TestPredefinedLabels:
    """Verify PREDEFINED_LABELS is well-formed."""

    def test_contains_ai_generated(self):
        assert "ai-generated" in PREDEFINED_LABELS

    def test_contains_feature(self):
        assert "feature" in PREDEFINED_LABELS

    def test_all_lowercase(self):
        for label in PREDEFINED_LABELS:
            assert label == label.lower(), f"Label not lowercase: {label}"

    def test_no_duplicates(self):
        assert len(PREDEFINED_LABELS) == len(set(PREDEFINED_LABELS))
