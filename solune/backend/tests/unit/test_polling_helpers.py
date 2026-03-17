"""Tests for copilot polling helpers (src/services/copilot_polling/helpers.py).

Covers:
- is_sub_issue(): title pattern matching, label-based detection, edge cases
"""

from types import SimpleNamespace

from src.services.copilot_polling.helpers import is_sub_issue


class TestIsSubIssue:
    """Tests for sub-issue detection via title pattern and labels."""

    def test_title_with_agent_prefix(self):
        """Title starting with [agent-name] is a sub-issue."""
        task = SimpleNamespace(title="[copilot-swe] Implement feature X", labels=[])
        assert is_sub_issue(task) is True

    def test_title_with_bracket_prefix_and_space(self):
        """Bracket prefix followed by a space matches the pattern."""
        task = SimpleNamespace(title="[speckit.plan] Design architecture", labels=[])
        assert is_sub_issue(task) is True

    def test_title_without_bracket_prefix(self):
        """Regular title without [agent] prefix is not a sub-issue."""
        task = SimpleNamespace(title="Fix the login page", labels=[])
        assert is_sub_issue(task) is False

    def test_label_sub_issue_dict_format(self):
        """Label dict with name='sub-issue' triggers detection."""
        task = SimpleNamespace(title="Normal title", labels=[{"name": "sub-issue"}])
        assert is_sub_issue(task) is True

    def test_label_sub_issue_string_format(self):
        """String label 'sub-issue' triggers detection."""
        task = SimpleNamespace(title="Normal title", labels=["sub-issue"])
        assert is_sub_issue(task) is True

    def test_label_other_labels_only(self):
        """Other labels without 'sub-issue' do not trigger."""
        task = SimpleNamespace(
            title="Normal title", labels=[{"name": "bug"}, {"name": "enhancement"}]
        )
        assert is_sub_issue(task) is False

    def test_no_labels_attribute(self):
        """Task with no labels attribute defaults gracefully."""
        task = SimpleNamespace(title="Normal title")
        assert is_sub_issue(task) is False

    def test_none_labels(self):
        """None labels are handled gracefully."""
        task = SimpleNamespace(title="Normal title", labels=None)
        assert is_sub_issue(task) is False

    def test_empty_title(self):
        """Empty title is not a sub-issue."""
        task = SimpleNamespace(title="", labels=[])
        assert is_sub_issue(task) is False

    def test_none_title(self):
        """None title is handled gracefully."""
        task = SimpleNamespace(title=None, labels=[])
        assert is_sub_issue(task) is False

    def test_no_title_attribute(self):
        """Task with no title attribute defaults gracefully."""
        task = SimpleNamespace(labels=[])
        assert is_sub_issue(task) is False

    def test_bracket_in_middle_of_title(self):
        """Brackets in the middle of title do not match (must be prefix)."""
        task = SimpleNamespace(title="Fix [agent] issue", labels=[])
        assert is_sub_issue(task) is False

    def test_both_title_and_label_match(self):
        """Both title pattern and label match — still returns True."""
        task = SimpleNamespace(title="[copilot-swe] Fix it", labels=[{"name": "sub-issue"}])
        assert is_sub_issue(task) is True
